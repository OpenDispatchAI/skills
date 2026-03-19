import struct
from pathlib import Path

import pytest
import yaml


class TestValidateTagsFile:
    def test_valid(self, tmp_path):
        from validate import validate_tags_file

        f = tmp_path / "tags.yaml"
        f.write_text(yaml.dump({"tags": ["smart-home", "lighting"]}))
        assert validate_tags_file(f) == []

    def test_missing_file(self, tmp_path):
        from validate import validate_tags_file

        f = tmp_path / "tags.yaml"
        errors = validate_tags_file(f)
        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_invalid_yaml(self, tmp_path):
        from validate import validate_tags_file

        f = tmp_path / "tags.yaml"
        f.write_text(":\n  - :\n    - : :")
        errors = validate_tags_file(f)
        assert len(errors) >= 1

    def test_missing_tags_key(self, tmp_path):
        from validate import validate_tags_file

        f = tmp_path / "tags.yaml"
        f.write_text(yaml.dump({"categories": ["a"]}))
        errors = validate_tags_file(f)
        assert any("missing 'tags'" in e for e in errors)

    def test_tags_not_array(self, tmp_path):
        from validate import validate_tags_file

        f = tmp_path / "tags.yaml"
        f.write_text(yaml.dump({"tags": "not-array"}))
        errors = validate_tags_file(f)
        assert any("must be an array" in e for e in errors)

    def test_non_string_tag(self, tmp_path):
        from validate import validate_tags_file

        f = tmp_path / "tags.yaml"
        f.write_text(yaml.dump({"tags": ["ok", 123]}))
        errors = validate_tags_file(f)
        assert any("must be a string" in e for e in errors)


class TestLoadAllowedTags:
    def test_loads_tags(self, tmp_path):
        from validate import load_allowed_tags

        f = tmp_path / "tags.yaml"
        f.write_text(yaml.dump({"tags": ["a", "b"]}))
        assert load_allowed_tags(f) == {"a", "b"}


def _make_png(width=256, height=256):
    """Create minimal PNG bytes with given dimensions."""
    magic = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">II", width, height) + b"\x08\x02\x00\x00\x00"
    ihdr_length = struct.pack(">I", len(ihdr_data))
    ihdr_type = b"IHDR"
    ihdr_crc = b"\x00\x00\x00\x00"
    return magic + ihdr_length + ihdr_type + ihdr_data + ihdr_crc


class TestValidateIcon:
    def test_valid_png(self, tmp_path):
        from validate import validate_icon

        icon = tmp_path / "icon.png"
        icon.write_bytes(_make_png())
        assert validate_icon(icon) == []

    def test_wrong_magic_bytes(self, tmp_path):
        from validate import validate_icon

        icon = tmp_path / "icon.png"
        icon.write_bytes(b"\x00" * 24)
        errors = validate_icon(icon)
        assert any("magic bytes" in e for e in errors)

    def test_wrong_dimensions(self, tmp_path):
        from validate import validate_icon

        icon = tmp_path / "icon.png"
        icon.write_bytes(_make_png(128, 128))
        errors = validate_icon(icon)
        assert any("256x256" in e for e in errors)

    def test_file_too_small(self, tmp_path):
        from validate import validate_icon

        icon = tmp_path / "icon.png"
        icon.write_bytes(b"\x89PNG")
        errors = validate_icon(icon)
        assert any("too small" in e for e in errors)
