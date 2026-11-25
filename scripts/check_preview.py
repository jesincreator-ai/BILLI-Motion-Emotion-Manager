#!/usr/bin/env python3
"""Validate the offline M6 preview and parse its inline JavaScript with Node."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
HTML_FILE = ROOT / "index.html"


class PreviewAssets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.script_sources = []
        self.external_assets = []
        self.inline_scripts = []
        self._inside_script = False
        self._script_parts = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "script":
            self._inside_script = True
            self._script_parts = []
            if values.get("src"):
                self.script_sources.append(values["src"])
        for key in ("src", "href"):
            value = values.get(key, "")
            if value.startswith(("http://", "https://", "//")):
                self.external_assets.append(value)

    def handle_data(self, data):
        if self._inside_script:
            self._script_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._inside_script:
            self.inline_scripts.append("".join(self._script_parts))
            self._script_parts = []
            self._inside_script = False


def main():
    if not HTML_FILE.is_file():
        print("ERROR: index.html is missing", file=sys.stderr)
        return 1

    parser = PreviewAssets()
    parser.feed(HTML_FILE.read_text(encoding="utf-8"))

    if parser.script_sources or parser.external_assets:
        print("ERROR: offline preview references external runtime assets",
              file=sys.stderr)
        print(parser.script_sources + parser.external_assets, file=sys.stderr)
        return 1
    if len(parser.inline_scripts) != 1 or not parser.inline_scripts[0].strip():
        print("ERROR: expected exactly one non-empty inline application script",
              file=sys.stderr)
        return 1

    node = shutil.which("node")
    if node is None:
        print("ERROR: Node.js is required for preview syntax validation",
              file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="m6-preview-") as temp_dir:
        script = Path(temp_dir) / "preview.js"
        script.write_text(parser.inline_scripts[0], encoding="utf-8")
        result = subprocess.run(
            [node, "--check", str(script)],
            cwd=str(ROOT),
            check=False,
            text=True,
            capture_output=True,
        )
    if result.returncode:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        return result.returncode

    print("PASS: preview is offline and inline JavaScript parses with Node.js")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
