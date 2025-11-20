#!/usr/bin/env python3
"""
Generate RTL Persian versions of the HTML pages by translating visible text,
setting the correct lang/dir attributes, and injecting RTL specific styles.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup, Comment, Doctype, NavigableString

ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT
ATTRS_TO_TRANSLATE = ("placeholder", "title", "alt", "aria-label", "value")
EXCLUDED_TEXT_PARENTS = {"script", "style"}
API_URL = "https://translate.googleapis.com/translate_a/single"
REQUEST_TIMEOUT = 15
SLEEP_SECONDS = 0.15


def split_text(text: str) -> Tuple[str, str, str]:
    stripped = text.strip()
    if not stripped:
        return "", "", ""
    leading_len = len(text) - len(text.lstrip())
    trailing_len = len(text) - len(text.rstrip())
    leading = text[:leading_len]
    trailing = text[len(text) - trailing_len :] if trailing_len else ""
    return leading, stripped, trailing


def collect_entries(soup: BeautifulSoup) -> List[Dict]:
    entries: List[Dict] = []
    for node in soup.find_all(string=True):
        if isinstance(node, (Comment, Doctype)):
            continue
        if node.parent and node.parent.name in EXCLUDED_TEXT_PARENTS:
            continue
        text = str(node)
        leading, stripped, trailing = split_text(text)
        if not stripped:
            continue
        entries.append(
            {
                "type": "text",
                "node": node,
                "leading": leading,
                "content": stripped,
                "trailing": trailing,
            }
        )
    for attr in ATTRS_TO_TRANSLATE:
        for element in soup.find_all(attrs={attr: True}):
            value = element.get(attr)
            if not value or not value.strip():
                continue
            leading, stripped, trailing = split_text(value)
            if not stripped:
                continue
            entries.append(
                {
                    "type": "attr",
                    "element": element,
                    "attr": attr,
                    "leading": leading,
                    "content": stripped,
                    "trailing": trailing,
                }
            )
    return entries


class GoogleTranslateClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.cache: Dict[str, str] = {}

    def translate(self, text: str) -> str:
        if text in self.cache:
            return self.cache[text]
        translated = self._translate_remote(text)
        self.cache[text] = translated
        return translated

    def _translate_remote(self, text: str) -> str:
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": "fa",
            "dt": "t",
            "q": text,
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        }
        last_error = None
        for attempt in range(3):
            try:
                response = self.session.get(
                    API_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()
                translated_segments = [segment[0] for segment in data[0] if segment[0]]
                translation = "".join(translated_segments)
                time.sleep(SLEEP_SECONDS)
                return translation
            except requests.RequestException as exc:  # pragma: no cover
                last_error = exc
                time.sleep(1 + attempt)
        raise RuntimeError(f"Translation failed after retries: {last_error}")


def translate_texts(entries: List[Dict], translator: GoogleTranslateClient) -> None:
    unique_strings: Dict[str, str] = {}
    for entry in entries:
        if entry["content"] not in unique_strings:
            unique_strings[entry["content"]] = ""
    for text in unique_strings:
        unique_strings[text] = translator.translate(text)
    for entry in entries:
        apply_translation(entry, unique_strings[entry["content"]])


def apply_translation(entry: Dict, translated_text: str) -> None:
    new_value = f"{entry['leading']}{translated_text}{entry['trailing']}"
    if entry["type"] == "text":
        node: NavigableString = entry["node"]
        node.replace_with(new_value)
    else:
        element = entry["element"]
        element[entry["attr"]] = new_value


def ensure_rtl_attributes(soup: BeautifulSoup) -> None:
    html_tag = soup.find("html")
    if html_tag:
        html_tag["lang"] = "fa"
        html_tag["dir"] = "rtl"
    body_tag = soup.find("body")
    if body_tag:
        body_tag["dir"] = "rtl"
        classes = body_tag.get("class", [])
        if "rtl-body" not in classes:
            classes.append("rtl-body")
            body_tag["class"] = classes


def ensure_rtl_stylesheet(soup: BeautifulSoup) -> None:
    head = soup.find("head")
    if not head:
        return
    existing = head.find("link", attrs={"href": "css/rtl.css"})
    if existing:
        return
    new_link = soup.new_tag("link", rel="stylesheet", href="css/rtl.css")
    style_link = head.find("link", attrs={"href": "css/style.css"})
    if style_link:
        style_link.insert_after(new_link)
    else:
        head.append(new_link)


def ensure_rtl_script(soup: BeautifulSoup) -> None:
    body = soup.find("body")
    if not body:
        return
    has_script = any(
        tag.get("src") == "js/rtl.js" for tag in body.find_all("script", attrs={"src": True})
    )
    if has_script:
        return
    main_script = body.find("script", attrs={"src": "js/main.js"})
    rtl_tag = soup.new_tag("script", src="js/rtl.js")
    if main_script:
        main_script.insert_after(rtl_tag)
    else:
        body.append(rtl_tag)


def main() -> None:
    translator = GoogleTranslateClient()
    html_files = sorted(
        path
        for path in HTML_DIR.glob("*.html")
        if not path.stem.endswith("-fa") and path.is_file()
    )
    for html_file in html_files:
        soup = BeautifulSoup(html_file.read_text(encoding="utf-8-sig"), "html.parser")
        ensure_rtl_attributes(soup)
        ensure_rtl_stylesheet(soup)
        ensure_rtl_script(soup)
        entries = collect_entries(soup)
        translate_texts(entries, translator)
        fa_file = html_file.with_name(f"{html_file.stem}-fa{html_file.suffix}")
        fa_file.write_text(soup.prettify(), encoding="utf-8")
        print(f"Created {fa_file.name} ({len(entries)} translated entries)")


if __name__ == "__main__":
    main()
