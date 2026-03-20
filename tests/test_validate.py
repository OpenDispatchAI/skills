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
        assert any("'tags' is a required property" in e for e in errors)

    def test_tags_not_array(self, tmp_path):
        from validate import validate_tags_file

        f = tmp_path / "tags.yaml"
        f.write_text(yaml.dump({"tags": "not-array"}))
        errors = validate_tags_file(f)
        assert any("is not of type 'array'" in e for e in errors)

    def test_non_string_tag(self, tmp_path):
        from validate import validate_tags_file

        f = tmp_path / "tags.yaml"
        f.write_text(yaml.dump({"tags": ["ok", 123]}))
        errors = validate_tags_file(f)
        assert any("is not of type 'string'" in e for e in errors)


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
        assert any("does not match" in e for e in errors)

    def test_skill_id_folder_mismatch(self, tmp_path):
        errors = self._write_and_validate(tmp_path, _valid_skill(), folder="wrong")
        assert any("must match folder name" in e for e in errors)

    def test_version_not_semver(self, tmp_path):
        data = _valid_skill()
        data["version"] = "1.0"
        errors = self._write_and_validate(tmp_path, data)
        assert any("does not match" in e for e in errors)

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
        assert any("is not of type 'string'" in e for e in errors)

    def test_built_in_rejected(self, tmp_path):
        data = _valid_skill()
        data["built_in"] = True
        errors = self._write_and_validate(tmp_path, data)
        assert len(errors) > 0
        assert any("built_in" in e for e in errors)

    def test_invalid_yaml(self, tmp_path):
        from validate import validate_skill_yaml

        f = tmp_path / "skill.yaml"
        f.write_text(":\n  bad: yaml: here:")
        errors = validate_skill_yaml(f, "test", set())
        assert len(errors) >= 1

    def test_action_id_must_have_dot_segments(self, tmp_path):
        data = _valid_skill()
        data["actions"][0]["id"] = "nodots"
        errors = self._write_and_validate(tmp_path, data)
        assert any("does not match" in e for e in errors)

    def test_action_id_uppercase_rejected(self, tmp_path):
        data = _valid_skill()
        data["actions"][0]["id"] = "Test.Action.Run"
        errors = self._write_and_validate(tmp_path, data)
        assert any("does not match" in e for e in errors)

    def test_confirmation_invalid_value(self, tmp_path):
        data = _valid_skill()
        data["actions"][0]["confirmation"] = "bad"
        errors = self._write_and_validate(tmp_path, data)
        assert any("is not one of" in e for e in errors)

    def test_confirmation_valid_values(self, tmp_path):
        for val in ("required", "none", "destructive_only"):
            data = _valid_skill()
            data["actions"][0]["confirmation"] = val
            assert self._write_and_validate(tmp_path, data) == []

    def test_empty_examples_rejected(self, tmp_path):
        data = _valid_skill()
        data["actions"][0]["examples"] = []
        errors = self._write_and_validate(tmp_path, data)
        assert len(errors) > 0

    def test_parameter_unknown_keys_rejected(self, tmp_path):
        data = _valid_skill()
        data["actions"][0]["parameters"] = [
            {"name": "p", "type": "string", "typo_field": "x"}
        ]
        errors = self._write_and_validate(tmp_path, data)
        assert any("Additional properties" in e for e in errors)

    def test_parameter_required_must_be_bool(self, tmp_path):
        data = _valid_skill()
        data["actions"][0]["parameters"] = [
            {"name": "p", "type": "string", "required": "yes"}
        ]
        errors = self._write_and_validate(tmp_path, data)
        assert any("is not of type 'boolean'" in e for e in errors)


class TestMain:
    def _setup_repo(self, tmp_path):
        """Create a minimal valid repo structure in tmp_path."""
        tags = tmp_path / "tags.yaml"
        tags.write_text(yaml.dump({"tags": ["smart-home"]}))

        skill_dir = tmp_path / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "skill.yaml").write_text(
            yaml.dump(_valid_skill(), default_flow_style=False)
        )
        return tmp_path

    def test_valid_repo_passes(self, tmp_path, monkeypatch):
        from validate import main

        self._setup_repo(tmp_path)
        monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
        assert main() == 0

    def test_invalid_skill_fails(self, tmp_path, monkeypatch):
        from validate import main

        self._setup_repo(tmp_path)
        # Break the skill
        skill_yaml = tmp_path / "skills" / "test-skill" / "skill.yaml"
        skill_yaml.write_text(yaml.dump({"skill_id": "test-skill"}))
        monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
        assert main() == 1

    def test_duplicate_skill_ids(self, tmp_path, monkeypatch):
        from validate import main

        self._setup_repo(tmp_path)
        # Add second skill with same skill_id
        dup_dir = tmp_path / "skills" / "duplicate"
        dup_dir.mkdir()
        dup_skill = _valid_skill()
        dup_skill["skill_id"] = "test-skill"  # same id, different folder
        (dup_dir / "skill.yaml").write_text(
            yaml.dump(dup_skill, default_flow_style=False)
        )
        monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
        assert main() == 1

    def test_invalid_icon_fails(self, tmp_path, monkeypatch):
        from validate import main

        self._setup_repo(tmp_path)
        icon = tmp_path / "skills" / "test-skill" / "icon.png"
        icon.write_bytes(b"not a png at all, definitely not")
        monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
        assert main() == 1

    def test_valid_icon_passes(self, tmp_path, monkeypatch):
        from validate import main

        self._setup_repo(tmp_path)
        icon = tmp_path / "skills" / "test-skill" / "icon.png"
        icon.write_bytes(_make_png(256, 256))
        monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
        assert main() == 0

    def test_missing_skill_yaml(self, tmp_path, monkeypatch):
        from validate import main

        self._setup_repo(tmp_path)
        # Add a directory without skill.yaml
        (tmp_path / "skills" / "empty-skill").mkdir()
        monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
        assert main() == 1
