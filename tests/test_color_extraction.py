from PIL import Image

from color_extraction import extract_dominant_color


def test_solid_color_image_returns_exact_hex():
    image = Image.new("RGB", (100, 100), (220, 20, 60))  # crimson
    result = extract_dominant_color(image)
    assert result["hex"] == "#dc143c"
    assert result["rgb"] == [220, 20, 60]


def test_returns_hex_and_rgb_keys():
    image = Image.new("RGB", (50, 50), (0, 128, 255))
    result = extract_dominant_color(image)
    assert set(result.keys()) == {"rgb", "hex"}
    assert result["hex"].startswith("#") and len(result["hex"]) == 7
