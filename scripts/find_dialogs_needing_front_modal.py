#!/usr/bin/env python3
"""Find dialog modules that should be revised to use bring_to_front_and_modal

Usage:
    python scripts/find_dialogs_needing_front_modal.py [--path PATH]

The script scans Python files under `desktop/ui/views/dialogs` (recursively)
and reports files that: use `.lift()`, `.focus_force()`, `safe_grab(`, `grab_set(`,
or `grab_set_global(` but do NOT already reference `bring_to_front_and_modal`.
"""
from pathlib import Path
import re
import argparse
import sys


PATTERNS = {
    "lift": re.compile(r"\.lift\s*\(") ,
    "focus_force": re.compile(r"\.focus_force\s*\(") ,
    "safe_grab": re.compile(r"\bsafe_grab\s*\(") ,
    "grab_set": re.compile(r"\.grab_set\s*\(") ,
    "grab_set_global": re.compile(r"\.grab_set_global\s*\(") ,
    "topmost_attr": re.compile(r"attributes\s*\(\s*['\"]-topmost['\"]"),
}

ALREADY = re.compile(r"\bbring_to_front_and_modal\b")


def scan_folder(folder: Path):
    results = {
        "needs": [],
        "already": [],
        "clean": [],
        "errors": [],
    }

    if not folder.exists():
        print(f"Path not found: {folder}")
        return results

    for p in sorted(folder.rglob("*.py")):
        try:
            text = p.read_text(encoding='utf-8')
        except Exception as e:
            results['errors'].append((str(p), str(e)))
            continue

        if ALREADY.search(text):
            results['already'].append(str(p))
            continue

        matches = []
        for name, rx in PATTERNS.items():
            if rx.search(text):
                matches.append(name)

        if matches:
            results['needs'].append((str(p), matches))
        else:
            results['clean'].append(str(p))

    return results


def print_report(res):
    print("\nScan report for dialog modules:\n")

    if res['needs']:
        print(f"Files that SHOULD be revised to use bring_to_front_and_modal ({len(res['needs'])}):")
        for f, matches in res['needs']:
            print(f" - {f}    (patterns: {', '.join(matches)})")
    else:
        print("No files found that need revision.")

    if res['already']:
        print(f"\nFiles already referencing bring_to_front_and_modal ({len(res['already'])}):")
        for f in res['already']:
            print(f" - {f}")

    if res['clean']:
        print(f"\nFiles scanned and appear clean ({len(res['clean'])}):")
        for f in res['clean']:
            print(f" - {f}")

    if res['errors']:
        print(f"\nFiles with read errors ({len(res['errors'])}):")
        for f, e in res['errors']:
            print(f" - {f}: {e}")

    print("\nSuggested quick replacement pattern:")
    print(" - Replace occurrences of `.lift(); .focus_force(); safe_grab(self)` or similar")
    print("   with `from desktop.core.ui_utils import bring_to_front_and_modal` and")
    print("   call `bring_to_front_and_modal(self, parent)` after dialog creation.")


def main():
    ap = argparse.ArgumentParser(description="Find dialogs to update for bring_to_front_and_modal")
    ap.add_argument('--path', '-p', default='desktop/ui/views/dialogs', help='Folder to scan')
    args = ap.parse_args()

    folder = Path(args.path)
    res = scan_folder(folder)
    print_report(res)

    # exit code 0 even if nothing found
    sys.exit(0)


if __name__ == '__main__':
    main()
