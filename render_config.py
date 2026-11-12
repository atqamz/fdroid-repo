import os
import pathlib

import yaml

SOURCE = pathlib.Path("config.example.yml")
PLACEHOLDERS = (
    "FDROID_KEYSTORE_PATH",
    "FDROID_INDEX_PASSWORD",
    "FDROID_KEY_PASSWORD",
)


def fill(value, values):
    if isinstance(value, dict):
        return {key: fill(item, values) for key, item in value.items()}
    if isinstance(value, list):
        return [fill(item, values) for item in value]
    if isinstance(value, str):
        for name, secret in values.items():
            value = value.replace("${" + name + "}", secret)
    return value


def main():
    values = {name: os.environ[name] for name in PLACEHOLDERS}
    config = fill(yaml.safe_load(SOURCE.read_text()), values)
    text = yaml.safe_dump(config, sort_keys=False)
    if "${" in text:
        raise SystemExit(f"unexpanded placeholder in {SOURCE}")
    target = pathlib.Path(os.environ["FDROID_CONFIG"])
    target.write_text(text)
    target.chmod(0o600)


if __name__ == "__main__":
    main()
