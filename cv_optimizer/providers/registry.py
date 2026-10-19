"""Provider registration and construction from JSON configuration."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Callable

from .base import JobProvider, ProfileProvider
from .gig_radar import GigRadarJsonJobProvider
from .json_file import JsonFileJobProvider, JsonFileProfileProvider
from .stubs import StubJobProvider, StubProfileProvider

ProfileFactory = Callable[[dict[str, Any], Path], ProfileProvider]
JobFactory = Callable[[dict[str, Any], Path], JobProvider]
_PROFILE_FACTORIES: dict[str, ProfileFactory] = {}
_JOB_FACTORIES: dict[str, JobFactory] = {}


def register_profile_provider(name: str, factory: ProfileFactory) -> None:
    if name in _PROFILE_FACTORIES:
        raise ValueError(f"Profile provider {name!r} is already registered")
    _PROFILE_FACTORIES[name] = factory


def register_job_provider(name: str, factory: JobFactory) -> None:
    if name in _JOB_FACTORIES:
        raise ValueError(f"Job provider {name!r} is already registered")
    _JOB_FACTORIES[name] = factory


def _resolved_path(spec: dict[str, Any], base_dir: Path) -> Path:
    value = spec.get("path")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("json_file provider needs a non-empty path")
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base_dir / path).resolve()


def _json_profile_factory(spec: dict[str, Any], base_dir: Path) -> ProfileProvider:
    return JsonFileProfileProvider(_resolved_path(spec, base_dir))


def _json_job_factory(spec: dict[str, Any], base_dir: Path) -> JobProvider:
    return JsonFileJobProvider(_resolved_path(spec, base_dir))


def _stub_profile_factory(spec: dict[str, Any], base_dir: Path) -> ProfileProvider:
    return StubProfileProvider(spec, base_dir)


def _stub_job_factory(spec: dict[str, Any], base_dir: Path) -> JobProvider:
    return StubJobProvider(spec, base_dir)


def _gig_radar_job_factory(spec: dict[str, Any], base_dir: Path) -> JobProvider:
    env_name = spec.get("path_env")
    if env_name is not None:
        if not isinstance(env_name, str) or not env_name.strip():
            raise ValueError("gig_radar_json path_env must be a non-empty environment variable name")
        import os

        path_value = os.environ.get(env_name)
        if not path_value:
            raise ValueError(f"Set {env_name} to Gig Radar's seen-listings.json path")
        path = Path(path_value).expanduser().resolve()
    else:
        path = _resolved_path(spec, base_dir)

    def string_option(name: str) -> list[str] | None:
        value = spec.get(name)
        if value is None:
            return None
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"gig_radar_json {name} must be a list of strings")
        return value

    return GigRadarJsonJobProvider(
        path,
        statuses=string_option("statuses"),
        fits=string_option("fits"),
        platforms=string_option("platforms"),
    )


register_profile_provider("json_file", _json_profile_factory)
register_profile_provider("stub", _stub_profile_factory)
register_job_provider("json_file", _json_job_factory)
register_job_provider("gig_radar_json", _gig_radar_job_factory)
register_job_provider("stub", _stub_job_factory)


def _build(spec: Any, base_dir: Path, factories: dict[str, Callable]) -> object:
    if not isinstance(spec, dict):
        raise ValueError("Each provider configuration must be a JSON object")
    name = spec.get("provider")
    if not isinstance(name, str) or name not in factories:
        available = ", ".join(sorted(factories))
        raise ValueError(f"Unknown provider {name!r}; registered providers: {available}")
    return factories[name](spec, base_dir)


def load_providers(config_path: str | Path) -> tuple[ProfileProvider, JobProvider]:
    """Load plugin modules, then construct providers relative to the config file."""
    path = Path(config_path).expanduser().resolve()
    with path.open("r", encoding="utf-8") as stream:
        config = json.load(stream)
    if not isinstance(config, dict):
        raise ValueError("Provider configuration must be a JSON object")

    plugins = config.get("plugins", [])
    if not isinstance(plugins, list) or not all(isinstance(item, str) for item in plugins):
        raise ValueError("plugins must be a list of importable module names")
    for module_name in plugins:
        importlib.import_module(module_name)

    profile = _build(config.get("profile"), path.parent, _PROFILE_FACTORIES)
    jobs = _build(config.get("jobs"), path.parent, _JOB_FACTORIES)
    return profile, jobs  # type: ignore[return-value]
