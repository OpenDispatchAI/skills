#!/usr/bin/env python3
"""Validate OpenDispatch skill definitions."""

import os
import re
import struct
import sys
from pathlib import Path
from typing import Any

import yaml

SKILL_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{3,}$")
ACTION_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
CONFIRMATION_VALUES = {"required", "none", "destructive_only"}
ALLOWED_PARAM_KEYS = {"name", "type", "description", "required"}


def validate_tags_file(tags_path: Path) -> list[str]:
    """Validate tags.yaml structure. Returns list of error messages."""
    errors: list[str] = []
    prefix = str(tags_path)

    if not tags_path.exists():
        errors.append(f"{prefix}: file not found")
        return errors

    try:
        with open(tags_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"{prefix}: invalid YAML: {e}")
        return errors

    if not isinstance(data, dict):
        errors.append(f"{prefix}: expected a mapping, got {type(data).__name__}")
        return errors

    if "tags" not in data:
        errors.append(f"{prefix}: missing 'tags' key")
        return errors

    tags = data["tags"]
    if not isinstance(tags, list):
        errors.append(f"{prefix}: 'tags' must be an array")
        return errors

    for i, tag in enumerate(tags):
        if not isinstance(tag, str):
            errors.append(
                f"{prefix}: tags[{i}] must be a string, got {type(tag).__name__}"
            )

    return errors


def load_allowed_tags(tags_path: Path) -> set[str]:
    """Load the set of allowed tags from tags.yaml."""
    with open(tags_path) as f:
        data = yaml.safe_load(f)
    return set(data.get("tags", []))
