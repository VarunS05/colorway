# S3 Thumbnail Service

A serverless image-thumbnail pipeline on AWS: drop a `.png` into an S3 bucket and a Lambda function automatically generates a thumbnail, re-uploads it, and records metadata in DynamoDB. A small REST API exposes the generated thumbnails.

## How it works

1. **Upload trigger** — an S3 `ObjectCreated` event (filtered to `.png`) fires `s3_thumbnail_generator`.
2. **Resize** — the original image is downloaded, resized to a square thumbnail (`Pillow`), and uploaded back to the same bucket as `<key>_thumbnail.png`.
3. **Metadata** — the thumbnail's URL and an approximate size reduction are written to a DynamoDB table.
4. **API** — three HTTP endpoints (via API Gateway) let a client list, fetch, or delete thumbnail records.

```
S3 (upload .png) → Lambda (resize) → S3 (thumbnail) + DynamoDB (metadata)
                                            ↑
                          API Gateway → Lambda (list / get / delete)
```

## Stack

- **Runtime**: Python 3.8 on AWS Lambda
- **Infra as code**: [Serverless Framework](https://www.serverless.com/) v3
- **Storage**: S3 (images) + DynamoDB (metadata)
- **Libraries**: `boto3`, `Pillow`

## Endpoints

| Method | Path                 | Description                          |
|--------|----------------------|---------------------------------------|
| GET    | `/images/all`        | List all generated thumbnails         |
| GET    | `/images/get/{id}`   | Fetch a single thumbnail record       |
| DELETE | `/images/delete/{id}`| Delete a thumbnail record             |

## Setup

```bash
npm install                      # installs serverless-python-requirements plugin
pip install -r requirements.txt  # for local development / testing
```

Update `serverless.yml`'s `custom.bucket`, `provider.profile`, and `provider.region` to your own AWS bucket/profile before deploying.

```bash
serverless deploy
```

## Project structure

```
handler.py       # Lambda function handlers
serverless.yml    # Infrastructure definition (S3 trigger, API Gateway routes, DynamoDB table)
requirements.txt  # Python dependencies
```
