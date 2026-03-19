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
