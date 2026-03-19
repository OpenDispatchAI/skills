# OpenDispatch Skills

Community-driven skill definitions for [OpenDispatch](https://opendispatch.org).

Each skill is a YAML file that teaches OpenDispatch how to interact with a device, service, or platform. Skills are validated automatically on pull request and synced to the marketplace on merge.

## Repository Structure

```
skills/
  tesla/
    skill.yaml
    icon.png          # optional, 256x256 PNG
  philips-hue/
    skill.yaml
tags.yaml             # maintainer-controlled allowed tags
```

## Quick Start

1. Fork this repository
2. Create a new folder under `skills/` matching your skill ID
3. Add a `skill.yaml` following the [schema reference](CONTRIBUTING.md#skill-yaml-schema)
4. Optionally add an `icon.png` (256x256 PNG)
5. Open a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

## License

[Apache 2.0](LICENSE)
