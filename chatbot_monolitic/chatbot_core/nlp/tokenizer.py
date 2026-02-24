"""
Tokenización de texto
"""
from typing import List


class Tokenizer:
    """Tokenización básica de texto"""
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tokeniza texto en palabras"""
        return text.lower().strip().replace("(", "").replace(")", "").split()
    
    @staticmethod
    def detokenize(tokens: List[str]) -> str:
        """Reconstruye texto desde tokens"""
        return " ".join(tokens)
