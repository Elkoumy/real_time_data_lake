import time
from schemas import pointer_schema
from pyspark.sql.functions import col, from_json, current_timestamp, input_file_name, lit, concat

def run_idempotent_merge(spark, table_name, files_df):
    columns = [c for c in files_df.columns if c != "uuid"]
    update_clause = ", ".join([f"target.{c} = source.{c}" for c in columns])
    insert_columns = ", ".join([f"`{c}`" for c in files_df.columns])
    insert_values = ", ".join([f"source.{c}" for c in files_df.columns])
    merge_sql = f"""
        MERGE INTO nessie.default.{table_name} AS target
        USING {table_name}_new_data AS source
        ON target.uuid = source.uuid
        WHEN MATCHED AND source.file_name > target.file_name THEN UPDATE SET {update_clause}
        WHEN NOT MATCHED THEN INSERT ({insert_columns}) VALUES ({insert_values})
    """
    spark.sql(merge_sql)

def count_files_iceberg(spark, table_name):
    files_df = spark.read.format("iceberg").load(f"nessie.default.{table_name}.files")
    return files_df.count()


def run_iceberg_compaction(spark, table_name, file_count_threshold, file_size_threshold, min_input_files):
    current_file_count = count_files_iceberg(spark, table_name)
    if current_file_count > file_count_threshold:
        print("File count exceeds threshold. Triggering compaction...")
        compaction_sql = f"""
            CALL nessie.system.rewrite_data_files(
                table => 'nessie.default.{table_name}',
                FILE_SIZE_THRESHOLD => {file_size_threshold},
                MIN_INPUT_FILES => {min_input_files}
            )
        """
        spark.sql(compaction_sql).show(truncate=False)

def run_iceberg_orphan_files_cleanup(spark, table_name):
    older_than_timestamp = int(time.time() * 1000) - 10000
    cleanup_sql = f"""
        CALL nessie.system.remove_orphan_files(
            table => 'nessie.default.{table_name}',
            older_than => {older_than_timestamp}
        )
    """
    spark.sql(cleanup_sql).show(truncate=False)

def run_data_validation(table_name, files_df):
    files_df = files_df.filter(col("uuid").isNotNull())
    if table_name == "sessions":
        valid_statuses = ["resubmission", "approved", "declined"]
        files_df = files_df.filter(col("status").isin(valid_statuses))
    return files_df

def process_topic(spark, topic_name, schema, table_name, file_count_threshold=50, file_size_threshold=1073741824, min_input_files=2):
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", topic_name) \
        .option("startingOffsets", "earliest") \
        .load()
    pointers_df = kafka_df.select(from_json(col("value").cast("string"), pointer_schema).alias("data")).select("data.*")

    def process_batch(batch_df, batch_id):
        batch_df = batch_df.withColumn("s3_path", concat(lit("s3a://"), col("file_path")))
        s3_paths = [row.s3_path for row in batch_df.select("s3_path").collect()]
        if s3_paths:
            files_df = spark.read.schema(schema).option("multiline", "true").json(s3_paths)
            files_df = files_df.withColumn("input_path", input_file_name())
            files_df = (files_df.join(
                batch_df.select("s3_path", "file_name"), files_df.input_path == batch_df.s3_path, how="left")
                        .drop("s3_path", "input_path"))
            files_df = run_data_validation(table_name, files_df)
            files_df = files_df.dropDuplicates(["uuid"])
            files_df = files_df.withColumn("ingestion_timestamp", current_timestamp().alias("ingestion_timestamp"))
            files_df.write.mode("overwrite").saveAsTable(f"{table_name}_new_data")
            run_idempotent_merge(spark, table_name, files_df)
            run_iceberg_compaction(spark, table_name, file_count_threshold, file_size_threshold, min_input_files)
            # the below cleanup should be scheduled as a separate job
            # run_iceberg_orphan_files_cleanup(spark, table_name)

    query = pointers_df.writeStream.foreachBatch(process_batch).trigger(processingTime="0.1 seconds").start()
    return query