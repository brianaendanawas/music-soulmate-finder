import os
import boto3

# Reused across invocations (good for Lambda performance)
dynamodb = boto3.resource("dynamodb")

def get_profiles_table():
    table_name = os.getenv("TABLE_NAME")
    if not table_name:
        raise ValueError("Missing TABLE_NAME environment variable")
    return dynamodb.Table(table_name)
