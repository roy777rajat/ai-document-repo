import json
import boto3
import redis
import struct
import re
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

# --------------------------------------------------------
# SECRETS
# --------------------------------------------------------

def get_secrets(secret_name):

    return json.loads(
        secretsmanager.get_secret_value(
            SecretId=secret_name
        )["SecretString"]
    )

secret = get_secrets("dev/python/api")

# --------------------------------------------------------
# REDIS CONNECTION
# --------------------------------------------------------

redis_conn = redis.Redis(

    host=secret["REDIS_HOST"],

    port=secret["REDIS_PORT"],

    username=secret["REDIS_USER"],

    password=secret["REDIS_PASS"],

    decode_responses=False
)

# --------------------------------------------------------
# EMBEDDING
# --------------------------------------------------------

def get_embedding(text):

    response = bedrock.invoke_model(

        modelId=MODEL_ID,

        contentType="application/json",

        accept="application/json",

        body=json.dumps({"inputText": text})
    )

    embedding = json.loads(response["body"].read())["embedding"]

    return embedding


# --------------------------------------------------------
# FLOAT LIST → BYTES
# --------------------------------------------------------

def to_float32_bytes(vector):

    return struct.pack(f"{len(vector)}f", *vector)


# --------------------------------------------------------
# SEARCH FUNCTION (HYBRID VECTOR + KEYWORD)
# --------------------------------------------------------

def search_documents(query, top_k=5, search_mode="vector"):

    query_embedding = get_embedding(query)

    query_vec_bytes = to_float32_bytes(query_embedding)

    # ----------------------------------------------------
    # VECTOR SEARCH
    # ----------------------------------------------------

    q = (

        Query(f"*=>[KNN {top_k} @embedding $vec]")

        .return_fields(
            "document_id",
            "filename",
            "text",
            "__embedding_score"
        )

        .dialect(2)
    )

    result = redis_conn.ft(REDIS_INDEX_NAME).search(

        q,

        query_params={"vec": query_vec_bytes}
    )

    vector_results = []

    for doc in result.docs:

        filename = doc.filename
        text = doc.text
        document_id = doc.document_id

        if isinstance(filename, bytes):
            filename = filename.decode()

        if isinstance(text, bytes):
            text = text.decode()

        if isinstance(document_id, bytes):
            document_id = document_id.decode()

        score = doc.__dict__.get("__embedding_score", 0)

        vector_results.append({

            "document_id": document_id,

            "filename": filename,

            "text": text,

            "score": score
        })

    # ----------------------------------------------------
    # IDENTIFIER DETECTION
    # ----------------------------------------------------

    identifier_pattern = re.compile(r"[A-Z0-9]{6,}")

    identifier_found = identifier_pattern.search(query)

    # ----------------------------------------------------
    # IF NOT IDENTIFIER → RETURN VECTOR
    # ----------------------------------------------------

    if not identifier_found:

        if vector_results:

            return vector_results

    # ----------------------------------------------------
    # KEYWORD SEARCH (IDENTIFIERS / FALLBACK)
    # ----------------------------------------------------

    safe_query = query.replace(".", " ").replace("-", " ")

    keyword_results = []

    try:

        keyword_query = Query(

            f"@text:{safe_query}"

        ).return_fields(

            "document_id",
            "filename",
            "text"

        ).paging(0, top_k)

        result = redis_conn.ft(REDIS_INDEX_NAME).search(keyword_query)

        for doc in result.docs:

            filename = doc.filename
            text = doc.text
            document_id = doc.document_id

            if isinstance(filename, bytes):
                filename = filename.decode()

            if isinstance(text, bytes):
                text = text.decode()

            if isinstance(document_id, bytes):
                document_id = document_id.decode()

            keyword_results.append({

                "document_id": document_id,

                "filename": filename,

                "text": text,

                "score": 0
            })

    except Exception as e:

        print("Keyword fallback search failed:", str(e))

    # ----------------------------------------------------
    # RETURN BEST AVAILABLE RESULTS
    # ----------------------------------------------------

    if keyword_results:

        return keyword_results

    return vector_results


# --------------------------------------------------------
# GET ALL DOCUMENT METADATA
# --------------------------------------------------------

def get_all_document_metadata():

    table = dynamodb.Table(TABLE_NAME)

    response = table.scan()

    items = response['Items']

    while 'LastEvaluatedKey' in response:

        response = table.scan(

            ExclusiveStartKey=response['LastEvaluatedKey']
        )

        items.extend(response['Items'])

    return items


# --------------------------------------------------------
# GENERATE PRE-SIGNED URL
# --------------------------------------------------------

def generate_presigned_url(document_id, filename):

    table = dynamodb.Table(TABLE_NAME)

    response = table.get_item(

        Key={"PK": f"DOC#{document_id}"}
    )

    if 'Item' not in response:

        raise ValueError(f"Document {document_id} not found")

    s3_key = response['Item']['s3_key']

    url = s3.generate_presigned_url(

        'get_object',

        Params={

            'Bucket': BUCKET_NAME,

            'Key': s3_key
        },

        ExpiresIn=3600
    )

    return url