"""
Internationalization (i18n) helper module for backend translations.
Provides translation support for ticket printing and other backend operations.
"""
import json
import os
from typing import Dict, Any, Optional

# Cache for loaded translations
_translations_cache: Dict[str, Dict[str, Any]] = {}

# Supported languages
SUPPORTED_LANGUAGES = ['en-US', 'es-MX']
DEFAULT_LANGUAGE = 'es-MX'

def _get_translations_path() -> str:
    """Get the absolute path to the translations directory."""
    # Get the project root (parent of app directory)
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(current_dir, 'translations')

def _load_translation_file(language: str) -> Dict[str, Any]:
    """
    Load translation file for the specified language.
    
    Args:
        language: Language code (e.g., 'en-US', 'es-MX')
    
    Returns:
        Dictionary with translations
    
    Raises:
        FileNotFoundError: If translation file doesn't exist
        json.JSONDecodeError: If translation file is invalid JSON
    """
    if language in _translations_cache:
        return _translations_cache[language]
    
    translations_path = _get_translations_path()
    file_path = os.path.join(translations_path, f'{language}.json')
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'Translation file not found: {file_path}')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        translations = json.load(f)
    
    _translations_cache[language] = translations
    return translations

def get_translation(key: str, language: str = DEFAULT_LANGUAGE, default: Optional[str] = None) -> str:
    """
    Get translation for a specific key.
    
    Args:
        key: Translation key in dot notation (e.g., 'TICKET.DATE')
        language: Language code (defaults to es-MX)
        default: Default value if translation not found
    
    Returns:
        Translated string or default value or the key itself
    
    Examples:
        >>> get_translation('TICKET.DATE', 'en-US')
        'DATE'
        >>> get_translation('TICKET.DATE', 'es-MX')
        'FECHA'
    """
    # Validate language
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    
    try:
        translations = _load_translation_file(language)
        
        # Navigate through nested keys
        keys = key.split('.')
        value = translations
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default if default is not None else key
        
        return str(value) if value is not None else (default if default is not None else key)
    
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f'Warning: Translation error for key "{key}" in language "{language}": {e}')
        return default if default is not None else key

def get_translations_dict(section: str, language: str = DEFAULT_LANGUAGE) -> Dict[str, str]:
    """
    Get all translations for a specific section.
    
    Args:
        section: Section name (e.g., 'TICKET')
        language: Language code (defaults to es-MX)
    
    Returns:
        Dictionary with all translations in the section
    
    Examples:
        >>> get_translations_dict('TICKET', 'en-US')
        {'DATE': 'DATE', 'TICKET_NUMBER': 'TICKET º', ...}
    """
    # Validate language
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    
    try:
        translations = _load_translation_file(language)
        
        if section in translations and isinstance(translations[section], dict):
            return translations[section]
        
        return {}
    
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f'Warning: Translation error for section "{section}" in language "{language}": {e}')
        return {}

def clear_cache():
    """Clear the translations cache. Useful for testing or reloading translations."""
    global _translations_cache
    _translations_cache.clear()
