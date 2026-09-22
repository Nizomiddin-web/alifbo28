"""yozuv — özbek alifbolari orasida ötkazgiç."""
from .alphabets import OKINA, TUTUQ
from .converter import (
    DEFAULT,
    Options,
    Result,
    Target,
    convert,
    cyr_to_lat,
    lat_to_cyr,
    new_to_old,
    old_to_new,
    options_from,
    to_cyrillic,
    to_new,
    to_old,
)
from .detect import Script, detect, is_mixed
from .tables import (ALPHABET_SIZE, alphabet_rows, alphabet_table,
                     example_pairs, examples_text, letter_note)

__version__ = "1.0.0"
__all__ = [
    "OKINA", "TUTUQ", "DEFAULT", "Options", "Result", "Target", "Script",
    "convert", "detect", "is_mixed", "cyr_to_lat", "lat_to_cyr",
    "new_to_old", "old_to_new", "options_from", "to_cyrillic", "to_new", "to_old",
    "ALPHABET_SIZE", "alphabet_rows", "alphabet_table", "example_pairs",
    "examples_text", "letter_note",
]
