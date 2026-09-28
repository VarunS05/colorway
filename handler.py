from datetime import datetime
import boto3
from io import BytesIO
from PIL import Image, ImageOps
import os
import uuid
import json

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource(
    'dynamodb', region_name=str(os.environ['REGION_NAME']))

# Environment variables
size = int(os.environ['THUMBNAIL_SIZE'])
dbtable = str(os.environ['DYNAMODB_TABLE'])

# Lambda handler triggered by S3 upload
def s3_thumbnail_generator(event, context):
    try:
        print("EVENT:::", event)
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        img_size = event['Records'][0]['s3']['object']['size']

        if not key.endswith("_thumbnail.png"):
            image = get_s3_image(bucket, key)
            thumbnail = image_to_thumbnail(image)
            thumbnail_key = new_filename(key)
            url = upload_to_s3(bucket, thumbnail_key, thumbnail, img_size)

            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'thumbnailUrl': url})
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Thumbnail already exists.'})
            }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

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
def upload_to_s3(bucket, key, image, img_size):
    out_thumbnail = BytesIO()
    image.save(out_thumbnail, 'PNG')
    out_thumbnail.seek(0)

    response = s3.put_object(
        Body=out_thumbnail,
        Bucket=bucket,
        ContentType='image/png',
        Key=key
    )
    print(response)

    url = '{}/{}/{}'.format(s3.meta.endpoint_url, bucket, key)
    s3_save_thumbnail_url_to_dynamo(url_path=url, img_size=img_size)
    return url

# Save metadata to DynamoDB
def s3_save_thumbnail_url_to_dynamo(url_path, img_size):
    toint = float(img_size * 0.53) / 1000
    table = dynamodb.Table(dbtable)
    response = table.put_item(
        Item={
            'id': str(uuid.uuid4()),
            'url': str(url_path),
            'approxReducedSize': str(toint) + ' KB',
            'createdAt': str(datetime.now()),
            'updatedAt': str(datetime.now())
        }
    )
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Saved to DynamoDB'})
    }

# Fetch all thumbnail metadata from DynamoDB
def s3_get_thumbnail_urls(event, context):
    table = dynamodb.Table(dbtable)
    response = table.scan()
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
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
