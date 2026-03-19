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


def _valid_skill():
    """Return a minimal valid skill dict."""
    return {
        "skill_id": "test-skill",
        "name": "Test Skill",
        "version": "1.0.0",
        "description": "A test skill",
        "author": "Test Author",
        "actions": [
            {
                "id": "test.action.run",
                "title": "Run Test",
                "examples": ["run the test"],
            }
        ],
    }


class TestValidateSkillYaml:
    def _write_and_validate(self, tmp_path, data, folder="test-skill", tags=None):
        from validate import validate_skill_yaml

        f = tmp_path / "skill.yaml"
        f.write_text(yaml.dump(data, default_flow_style=False))
        return validate_skill_yaml(f, folder, tags or set())

    def test_valid_minimal(self, tmp_path):
        assert self._write_and_validate(tmp_path, _valid_skill()) == []

    def test_missing_required_fields(self, tmp_path):
        errors = self._write_and_validate(tmp_path, {})
        for field in ("skill_id", "name", "version", "description", "author", "actions"):
            assert any(field in e for e in errors), f"Expected error for '{field}'"

    def test_skill_id_regex_too_short(self, tmp_path):
        data = _valid_skill()
        data["skill_id"] = "ab"
        errors = self._write_and_validate(tmp_path, data, folder="ab")
        assert any("must match" in e for e in errors)

    def test_skill_id_folder_mismatch(self, tmp_path):
        errors = self._write_and_validate(tmp_path, _valid_skill(), folder="wrong")
        assert any("must match folder name" in e for e in errors)

    def test_version_not_semver(self, tmp_path):
        data = _valid_skill()
        data["version"] = "1.0"
        errors = self._write_and_validate(tmp_path, data)
        assert any("semver" in e for e in errors)

    def test_tags_checked_against_allowed(self, tmp_path):
        data = _valid_skill()
        data["tags"] = ["valid-tag", "bad-tag"]
        errors = self._write_and_validate(tmp_path, data, tags={"valid-tag"})
        assert any("bad-tag" in e and "not in tags.yaml" in e for e in errors)
        assert not any("valid-tag" in e and "not in tags.yaml" in e for e in errors)

    def test_bridge_shortcut_requires_share_url(self, tmp_path):
        data = _valid_skill()
        data["bridge_shortcut"] = "my-shortcut"
        errors = self._write_and_validate(tmp_path, data)
        assert any("bridge_shortcut_share_url" in e for e in errors)

    def test_bridge_shortcut_with_share_url_valid(self, tmp_path):
        data = _valid_skill()
        data["bridge_shortcut"] = "my-shortcut"
        data["bridge_shortcut_share_url"] = "https://example.com/share"
        assert self._write_and_validate(tmp_path, data) == []

    def test_languages_must_be_string_array(self, tmp_path):
        data = _valid_skill()
        data["languages"] = ["en", 42]
        errors = self._write_and_validate(tmp_path, data)
        assert any("must be a string" in e for e in errors)

    def test_invalid_yaml(self, tmp_path):
        from validate import validate_skill_yaml

        f = tmp_path / "skill.yaml"
        f.write_text(":\n  bad: yaml: here:")
        errors = validate_skill_yaml(f, "test", set())
        assert len(errors) >= 1


class TestValidateAction:
    def test_valid_minimal(self):
        from validate import validate_action

        action = {"id": "test.action.run", "title": "Run", "examples": ["run it"]}
        assert validate_action("test", 0, action) == []

    def test_missing_required_fields(self):
        from validate import validate_action

        errors = validate_action("test", 0, {})
        assert any("'id'" in e for e in errors)
        assert any("'title'" in e for e in errors)
        assert any("'examples'" in e for e in errors)

    def test_id_must_have_dot_segments(self):
        from validate import validate_action

        action = {"id": "nodots", "title": "Run", "examples": ["run"]}
        errors = validate_action("test", 0, action)
        assert any("must match" in e for e in errors)

    def test_id_uppercase_rejected(self):
        from validate import validate_action

        action = {"id": "Test.Action.Run", "title": "Run", "examples": ["run"]}
        errors = validate_action("test", 0, action)
        assert any("must match" in e for e in errors)

    def test_confirmation_invalid_value(self):
        from validate import validate_action

        action = {"id": "t.a.r", "title": "R", "examples": ["r"], "confirmation": "bad"}
        errors = validate_action("test", 0, action)
        assert any("confirmation" in e for e in errors)

    def test_confirmation_valid_values(self):
        from validate import validate_action

        for val in ("required", "none", "destructive_only"):
            action = {"id": "t.a.r", "title": "R", "examples": ["r"], "confirmation": val}
            assert validate_action("test", 0, action) == []

    def test_empty_examples_rejected(self):
        from validate import validate_action

        action = {"id": "t.a.r", "title": "R", "examples": []}
        errors = validate_action("test", 0, action)
        assert any("non-empty" in e for e in errors)

    def test_negative_examples_validated(self):
        from validate import validate_action

        action = {"id": "t.a.r", "title": "R", "examples": ["r"], "negative_examples": [123]}
        errors = validate_action("test", 0, action)
        assert any("must be a string" in e for e in errors)

    def test_shortcut_arguments_must_be_object(self):
        from validate import validate_action

        action = {"id": "t.a.r", "title": "R", "examples": ["r"], "shortcut_arguments": "bad"}
        errors = validate_action("test", 0, action)
        assert any("must be an object" in e for e in errors)

    def test_parameters_validated(self):
        from validate import validate_action

        action = {
            "id": "t.a.r",
            "title": "R",
            "examples": ["r"],
            "parameters": [{"name": "p", "type": "string", "typo_field": "x"}],
        }
        errors = validate_action("test", 0, action)
        assert any("unknown" in e for e in errors)


class TestValidateParameter:
    def test_valid_minimal(self):
        from validate import validate_parameter

        assert validate_parameter("ctx", 0, {"name": "p", "type": "string"}) == []

    def test_valid_all_fields(self):
        from validate import validate_parameter

        param = {"name": "p", "type": "string", "description": "desc", "required": False}
        assert validate_parameter("ctx", 0, param) == []

    def test_missing_name(self):
        from validate import validate_parameter

        errors = validate_parameter("ctx", 0, {"type": "string"})
        assert any("'name'" in e for e in errors)

    def test_missing_type(self):
        from validate import validate_parameter

        errors = validate_parameter("ctx", 0, {"name": "p"})
        assert any("'type'" in e for e in errors)

    def test_unknown_keys_rejected(self):
        from validate import validate_parameter

        errors = validate_parameter("ctx", 0, {"name": "p", "type": "s", "oops": 1})
        assert any("unknown" in e for e in errors)

    def test_required_must_be_bool(self):
        from validate import validate_parameter

        errors = validate_parameter("ctx", 0, {"name": "p", "type": "s", "required": "yes"})
        assert any("boolean" in e for e in errors)
