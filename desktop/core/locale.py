"""
Locale and i18n management for MyRhythmNexus Desktop Application
Provides gettext-based translation support for Turkish and English
"""

import gettext
import os
from pathlib import Path
from typing import Optional

# Get the locale directory
LOCALE_DIR = Path(__file__).parent.parent / "locale"

# Default language
DEFAULT_LANGUAGE = "tr"

# Available languages
AVAILABLE_LANGUAGES = {
    "tr": "Türkçe",
    "en": "English"
}

# Global translation object
_translation = None
_current_language = DEFAULT_LANGUAGE


def initialize_locale(language: str = DEFAULT_LANGUAGE) -> None:
    """
    Initialize the gettext translation system.
    
    Args:
        language: Language code ('tr' or 'en')
    
    Raises:
        ValueError: If language is not supported
    """
    global _translation, _current_language
    
    if language not in AVAILABLE_LANGUAGES:
        raise ValueError(f"Language '{language}' not supported. Available: {list(AVAILABLE_LANGUAGES.keys())}")
    
    _current_language = language
    
    try:
        _translation = gettext.translation(
            'messages',
            localedir=str(LOCALE_DIR),
            languages=[language],
            fallback=True
        )
    except Exception as e:
        print(f"Warning: Failed to load translation for '{language}': {e}")
        _translation = gettext.NullTranslations()


def _translate(message: str) -> str:
    """
    Translate a message string using gettext.
    
    Args:
        message: The message to translate
    
    Returns:
        Translated message or original if translation not found
    """
    if _translation is None:
        return message
    
    return _translation.gettext(message)


def _(message: str) -> str:
    """
    Gettext translation function. Use this to mark strings for translation.
    
    Example:
        from desktop.core.locale import _
        label = _("Hello World")
    
    Args:
        message: The message to translate
    
    Returns:
        Translated message or original if translation not found
    """
    return _translate(message)


def get_current_language() -> str:
    """Get the currently active language code."""
    return _current_language


def set_language(language: str) -> None:
    """
    Change the active language.
    
    Args:
        language: Language code ('tr' or 'en')
    
    Raises:
        ValueError: If language is not supported
    """
    initialize_locale(language)


def get_available_languages() -> dict:
    """Get dictionary of available languages {code: display_name}."""
    return AVAILABLE_LANGUAGES.copy()


def ngettext(singular: str, plural: str, count: int) -> str:
    """
    Translate plural forms.
    
    Args:
        singular: Singular form of the message
        plural: Plural form of the message
        count: Count to determine which form to use
    
    Returns:
        Translated message in appropriate form
    """
    if _translation is None:
        return singular if count == 1 else plural
    
    return _translation.ngettext(singular, plural, count)
