"""Issues presigned S3 PUT URLs so the React gallery can upload images
directly to S3 from the browser, instead of proxying image bytes through
API Gateway/Lambda (which has a 10MB payload limit and adds needless cost).
The browser PUTs directly to S3 using the URL this returns; the existing S3
ObjectCreated trigger then kicks off the Colorway pipeline as normal.
"""
import json
import os
import uuid

import boto3

s3 = boto3.client('s3', region_name=str(os.environ['REGION_NAME']))
bucket = os.environ['UPLOAD_BUCKET']


def get_upload_url(event, context):
    params = (event or {}).get('queryStringParameters') or {}
    filename = params.get('filename', 'upload.png')
    content_type = params.get('contentType', 'image/png')

    extension = filename.rsplit('.', 1)[-1] if '.' in filename else 'png'
    key = f"uploads/{uuid.uuid4()}.{extension}"

    upload_url = s3.generate_presigned_url(
        'put_object',
        Params={'Bucket': bucket, 'Key': key, 'ContentType': content_type},
        ExpiresIn=300,
    )

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'uploadUrl': upload_url, 'key': key}),
    }
