# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import shutil

#!/usr/bin/env python3
"""
Translate unfinished (empty) translations in a Qt .ts file.
The target language is automatically derived from the filename.
Example: fr_FR.ts -> French, ar_SA.ts -> Arabic.

Requires: trans (translate-shell)
"""
import sys
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

def get_target_language(ts_file: str) -> str:
    """Extract two-letter language code from filename like fr_FR.ts -> fr."""
    stem = Path(ts_file).stem  # e.g., 'fr_FR' or 'ar_SA'
    # Take first two letters (ISO 639-1)
    lang = stem[:2].lower()
    # Validate: common codes are 2 letters
    if lang not in ['en', 'fr', 'de', 'es', 'it', 'pt', 'nl', 'ru', 'zh', 'ja', 'ko', 'ar', 'hi', 'tr', 'pl', 'uk']:
        print(f"Warning: unknown language code '{lang}' from filename {ts_file}, using as is.")
    return lang

def translate_text(text: str, target_lang: str) -> str:
    """Translate English -> target_lang using trans."""
    try:
        result = subprocess.run(
            ['trans', '-brief', f'en:{target_lang}', text],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"Translation failed for: {text} (error: {result.stderr})", file=sys.stderr)
            return ""
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return ""

def update_ts(ts_file: str):
    target = get_target_language(ts_file)
    print(f"Target language from filename: {target}")

    shutil.copy(ts_file, ts_file + '.old')
    tree = ET.parse(ts_file)
    root = tree.getroot()
    changed = False

    for message in root.findall('.//message'):
        source_elem = message.find('source')
        trans_elem = message.find('translation')
        if source_elem is None or trans_elem is None:
            continue

        # Check if translation is missing or unfinished
        if (trans_elem.text is None or
            trans_elem.get('type') == 'unfinished' or
            trans_elem.text.strip() == ''):
            source_text = source_elem.text
            if source_text:
                translated = translate_text(source_text, target)
                if translated:
                    trans_elem.text = translated
                    print(f"Translated: {source_text} -> {target} -> {translated}")
                    # Remove type attribute (makes it finished)
                    if 'type' in trans_elem.attrib:
                        del trans_elem.attrib['type']
                    changed = True
                else:
                    print(f"Translated: {source_text} -> {target} -> No translation")

    if changed:
        tree.write(ts_file, encoding='utf-8', xml_declaration=True)
        doc_type = "<!DOCTYPE TS>\n"
        with open(ts_file, 'r') as file:
            lines = file.readlines()
        lines.insert(1, doc_type)
        with open(ts_file, 'w') as file:
            file.writelines(lines)
        print(f"Updated {ts_file}")
    else:
        print("No unfinished translations found.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <some_locale.ts>")
        sys.exit(1)
    update_ts(sys.argv[1])