import os
import json
from flask import request

LOCALES_DIR = os.path.join(os.path.dirname(__file__), 'locales')
_translations = {}

def load_translations():
    global _translations
    # Always reload for now so translations update immediately without server restart
        
    for lang in ['zh', 'en']:
        path = os.path.join(LOCALES_DIR, f'{lang}.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                _translations[lang] = json.load(f)
        else:
            _translations[lang] = {}
            
    return _translations

def get_locale():
    # Priority: Cookie -> Default to zh
    return request.cookies.get('lang', 'zh')

def get_locale_dict():
    lang = get_locale()
    translations = load_translations()
    return translations.get(lang, translations.get('zh', {}))

def _(key):
    lang = get_locale()
    translations = load_translations()
    
    # Try current language, fallback to key itself
    lang_dict = translations.get(lang, {})
    
    # If key doesn't exist in dict, return the key as fallback
    return lang_dict.get(key, key)
