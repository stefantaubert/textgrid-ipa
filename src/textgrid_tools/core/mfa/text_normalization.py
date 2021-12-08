
from text_utils.language import Language
from text_utils.symbol_format import SymbolFormat
from text_utils.text import text_normalize


def normalize_text(original_text: str) -> str:
  original_text = original_text.replace("\n", " ")
  original_text = original_text.replace("\r", "")

  result = text_normalize(
    text=original_text,
    lang=Language.ENG,
    text_format=SymbolFormat.GRAPHEMES,
  )

  return result
