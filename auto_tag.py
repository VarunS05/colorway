"""Auto-tags an uploaded image using Amazon Rekognition's label detection.

Triggered as a Step Functions task after color extraction. Takes the object
directly from S3 (Rekognition reads it in-place, no download needed) and
returns a list of tags above a confidence threshold.
"""
import boto3

DEFAULT_MIN_CONFIDENCE = 75
DEFAULT_MAX_LABELS = 10


def get_tags(rekognition_client, bucket, key, min_confidence=DEFAULT_MIN_CONFIDENCE, max_labels=DEFAULT_MAX_LABELS):
    """Calls Rekognition DetectLabels and returns a simplified list of
    {"name": ..., "confidence": ...} tags, sorted by confidence.
    """
    response = rekognition_client.detect_labels(
        Image={"S3Object": {"Bucket": bucket, "Name": key}},
        MaxLabels=max_labels,
        MinConfidence=min_confidence,
    )
    tags = [
        {"name": label["Name"], "confidence": round(label["Confidence"], 1)}
        for label in response["Labels"]
    ]
    return sorted(tags, key=lambda t: t["confidence"], reverse=True)


def handler(event, context):
    """Step Functions task input: {"bucket": ..., "key": ..., "colorway": ...}.
    Passes through bucket/key/colorway and adds "tags".
    """
    rekognition = boto3.client("rekognition")
    tags = get_tags(rekognition, event["bucket"], event["key"])
    return {**event, "tags": tags}
