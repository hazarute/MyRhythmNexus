#!/usr/bin/env python
"""
Automatic translation wrapping tool for desktop UI files.
This script wraps Turkish strings with _() function automatically.
"""

import re
from pathlib import Path
from typing import List, Tuple

DESKTOP_DIR = Path(__file__).parent / "desktop"

# Patterns to wrap (text=, placeholder_text=, title=)
PATTERNS_TO_WRAP = [
    (r'(text=)"([^"]*[ÇçĞğıİÖöŞşÜüÂâÎîûÛ][^"]*)"', r'\1_("\2")'),  # text="Turkish..."
    (r"(text=)'([^']*[ÇçĞğıİÖöŞşÜüÂâÎîûÛ][^']*)'", r"\1_('\2')"),    # text='Turkish...'
    (r'(placeholder_text=)"([^"]*[ÇçĞğıİÖöŞşÜüÂâÎîûÛ][^"]*)"', r'\1_("\2")'),  # placeholder_text="Turkish..."
    (r"(placeholder_text=)'([^']*[ÇçĞğıİÖöŞşÜüÂâÎîûÛ][^']*)'", r"\1_('\2')"),  # placeholder_text='Turkish...'
    (r'(title=)"([^"]*[ÇçĞğıİÖöŞşÜüÂâÎîûÛ][^"]*)"', r'\1_("\2")'),  # title="Turkish..."
    (r"(title=)'([^']*[ÇçĞğıİÖöŞşÜüÂâÎîûÛ][^']*)'", r"\1_('\2')"),  # title='Turkish...'
]

# Skip patterns
SKIP_PATTERNS = [
    r'_\(".*"\)',  # Already wrapped
    r'f".*{.*}.*"',  # f-strings
    r"f'.*{.*}.*'",
    r'_\(.*\)',  # Already has _()
]

def should_skip(match_str: str) -> bool:
    """Check if string should be skipped."""
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, match_str):
            return True
    return False

def needs_import(content: str) -> bool:
    """Check if file already imports _()"""
    return "from desktop.core.locale import _" in content

def add_import(content: str) -> str:
    """Add translation import to file"""
    if needs_import(content):
        return content
    
    # Find the line with the first import statement
    lines = content.split('\n')
    insert_pos = 0
    
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            insert_pos = i + 1
            break
    
    lines.insert(insert_pos, "from desktop.core.locale import _")
    return '\n'.join(lines)

def wrap_strings_in_file(file_path: Path) -> Tuple[int, int]:
    """
    Wrap Turkish strings in a file.
    Returns: (modifications_count, total_patterns_found)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Skip if already has locale import or is not a UI file
        if needs_import(content) or 'ui' not in str(file_path):
            return 0, 0
        
        # Add import
        content = add_import(content)
        
        # Apply wrapping patterns
        modifications = 0
        for pattern, replacement in PATTERNS_TO_WRAP:
            def replacer(match):
                if should_skip(match.group(0)):
                    return match.group(0)
                modifications += 1
                return re.sub(pattern, replacement, match.group(0))
            
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return modifications, len(PATTERNS_TO_WRAP)
        
        return 0, 0
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0, 0

def main():
    """Main entry point."""
    print("🔧 Auto-wrapping Turkish strings with _() function...\n")
    
    # Find all Python files in desktop/ui/
    ui_files = list((DESKTOP_DIR / "ui").glob("**/*.py"))
    
    total_mods = 0
    processed = 0
    
    for file_path in sorted(ui_files):
        if "__pycache__" in str(file_path):
            continue
        
        mods, patterns = wrap_strings_in_file(file_path)
        if mods > 0:
            print(f"✅ {file_path.relative_to(DESKTOP_DIR)}: {mods} strings wrapped")
            total_mods += mods
            processed += 1
    
    print(f"\n📊 Summary:")
    print(f"   Files processed: {processed}")
    print(f"   Strings wrapped: {total_mods}")
    print(f"\nNext step: Run 'python i18n_manager.py extract' to extract all strings")

if __name__ == "__main__":
    main()
