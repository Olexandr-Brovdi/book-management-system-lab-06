"""YAML paths are relative to the configuration file; env override is optional."""

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from book_catalog.exceptions import ConfigurationError
from book_catalog.models import YearPolicy


@dataclass(frozen=True, slots=True)
class Config:
    policy: YearPolicy
    input: Path
    output: Path


def get_environment() -> str:
    return os.getenv("BOOK_ENV", "development")


def load_config(path: Path) -> Config:
    try:
        with path.open(encoding="utf-8-sig") as handle:
            raw = yaml.safe_load(handle)
        if not isinstance(raw, dict):
            raise ValueError("Configuration must be a mapping")
        policy = YearPolicy(raw["min_year"], raw["max_year"])
        override = os.getenv("BOOK_MAX_YEAR")
        if override is not None:
            policy = YearPolicy(policy.min_year, int(override))

        def resolve(value: object) -> Path:
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Path must be nonempty text")
            return (path.resolve().parent / value).resolve()

        incoming, outgoing = resolve(raw["input"]), resolve(raw["output"])
        if len({incoming, outgoing, path.resolve()}) != 3:
            raise ValueError("Input output and config paths must differ")
        return Config(policy, incoming, outgoing)
    except (
        OSError,
        UnicodeError,
        yaml.YAMLError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        raise ConfigurationError("Invalid book catalog configuration") from error
