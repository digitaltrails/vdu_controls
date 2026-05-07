#!/usr/bin/env python3
"""
Translate a text file (as a single block) using translate-shell.
Output filename: <basename>-<locale>.<extension>

Usage: translate_to_locale.py <locale> <input_file>
Example: translate_to_locale.py fr_FR about.html
Output: about-fr_FR.html
"""
import sys
import subprocess

from pathlib import Path


def translate_text(text: str, target_lang: str) -> str:
    """Translate entire text block from English to target language."""
    if not text.strip():
        return text
    try:
        # Pass the whole text via stdin to avoid command-line length limits
        result = subprocess.run(
            ['trans', '-brief', f'en:{target_lang}'],
            input=text, capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"Translation failed: {result.stderr}", file=sys.stderr)
            return text
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return text


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    locale = sys.argv[1]
    input_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Error: {input_path} not found.")
        sys.exit(1)

    # Build output path: stem-locale.suffix
    stem = input_path.stem
    suffix = input_path.suffix
    output_filename = f"{stem}-{locale}{suffix}"
    output_path = Path('translations') / output_filename

    # Read entire file
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"Translating {input_path} as a single block...")

    # Extract two-letter language code (e.g., 'fr' from 'fr_FR')
    lang_code = locale.split('_')[0]
    translated = translate_text(content, lang_code)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(translated)

    print(f"\nSaved translated file to: {output_path}")


if __name__ == '__main__':
    main()