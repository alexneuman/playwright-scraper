
from fuzzywuzzy import fuzz, process

def closest_match(string: str, choices: list[str], min_score: float|bool = None) -> str:
    """
    Returns the closest match to string in choices.
    """
    closest = process.extractOne(string, choices)
    if min_score:
        if closest[1] < min_score:
            return ''
    return closest[0]


def is_close_match(string: str, choices: list[str] | str, min_score=0.8) -> bool:
    """
    Returns True if string is a close match to one of the choices.
    Can either be a list of choices or a single choice.
    """
    return fuzz.ratio(string, closest_match(string, choices)) > min_score

