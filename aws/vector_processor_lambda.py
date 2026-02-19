import json
import boto3
import uuid
import traceback
import time
import redis
import struct
from urllib.parse import unquote_plus
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

# -----------------------------
# CONFIG
# -----------------------------
REGION = "eu-west-1"
REDIS_INDEX_NAME = "doc_index"
VECTOR_DIM = 1024
KEY_PREFIX = "doc:"

print("Lambda cold start initiated...")
print(f"Region: {REGION}")
print(f"Redis Index: {REDIS_INDEX_NAME}")

# -----------------------------
# AWS CLIENTS
# -----------------------------
s3 = boto3.client("s3")
textract = boto3.client("textract")
bedrock = boto3.client("bedrock-runtime")
secretsmanager = boto3.client("secretsmanager", region_name=REGION)

# -----------------------------
# SECRETS
# -----------------------------
def get_secrets(secret_name):
    return json.loads(
        secretsmanager.get_secret_value(SecretId=secret_name)["SecretString"]
    )

secret = get_secrets("dev/python/api")

# -----------------------------
# REDIS CONNECTION
# -----------------------------
redis_conn = redis.Redis(
    host=secret["REDIS_HOST"],
    port=secret["REDIS_PORT"],
    username=secret["REDIS_USER"],
    password=secret["REDIS_PASS"],
    decode_responses=False  # required for binary vectors
)

print("Redis client initialized.")

# -----------------------------
# REDIS INDEX
# -----------------------------
def ensure_redis_index():
    try:
        redis_conn.ft(REDIS_INDEX_NAME).info()
        print("Redis index already exists.")
    except Exception:
        print("Creating Redis vector index...")
        redis_conn.ft(REDIS_INDEX_NAME).create_index(
            fields=[
                TextField("document_id"),
                TextField("chunk_id"),
                TextField("filename"),
                TextField("text"),
                VectorField(
                    "embedding",
                    "FLAT",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": VECTOR_DIM,
                        "DISTANCE_METRIC": "COSINE"
                    }
                )
            ],
            definition=IndexDefinition(
                prefix=[KEY_PREFIX],
                index_type=IndexType.HASH
            )
        )
        print("Redis vector index created.")

# -----------------------------
# TEXTRACT (ASYNC)
# -----------------------------
def extract_text(bucket, key):
    print(f"Starting Textract job for {key}")

    job_id = textract.start_document_text_detection(
        DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}}
    )["JobId"]

    while True:
        result = textract.get_document_text_detection(JobId=job_id)
        status = result["JobStatus"]
        print(f"Textract status: {status}")

        if status in ["SUCCEEDED", "FAILED"]:
            break
        time.sleep(2)

    if status == "FAILED":
        raise Exception("Textract failed")

    text = ""
    for block in result["Blocks"]:
        if block["BlockType"] == "LINE":
            text += block["Text"] + "\n"

    print(f"Extracted {len(text)} characters.")
    return text

# -----------------------------
# CHUNKING
# -----------------------------
def chunk_text(text, size=1000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    print(f"Created {len(chunks)} chunks.")
    return chunks

# -----------------------------
# EMBEDDING
# -----------------------------
def get_embedding(text):
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": text})
    )
    embedding = json.loads(response["body"].read())["embedding"]
    print(f"Embedding dimension: {len(embedding)}")
    return embedding

# -----------------------------
# FLOAT LIST → BYTES (NO NUMPY)
# -----------------------------
def to_float32_bytes(vector):
    return struct.pack(f"{len(vector)}f", *vector)

# -----------------------------
# DELETE UTILITIES
# -----------------------------
def delete_vectors_by_document_id(document_id):
    pattern = f"{KEY_PREFIX}{document_id}:*"
    keys = redis_conn.keys(pattern)

    if not keys:
        print(f"No vectors found for document_id={document_id}")
        return 0

    redis_conn.delete(*keys)
    print(f"Deleted {len(keys)} chunks for document_id={document_id}")
    return len(keys)


def delete_vectors_by_doc_all():
    pattern = f"{KEY_PREFIX}*"
    keys = redis_conn.keys(pattern)

    if not keys:
        print("No vectors found in Redis.")
        return 0

    redis_conn.delete(*keys)
    print(f"Deleted ALL vectors. Count={len(keys)}")
    return len(keys)

# -----------------------------
# LAMBDA HANDLER
# -----------------------------
def lambda_handler(event, context):

    print("Lambda triggered.")
    print("Incoming event:", json.dumps(event))

    try:
        ensure_redis_index()

        # =========================
        # MANUAL TEST MODES
        # =========================
        if event.get("test_mode") == "vector_insert":
            vector_bytes = to_float32_bytes([0.1] * VECTOR_DIM)
            redis_conn.hset(
                f"{KEY_PREFIX}manual-test:1",
                mapping={
                    "document_id": "manual-test",
                    "chunk_id": "1",
                    "filename": "manual.txt",
                    "text": "Test document about finance and insurance.",
                    "embedding": vector_bytes
                }
            )
            return {"statusCode": 200, "message": "Dummy vector inserted"}

        if event.get("test_mode") == "fetch_all":
            q = Query("*").return_fields("document_id", "filename", "text").paging(0, 10)
            result = redis_conn.ft(REDIS_INDEX_NAME).search(q)
            return {"total": result.total, "docs": [d.__dict__ for d in result.docs]}

        if event.get("test_mode") == "vector_search":
            query_vec = to_float32_bytes([0.1] * VECTOR_DIM)
            q = (
                Query("*=>[KNN 3 @embedding $vec]")
                .return_fields("filename", "text", "__embedding_score")
                .dialect(2)
            )
            result = redis_conn.ft(REDIS_INDEX_NAME).search(
                q, query_params={"vec": query_vec}
            )
            return {"results": [d.__dict__ for d in result.docs]}

        if event.get("test_mode") == "delete_vector":
            document_id = event.get("document_id")
            if not document_id:
                return {"statusCode": 400, "message": "document_id is required"}
            deleted = delete_vectors_by_document_id(document_id)
            return {"statusCode": 200, "deleted_chunks": deleted}

        if event.get("test_mode") == "delete_vector_all":
            deleted = delete_vectors_by_doc_all()
            return {"statusCode": 200, "deleted_vectors": deleted}

        # =========================
        # REAL S3 EXECUTION
        # =========================
        if "Records" in event:
            for record in event["Records"]:
                bucket = record["s3"]["bucket"]["name"]
                key = unquote_plus(record["s3"]["object"]["key"])

                if not key.lower().endswith((".pdf", ".doc", ".docx", ".jpg", ".jpeg")):
                    continue

                text = extract_text(bucket, key)
                chunks = chunk_text(text)
                document_id = str(uuid.uuid4())
                filename = key.split("/")[-1]

                for i, chunk in enumerate(chunks):
                    embedding = get_embedding(chunk)
                    redis_conn.hset(
                        f"{KEY_PREFIX}{document_id}:{i}",
                        mapping={
                            "document_id": document_id,
                            "chunk_id": f"{document_id}_{i}",
                            "filename": filename,
                            "text": chunk,
                            "embedding": to_float32_bytes(embedding)
                        }
                    )

            return {"statusCode": 200}

        return {"statusCode": 400, "message": "Invalid event"}

    except Exception as e:
        print("ERROR:", str(e))
        print(traceback.format_exc())
        return {"statusCode": 500, "error": str(e)}
