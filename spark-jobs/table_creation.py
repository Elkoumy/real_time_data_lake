def create_tables(spark):
    spark.sql("""
        CREATE TABLE IF NOT EXISTS nessie.default.sessions (
            uuid STRING,
            status STRING,
            client_uuid STRING,
            specialist_uuid STRING,
            file_name STRING,
            ingestion_timestamp TIMESTAMP
        ) USING iceberg
        PARTITIONED BY (days(ingestion_timestamp), status)
        TBLPROPERTIES (
            'format-version' = '2',
            'write.parquet.compression-codec' = 'zstd',
            'history.expire.max-snapshot-age-ms' = '1d',
            'gc-enabled' = 'true'
        )
    """)

    spark.sql("""
        CREATE TABLE IF NOT EXISTS nessie.default.employees (
            uuid STRING,
            first_name STRING,
            last_name STRING,
            email STRING,
            role_uuid STRING,
            file_name STRING,
            ingestion_timestamp TIMESTAMP
        ) USING iceberg
        TBLPROPERTIES (
            'format-version' = '2',
            'write.delete.parquet.compression-codec' = 'zstd',
            'history.expire.max-snapshot-age-ms' = '1d',
            'gc-enabled' = 'true'
        )
    """)

    spark.sql("""
        CREATE TABLE IF NOT EXISTS nessie.default.clients (
            uuid STRING,
            client_name STRING,
            industry STRING,
            crm_account_id INT,
            file_name STRING,
            ingestion_timestamp TIMESTAMP
        ) USING iceberg
        TBLPROPERTIES (
            'format-version' = '2',
            'write.delete.parquet.compression-codec' = 'zstd',
            'history.expire.max-snapshot-age-ms' = '1d',
            'gc-enabled' = 'true'
        )
    """)