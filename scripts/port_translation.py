#!/usr/bin/env python3
"""
Ports a legacy translation to the 2025 key set. Moves the values-X folder into /legacy,
and generates a new strings.xml with the new keys applied.

NOTE: This file was partially AI generated, with the purpose of providing ways for
translators who were previously working on Inware translations to quickly map old keys
to new keys. The final result may contain flaws. Make sure to double check the
generated strings.xml file.

Usage:
    python port_translation.py pt-rBR
"""

import argparse
import csv
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import xml.etree.ElementTree as ET

ET.register_namespace("tools", "http://schemas.android.com/tools")
ET.register_namespace("xliff", "urn:oasis:names:tc:xliff:document:1.2")

"""Regex that captures each `<string>` element header/body/footer tuple."""
STRING_RE = re.compile(
    r'(<string\s+[^>]*name="(?P<name>[^"]+)"[^>]*>)(?P<body>.*?)(</string>)',
    re.DOTALL,
)

@dataclass
class PortStats:
    applied: int = 0
    fallback_existing: int = 0
    fallback_default: int = 0
    missing_old: set = None  # type: ignore[assignment]
    missing_new: set = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.missing_old is None:
            self.missing_old = set()
        if self.missing_new is None:
            self.missing_new = set()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Port an Inware translation from legacy keys to the 2025 set."
    )
    parser.add_argument(
        "language",
        help="BCP 47 language identifier, e.g. 'pt-rBR'.",
    )
    return parser.parse_args()


def element_inner_xml(elem: ET.Element) -> str:
    parts: List[str] = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        child_xml = ET.tostring(child, encoding="unicode")
        child_xml = re.sub(r'\s+xmlns(:\w+)?="[^"]+"', "", child_xml)
        parts.append(child_xml)
    return "".join(parts)


def parse_string_bodies(content: str) -> Dict[str, str]:
    """Return a map of string names to their raw inner XML bodies."""
    return {match.group("name"): match.group("body") for match in STRING_RE.finditer(content)}


def load_mapping(path: Path) -> List[Tuple[str, str]]:
    """Read the CSV mapping produced earlier and return (new_key, old_key) tuples."""
    rows: List[Tuple[str, str]] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != ["new_key", "old_key"]:
            raise ValueError(f"Unexpected mapping headers: {reader.fieldnames}")
        for row in reader:
            rows.append((row["new_key"], row["old_key"]))
    return rows


def read_existing_strings(lang_dir: Path) -> Dict[str, str]:
    """Load the current locale strings (before porting) for fallback use."""
    source_strings_path = lang_dir / "strings.xml"
    if not source_strings_path.exists():
        return {}
    existing_content = source_strings_path.read_text(encoding="utf-8")
    return parse_string_bodies(existing_content)


def rewrite_strings(
    target_content: str, replacements: Dict[str, str], destination: Path
) -> None:
    """Apply the replacements to the base XML while preserving its formatting."""
    if not replacements:
        return
    new_content_parts: List[str] = []
    last_idx = 0
    for match in STRING_RE.finditer(target_content):
        name = match.group("name")
        new_body = replacements.get(name)
        new_content_parts.append(target_content[last_idx : match.start()])
        if new_body is None:
            new_content_parts.append(match.group(0))
        else:
            new_content_parts.append(match.group(1))
            new_content_parts.append(new_body)
            new_content_parts.append(match.group(4))
        last_idx = match.end()
    new_content_parts.append(target_content[last_idx:])
    destination.write_text("".join(new_content_parts), encoding="utf-8")


def apply_mappings(
    mappings: Iterable[Tuple[str, str]],
    legacy_strings: Dict[str, ET.Element],
    existing_strings: Dict[str, str],
    match_map: Dict[str, re.Match],
    default_bodies: Dict[str, str],
) -> Tuple[Dict[str, str], PortStats]:
    """Resolve each mapping to either a legacy translation, existing text, or fallback."""
    replacements: Dict[str, str] = {}
    stats = PortStats()

    for new_key, old_key in mappings:
        match = match_map.get(new_key)
        if match is None:
            stats.missing_new.add(new_key)
            continue

        legacy_elem = legacy_strings.get(old_key)
        if legacy_elem is not None:
            replacements[new_key] = element_inner_xml(legacy_elem)
            stats.applied += 1
            continue

        fallback = existing_strings.get(new_key)
        if fallback is not None:
            replacements[new_key] = fallback
            stats.fallback_existing += 1
        else:
            replacements[new_key] = default_bodies.get(new_key, "")
            stats.fallback_default += 1
        stats.missing_old.add(old_key)

    for key, body in existing_strings.items():
        if key.startswith("legacy_") or key in replacements or key not in match_map:
            continue
        replacements[key] = body

    return replacements, stats


def report_stats(stats: PortStats) -> None:
    print(f"Applied {stats.applied} translations.")
    if stats.fallback_existing:
        print(f"Kept {stats.fallback_existing} existing translations where no legacy match was found.")
    if stats.fallback_default:
        print(f"Used base English defaults for {stats.fallback_default} strings with no translation.")
    if stats.missing_old:
        print(f"Skipped {len(stats.missing_old)} missing legacy keys.")
    if stats.missing_new:
        print(f"Skipped {len(stats.missing_new)} unknown new keys.")


def main() -> int:
    args = parse_args()
    lang = args.language

    scripts_dir = Path(__file__).resolve().parent
    translations_dir = scripts_dir.parent
    mapping_path = scripts_dir / "mapping_2025.csv"
    base_strings = translations_dir / "values" / "strings.xml"
    lang_folder_name = f"values-{lang}"
    lang_dir = translations_dir / lang_folder_name
    legacy_dir = translations_dir / "legacy" / lang_folder_name

    if not base_strings.exists():
        print(f"Missing base translation file: {base_strings}", file=sys.stderr)
        return 1
    if not lang_dir.exists():
        print(f"Translation folder {lang_dir} does not exist.", file=sys.stderr)
        return 1
    if legacy_dir.exists():
        print(
            f"Legacy destination {legacy_dir} already exists. "
            "Please move or remove it first.",
            file=sys.stderr,
        )
        return 1
    if not mapping_path.exists():
        print(f"Mapping file {mapping_path} is missing.", file=sys.stderr)
        return 1

    existing_strings = read_existing_strings(lang_dir)

    legacy_dir.parent.mkdir(parents=True, exist_ok=True)

    print(f"Moving {lang_dir} -> {legacy_dir}")
    shutil.move(str(lang_dir), str(legacy_dir))

    print(f"Creating fresh folder {lang_dir}")
    lang_dir.mkdir(parents=True, exist_ok=True)
    target_strings_path = lang_dir / "strings.xml"
    shutil.copy2(base_strings, target_strings_path)

    print("Loading mapping...")
    mappings = load_mapping(mapping_path)

    print(f"Loading legacy translations from {legacy_dir / 'strings.xml'}")
    legacy_strings_path = legacy_dir / "strings.xml"
    if not legacy_strings_path.exists():
        print(
            f"Legacy strings file missing at {legacy_strings_path}.",
            file=sys.stderr,
        )
        return 1

    legacy_tree = ET.parse(legacy_strings_path)
    legacy_root = legacy_tree.getroot()
    legacy_strings = {elem.attrib["name"]: elem for elem in legacy_root.findall("string")}

    target_content = target_strings_path.read_text(encoding="utf-8")
    matches = list(STRING_RE.finditer(target_content))
    match_map = {match.group("name"): match for match in matches}
    default_bodies = {match.group("name"): match.group("body") for match in matches}

    replacements, stats = apply_mappings(
        mappings, legacy_strings, existing_strings, match_map, default_bodies
    )

    rewrite_strings(target_content, replacements, target_strings_path)
    report_stats(stats)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
