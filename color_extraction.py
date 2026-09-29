"""Extracts the dominant colorway of an uploaded image.

Triggered as a Step Functions task after thumbnail generation. Downloads the
original image from S3, reduces it to a small color palette (PIL's median-cut
quantization), and picks the most frequent palette color as the "colorway" --
returned as both an RGB tuple and a hex string so the frontend gallery can
render a color swatch without re-decoding the image.
"""
import json
import os
from io import BytesIO

import boto3
from PIL import Image

s3 = boto3.client("s3")


def extract_dominant_color(image, palette_size=5, resize_to=(150, 150)):
    """image: a PIL Image. Returns {"rgb": (r, g, b), "hex": "#rrggbb"}."""
    small = image.convert("RGB").resize(resize_to)
    quantized = small.quantize(colors=palette_size, method=Image.MEDIANCUT)

    palette = quantized.getpalette()[: palette_size * 3]
    color_counts = sorted(quantized.getcolors(), reverse=True)  # [(count, palette_index), ...]
    dominant_index = color_counts[0][1]

    r, g, b = palette[dominant_index * 3: dominant_index * 3 + 3]
    return {"rgb": [r, g, b], "hex": "#{:02x}{:02x}{:02x}".format(r, g, b)}


def handler(event, context):
    """Step Functions task input: the thumbnail_generator's output. Reads the
    already-generated thumbnail (smaller/cheaper than the original) to
    determine the colorway, and passes the full event through plus "colorway".
    """
    bucket = event["bucket"]
    source_key = event.get("thumbnail_key", event["key"])

    response = s3.get_object(Bucket=bucket, Key=source_key)
    image = Image.open(BytesIO(response["Body"].read()))
    colorway = extract_dominant_color(image)

    return {**event, "colorway": colorway}
