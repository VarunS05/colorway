import json
import os

os.environ.setdefault("UPLOAD_BUCKET", "test-bucket")

from upload import get_upload_url


def test_get_upload_url_returns_signed_url_and_unique_key():
    result = get_upload_url({"queryStringParameters": {"filename": "shoe.png"}}, None)
    body = json.loads(result["body"])

    assert result["statusCode"] == 200
    assert body["uploadUrl"].startswith("https://")
    assert "Signature" in body["uploadUrl"] or "X-Amz-Signature" in body["uploadUrl"]
    assert body["key"].startswith("uploads/") and body["key"].endswith(".png")


def test_get_upload_url_preserves_file_extension():
    result = get_upload_url({"queryStringParameters": {"filename": "photo.jpeg"}}, None)
    body = json.loads(result["body"])
    assert body["key"].endswith(".jpeg")


def test_get_upload_url_defaults_when_no_params():
    result = get_upload_url({}, None)
    body = json.loads(result["body"])
    assert body["key"].endswith(".png")
