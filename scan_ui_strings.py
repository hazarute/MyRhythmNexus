#!/usr/bin/env python
"""
Helper script to wrap Turkish strings with _() function in desktop UI files.
This is a convenience tool for identifying and wrapping translatable strings.
"""

import re
import os
from pathlib import Path
from typing import List, Tuple

# Desktop UI files to process
DESKTOP_DIR = Path(__file__).parent / "desktop"
TARGET_PATTERNS = [
    "ui/windows/*.py",
    "ui/views/*.py",
    "ui/views/**/*.py",
    "ui/components/**/*.py",
]

# Strings that should NOT be wrapped (e.g., format strings, variables, etc)
SKIP_PATTERNS = [
    r'f".*{.*}.*"',  # f-strings with variables
    r"f'.*{.*}.*'",
    r'r".*"',  # raw strings
    r"r'.*'",
    r'"{.*}"',  # Just variables
    r"'{.*}'",
    r'^"$',  # Empty strings
    r"^''$",
]

# Common Turkish UI strings to look for
TURKISH_KEYWORDS = [
    "Uyarı", "Hata", "Başarılı", "Lütfen", "Geriş", "Düzenle", "Sil", "Kaydet",
    "İptal", "Ekle", "Güncelle", "Ara", "Seç", "Seçin", "Var", "Yok", "Evet",
    "Hayır", "Tamam", "Devam", "Sonra", "Önceki", "Sonraki", "Tümü", "Hiçbiri",
    "Kapat", "Aç", "Düzenle", "Yönet", "Tanım", "Ayar", "Tercih", "Kurulum",
    "Bilgi", "Detay", "Sayfan", "Menu", "Listem", "Yükle", "İndir", "Gönder",
    "Kopyala", "Yapıştır", "Kes", "Temizle", "Sıfırla", "Onayla", "Reddet",
]

def file_search(pattern: str, base_path: Path = DESKTOP_DIR) -> List[Path]:
    """Search for files matching glob pattern."""
    return list(base_path.glob(pattern))

def should_wrap(string_value: str) -> bool:
    """Check if a string should be wrapped with _()."""
    for skip_pattern in SKIP_PATTERNS:
        if re.match(skip_pattern, string_value):
            return False
    return True

def extract_strings(file_path: Path) -> List[Tuple[int, str, str]]:
    """Extract translatable strings from Python file."""
    strings = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Find string literals in common UI patterns
        patterns = [
            r'text=(["\'])(.+?)\1',  # text="..."
            r'placeholder_text=(["\'])(.+?)\1',  # placeholder_text="..."
            r'title=(["\'])(.+?)\1',  # title="..."
            r'configure\(text=(["\'])(.+?)\1',  # configure(text="...")
        ]
        
        for line_num, line in enumerate(content.split('\n'), 1):
            for pattern in patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    string_value = match.group(2)
                    if should_wrap(string_value) and any(kw in string_value for kw in TURKISH_KEYWORDS):
                        strings.append((line_num, match.group(0), string_value))
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return strings

def main():
    """Main entry point."""
    print("🔍 Scanning desktop UI files for translatable strings...\n")
    
    all_files = []
    for pattern in TARGET_PATTERNS:
        files = file_search(pattern)
        all_files.extend(files)
    
    total_strings = 0
    for file_path in sorted(set(all_files)):
        # Skip __pycache__
        if "__pycache__" in str(file_path):
            continue
        
        # Skip if already has _() import
        if "from desktop.core.locale import _" in file_path.read_text(encoding='utf-8', errors='ignore'):
            continue
        
        strings = extract_strings(file_path)
        if strings:
            print(f"📄 {file_path.relative_to(DESKTOP_DIR)}")
            for line_num, original, string_value in strings:
                print(f"   Line {line_num}: {original[:60]}")
            print()
            total_strings += len(strings)
    
    print(f"\n📊 Found {total_strings} potentially translatable strings across {len(set(all_files))} files")
    print("Next step: Use i18n_manager.py to extract and manage translations")

if __name__ == "__main__":
    main()
