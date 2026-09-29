from io import BytesIO
from unittest.mock import patch

from PIL import Image

import color_extraction


def _fake_s3_response(image):
    buf = BytesIO()
    image.save(buf, "PNG")
    buf.seek(0)
    return {"Body": buf}


def test_handler_reads_thumbnail_when_present_and_passes_event_through():
    image = Image.new("RGB", (50, 50), (0, 255, 0))
    event = {"bucket": "b", "key": "orig.png", "thumbnail_key": "orig_thumbnail.png", "img_size": 123}

    with patch.object(color_extraction, "s3") as mock_s3:
        mock_s3.get_object.return_value = _fake_s3_response(image)
        result = color_extraction.handler(event, None)

    mock_s3.get_object.assert_called_once_with(Bucket="b", Key="orig_thumbnail.png")
    assert result["colorway"]["hex"] == "#00ff00"
    assert result["key"] == "orig.png"  # original event fields preserved
    assert result["img_size"] == 123
