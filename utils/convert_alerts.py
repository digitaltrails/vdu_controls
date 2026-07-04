#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
import re
import sys
from pathlib import Path

from mypy.server import target

# Maps GitHub alert tags to MkDocs Material names and titles
TAG_MAP = {
    "TIP": ("tip", "Tip"),
    "NOTE": ("note", "Note"),
    "WARNING": ("warning", "Warning"),
    "IMPORTANT": ("warning", "Important"),
    "CAUTION": ("danger", "Caution")
}

def convert_file(target_file: str):
    file_path = Path(target_file)
    
    if not file_path.is_file():
        print(f"Error: Target file '{target_file}' not found.")
        sys.exit(1)
        
    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines = []
    in_github_alert = False
    
    for line_no, line in enumerate(lines):
        # Match pattern with spaces and ignore case (e.g., > [!TIP])
        alert_match = re.match(r"^> *\[\!(TIP|NOTE|WARNING|IMPORTANT|CAUTION)\]\s*$", line.strip(), flags=re.IGNORECASE)

        if alert_match:
            tag = alert_match.group(1).upper()
            mkdocs_type, mkdocs_title = TAG_MAP[tag]
            print(f"{line_no} {tag}", file=sys.stderr)
            new_lines.append(f"!!! {mkdocs_type} \"{mkdocs_title}\"\n")
            in_github_alert = True
            continue

        if in_github_alert:
            if line.startswith(">"):
                content = line[1:]
                if content.startswith(" "):
                    content = content[1:]
                new_lines.append(f"    {content}")
            else:
                # The blockquote block ended
                in_github_alert = False
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    file_path.write_text("".join(new_lines), encoding="utf-8")
    print(f"Successfully converted GitHub alerts in {target_file}")

if __name__ == "__main__":
    if len(sys.argv) != 1:
        print("Error: no filename argument was supplied", file=sys.stderr)
        sys.exit(1)
    target = sys.argv[1]
    convert_file(target)
