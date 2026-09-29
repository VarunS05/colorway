import os

# handler.py reads these at import time to configure the Lambda; set safe
# dummy values before any test imports it.
os.environ.setdefault("REGION_NAME", "us-east-1")
os.environ.setdefault("THUMBNAIL_SIZE", "128")
os.environ.setdefault("DYNAMODB_TABLE", "test-table")
os.environ.setdefault("UPLOAD_BUCKET", "test-bucket")

# boto3 needs *some* credentials to construct clients / sign presigned URLs,
# even though these tests never make a real AWS call. Fake values keep the
# suite hermetic (no dependency on the environment having real AWS secrets).
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
