import re

OFFENSIVE_WORDS = [
    # Español
    "idiota", "imbécil", "estúpido", "maldito", "mierda", "puta", "puto",
    "pendejo", "cabrón", "hijo de puta", "hijueputa", "gonorrea", "marica",
    "maricón", "culero", "verga", "coño", "joder", "culo",
    # English
    "fuck", "shit", "asshole", "bitch", "bastard", "damn", "crap",
    "dick", "pussy", "nigger", "faggot",
]

def contains_profanity(text: str) -> bool:
    text_lower = text.lower()
    for word in OFFENSIVE_WORDS:
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, text_lower):
            return True
    return False