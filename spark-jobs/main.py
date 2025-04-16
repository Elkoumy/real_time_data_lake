from data_processing import process_topic
from spark_session import create_spark_session
from schemas import session_schema, employee_schema, client_schema
from table_creation import create_tables


if __name__ == "__main__":
    spark = create_spark_session()
    if not spark.sql("SHOW NAMESPACES IN nessie LIKE 'default'").count() > 0:
        spark.sql("CREATE NAMESPACE IF NOT EXISTS nessie.default")

    create_tables(spark)

    queries = [
        process_topic(spark, "session_topic", session_schema, "sessions", file_count_threshold=500, file_size_threshold=1073741824, min_input_files=2),
        process_topic(spark, "employee_topic", employee_schema, "employees", file_count_threshold=50, file_size_threshold=1073741824, min_input_files=2),
        process_topic(spark, "client_topic", client_schema, "clients", file_count_threshold=30, file_size_threshold=1073741824, min_input_files=2)
    ]

    for query in queries:
        query.awaitTermination()