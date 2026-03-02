"""Markdown to HTML transformer with a small safe parser and CLI."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_ORDERED_ITEM_RE = re.compile(r"^\d+\.\s+(.+)$")
_UNORDERED_ITEM_RE = re.compile(r"^[-*]\s+(.+)$")
AAA = "bbb"


def _process_inline(text: str) -> str:
    """Convert inline markdown syntax to HTML with escaped user content."""
    escaped = html.escape(text, quote=True)

    escaped = _INLINE_CODE_RE.sub(
        lambda m: f"<code>{m.group(1)}</code>", escaped
    )

    def _replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        url = match.group(2)
        return f'<a href="{url}">{label}</a>'

    escaped = _LINK_RE.sub(_replace_link, escaped)
    escaped = _BOLD_RE.sub(r"<strong>\1</strong>", escaped)
    escaped = _ITALIC_RE.sub(r"<em>\1</em>", escaped)
    return escaped


def transform_markdown(md: str) -> str:
    """Transform markdown text into HTML text using a safe subset parser."""
    if not md or not md.strip():
        return ""

    lines = md.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            language = stripped[3:].strip()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and lines[i].strip() != "```":
                code_lines.append(lines[i])
                i += 1
            if i < len(lines) and lines[i].strip() == "```":
                i += 1
            class_attr = (
                f' class="language-{html.escape(language, quote=True)}"'
                if language
                else ""
            )
            code_text = html.escape("\n".join(code_lines), quote=True)
            output.append(f"<pre><code{class_attr}>{code_text}\n</code></pre>")
            continue

        if stripped.startswith("### "):
            output.append(f"<h3>{_process_inline(stripped[4:].strip())}</h3>")
            i += 1
            continue

        if stripped.startswith("## "):
            output.append(f"<h2>{_process_inline(stripped[3:].strip())}</h2>")
            i += 1
            continue

        if stripped.startswith("# "):
            output.append(f"<h1>{_process_inline(stripped[2:].strip())}</h1>")
            i += 1
            continue

        unordered_items: list[str] = []
        while i < len(lines):
            current = lines[i].strip()
            match = _UNORDERED_ITEM_RE.match(current)
            if not match:
                break
            unordered_items.append(f"<li>{_process_inline(match.group(1))}</li>")
            i += 1
        if unordered_items:
            output.append("<ul>")
            output.extend(unordered_items)
            output.append("</ul>")
            continue

        ordered_items: list[str] = []
        while i < len(lines):
            current = lines[i].strip()
            match = _ORDERED_ITEM_RE.match(current)
            if not match:
                break
            ordered_items.append(f"<li>{_process_inline(match.group(1))}</li>")
            i += 1
        if ordered_items:
            output.append("<ol>")
            output.extend(ordered_items)
            output.append("</ol>")
            continue

        paragraph_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if (
                not nxt
                or nxt.startswith("#")
                or nxt.startswith("```")
                or _UNORDERED_ITEM_RE.match(nxt)
                or _ORDERED_ITEM_RE.match(nxt)
            ):
                break
            paragraph_lines.append(nxt)
            i += 1
        paragraph_text = " ".join(paragraph_lines)
        output.append(f"<p>{_process_inline(paragraph_text)}</p>")

    return "\n".join(output)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transform markdown file content into HTML file."
    )
    parser.add_argument("input_path", type=Path, help="Input markdown file path")
    parser.add_argument("output_path", type=Path, help="Output HTML file path")
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint."""
    args = _parse_args()
    markdown_text = args.input_path.read_text(encoding="utf-8")
    html_text = transform_markdown(markdown_text)
    args.output_path.write_text(html_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
