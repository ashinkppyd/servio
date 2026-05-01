import json
import os

import boto3

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
QUEUE_URL = os.getenv("SQS_QUEUE_URL")

client_kwargs = {"region_name": AWS_REGION}

if AWS_ACCESS_KEY and AWS_SECRET_KEY:
    client_kwargs.update(
        {
            "aws_access_key_id": AWS_ACCESS_KEY,
            "aws_secret_access_key": AWS_SECRET_KEY,
        }
    )

sqs = boto3.client("sqs", **client_kwargs)


def send_to_sqs(data):
    if not QUEUE_URL:
        raise RuntimeError("SQS_QUEUE_URL is not configured")

    response = sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(data))
    print("SQS send_message response:", response)
    return response
