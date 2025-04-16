from pyspark.sql.types import StructType, StructField, StringType, IntegerType

pointer_schema = StructType([
    StructField("file_name", StringType(), False),
    StructField("file_path", StringType(), False)
])

session_schema = StructType([
    StructField("uuid", StringType(), False),
    StructField("status", StringType(), False),
    StructField("client_uuid", StringType(), False),
    StructField("specialist_uuid", StringType(), False)
])

employee_schema = StructType([
    StructField("uuid", StringType(), False),
    StructField("first_name", StringType(), False),
    StructField("last_name", StringType(), False),
    StructField("email", StringType(), False),
    StructField("role_uuid", StringType(), False)
])

client_schema = StructType([
    StructField("uuid", StringType(), False),
    StructField("client_name", StringType(), False),
    StructField("industry", StringType(), False),
    StructField("crm_account_id", IntegerType(), False)
])