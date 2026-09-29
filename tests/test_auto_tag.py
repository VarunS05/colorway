from unittest.mock import MagicMock

from auto_tag import get_tags


def test_get_tags_sorted_by_confidence_and_calls_rekognition_correctly():
    mock_client = MagicMock()
    mock_client.detect_labels.return_value = {
        "Labels": [
            {"Name": "Shoe", "Confidence": 98.234},
            {"Name": "Sneaker", "Confidence": 95.1},
            {"Name": "Footwear", "Confidence": 99.9},
        ]
    }

    tags = get_tags(mock_client, "my-bucket", "shoe.png")

    assert [t["name"] for t in tags] == ["Footwear", "Shoe", "Sneaker"]
    assert tags[0]["confidence"] == 99.9
    mock_client.detect_labels.assert_called_once_with(
        Image={"S3Object": {"Bucket": "my-bucket", "Name": "shoe.png"}},
        MaxLabels=10,
        MinConfidence=75,
    )


def test_get_tags_respects_custom_thresholds():
    mock_client = MagicMock()
    mock_client.detect_labels.return_value = {"Labels": []}

    get_tags(mock_client, "b", "k", min_confidence=90, max_labels=3)

    mock_client.detect_labels.assert_called_once_with(
        Image={"S3Object": {"Bucket": "b", "Name": "k"}}, MaxLabels=3, MinConfidence=90
    )
