from fastapi import FastAPI, HTTPException, UploadFile, File
from confluent_kafka import Producer
from typing import Dict
import json
import os
from minio import Minio

app = FastAPI()


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
producer_conf = {'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS}
producer = Producer(producer_conf)


def send_to_kafka(topic: str, data: Dict):
    try:
        producer.produce(topic, json.dumps(data).encode('utf-8'))
        producer.flush()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kafka error: {str(e)}")



MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "storage:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "password")
UPLOADS_BUCKET_NAME = os.getenv("UPLOADS_BUCKET_NAME", "uploads")
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)


def ensure_bucket_exists():
    if not minio_client.bucket_exists(UPLOADS_BUCKET_NAME):
        try:
            minio_client.make_bucket(UPLOADS_BUCKET_NAME)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Bucket creation error: {str(e)}")


def upload_file_to_minio(folder: str, file_name: str, file: UploadFile) -> str:
    ensure_bucket_exists()
    try:
        file.file.seek(0, 2)
        file_length = file.file.tell()
        file.file.seek(0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")

    object_name = f"{folder}/{file_name}"
    try:
        minio_client.put_object(
            UPLOADS_BUCKET_NAME,
            object_name,
            file.file,
            file_length,
            content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MinIO upload error: {str(e)}")

    return object_name



@app.post("/upload/file/{file_name}")
async def upload_file(file_name: str, file: UploadFile = File(...)):
    file_name_lower = file_name.lower()
    routing = None
    if "sessions" in file_name_lower:
        routing = {"folder": "sessions", "topic": "session_topic"}
    elif "employee" in file_name_lower:
        routing = {"folder": "employee_files", "topic": "employee_topic"}
    elif "client" in file_name_lower:
        routing = {"folder": "client_files", "topic": "client_topic"}
    else:
        raise HTTPException(status_code=400, detail="File name does not contain a valid type identifier.")

    object_name = upload_file_to_minio(routing["folder"], file_name, file)
    file_pointer = f"{UPLOADS_BUCKET_NAME}/{object_name}"

    kafka_payload = {"file_name": file_name, "file_path": file_pointer}
    send_to_kafka(routing["topic"], kafka_payload)

    return {"status": "sent to Kafka", "file_path": file_pointer}