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


def validate_icon(icon_path: Path) -> list[str]:
    """Validate an icon.png file. Returns list of error messages."""
    errors: list[str] = []
    prefix = str(icon_path)

    try:
        with open(icon_path, "rb") as f:
            header = f.read(24)
    except OSError as e:
        errors.append(f"{prefix}: could not read file: {e}")
        return errors

    if len(header) < 24:
        errors.append(f"{prefix}: file too small to be a valid PNG")
        return errors

    if header[:8] != PNG_MAGIC:
        errors.append(f"{prefix}: not a valid PNG (wrong magic bytes)")
        return errors

    width = struct.unpack(">I", header[16:20])[0]
    height = struct.unpack(">I", header[20:24])[0]

    if width != 256 or height != 256:
        errors.append(f"{prefix}: must be 256x256, got {width}x{height}")

    return errors


def validate_skill_yaml(
    skill_path: Path, folder_name: str, allowed_tags: set[str]
) -> list[str]:
    """Validate a single skill.yaml. Returns list of error messages."""
    errors: list[str] = []
    prefix = str(skill_path)

    try:
        with open(skill_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"{prefix}: invalid YAML: {e}")
        return errors

    if not isinstance(data, dict):
        errors.append(f"{prefix}: expected a mapping")
        return errors

    # Required non-empty string fields
    for field in ("skill_id", "name", "version", "description", "author"):
        if field not in data:
            errors.append(f"{prefix}: missing required field '{field}'")
        elif not isinstance(data[field], str) or not data[field].strip():
            errors.append(f"{prefix}: '{field}' must be a non-empty string")

    # skill_id regex + folder match
    skill_id = data.get("skill_id", "")
    if isinstance(skill_id, str) and skill_id.strip():
        if not SKILL_ID_RE.match(skill_id):
            errors.append(f"{prefix}: 'skill_id' must match {SKILL_ID_RE.pattern}")
        if skill_id != folder_name:
            errors.append(
                f"{prefix}: 'skill_id' ('{skill_id}') must match folder name ('{folder_name}')"
            )

    # version semver
    version = data.get("version", "")
    if isinstance(version, str) and version.strip():
        if not SEMVER_RE.match(version):
            errors.append(f"{prefix}: 'version' must be semver X.Y.Z")

    # Optional string fields
    if "author_url" in data and not isinstance(data["author_url"], str):
        errors.append(f"{prefix}: 'author_url' must be a string")

    # tags
    if "tags" in data:
        if not isinstance(data["tags"], list):
            errors.append(f"{prefix}: 'tags' must be an array")
        else:
            for i, tag in enumerate(data["tags"]):
                if not isinstance(tag, str):
                    errors.append(f"{prefix}: tags[{i}] must be a string")
                elif tag not in allowed_tags:
                    errors.append(f"{prefix}: tags[{i}] ('{tag}') is not in tags.yaml")

    # languages
    if "languages" in data:
        if not isinstance(data["languages"], list):
            errors.append(f"{prefix}: 'languages' must be an array")
        else:
            for i, lang in enumerate(data["languages"]):
                if not isinstance(lang, str):
                    errors.append(f"{prefix}: languages[{i}] must be a string")

    # bridge_shortcut
    if "bridge_shortcut" in data:
        if not isinstance(data["bridge_shortcut"], str):
            errors.append(f"{prefix}: 'bridge_shortcut' must be a string")
        if "bridge_shortcut_share_url" not in data:
            errors.append(
                f"{prefix}: 'bridge_shortcut_share_url' is required when 'bridge_shortcut' is set"
            )

    if "bridge_shortcut_share_url" in data:
        if not isinstance(data["bridge_shortcut_share_url"], str):
            errors.append(f"{prefix}: 'bridge_shortcut_share_url' must be a string")

    # actions
    if "actions" not in data:
        errors.append(f"{prefix}: missing required field 'actions'")
    elif not isinstance(data["actions"], list) or len(data["actions"]) == 0:
        errors.append(f"{prefix}: 'actions' must be a non-empty array")
    else:
        for i, action in enumerate(data["actions"]):
            errors.extend(validate_action(prefix, i, action))

    return errors


def validate_action(prefix: str, index: int, action: Any) -> list[str]:
    """Validate a single action entry."""
    errors: list[str] = []
    ctx = f"{prefix}: actions[{index}]"

    if not isinstance(action, dict):
        errors.append(f"{ctx}: must be a mapping")
        return errors

    # id
    if "id" not in action:
        errors.append(f"{ctx}: missing required field 'id'")
    elif not isinstance(action["id"], str) or not action["id"]:
        errors.append(f"{ctx}: 'id' must be a non-empty string")
    elif not ACTION_ID_RE.match(action["id"]):
        errors.append(f"{ctx}: 'id' must match {ACTION_ID_RE.pattern}")

    # title
    if "title" not in action:
        errors.append(f"{ctx}: missing required field 'title'")
    elif not isinstance(action["title"], str) or not action["title"].strip():
        errors.append(f"{ctx}: 'title' must be a non-empty string")

    # description (optional)
    if "description" in action and not isinstance(action["description"], str):
        errors.append(f"{ctx}: 'description' must be a string")

    # examples
    if "examples" not in action:
        errors.append(f"{ctx}: missing required field 'examples'")
    elif not isinstance(action["examples"], list) or len(action["examples"]) == 0:
        errors.append(f"{ctx}: 'examples' must be a non-empty array")
    else:
        for j, ex in enumerate(action["examples"]):
            if not isinstance(ex, str):
                errors.append(f"{ctx}: examples[{j}] must be a string")

    # negative_examples (optional)
    if "negative_examples" in action:
        if not isinstance(action["negative_examples"], list):
            errors.append(f"{ctx}: 'negative_examples' must be an array")
        else:
            for j, ex in enumerate(action["negative_examples"]):
                if not isinstance(ex, str):
                    errors.append(f"{ctx}: negative_examples[{j}] must be a string")

    # confirmation (optional)
    if "confirmation" in action:
        if action["confirmation"] not in CONFIRMATION_VALUES:
            errors.append(
                f"{ctx}: 'confirmation' must be one of {sorted(CONFIRMATION_VALUES)}"
            )

    # shortcut_arguments (optional)
    if "shortcut_arguments" in action:
        if not isinstance(action["shortcut_arguments"], dict):
            errors.append(f"{ctx}: 'shortcut_arguments' must be an object")

    # parameters (optional)
    if "parameters" in action:
        if not isinstance(action["parameters"], list):
            errors.append(f"{ctx}: 'parameters' must be an array")
        else:
            for j, param in enumerate(action["parameters"]):
                errors.extend(validate_parameter(ctx, j, param))

    return errors


def validate_parameter(ctx: str, index: int, param: Any) -> list[str]:
    """Validate a single parameter entry."""
    errors: list[str] = []
    pctx = f"{ctx}: parameters[{index}]"

    if not isinstance(param, dict):
        errors.append(f"{pctx}: must be a mapping")
        return errors

    # Unknown keys
    unknown = set(param.keys()) - ALLOWED_PARAM_KEYS
    if unknown:
        errors.append(f"{pctx}: unknown keys: {sorted(unknown)}")

    # name
    if "name" not in param:
        errors.append(f"{pctx}: missing required field 'name'")
    elif not isinstance(param["name"], str):
        errors.append(f"{pctx}: 'name' must be a string")

    # type
    if "type" not in param:
        errors.append(f"{pctx}: missing required field 'type'")
    elif not isinstance(param["type"], str):
        errors.append(f"{pctx}: 'type' must be a string")

    # description (optional)
    if "description" in param and not isinstance(param["description"], str):
        errors.append(f"{pctx}: 'description' must be a string")

    # required (optional)
    if "required" in param and not isinstance(param["required"], bool):
        errors.append(f"{pctx}: 'required' must be a boolean")

    return errors
