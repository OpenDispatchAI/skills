# Contributing to OpenDispatch Skills

Thank you for your interest in contributing a skill to OpenDispatch! This guide walks you through the process of creating and submitting a skill definition.

## Table of Contents

- [How to Submit a Skill](#how-to-submit-a-skill)
- [Skill YAML Schema](#skill-yaml-schema)
  - [Top-Level Fields](#top-level-fields)
  - [Action Fields](#action-fields)
  - [Parameter Fields](#parameter-fields)
- [Icon Requirements](#icon-requirements)
- [Running Validation Locally](#running-validation-locally)
- [Pull Request Process](#pull-request-process)

---

## How to Submit a Skill

1. **Fork** this repository on GitHub.
2. **Create a new folder** under `skills/` whose name matches your skill ID (e.g., `skills/philips-hue/`).
3. **Add a `skill.yaml`** file inside that folder following the schema reference below.
4. **Optionally add an `icon.png`** to the same folder (see [Icon Requirements](#icon-requirements)).
5. **Open a pull request** against the `main` branch.

Your PR will be validated automatically by CI. Once it passes and is reviewed by a maintainer, it will be merged and your skill will be synced to the OpenDispatch marketplace.

---

## Skill YAML Schema

Every skill is defined by a single `skill.yaml` file. Below is the complete schema reference.

### Top-Level Fields

| Field | Required | Type | Rule |
|---|---|---|---|
| `skill_id` | Yes | string | Must match `^[a-zA-Z0-9_-]{3,}$` and must match the folder name under `skills/`. |
| `name` | Yes | string | Non-empty display name for the skill. |
| `version` | Yes | string | Semantic version in `X.Y.Z` format (e.g., `1.0.0`). |
| `description` | Yes | string | Non-empty description of what the skill does. |
| `author` | Yes | string | Non-empty author name or organization. |
| `author_url` | No | string | URL for the author's website or profile. |
| `tags` | No | array of strings | Each tag must exist in the repository's `tags.yaml` file. |
| `languages` | No | array of strings | Languages the skill supports (e.g., `["en", "nl"]`). |
| `bridge_shortcut` | No | string | Name of the Apple Shortcut used as a bridge. |
| `bridge_shortcut_share_url` | No | string | Required if `bridge_shortcut` is set. The iCloud share URL for the shortcut. |
| `actions` | Yes | array | Non-empty array of action objects (see below). |

### Action Fields

Each entry in the `actions` array describes one action the skill can perform.

| Field | Required | Type | Rule |
|---|---|---|---|
| `id` | Yes | string | Must match `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$` (dot-separated segments, e.g., `lights.turn_on`). |
| `title` | Yes | string | Non-empty human-readable title for the action. |
| `description` | No | string | Longer description of what the action does. |
| `examples` | Yes | array of strings | Non-empty array of example phrases that should trigger this action. |
| `negative_examples` | No | array of strings | Phrases that should *not* trigger this action, used to improve intent matching. |
| `confirmation` | No | string | One of: `required`, `none`, `destructive_only`. Controls whether the user is prompted before execution. |
| `shortcut_arguments` | No | object | Key-value pairs (string keys, string values) passed to the shortcut. |
| `parameters` | No | array | Array of parameter objects (see below). |

### Parameter Fields

Each entry in the `parameters` array describes a parameter that the action accepts.

| Field | Required | Type | Rule |
|---|---|---|---|
| `name` | Yes | string | The parameter name. |
| `type` | Yes | string | The parameter type (e.g., `string`, `number`, `boolean`). |
| `description` | No | string | Description of what the parameter is for. |
| `required` | No | boolean | Whether the parameter is required. Defaults to `true`. |

### Example `skill.yaml`

```yaml
skill_id: philips-hue
name: Philips Hue
version: 1.0.0
description: Control Philips Hue smart lights
author: OpenDispatch Contributors
tags:
  - smart-home
  - lighting
languages:
  - en
actions:
  - id: lights.turn_on
    title: Turn on lights
    description: Turn on one or more Philips Hue lights
    examples:
      - "Turn on the living room lights"
      - "Switch on the kitchen light"
    negative_examples:
      - "Turn off the lights"
    confirmation: none
    parameters:
      - name: room
        type: string
        description: The room or light name
        required: true
  - id: lights.turn_off
    title: Turn off lights
    examples:
      - "Turn off the bedroom lights"
      - "Switch off all lights"
    confirmation: none
    parameters:
      - name: room
        type: string
        description: The room or light name
        required: false
```

---

## Icon Requirements

Adding an icon is optional but recommended. If you include one, it must meet these requirements:

- **Filename:** `icon.png`
- **Format:** PNG
- **Dimensions:** 256x256 pixels exactly
- **Location:** Inside your skill folder (e.g., `skills/philips-hue/icon.png`)

---

## Running Validation Locally

Before opening a pull request, you can run the validation script locally to catch errors early:

```bash
pip install pyyaml && python scripts/validate.py
```

The script checks all skill folders under `skills/` and verifies:

- The YAML is syntactically valid
- All required fields are present
- `skill_id` matches the folder name
- `version` follows semver format
- `tags` (if any) exist in `tags.yaml`
- Action IDs match the required pattern
- Each action has `examples`

---

## Pull Request Process

1. **Automated validation** runs on every pull request via GitHub Actions. Your PR must pass validation before it can be merged.
2. **Maintainer review** -- a project maintainer will review your skill definition for quality and completeness.
3. **Merge and sync** -- once approved and merged, your skill is automatically synced to the OpenDispatch marketplace.

If validation fails, check the CI output for details on what needs to be fixed. You can also run validation locally (see above) to iterate faster.
