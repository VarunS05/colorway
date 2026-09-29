import json
from unittest.mock import MagicMock, patch

import handler


def test_new_filename_appends_thumbnail_suffix():
    assert handler.new_filename("photos/shoe.png") == "photos/shoe_thumbnail.png"


def test_store_metadata_writes_item_with_colorway_and_tags():
    event = {
        "bucket": "b",
        "key": "shoe.png",
        "thumbnail_url": "https://s3/b/shoe_thumbnail.png",
        "img_size": 1000,
        "colorway": {"hex": "#dc143c", "rgb": [220, 20, 60]},
        "tags": [{"name": "Shoe", "confidence": 98.2}],
    }

    with patch.object(handler, "dynamodb") as mock_dynamodb:
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        result = handler.store_metadata(event, None)

        assert result["statusCode"] == 200
        put_call = mock_table.put_item.call_args.kwargs["Item"]
        assert put_call["colorway"] == event["colorway"]
        assert put_call["tags"] == event["tags"]
        assert put_call["url"] == event["thumbnail_url"]


def test_store_metadata_skips_when_thumbnail_already_existed():
    event = {"bucket": "b", "key": "k", "skipped": True, "reason": "Thumbnail already exists."}

    with patch.object(handler, "dynamodb") as mock_dynamodb:
        result = handler.store_metadata(event, None)
        mock_dynamodb.Table.return_value.put_item.assert_not_called()
        assert json.loads(result["body"])["message"] == "Thumbnail already exists."


def test_list_filters_by_color_and_tag():
    items = [
        {"id": "1", "colorway": {"hex": "#111111"}, "tags": [{"name": "Shoe"}]},
        {"id": "2", "colorway": {"hex": "#222222"}, "tags": [{"name": "Bag"}]},
    ]
    with patch.object(handler, "dynamodb") as mock_dynamodb:
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": items}
        mock_dynamodb.Table.return_value = mock_table

        result = handler.s3_get_thumbnail_urls({"queryStringParameters": {"color": "#111111"}}, None)
        body = json.loads(result["body"])
        assert [item["id"] for item in body] == ["1"]

        result = handler.s3_get_thumbnail_urls({"queryStringParameters": {"tag": "bag"}}, None)
        body = json.loads(result["body"])
        assert [item["id"] for item in body] == ["2"]
