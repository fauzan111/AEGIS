# -*- coding: utf-8 -*-
"""Fix the Roadmap & Timeline slide's background SmartArt, which ships in the
official template with hardcoded Italian month labels (Gennaio-Settembre,
i.e. Jan-Sep) baked into its diagram data model. python-pptx can't edit
SmartArt content directly, so this patches the two relevant XML parts
in-place inside the already-built pptx (data1.xml = the data model PowerPoint
recalculates the layout from; drawing1.xml = the cached fallback drawing
other viewers may render instead).

Relabels the 6 leftmost slots to the real course span (May-October) and
blanks the 3 trailing slots rather than deleting SmartArt nodes outright,
which risks corrupting the diagram's internal node/connection structure.

Run this AFTER make_gate1_official_deck.py, before patch_gate1_official_notes.py.

Run:  .venv/Scripts/python AEGIS/src/fix_smartart_months.py
"""

import os
import re
import zipfile
import shutil
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PPTX = os.path.join(HERE, "..", "slides", "AEGIS_Gate1_Official.pptx")

MAPPING = [
    ("Gennaio", "May"),
    ("Febbraio", "June"),
    ("Marzo", "July"),
    ("Aprile", "August"),
    ("Maggio ", "September"),
    ("Giugno", "October"),
    ("Luglio", ""),
    ("Agosto ", ""),
    ("Settembre", ""),
]

TARGETS = ["ppt/diagrams/data1.xml", "ppt/diagrams/drawing1.xml"]


def patch_xml(content: str) -> tuple[str, int]:
    total = 0
    for old, new in MAPPING:
        pattern = "<a:t>" + re.escape(old) + "</a:t>"
        replacement = "<a:t>" + new + "</a:t>"
        total += len(re.findall(pattern, content))
        content = re.sub(pattern, replacement, content)
    return content, total


def main():
    with zipfile.ZipFile(PPTX, "r") as zin:
        names = {i.filename: i for i in zin.infolist()}
        for target in TARGETS:
            if target not in names:
                raise RuntimeError(f"{target} not found in {PPTX} - template structure may have changed")

        patched = {}
        for target in TARGETS:
            content = zin.read(target).decode("utf-8")
            new_content, n = patch_xml(content)
            patched[target] = new_content.encode("utf-8")
            print(f"{target}: {n} label(s) replaced")

        fd, tmp_path = tempfile.mkstemp(suffix=".pptx", dir=os.path.dirname(PPTX))
        os.close(fd)
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = patched.get(item.filename, zin.read(item.filename))
                zout.writestr(item, data)

    shutil.move(tmp_path, PPTX)
    print(f"Patched {PPTX}")


if __name__ == "__main__":
    main()
