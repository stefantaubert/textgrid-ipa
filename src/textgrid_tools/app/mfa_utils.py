from pathlib import Path

from pronunciation_dict_parser import export
from text_utils.language import Language
from text_utils.symbol_format import SymbolFormat
from textgrid.textgrid import TextGrid
from textgrid_tools.core.mfa_utils import (add_layer_containing_original_text,
                                           add_layer_containing_punctuation,
                                           get_pronunciation_dict)


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


def add_original_text_layer(base_dir: Path, grid_path: Path, reference_tier_name: str, new_tier_name: str, overwrite_existing_tier: bool, text_path: Path, text_format: SymbolFormat, language: Language, out_path: Path):

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
  )

  out_path.parent.mkdir(parents=True, exist_ok=True)
  grid.write(out_path)


def add_arpa_punctuation_layer(base_dir: Path, grid_path: Path, reference_tier_name: str, original_text_tier_name: str, new_tier_name: str, overwrite_existing_tier: bool, text_format: SymbolFormat, language: Language, out_path: Path):
  if not grid_path.exists():
    raise Exception("Grid not found!")

  grid = TextGrid()
  grid.read(grid_path)

  add_layer_containing_punctuation(
    grid=grid,
    language=language,
    new_tier_name=new_tier_name,
    original_text_tier_name=original_text_tier_name,
    pronunciation_dict=None, # TODO
    overwrite_existing_tier=overwrite_existing_tier,
    reference_tier_name=reference_tier_name,
    text_format=text_format,
  )

  out_path.parent.mkdir(parents=True, exist_ok=True)
  grid.write(out_path)
