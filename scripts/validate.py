#!/usr/bin/env python3
"""Validate OpenDispatch skill definitions."""

import json
import os
import struct
import sys
from pathlib import Path

import jsonschema
import yaml

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _load_schema(name: str) -> dict:
    """Load a JSON Schema from the schemas directory."""
    with open(SCHEMA_DIR / name) as f:
        return json.load(f)


def validate_with_schema(data, schema: dict, prefix: str) -> list[str]:
    """Validate data against a JSON Schema. Returns list of error messages."""
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in error.absolute_path)
        location = f"{path}: " if path else ""
        errors.append(f"{prefix}: {location}{error.message}")
    return errors


def validate_tags_file(tags_path: Path) -> list[str]:
    """Validate tags.yaml. Returns list of error messages."""
    prefix = str(tags_path)

    if not tags_path.exists():
        return [f"{prefix}: file not found"]

    try:
        with open(tags_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"{prefix}: invalid YAML: {e}"]

    return validate_with_schema(data, _load_schema("tags.schema.json"), prefix)


def load_allowed_tags(tags_path: Path) -> set[str]:
    """Load the set of allowed tags from tags.yaml."""
    with open(tags_path) as f:
        data = yaml.safe_load(f)
    return set(data.get("tags", []))


def validate_icon(icon_path: Path) -> list[str]:
    """Validate an icon.png file. Returns list of error messages."""
    errors: list[str] = []
    prefix = str(icon_path)

    try:
        with open(icon_path, "rb") as f:
            header = f.read(24)
    except OSError as e:
        return [f"{prefix}: could not read file: {e}"]

    if len(header) < 24:
        return [f"{prefix}: file too small to be a valid PNG"]

    if header[:8] != PNG_MAGIC:
        return [f"{prefix}: not a valid PNG (wrong magic bytes)"]

    width = struct.unpack(">I", header[16:20])[0]
    height = struct.unpack(">I", header[20:24])[0]

    if width != 256 or height != 256:
        errors.append(f"{prefix}: must be 256x256, got {width}x{height}")

    return errors


def validate_skill_yaml(
    skill_path: Path, folder_name: str, allowed_tags: set[str]
) -> list[str]:
    """Validate a single skill.yaml. Returns list of error messages."""
    prefix = str(skill_path)

    try:
        with open(skill_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"{prefix}: invalid YAML: {e}"]

    if not isinstance(data, dict):
        return [f"{prefix}: expected a mapping"]

    # JSON Schema structural validation
    errors = validate_with_schema(data, _load_schema("skill.schema.json"), prefix)

    # Cross-file: skill_id must match folder name
    skill_id = data.get("skill_id", "")
    if isinstance(skill_id, str) and skill_id.strip():
        if skill_id != folder_name:
            errors.append(
                f"{prefix}: 'skill_id' ('{skill_id}') must match folder name ('{folder_name}')"
            )

    # Cross-file: tags must exist in tags.yaml
    if "tags" in data and isinstance(data["tags"], list):
        for i, tag in enumerate(data["tags"]):
            if isinstance(tag, str) and tag not in allowed_tags:
                errors.append(f"{prefix}: tags[{i}] ('{tag}') is not in tags.yaml")

    return errors


def main() -> int:
    """Main entry point. Returns 0 on success, 1 on validation errors."""
    repo_root = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
    tags_path = repo_root / "tags.yaml"
    skills_dir = repo_root / "skills"

    all_errors: list[str] = []

    # 1. Validate tags.yaml
    all_errors.extend(validate_tags_file(tags_path))

    # Load allowed tags for cross-referencing
    allowed_tags: set[str] = set()
    if tags_path.exists() and not all_errors:
        allowed_tags = load_allowed_tags(tags_path)

    # 2. Validate each skill
    skill_ids: dict[str, str] = {}  # skill_id -> folder path

    if skills_dir.is_dir():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                continue

            skill_yaml = skill_dir / "skill.yaml"
            if not skill_yaml.exists():
                all_errors.append(f"{skill_dir}: missing skill.yaml")
                continue

            folder_name = skill_dir.name
            all_errors.extend(
                validate_skill_yaml(skill_yaml, folder_name, allowed_tags)
            )

            # Duplicate skill_id check
            try:
                with open(skill_yaml) as f:
                    data = yaml.safe_load(f)
                if isinstance(data, dict) and "skill_id" in data:
                    sid = data["skill_id"]
                    if sid in skill_ids:
                        all_errors.append(
                            f"{skill_yaml}: duplicate skill_id '{sid}' "
                            f"(also in {skill_ids[sid]})"
                        )
                    else:
                        skill_ids[sid] = str(skill_yaml)
            except Exception:
                pass  # YAML errors already reported above

            # 3. Validate icon if present
            icon_path = skill_dir / "icon.png"
            if icon_path.exists():
                all_errors.extend(validate_icon(icon_path))

    # Output errors as GitHub Actions annotations
    for error in all_errors:
        colon_idx = error.find(": ", 1)
        file_path = error[:colon_idx] if colon_idx > 0 else ""
        print(f"::error file={file_path}::{error}")

    if all_errors:
        print(f"\n{len(all_errors)} validation error(s) found.")
        return 1

    print("All validations passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
