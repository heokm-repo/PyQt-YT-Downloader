"""Startup dependency checks for Python packages.

This module uses importlib metadata rather than importing application modules so
missing packages can be reported before the GUI is constructed.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from typing import Iterable

from constants import STARTUP_OPTIONAL_DEPENDENCY_SPECS, STARTUP_REQUIRED_DEPENDENCY_SPECS


@dataclass(frozen=True)
class DependencySpec:
    module: str
    package: str


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


def _build_required_dependencies() -> tuple[DependencySpec, ...]:
    return tuple(
        DependencySpec(module, package)
        for module, package in STARTUP_REQUIRED_DEPENDENCY_SPECS
    )


def _build_optional_dependencies() -> tuple[DependencySpec, ...]:
    return tuple(
        DependencySpec(module, package)
        for module, package, _feature in STARTUP_OPTIONAL_DEPENDENCY_SPECS
    )


REQUIRED_DEPENDENCIES: tuple[DependencySpec, ...] = _build_required_dependencies()
OPTIONAL_DEPENDENCIES: tuple[DependencySpec, ...] = _build_optional_dependencies()


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
