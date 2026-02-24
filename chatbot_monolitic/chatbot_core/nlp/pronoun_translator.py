"""
Traductor de pronombres
"""
from typing import List, Dict, Optional


class PronounTranslator:
    """Traduce pronombres en binding lists"""
    
    DEFAULT_PRONOUN_MAP = {
        "i": "you", "you": "i", "my": "your", "me": "you", "your": "my",
        "i've": "you've", "we've": "they've",
        "fred": "he", "jack": "he", "jane": "she",
    }
    
    def __init__(self, custom_map: Optional[Dict[str, str]] = None):
        self.pronoun_map = {**self.DEFAULT_PRONOUN_MAP}
        if custom_map:
            self.pronoun_map.update(custom_map)
    
    def translate(self, binding_list: List[List[str]]) -> List[List[str]]:
        """Traduce pronombres en una binding list"""
        result = []
        for binding in binding_list:
            if isinstance(binding, list):
                translated = [binding[0]]
                for word in binding[1:]:
                    translated.append(self.pronoun_map.get(word.lower(), word))
                result.append(translated)
            else:
                result.append(binding)
        return result
