#!/usr/bin/env python3
"""Safely initialize a Sanity Node runtime workspace."""

from __future__ import annotations

import argparse
import grp
import os
from pathlib import Path
import pwd
import re
import stat
import sys
import tempfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
STARTER_CONFIG = REPOSITORY_ROOT / "examples" / "config.starter.yaml"
ENV_EXAMPLE = REPOSITORY_ROOT / ".env.example"

MANAGED_DIRECTORIES = (
    ("config", 0o775),
    ("html", 0o775),
    ("logs", 0o775),
    ("ssh", 0o700),
)


class BootstrapError(RuntimeError):
    """Raised when the workspace cannot be initialized safely."""


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a safe Sanity Node first-run workspace without "
            "overwriting existing user files."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPOSITORY_ROOT,
        help=(
            "alternate target root for tests or advanced use; "
            "normal installations should omit this option "
            f"(default: {REPOSITORY_ROOT})"
        ),
    )
    parser.add_argument(
        "--create-env",
        action="store_true",
        help=(
            "create .env from .env.example and set PUID/PGID to "
            "the current user"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "replace bootstrap-managed config/config.yaml and, when "
            "--create-env is used, .env"
        ),
    )
    return parser.parse_args()


def absolute_path(path: Path) -> Path:
    return Path(os.path.abspath(os.path.expanduser(str(path))))


def ensure_workspace_root(root: Path) -> None:
    if root.is_symlink():
        raise BootstrapError(
            f"workspace root must not be a symbolic link: {root}"
        )

    if not root.exists():
        raise BootstrapError(f"workspace root does not exist: {root}")

    if not root.is_dir():
        raise BootstrapError(
            f"workspace root is not a directory: {root}"
        )


def verify_directory_writable(path: Path) -> None:
    probe_path: str | None = None

    try:
        descriptor, probe_path = tempfile.mkstemp(
            prefix=".sanity-node-write-test-",
            dir=path,
        )
        os.close(descriptor)
    except OSError as exc:
        raise BootstrapError(
            f"directory is not writable: {path}: {exc}"
        ) from exc
    finally:
        if probe_path is not None:
            try:
                os.unlink(probe_path)
            except FileNotFoundError:
                pass


def ensure_directory(path: Path, mode: int) -> str:
    if path.is_symlink():
        raise BootstrapError(
            f"managed directory must not be a symbolic link: {path}"
        )

    if path.exists():
        if not path.is_dir():
            raise BootstrapError(
                f"managed directory path is not a directory: {path}"
            )
        result = "PRESERVED"
    else:
        try:
            path.mkdir(mode=mode)
            os.chmod(path, mode)
        except OSError as exc:
            raise BootstrapError(
                f"could not create directory {path}: {exc}"
            ) from exc
        result = "CREATED"

    verify_directory_writable(path)
    return result


def read_regular_source(path: Path) -> str:
    if path.is_symlink():
        raise BootstrapError(
            f"bootstrap source must not be a symbolic link: {path}"
        )

    if not path.exists():
        raise BootstrapError(f"bootstrap source is missing: {path}")

    if not stat.S_ISREG(path.lstat().st_mode):
        raise BootstrapError(
            f"bootstrap source is not a regular file: {path}"
        )

    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BootstrapError(
            f"could not read bootstrap source {path}: {exc}"
        ) from exc


def atomic_write(path: Path, content: str) -> None:
    descriptor = -1
    temporary_path: str | None = None

    try:
        descriptor, temporary_path = tempfile.mkstemp(
            prefix=f".{path.name}.",
            dir=path.parent,
            text=True,
        )
        os.fchmod(descriptor, 0o644)

        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            descriptor = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temporary_path, path)
        temporary_path = None
    except OSError as exc:
        raise BootstrapError(
            f"could not write managed file {path}: {exc}"
        ) from exc
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass

        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


def write_managed_file(
    path: Path,
    content: str,
    force: bool,
) -> str:
    if path.is_symlink():
        raise BootstrapError(
            f"managed file must not be a symbolic link: {path}"
        )

    existed = path.exists()

    if existed:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise BootstrapError(
                f"managed file path is not a regular file: {path}"
            )

        if not force:
            if not os.access(path, os.R_OK):
                raise BootstrapError(
                    f"existing managed file is not readable: {path}"
                )
            return "PRESERVED"

    atomic_write(path, content)
    return "REPLACED" if existed else "CREATED"


def render_environment_file(template: str) -> str:
    rendered, puid_count = re.subn(
        r"(?m)^PUID=.*$",
        f"PUID={os.getuid()}",
        template,
    )
    rendered, pgid_count = re.subn(
        r"(?m)^PGID=.*$",
        f"PGID={os.getgid()}",
        rendered,
    )

    if puid_count != 1 or pgid_count != 1:
        raise BootstrapError(
            ".env.example must contain exactly one PUID and one PGID line"
        )

    return rendered


def identity_name(identifier: int, group: bool = False) -> str:
    try:
        if group:
            return grp.getgrgid(identifier).gr_name
        return pwd.getpwuid(identifier).pw_name
    except KeyError:
        return str(identifier)


def describe_path(path: Path) -> str:
    metadata = path.lstat()
    mode = stat.S_IMODE(metadata.st_mode)
    owner = identity_name(metadata.st_uid)
    group = identity_name(metadata.st_gid, group=True)

    return (
        f"{path} "
        f"owner={owner}:{group} "
        f"mode={mode:04o}"
    )


def print_next_steps(root: Path) -> None:
    print()

    if root != REPOSITORY_ROOT:
        print("Alternate workspace initialized.")
        print(
            "Deployment commands are omitted because --root does not "
            "point to the cloned Sanity Node repository."
        )
        print(
            "For a normal installation, run "
            "./scripts/bootstrap-workspace.py from the repository root "
            "without --root."
        )
        return

    print("Next steps:")
    print(f"  cd {root}")
    print("  ./scripts/validate-config.py config/config.yaml")
    print("  docker compose up --build --wait && docker compose ps")
    print("  Open in a browser: http://<collector-ip>:8099")


def bootstrap(
    root: Path,
    create_env: bool,
    force: bool,
) -> None:
    root = absolute_path(root)
    ensure_workspace_root(root)

    starter_content = read_regular_source(STARTER_CONFIG)
    env_content = None

    if create_env:
        env_content = render_environment_file(
            read_regular_source(ENV_EXAMPLE)
        )

    print("=== SANITY NODE WORKSPACE BOOTSTRAP ===")
    print(f"Workspace: {root}")
    print()

    managed_paths: list[Path] = []

    for relative_path, mode in MANAGED_DIRECTORIES:
        path = root / relative_path
        result = ensure_directory(path, mode)
        managed_paths.append(path)
        print(f"{result}: directory {path}")

    config_path = root / "config" / "config.yaml"
    config_result = write_managed_file(
        config_path,
        starter_content,
        force=force,
    )
    managed_paths.append(config_path)
    print(f"{config_result}: file {config_path}")

    env_path = root / ".env"

    if create_env:
        assert env_content is not None
        env_result = write_managed_file(
            env_path,
            env_content,
            force=force,
        )
        managed_paths.append(env_path)
        print(f"{env_result}: file {env_path}")
    else:
        print(
            f"SKIPPED: file {env_path} "
            "(use --create-env to create it)"
        )

    print()
    print("Ownership and permissions:")

    for path in managed_paths:
        print(f"  {describe_path(path)}")

    ssh_path = root / "ssh"
    ssh_mode = stat.S_IMODE(ssh_path.lstat().st_mode)

    if ssh_mode & 0o077:
        print(
            "WARNING: ssh directory permits group or other access; "
            "consider chmod 700 ssh",
            file=sys.stderr,
        )

    print_next_steps(root)


def main() -> int:
    arguments = parse_arguments()

    try:
        bootstrap(
            root=arguments.root,
            create_env=arguments.create_env,
            force=arguments.force,
        )
    except BootstrapError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
