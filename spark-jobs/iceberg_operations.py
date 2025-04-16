import time
from pyspark.sql.functions import col

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