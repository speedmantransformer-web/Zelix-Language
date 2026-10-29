"""Local project manifests and path-based Zelix dependencies."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[reportMissingImports]


MANIFEST_NAME = "zelix.toml"
LOCK_NAME = "zelix.lock"
PACKAGE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
PACKAGE_VERSION = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
USE_LINE = re.compile(r"^\s*use\s+([A-Za-z_][A-Za-z0-9_-]*)\s*$", re.IGNORECASE)


class ProjectError(Exception):
    pass


@dataclass(frozen=True)
class Dependency:
    name: str
    root: Path


@dataclass(frozen=True)
class Project:
    root: Path
    name: str
    version: str
    entry: Path
    dependencies: dict[str, Dependency]


def _read_manifest(root: Path) -> Project:
    manifest_path = root / MANIFEST_NAME
    try:
        raw = manifest_path.read_bytes()
    except OSError as exc:
        raise ProjectError(f"Cannot read project manifest {manifest_path}: {exc}") from exc
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ProjectError(f"Invalid {manifest_path}: {exc}") from exc

    package = data.get("package")
    if not isinstance(package, dict):
        raise ProjectError(f"{manifest_path} must define a [package] table")
    name = package.get("name")
    version = package.get("version")
    entry_name = package.get("entry", "src/main.zelix")
    if not isinstance(name, str) or not PACKAGE_NAME.fullmatch(name):
        raise ProjectError("Package name must start with a letter or digit and contain only letters, digits, _ or -")
    if not isinstance(version, str) or not PACKAGE_VERSION.fullmatch(version):
        raise ProjectError(f"Package {name!r} must use a stable MAJOR.MINOR.PATCH version")
    if not isinstance(entry_name, str) or not entry_name:
        raise ProjectError(f"Package {name!r} must define a non-empty entry path")
    entry = (root / entry_name).resolve()
    if not entry.is_relative_to(root.resolve()):
        raise ProjectError(f"Package entry path must stay inside the project: {entry_name!r}")
    if not entry.is_file():
        raise ProjectError(f"Package entry file does not exist: {entry}")

    raw_dependencies = data.get("dependencies", {})
    if not isinstance(raw_dependencies, dict):
        raise ProjectError(f"{manifest_path} [dependencies] must be a table")
    dependencies: dict[str, Dependency] = {}
    for dependency_name, spec in raw_dependencies.items():
        if not isinstance(dependency_name, str) or not PACKAGE_NAME.fullmatch(dependency_name):
            raise ProjectError(f"Invalid dependency name: {dependency_name!r}")
        if not isinstance(spec, dict) or set(spec) != {"path"}:
            raise ProjectError(
                f"Dependency {dependency_name!r} must use only a local path, "
                'for example: helper = { path = "../helper" }'
            )
        relative_path = spec["path"]
        if not isinstance(relative_path, str) or not relative_path:
            raise ProjectError(f"Dependency {dependency_name!r} requires a non-empty path")
        dependency_root = (root / relative_path).resolve()
        if not dependency_root.is_dir():
            raise ProjectError(f"Dependency {dependency_name!r} directory does not exist: {dependency_root}")
        dependencies[dependency_name] = Dependency(dependency_name, dependency_root)
    return Project(root.resolve(), name, version, entry, dependencies)


def find_project_root(path: Path) -> Path | None:
    current = path.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / MANIFEST_NAME).is_file():
            return candidate
    return None


def load_project(path: Path) -> Project:
    root = path.resolve()
    if root.is_file():
        root = root.parent
    if not (root / MANIFEST_NAME).is_file():
        raise ProjectError(f"No {MANIFEST_NAME} found in {root}")
    return _read_manifest(root)


def project_entry(path: Path) -> Path:
    project = load_project(path)
    return project.entry


def _source_digest(project: Project) -> str:
    digest = hashlib.sha256()
    for path in (project.root / MANIFEST_NAME, project.entry):
        digest.update(path.relative_to(project.root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise ProjectError(f"Cannot read package file {path}: {exc}") from exc
        digest.update(content.replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
        digest.update(b"\0")
    return digest.hexdigest()


def _dependency_graph(project: Project) -> dict[str, dict[str, str]]:
    packages: dict[str, dict[str, str]] = {}
    roots: dict[str, Path] = {project.name: project.root}
    active: list[Path] = [project.root]

    def visit(owner: Project) -> None:
        for dependency in owner.dependencies.values():
            child = _read_manifest(dependency.root)
            if child.name != dependency.name:
                raise ProjectError(
                    f"Dependency key {dependency.name!r} does not match package name {child.name!r}"
                )
            if child.root in active:
                chain = " -> ".join(path.name for path in (*active, child.root))
                raise ProjectError(f"Local package dependency cycle: {chain}")
            previous = roots.get(child.name)
            if previous is not None and previous != child.root:
                raise ProjectError(
                    f"Package {child.name!r} resolves to multiple paths: {previous} and {child.root}"
                )
            roots[child.name] = child.root
            try:
                relative_path = Path(os.path.relpath(child.root, project.root)).as_posix()
            except ValueError:
                relative_path = child.root.as_posix()
            packages[child.name] = {
                "version": child.version,
                "path": relative_path,
                "sha256": _source_digest(child),
            }
            active.append(child.root)
            visit(child)
            active.pop()

    visit(project)
    return dict(sorted(packages.items()))


def _lock_data(project: Project) -> dict[str, Any]:
    return {
        "lock_version": 1,
        "package": {"name": project.name, "version": project.version},
        "dependencies": _dependency_graph(project),
    }


def install_project(path: Path) -> Path:
    project = load_project(path)
    lock_data = _lock_data(project)
    lock_path = project.root / LOCK_NAME
    content = json.dumps(lock_data, indent=2, sort_keys=True) + "\n"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=project.root, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
        temporary_path.replace(lock_path)
    except OSError as exc:
        raise ProjectError(f"Cannot write {lock_path}: {exc}") from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return lock_path


def init_project(path: Path) -> tuple[Path, Path]:
    root = path.resolve()
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ProjectError(f"Cannot create project directory {root}: {exc}") from exc
    manifest = root / MANIFEST_NAME
    source_dir = root / "src"
    entry = source_dir / "main.zelix"
    if manifest.exists() or entry.exists():
        raise ProjectError(f"Project files already exist in {root}")
    name = re.sub(r"[^A-Za-z0-9_-]+", "-", root.name).strip("-") or "zelix-project"
    if not name[0].isalnum():
        name = f"project-{name.lstrip('_-')}"
    try:
        source_dir.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            f'[package]\nname = "{name}"\nversion = "0.1.0"\nentry = "src/main.zelix"\n\n'
            "[dependencies]\n",
            encoding="utf-8",
        )
        entry.write_text("display text Hello from Zelix end text\n", encoding="utf-8")
    except OSError as exc:
        raise ProjectError(f"Cannot create project in {root}: {exc}") from exc
    return manifest, entry


def _strip_use_lines(source: str, project: Project) -> tuple[str, list[str]]:
    lines = source.splitlines()
    imports: list[str] = []
    block_depth = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"(?i)^use(?:\s|$)", stripped):
            if block_depth:
                raise ProjectError(f"Line {index + 1}: Package imports must be top-level statements")
            match = USE_LINE.fullmatch(line)
            if not match:
                raise ProjectError(f"Line {index + 1}: Expected a top-level 'use package_name' statement")
            name = match.group(1)
            if name not in project.dependencies:
                raise ProjectError(
                    f"Line {index + 1}: Package {name!r} is not declared in {MANIFEST_NAME} [dependencies]"
                )
            if name not in imports:
                imports.append(name)
            lines[index] = ""
            continue
        lower = stripped.lower()
        if lower.startswith(("if ", "while ", "repeat ", "function ")):
            block_depth += 1
        elif lower in {"end if", "end loop", "end function"}:
            block_depth = max(0, block_depth - 1)
    return "\n".join(lines), imports


def resolve_project_source(source: str, source_path: Path | None = None) -> str:
    root = find_project_root(source_path) if source_path is not None else None
    has_use = any(
        re.match(r"(?i)^use(?:\s|$)", line.strip()) for line in source.splitlines()
    )
    if root is None:
        if has_use:
            raise ProjectError(f"Package imports require a project with {MANIFEST_NAME}")
        return source

    project = load_project(root)
    stripped_source, imports = _strip_use_lines(source, project)
    if not imports:
        return source

    expected_lock = _lock_data(project)
    lock_path = project.root / LOCK_NAME
    try:
        actual_lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProjectError(f"Missing {LOCK_NAME}; run 'zelix install {project.root}' first") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectError(f"Cannot read valid {LOCK_NAME}: {exc}") from exc
    if actual_lock != expected_lock:
        raise ProjectError(f"{LOCK_NAME} is out of date; run 'zelix install {project.root}'")

    modules: list[str] = []
    loaded: set[Path] = set()
    active: list[Path] = [project.root]

    def load_library(owner: Project, name: str) -> None:
        dependency = owner.dependencies.get(name)
        if dependency is None:
            raise ProjectError(f"Package {name!r} is not declared in {MANIFEST_NAME}")
        package = _read_manifest(dependency.root)
        if package.name != name:
            raise ProjectError(f"Dependency {name!r} does not match package name {package.name!r}")
        if package.root in active:
            raise ProjectError(f"Package import cycle involving {package.name!r}")
        if package.root in loaded:
            return
        active.append(package.root)
        try:
            try:
                package_source = package.entry.read_text(encoding="utf-8")
            except OSError as exc:
                raise ProjectError(f"Cannot read package entry {package.entry}: {exc}") from exc
            library_source, nested_imports = _strip_use_lines(package_source, package)
            for nested_name in nested_imports:
                load_library(package, nested_name)
            from compiler import ZelixParser

            if ZelixParser("\n".join((*modules, library_source))).parse().body:
                raise ProjectError(
                    f"Dependency package {package.name!r} entry must contain function definitions only"
                )
            modules.append(library_source)
            loaded.add(package.root)
        finally:
            active.pop()

    for import_name in imports:
        load_library(project, import_name)
    return stripped_source + "\n" + "\n".join(modules)
