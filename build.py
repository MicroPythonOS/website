#!/usr/bin/env python3
"""
Build script for MicroPythonOS website.

Reads .env to determine build mode:
  LOCAL=true  -> initializes submodules, builds docs, outputs site with relative links
  LOCAL=false -> outputs site with production (remote) URLs

Output goes to dist/ which can be served with any static file server.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
ENV_FILE = ROOT / ".env"


def read_env():
    """Read .env file and return dict of key=value pairs."""
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def is_local_mode():
    env = read_env()
    return env.get("LOCAL", "false").lower() == "true"


def run(cmd, cwd=None):
    """Run a shell command and exit on failure."""
    print(f"  > {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd or ROOT)
    if result.returncode != 0:
        print(f"ERROR: Command failed with exit code {result.returncode}")
        sys.exit(1)


def init_submodules():
    """Initialize and update git submodules."""
    print("\n[1/3] Initializing submodules...")
    run("git submodule update --init --recursive")


def build_docs():
    """Build MkDocs documentation."""
    docs_dir = ROOT / "docs"
    if not docs_dir.exists():
        print("ERROR: docs submodule not found. Run: git submodule update --init")
        sys.exit(1)

    print("\n[2/3] Building documentation (mkdocs)...")
    run("python -m mkdocs build", cwd=docs_dir)


def rewrite_links(html):
    """Replace production URLs with local relative paths."""
    replacements = [
        # Install links
        (r'href="https://install\.micropythonos\.com/?"', 'href="install/index.html"'),
        # Docs links
        (r'href="https://docs\.MicroPythonOS\.com/?"', 'href="docs/site/index.html"'),
        (r'href="https://docs\.micropythonos\.com/?"', 'href="docs/site/index.html"'),
        # Chat/Community links -> Telegram (no local equivalent)
        (r'href="https://chat\.MicroPythonOS\.com"', 'href="https://t.me/MicroPythonOS"'),
    ]

    for pattern, replacement in replacements:
        html = re.sub(pattern, replacement, html, flags=re.IGNORECASE)

    # Remove target="_blank" from links we've made local
    # (keeps them opening in the same tab for local navigation)
    html = html.replace('href="install/index.html" target="_blank"', 'href="install/index.html"')
    html = html.replace('href="docs/site/index.html" target="_blank"', 'href="docs/site/index.html"')

    return html


def build_dist(local_mode):
    """Assemble the dist/ directory."""
    print("\n[3/3] Building dist/...")

    # Clean and recreate dist
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    # Copy all site files (excluding build artifacts, .git, submodule sources)
    exclude = {".git", ".env", ".env.example", "dist", "build.py", "__pycache__"}

    for item in ROOT.iterdir():
        if item.name in exclude:
            continue
        dest = DIST / item.name
        if item.is_dir():
            if local_mode:
                # For local mode, copy submodule output
                if item.name == "docs":
                    site_dir = item / "site"
                    if site_dir.exists():
                        shutil.copytree(site_dir, dest / "site")
                    continue
                elif item.name == "install":
                    shutil.copytree(item, dest, ignore=shutil.ignore_patterns(".git"))
                    continue
            else:
                # Production mode: skip submodule dirs entirely
                if item.name in ("docs", "install"):
                    continue
            shutil.copytree(item, dest, ignore=shutil.ignore_patterns(".git"))
        else:
            shutil.copy2(item, dest)

    # Rewrite index.html if local mode
    index_src = DIST / "index.html"
    if local_mode and index_src.exists():
        html = index_src.read_text(encoding="utf-8")
        html = rewrite_links(html)
        index_src.write_text(html, encoding="utf-8")


def main():
    local_mode = is_local_mode()
    mode_name = "LOCAL" if local_mode else "PRODUCTION"
    print(f"=== MicroPythonOS Website Build ({mode_name} mode) ===")

    if local_mode:
        init_submodules()
        build_docs()

    build_dist(local_mode)

    print(f"\n✓ Build complete! Serve with:")
    print(f"  python -m http.server 8000 -d dist")


if __name__ == "__main__":
    main()
