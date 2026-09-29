from datetime import datetime
import boto3
from io import BytesIO
from PIL import Image, ImageOps
import os
import uuid
import json

# AWS clients
s3 = boto3.client('s3', region_name=str(os.environ['REGION_NAME']))
stepfunctions = boto3.client('stepfunctions', region_name=str(os.environ['REGION_NAME']))
dynamodb = boto3.resource(
    'dynamodb', region_name=str(os.environ['REGION_NAME']))

# Environment variables
size = int(os.environ['THUMBNAIL_SIZE'])
dbtable = str(os.environ['DYNAMODB_TABLE'])
state_machine_arn = os.environ.get('STATE_MACHINE_ARN')

# Entry point, triggered by an S3 upload event. Generates a thumbnail, then
# starts the Colorway Step Functions workflow (ExtractColor -> AutoTag ->
# StoreMetadata) with the result -- S3 can't invoke Step Functions directly,
# so this Lambda is the bridge between the upload event and the workflow.
def s3_thumbnail_generator(event, context):
    print("EVENT:::", event)
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    img_size = event['Records'][0]['s3']['object']['size']

    if key.endswith("_thumbnail.png"):
        return {'statusCode': 200, 'body': json.dumps({'message': 'Thumbnail already exists.'})}

    image = get_s3_image(bucket, key)
    thumbnail = image_to_thumbnail(image)
    thumbnail_key = new_filename(key)
    thumbnail_url = upload_to_s3(bucket, thumbnail_key, thumbnail)

    workflow_input = {
        'bucket': bucket,
        'key': key,
        'img_size': img_size,
        'thumbnail_key': thumbnail_key,
        'thumbnail_url': thumbnail_url,
    }
    stepfunctions.start_execution(
        stateMachineArn=state_machine_arn,
        input=json.dumps(workflow_input),
    )
    return {'statusCode': 200, 'body': json.dumps({'thumbnailUrl': thumbnail_url, 'workflowStarted': True})}

# Download original image from S3
def get_s3_image(bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    imagecontent = response['Body'].read()
    file = BytesIO(imagecontent)
    img = Image.open(file)
    return img

# Create thumbnail
def image_to_thumbnail(image):
    return ImageOps.fit(image, (size, size), Image.LANCZOS)

# Generate thumbnail filename
def new_filename(key):
    key_split = key.rsplit('.', 1)
    return key_split[0] + "_thumbnail.png"

# Upload thumbnail to S3 (no ACL)
def upload_to_s3(bucket, key, image):
    out_thumbnail = BytesIO()
    image.save(out_thumbnail, 'PNG')
    out_thumbnail.seek(0)

    s3.put_object(
        Body=out_thumbnail,
        Bucket=bucket,
        ContentType='image/png',
        Key=key
    )
    return '{}/{}/{}'.format(s3.meta.endpoint_url, bucket, key)


# Final step of the Colorway workflow: writes the asset's thumbnail URL,
# dominant colorway, and Rekognition tags to DynamoDB as one record.
def store_metadata(event, context):
    if event.get('skipped'):
        return {'statusCode': 200, 'body': json.dumps({'message': event.get('reason', 'Skipped.')})}

    toint = float(event.get('img_size', 0) * 0.53) / 1000
    table = dynamodb.Table(dbtable)
    item = {
        'id': str(uuid.uuid4()),
        'url': event['thumbnail_url'],
        'sourceKey': event['key'],
        'colorway': event.get('colorway', {}),
        'tags': event.get('tags', []),
        'approxReducedSize': str(toint) + ' KB',
        'createdAt': str(datetime.now()),
        'updatedAt': str(datetime.now()),
    }
    table.put_item(Item=item)
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Saved to DynamoDB', 'id': item['id']})
    }

# Fetch all thumbnail metadata from DynamoDB, optionally filtered by
# ?color=hex and/or ?tag=name query params. Filtering happens after the scan
# (fine at demo/gallery scale; a production-sized table would want a GSI on
# tags instead of a full scan).
def s3_get_thumbnail_urls(event, context):
    table = dynamodb.Table(dbtable)
    response = table.scan()
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    params = (event or {}).get('queryStringParameters') or {}
    color_filter = params.get('color')
    tag_filter = params.get('tag')

    if color_filter:
        data = [item for item in data if item.get('colorway', {}).get('hex') == color_filter]
    if tag_filter:
        data = [
            item for item in data
            if any(t['name'].lower() == tag_filter.lower() for t in item.get('tags', []))
        ]

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(data)
    }

# Fetch a single thumbnail metadata item
def s3_get_item(event, context):
    table = dynamodb.Table(dbtable)
    response = table.get_item(Key={
        'id': event['pathParameters']['id']
    })
    item = response.get('Item', {})
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(item),
        'isBase64Encoded': False,
    }

# Delete a thumbnail record from DynamoDB
def s3_delete_item(event, context):
    item_id = event['pathParameters']['id']
    table = dynamodb.Table(dbtable)
    response = table.delete_item(Key={'id': item_id})
    all_good_response = {
        "deleted": True,
        "itemDeletedId": item_id
    }
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return {
            "statusCode": 200,
            'headers': {'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(all_good_response),
        }
    else:
        return {
            "statusCode": 500,
            "body": f"An error occurred while deleting post {item_id}"
        }
