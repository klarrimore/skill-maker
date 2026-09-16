#!/usr/bin/env python3
"""Install a skill into a skills directory.

Builds a clean copy of a skill folder - dev-only trees (`tests/`, `evals/`),
caches, and bytecode are stripped using the same rules as
`scripts.package_skill` - then places it at `<target>/<name>/`.

Usage:
    python -m scripts.install_skill <path/to/skill-folder> [options]

Options:
    --target DIR   Skills directory to install into (default: ~/.agents/skills)
    --force        Replace an existing installation at the destination
    --dry-run      Report what would happen without writing anything
    --json         Emit a machine-readable result on stdout

Examples:
    python -m scripts.install_skill ./my-skill
    python -m scripts.install_skill ./my-skill --target ./.agents/skills
    python -m scripts.install_skill ./my-skill --force

Exit codes:
    0  installed (or would install, under --dry-run)
    1  usage error, or the source skill failed validation
    2  destination already exists and --force was not given
    3  install failed (I/O)
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from scripts.quick_validate import validate_skill
from scripts.utils import walk_skill

DEFAULT_TARGET = Path.home() / ".agents" / "skills"

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_EXISTS = 2
EXIT_IO = 3


class InstallError(Exception):
    """A failure carrying the message and exit code the CLI should report."""

    def __init__(self, message, code=EXIT_USAGE):
        super().__init__(message)
        self.message = message
        self.code = code


def _is_within(child, parent):
    """True if `child` resolves to, or sits under, `parent`."""
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


def _resolve_target(target):
    return Path(target).expanduser().resolve()


def install_skill(skill_path, target=None, force=False, dry_run=False):
    """Build a skill and install it into a skills directory.

    Returns a result dict on success; raises InstallError on failure. With
    dry_run=True nothing is written and the result reports ``installed: False``.
    """
    skill_path = Path(skill_path)
    if not skill_path.exists():
        raise InstallError(f"Skill folder not found: {skill_path}")
    if not skill_path.is_dir():
        raise InstallError(f"Not a directory: {skill_path}")
    if not (skill_path / "SKILL.md").exists():
        raise InstallError(f"SKILL.md not found in {skill_path}")

    valid, message = validate_skill(skill_path)
    if not valid:
        raise InstallError(f"Validation failed: {message}")

    name = skill_path.resolve().name
    resolved_target = _resolve_target(target) if target else _resolve_target(DEFAULT_TARGET)
    destination = resolved_target / name

    # Installing a skill onto itself (or into a tree that contains itself)
    # would delete the source mid-build; refuse before touching the filesystem.
    if _is_within(skill_path, destination) or _is_within(destination, skill_path):
        raise InstallError(
            f"Refusing to install {skill_path} onto itself: "
            f"{destination} overlaps the source skill."
        )

    if destination.exists() and not force:
        raise InstallError(
            f"{destination} already exists. Re-run with --force to replace it.",
            code=EXIT_EXISTS,
        )

    result = {
        "skill": name,
        "target": str(resolved_target),
        "destination": str(destination),
        "dry_run": bool(dry_run),
        "installed": False,
        "files": 0,
    }

    if dry_run:
        return result

    resolved_target.mkdir(parents=True, exist_ok=True)
    staging_parent = Path(tempfile.mkdtemp(prefix=".install-", dir=resolved_target))
    staged = staging_parent / name
    backup = None
    try:
        copied = 0
        for file_path, arcname, excluded in walk_skill(skill_path):
            if excluded:
                continue
            out = staging_parent / arcname
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, out)
            copied += 1

        # Move an existing install aside first so a failed swap can be undone.
        if destination.exists():
            backup = staging_parent / f"{name}.replaced"
            os.replace(destination, backup)
        try:
            os.replace(staged, destination)
        except OSError:
            if backup is not None and backup.exists():
                os.replace(backup, destination)
            raise

        result["installed"] = True
        result["files"] = copied
        return result
    except OSError as e:
        raise InstallError(f"Install failed: {e}", code=EXIT_IO)
    finally:
        if backup is not None and backup.exists():
            shutil.rmtree(backup, ignore_errors=True)
        shutil.rmtree(staging_parent, ignore_errors=True)


class _ArgumentParser(argparse.ArgumentParser):
    """Argparse, but usage errors exit 1 (not argparse's default 2)."""

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: error: {message}\n")


def main(argv=None):
    parser = _ArgumentParser(
        prog="python -m scripts.install_skill",
        description="Build a skill and install it into a skills directory.",
    )
    parser.add_argument("skill_path", help="Path to the skill folder to install")
    parser.add_argument(
        "--target",
        default=None,
        help="Skills directory to install into (default: ~/.agents/skills)",
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing installation")
    parser.add_argument("--dry-run", action="store_true", help="Report actions without writing")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable result on stdout")
    args = parser.parse_args(argv)

    try:
        result = install_skill(
            args.skill_path,
            target=args.target,
            force=args.force,
            dry_run=args.dry_run,
        )
    except InstallError as e:
        if args.json:
            json.dump({"ok": False, "error": e.message, "code": e.code}, sys.stdout)
            sys.stdout.write("\n")
        else:
            print(f"error: {e.message}", file=sys.stderr)
        sys.exit(e.code)

    if args.json:
        json.dump({"ok": True, **result}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        verb = "Would install" if result["dry_run"] else "Installed"
        print(f"{verb} {result['destination']}")
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
