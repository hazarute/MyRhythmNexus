#!/usr/bin/env python
"""
Translation management helper script for MyRhythmNexus Desktop Application
Handles extraction, initialization, and compilation of translation files
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List

# Project paths
PROJECT_ROOT = Path(__file__).parent
DESKTOP_DIR = PROJECT_ROOT / "desktop"
LOCALE_DIR = DESKTOP_DIR / "locale"
BABEL_CFG = PROJECT_ROOT / "babel.cfg"

# Supported languages
LANGUAGES = ["tr", "en"]
DOMAIN = "messages"


def run_command(cmd: List[str], description: str) -> bool:
    """
    Run a command and handle errors.
    
    Args:
        cmd: Command to run as list
        description: Description of what the command does
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"📝 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {description} failed with code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Error: Command not found. Make sure Babel is installed:")
        print(f"   pip install babel")
        return False


def extract_messages() -> bool:
    """Extract translatable strings from source code."""
    cmd = [
        sys.executable, "-m", "babel.messages.frontend",
        "extract",
        "-F", str(BABEL_CFG),
        "-o", str(LOCALE_DIR / "messages.pot"),
        "--project", "MyRhythmNexus",
        "--copyright-holder", "MyRhythmNexus Contributors",
        "--version", "1.0",
        str(DESKTOP_DIR)
    ]
    return run_command(cmd, "Extract translatable strings")


def init_catalog() -> bool:
    """Initialize translation catalogs for all languages."""
    success = True
    
    for lang in LANGUAGES:
        cmd = [
            sys.executable, "-m", "babel.messages.frontend",
            "init",
            f"--input-file={LOCALE_DIR / 'messages.pot'}",
            f"--output-dir={LOCALE_DIR}",
            f"--domain={DOMAIN}",
            f"--locale={lang}"
        ]
        
        if not run_command(cmd, f"Initialize {lang} catalog"):
            success = False
    
    return success


def update_catalog() -> bool:
    """Update existing translation catalogs."""
    success = True
    
    for lang in LANGUAGES:
        cmd = [
            sys.executable, "-m", "babel.messages.frontend",
            "update",
            f"--input-file={LOCALE_DIR / 'messages.pot'}",
            f"--output-dir={LOCALE_DIR}",
            f"--domain={DOMAIN}",
            f"--locale={lang}"
        ]
        
        if not run_command(cmd, f"Update {lang} catalog"):
            success = False
    
    return success


def compile_catalog() -> bool:
    """Compile translation catalogs to binary format."""
    success = True
    
    for lang in LANGUAGES:
        cmd = [
            sys.executable, "-m", "babel.messages.frontend",
            "compile",
            "-d", str(LOCALE_DIR),
            "-D", DOMAIN,
            "-l", lang,
            "--use-fuzzy"
        ]
        
        if not run_command(cmd, f"Compile {lang} catalog"):
            success = False
    
    return success


def show_usage():
    """Show usage information."""
    print("""
Usage: python i18n_manager.py <command>

Commands:
    extract     Extract translatable strings from source code
    init        Initialize translation catalogs for all languages
    update      Update existing translation catalogs
    compile     Compile translation catalogs to binary format
    workflow    Run complete workflow: extract -> update -> compile
    help        Show this help message

Example workflow:
    1. Wrap strings with _("string") in source code
    2. python i18n_manager.py extract
    3. Edit .po files in desktop/locale/{lang}/LC_MESSAGES/
    4. python i18n_manager.py compile

For more information, visit: https://babel.pocoo.org/
""")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Error: No command specified\n")
        show_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Ensure locale directory exists
    LOCALE_DIR.mkdir(parents=True, exist_ok=True)
    
    if command == "extract":
        success = extract_messages()
    elif command == "init":
        if not extract_messages():
            sys.exit(1)
        success = init_catalog()
    elif command == "update":
        if not extract_messages():
            sys.exit(1)
        success = update_catalog()
    elif command == "compile":
        success = compile_catalog()
    elif command == "workflow":
        print("\n🚀 Running complete i18n workflow...")
        success = extract_messages() and update_catalog() and compile_catalog()
        if success:
            print("\n✨ i18n workflow completed successfully!")
            print("Next step: Edit .po files in desktop/locale/{lang}/LC_MESSAGES/")
    elif command == "help":
        show_usage()
        sys.exit(0)
    else:
        print(f"Error: Unknown command '{command}'\n")
        show_usage()
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
