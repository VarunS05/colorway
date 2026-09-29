# Colorway

A serverless design-asset pipeline: upload an image, and a Step Functions workflow of Lambdas generates a thumbnail, extracts the image's dominant colorway, and auto-tags it with Amazon Rekognition — all exposed through a REST API and a React gallery where you can filter the library by color and tag.

## Architecture

```
Browser --(PUT via presigned URL)--> S3
                                       |
                          S3 ObjectCreated event
                                       |
                                       v
                        s3_thumbnail_generator (Lambda)
                     generates thumbnail, starts Step Functions
                                       |
                                       v
                    ┌─── ColorwayStateMachine (Step Functions) ───┐
                    │  ExtractColor -> AutoTag -> StoreMetadata   │
                    │  (dominant color   (Rekognition   (writes    │
                    │   via Pillow)       DetectLabels)  to DynamoDB)│
                    └───────────────────────────────────────────┘
                                       |
                                       v
                    API Gateway (list / get / delete) <-- React gallery
```

- **Upload** — the gallery requests a presigned S3 PUT URL from the API and uploads directly to S3 (not proxied through Lambda, which has payload-size limits).
- **Thumbnail generation** — `s3_thumbnail_generator` fires on the S3 upload event, creates a thumbnail, and starts the Step Functions execution (S3 can't invoke Step Functions directly, so this Lambda bridges the two).
- **Color extraction** — `color_extraction.py` reduces the thumbnail to a small palette (PIL median-cut quantization) and returns the most frequent color as a hex/RGB "colorway".
- **Auto-tagging** — `auto_tag.py` calls Amazon Rekognition's `DetectLabels` on the original image.
- **Storage** — `StoreMetadata` writes the thumbnail URL, colorway, and tags to DynamoDB as one record.
- **API** — list (with `?color=` / `?tag=` filters), get, delete, all via API Gateway.
- **Frontend** — a small React gallery (`frontend/`) that uploads images, renders swatches/tags, and filters the library.

## Setup

```bash
pip install -r requirements-dev.txt   # backend + pytest
npm install                            # serverless-python-requirements plugin
npm run --prefix frontend install      # frontend deps
```

Update `serverless.yml`'s `custom.bucket` and `provider.region` to your own AWS account before deploying.

```bash
# locally: export AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY, or add --aws-profile <name>
serverless deploy
```

CI/CD (`.github/workflows/ci.yml`) runs the Python test suite and the frontend's Jest tests on every push/PR, and deploys on push to `main` — this needs `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` configured as repo secrets for an IAM user scoped to this stack.

## Testing

```bash
pytest tests/ -v                  # backend: 9 tests covering color extraction,
                                   # Rekognition response parsing, DynamoDB writes,
                                   # list filtering, and presigned URL generation
npm run --prefix frontend test    # frontend: Jest + React Testing Library
```

Backend tests mock AWS calls (boto3 clients are patched) so the suite runs without real AWS credentials. The frontend was verified to actually build (`vite build`) and render correctly, including its error-handling path when the API is unreachable.

## Project structure

```
handler.py            # thumbnail generation, DynamoDB CRUD, list filtering
color_extraction.py    # dominant-color extraction (Step Functions task)
auto_tag.py             # Rekognition auto-tagging (Step Functions task)
upload.py                 # presigned S3 upload URLs
serverless.yml              # infra as code: Lambdas, API Gateway, DynamoDB, Step Functions state machine, IAM
tests/                        # pytest suite (mocked AWS)
frontend/                      # React gallery (Vite + Jest)
.github/workflows/ci.yml        # test + deploy pipeline
```

## Limitations

- Color extraction runs on the thumbnail (fast, cheap) rather than the full-resolution original — fine for a dominant "colorway" swatch, not a precise color analysis.
- List filtering scans the whole DynamoDB table and filters in Python; fine at gallery scale, would need a GSI on tags/color for a large catalog.
- The Step Functions template and IAM roles were validated for correctness (pytest-verified business logic, syntactically valid CloudFormation, standard well-established resource shapes) but not deployed against a live AWS account as part of this build.
