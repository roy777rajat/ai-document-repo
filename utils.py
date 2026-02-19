import json
import boto3
import redis
import struct
from redis.commands.search.query import Query
from urllib.parse import unquote_plus
from botocore.exceptions import NoCredentialsError

# Configuration
REGION = "eu-west-1"
REDIS_INDEX_NAME = "doc_index"
VECTOR_DIM = 1024
KEY_PREFIX = "doc:"
BUCKET_NAME = "family-docs-raw"
TABLE_NAME = "DocumentMetadata"
MODEL_ID = "amazon.titan-embed-text-v2:0"

# AWS Clients
s3 = boto3.client("s3", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
bedrock = boto3.client("bedrock-runtime", region_name=REGION)
secretsmanager = boto3.client("secretsmanager", region_name=REGION)

# Secrets
def get_secrets(secret_name):
    return json.loads(
        secretsmanager.get_secret_value(SecretId=secret_name)["SecretString"]
    )

secret = get_secrets("dev/python/api")

# Redis Connection
redis_conn = redis.Redis(
    host=secret["REDIS_HOST"],
    port=secret["REDIS_PORT"],
    username=secret["REDIS_USER"],
    password=secret["REDIS_PASS"],
    decode_responses=False
)

# Embedding function
def get_embedding(text):
    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": text})
    )
    embedding = json.loads(response["body"].read())["embedding"]
    return embedding

# Float list to bytes
def to_float32_bytes(vector):
    return struct.pack(f"{len(vector)}f", *vector)

# Search function
def search_documents(query, top_k=5):
    query_embedding = get_embedding(query)
    query_vec_bytes = to_float32_bytes(query_embedding)
    
    q = (
        Query(f"*=>[KNN {top_k} @embedding $vec]")
        .return_fields("document_id", "filename", "text")
        .dialect(2)
    )
    result = redis_conn.ft(REDIS_INDEX_NAME).search(q, query_params={"vec": query_vec_bytes})
    
    results = []
    for doc in result.docs:
        results.append({
            "document_id": doc.document_id,
            "filename": doc.filename,
            "text": doc.text,
            "score": doc.__dict__.get("__embedding_score", 0)
        })
    return results

# Get all document metadata
def get_all_document_metadata():
    table = dynamodb.Table(TABLE_NAME)
    response = table.scan()
    items = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    return items

# Generate pre-signed URL
def generate_presigned_url(document_id, filename):
    # First, get the s3_key from metadata
    table = dynamodb.Table(TABLE_NAME)
    response = table.get_item(Key={"PK": f"DOC#{document_id}"})
    if 'Item' not in response:
        raise ValueError(f"Document {document_id} not found")
    s3_key = response['Item']['s3_key']
    
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
        ExpiresIn=3600  # 1 hour
    )
    return url