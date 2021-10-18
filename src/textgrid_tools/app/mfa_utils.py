from logging import getLogger
from pathlib import Path

from pronunciation_dict_parser import export
from pronunciation_dict_parser.parser import parse_file
from text_utils.language import Language
from text_utils.symbol_format import SymbolFormat
from textgrid.textgrid import TextGrid
from textgrid_tools.core.mfa_utils import (
    add_ipa_layer_containing_punctuation, add_layer_containing_original_text,
    convert_original_text_to_arpa, convert_original_text_to_ipa,
    get_pronunciation_dict, normalize_text)


def convert_text_to_dict(base_dir: Path, text_path: Path, text_format: SymbolFormat, language: Language, out_path: Path):
  if not text_path.exists():
    raise Exception("File does not exist!")

  text = text_path.read_text()
  text = text.strip()

  pronunciation_dict = get_pronunciation_dict(
    language=language,
    text=text,
    text_format=text_format,
  )

  out_path.parent.mkdir(parents=True, exist_ok=True)

  export(
    include_counter=True,
    path=out_path,
    pronunciation_dict=pronunciation_dict,
    symbol_sep=" ",
    word_pronunciation_sep="  ",
  )


def normalize_text_file(base_dir: Path, text_path: Path, text_format: SymbolFormat, language: Language, out_path: Path) -> None:
  if not text_path.exists():
    raise Exception("File does not exist!")

  text = text_path.read_text()

  new_text = normalize_text(
    original_text=text,
    text_format=text_format,
    language=language,
  )

  # backup_path = Path(text_path + ".backup")
  # backup_path.write_text(text, encoding="UTF-8")
  out_path.write_text(new_text, encoding="UTF-8")
  logger = getLogger(__name__)
  #logger.info(f"Created backup: {backup_path}")
  logger.info(f"Written normalized output to: {out_path}")


def add_original_text_layer(base_dir: Path, grid_path: Path, reference_tier_name: str, new_tier_name: str, overwrite_existing_tier: bool, text_path: Path, text_format: SymbolFormat, language: Language, out_path: Path, trim_symbols: str):

  if not text_path.exists():
    raise Exception("File does not exist!")

  text = text_path.read_text()
  text = text.strip()

  if not grid_path.exists():
    raise Exception("Grid not found!")

  grid = TextGrid()
  grid.read(grid_path)

  add_layer_containing_original_text(
    grid=grid,
    language=language,
    new_tier_name=new_tier_name,
    original_text=text,
    overwrite_existing_tier=overwrite_existing_tier,
    reference_tier_name=reference_tier_name,
    text_format=text_format,
    trim_symbols=set(trim_symbols),
  )

  out_path.parent.mkdir(parents=True, exist_ok=True)
  grid.write(out_path)


def add_arpa_from_words(base_dir: Path, grid_path: Path, original_text_tier_name: str, new_tier_name: str, overwrite_existing_tier: bool, text_format: SymbolFormat, language: Language, pronunciation_dict_file: Path, out_path: Path, trim_symbols: str):
  if not grid_path.exists():
    raise Exception("Grid not found!")

  grid = TextGrid()
  grid.read(grid_path)

  if not pronunciation_dict_file.exists():
    raise Exception("Pronunciation dictionary not found!")

  pronunciation_dict = parse_file(pronunciation_dict_file)

  convert_original_text_to_arpa(
    grid=grid,
    language=language,
    new_tier_name=new_tier_name,
    original_text_tier_name=original_text_tier_name,
    pronunciation_dict=pronunciation_dict,
    overwrite_existing_tier=overwrite_existing_tier,
    text_format=text_format,
    trim_symbols=set(trim_symbols),
  )

  out_path.parent.mkdir(parents=True, exist_ok=True)
  grid.write(out_path)


def add_ipa_from_words(base_dir: Path, grid_path: Path, original_text_tier_name: str, new_tier_name: str, overwrite_existing_tier: bool, text_format: SymbolFormat, language: Language, pronunciation_dict_file: Path, out_path: Path, trim_symbols: str):
  if not grid_path.exists():
    raise Exception("Grid not found!")

  grid = TextGrid()
  grid.read(grid_path)

  if not pronunciation_dict_file.exists():
    raise Exception("Pronunciation dictionary not found!")

  pronunciation_dict = parse_file(pronunciation_dict_file)

  convert_original_text_to_ipa(
    grid=grid,
    language=language,
    new_tier_name=new_tier_name,
    original_text_tier_name=original_text_tier_name,
    pronunciation_dict=pronunciation_dict,
    overwrite_existing_tier=overwrite_existing_tier,
    text_format=text_format,
    trim_symbols=set(trim_symbols),
  )

  out_path.parent.mkdir(parents=True, exist_ok=True)
  grid.write(out_path)


def add_ipa_punctuation_layer(base_dir: Path, grid_path: Path, reference_tier_name: str, original_text_tier_name: str, new_tier_name: str, overwrite_existing_tier: bool, text_format: SymbolFormat, language: Language, pronunciation_dict_file: Path, out_path: Path, trim_symbols: str):
  if not grid_path.exists():
    raise Exception("Grid not found!")

  grid = TextGrid()
  grid.read(grid_path)

  if not pronunciation_dict_file.exists():
    raise Exception("Pronunciation dictionary not found!")

  pronunciation_dict = parse_file(pronunciation_dict_file)

  add_ipa_layer_containing_punctuation(
    grid=grid,
    language=language,
    new_tier_name=new_tier_name,
    original_text_tier_name=original_text_tier_name,
    pronunciation_dict=pronunciation_dict,
    overwrite_existing_tier=overwrite_existing_tier,
    reference_tier_name=reference_tier_name,
    text_format=text_format,
    trim_symbols=set(trim_symbols),
  )

  out_path.parent.mkdir(parents=True, exist_ok=True)
  grid.write(out_path)
