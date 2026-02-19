import json
import base64
import uuid
import boto3
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

BUCKET_NAME = "family-docs-raw"
TABLE_NAME = "DocumentMetadata"

table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        
        filename = body["filename"]
        content_type = body["contentType"]
        file_data = body["data"]
        sender = body["sender"]
        subject = body["subject"]
        received_at = body["receivedAt"]

        # Decode base64
        file_bytes = base64.b64decode(file_data)

        # Generate document ID
        document_id = str(uuid.uuid4())

        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")

        s3_key = f"year={year}/month={month}/{document_id}/{filename}"

        # Upload to S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type
        )

        # Store metadata in DynamoDB
        table.put_item(
            Item={
                "PK": f"DOC#{document_id}",
                "document_id": document_id,
                "sender_email": sender,
                "subject": subject,
                "filename": filename,
                "s3_bucket": BUCKET_NAME,
                "s3_key": s3_key,
                "content_type": content_type,
                "received_at": received_at,
                "status": "RECEIVED"
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Success"})
        }

    except Exception as e:
        print("Error:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
