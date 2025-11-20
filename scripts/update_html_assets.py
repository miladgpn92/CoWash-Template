#!/usr/bin/env python3
"""Update English HTML files to use bundled CSS/JS assets."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_SRC_PATTERN = re.compile(r'<script[^>]+src="([^"]+)"')
OLD_JS_FILES = {
    "js/jquery-3.7.1.min.js",
    "js/jquery-migrate-3.4.1.min.js",
    "js/modernizr-2.6.2.min.js",
    "js/imagesloaded.pkgd.min.js",
    "js/jquery.isotope.v3.0.2.js",
    "js/popper.min.js",
    "js/bootstrap.min.js",
    "js/scrollIt.min.js",
    "js/jquery.waypoints.min.js",
    "js/owl.carousel.min.js",
    "js/jquery.stellar.min.js",
    "js/jquery.magnific-popup.js",
    "js/YouTubePopUp.js",
    "js/custom.js",
}
MAIN_SCRIPT_TAG = '    <script src="js/main.js"></script>'


def update_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    new_lines = []
    inserted_script = False
    for line in lines:
        if "css/plugins.css" in line:
            continue
        match = SCRIPT_SRC_PATTERN.search(line)
        if match and match.group(1) in OLD_JS_FILES:
            continue
        if "</body>" in line and not inserted_script:
            new_lines.append(MAIN_SCRIPT_TAG + newline)
            inserted_script = True
        new_lines.append(line)
    if not inserted_script:
        new_lines.append(newline + MAIN_SCRIPT_TAG + newline)
    path.write_text("".join(new_lines), encoding="utf-8")


def main() -> None:
    html_files = [
        path
        for path in ROOT.glob("*.html")
        if path.is_file() and not path.stem.endswith("-fa")
    ]
    for html_file in html_files:
        update_file(html_file)
        print(f"Updated {html_file.name}")


if __name__ == "__main__":
    main()
