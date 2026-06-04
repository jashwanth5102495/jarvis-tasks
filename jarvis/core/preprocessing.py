import re
from typing import List, Tuple


class Preprocessor:
    def __init__(self):
        # "up", "down", "left", "right" are intentionally NOT stop words —
        # they are directional keywords needed for desktop control commands
        # like "scroll down", "move mouse to the right", "press up".
        self.stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "shall", "should", "can", "could", "may", "might",
            "must", "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
            "you", "your", "yours", "yourself", "yourselves", "he", "him", "his",
            "himself", "she", "her", "hers", "herself", "it", "its", "itself",
            "they", "them", "their", "theirs", "themselves", "what", "which",
            "who", "whom", "this", "that", "these", "those", "am",
        }

    def preprocess(self, text: str) -> Tuple[str, List[str]]:
        # Lowercase the text
        text_lower = text.lower()

        # Remove extra whitespace and special characters
        text_clean = re.sub(r'[^\w\s]', '', text_lower)
        text_clean = re.sub(r'\s+', ' ', text_clean).strip()

        # Tokenize
        tokens = text_clean.split()

        # Remove stop words
        tokens_filtered = [token for token in tokens if token not in self.stop_words]

        return text_clean, tokens_filtered
