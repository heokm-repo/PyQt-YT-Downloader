"""Startup dependency checks for Python packages.

This module uses importlib metadata rather than importing application modules so
missing packages can be reported before the GUI is constructed.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from typing import Iterable


@dataclass(frozen=True)
class DependencySpec:
    module: str
    package: str
    required: bool = True
    feature: str | None = None


@dataclass(frozen=True)
class DependencyReport:
    missing_required: tuple[DependencySpec, ...]
    missing_optional: tuple[DependencySpec, ...]

    @property
    def ok(self) -> bool:
        return not self.missing_required

    def format_missing_required(self) -> str:
        return format_dependency_names(self.missing_required)

    def format_missing_optional(self) -> str:
        return format_dependency_names(self.missing_optional)

    def is_missing_required(self, name: str) -> bool:
        return any(dep.package == name or dep.module == name for dep in self.missing_required)


REQUIRED_DEPENDENCIES: tuple[DependencySpec, ...] = (
    DependencySpec("PyQt5.QtWidgets", "PyQt5"),
    DependencySpec("requests", "requests"),
    DependencySpec("packaging", "packaging"),
    DependencySpec("qtawesome", "qtawesome"),
    DependencySpec("yt_dlp", "yt-dlp"),
)

OPTIONAL_DEPENDENCIES: tuple[DependencySpec, ...] = (
    DependencySpec("PyQt5.QtWebEngineWidgets", "PyQtWebEngine", required=False, feature="in-app login"),
)


def is_module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (AttributeError, ImportError, ModuleNotFoundError, ValueError):
        return False


def format_dependency_names(dependencies: Iterable[DependencySpec]) -> str:
    seen: set[str] = set()
    names: list[str] = []
    for dependency in dependencies:
        if dependency.package not in seen:
            seen.add(dependency.package)
            names.append(dependency.package)
    return ", ".join(names)


def check_startup_dependencies(
    required_dependencies: Iterable[DependencySpec] = REQUIRED_DEPENDENCIES,
    optional_dependencies: Iterable[DependencySpec] = OPTIONAL_DEPENDENCIES,
    include_optional: bool = True,
) -> DependencyReport:
    missing_required = tuple(
        dependency for dependency in required_dependencies
        if not is_module_available(dependency.module)
    )
    missing_optional: tuple[DependencySpec, ...] = ()
    if include_optional:
        missing_optional = tuple(
            dependency for dependency in optional_dependencies
            if not is_module_available(dependency.module)
        )
    return DependencyReport(missing_required, missing_optional)