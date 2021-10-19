import os
from logging import getLogger
from pathlib import Path
from typing import Dict, List

from pronunciation_dict_parser import export
from pronunciation_dict_parser.parser import parse_file
from text_utils.language import Language
from text_utils.symbol_format import SymbolFormat
from textgrid.textgrid import TextGrid
from textgrid_tools.core.mfa_utils import (
    add_layer_containing_original_text,
    add_phoneme_layer_containing_punctuation,
    convert_original_text_to_phonemes, get_pronunciation_dict, normalize_text)
from tqdm import tqdm


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
  # logger.info(f"Created backup: {backup_path}")
  logger.info(f"Written normalized output to: {out_path}")


def get_filepaths(parent_dir: Path) -> List[Path]:
  names = get_filenames(parent_dir)
  res = [parent_dir / x for x in names]
  return res


def get_filenames(parent_dir: Path) -> List[Path]:
  assert parent_dir.is_dir()
  _, _, filenames = next(os.walk(parent_dir))
  filenames.sort()
  filenames = [Path(filename) for filename in filenames]
  return filenames


def normalize_text_files_in_folder(base_dir: Path, folder_in: Path, text_format: SymbolFormat, language: Language, folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not folder_in.exists():
    raise Exception("Folder does not exist!")

  all_files = get_filepaths(folder_in)
  text_files = [file for file in all_files if str(file).endswith(".txt")]
  logger.info(f"Found {len(text_files)} .txt files.")

  text_file_in: Path
  for text_file_in in tqdm(text_files):
    text_file_out = folder_out / text_file_in.name
    if text_file_out.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {text_file_in.name}")
      continue

    logger.info(f"Processing {text_file_in}...")

    text = text_file_in.read_text()

    new_text = normalize_text(
      original_text=text,
      text_format=text_format,
      language=language,
    )

    folder_out.mkdir(parents=True, exist_ok=True)
    text_file_out.write_text(new_text, encoding="UTF-8")

  logger.info(f"Written normalized output to: {folder_out}")


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


def add_original_texts_layer(base_dir: Path, text_folder: Path, textgrid_folder_in: Path, reference_tier_name: str, new_tier_name: str, text_format: SymbolFormat, language: Language, trim_symbols: str, textgrid_folder_out: Path, overwrite: bool):
  logger = getLogger(__name__)

  if not text_folder.exists():
    raise Exception("Text folder does not exist!")

  if not textgrid_folder_in.exists():
    raise Exception("TextGrid folder does not exist!")

  all_files_text_folder = get_filepaths(text_folder)
  text_files_text_folder = [file for file in all_files_text_folder if str(file).endswith(".txt")]

  logger.info(f"Found {len(text_files_text_folder)} .txt files.")

  all_files_textgrid_folder = get_filepaths(textgrid_folder_in)
  textgrid_files_textgrid_folder = [
    file for file in all_files_textgrid_folder if str(file).endswith(".TextGrid")]

  logger.info(f"Found {len(textgrid_files_textgrid_folder)} .TextGrid files.")

  txt_files: Dict[str, Path] = {file.stem: file for file in text_files_text_folder}
  textgrid_files: Dict[str, Path] = {file.stem: file for file in textgrid_files_textgrid_folder}

  all_filenames = txt_files.keys() | textgrid_files.keys()

  logger.info(f"Found {len(all_filenames)} file names.")
  trim_symbols_set = set(trim_symbols)
  logger.info(f"Trim symbols: {' '.join(sorted(trim_symbols_set))} (#{len(trim_symbols_set)})")

  filename: str
  for filename in tqdm(sorted(all_filenames)):
    textgrid_file_out = textgrid_folder_out / f"{filename}.TextGrid"
    if textgrid_file_out.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {textgrid_file_out.name}")
      continue
    if filename not in txt_files:
      logger.warning(f"The .txt file for {filename} was not found!")
      continue
    if filename not in textgrid_files:
      logger.warning(f"The .TextGrid file for {filename} was not found!")
      continue

    logger.info(f"Processing {filename}...")

    txt_path = txt_files[filename]
    textgrid_path = textgrid_files[filename]

    grid = TextGrid()
    grid.read(textgrid_path)
    text = txt_path.read_text()

    add_layer_containing_original_text(
      grid=grid,
      language=language,
      new_tier_name=new_tier_name,
      original_text=text,
      overwrite_existing_tier=True,
      reference_tier_name=reference_tier_name,
      text_format=text_format,
      trim_symbols=trim_symbols_set,
    )

    textgrid_folder_out.mkdir(parents=True, exist_ok=True)
    grid.write(textgrid_file_out)

  logger.info(f"Written output .TextGrid files to: {textgrid_folder_out}")


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

  convert_original_text_to_phonemes(
    grid=grid,
    language=language,
    new_ipa_tier_name=new_tier_name,
    original_text_tier_name=original_text_tier_name,
    pronunciation_dict=pronunciation_dict,
    overwrite_existing_tiers=overwrite_existing_tier,
    text_format=text_format,
    trim_symbols=set(trim_symbols),
  )

  out_path.parent.mkdir(parents=True, exist_ok=True)
  grid.write(out_path)


def add_phonemes_from_words(base_dir: Path, folder_in: Path, original_text_tier_name: str, new_ipa_tier_name: str, new_arpa_tier_name: str, overwrite_existing_tiers: bool, text_format: SymbolFormat, language: Language, pronunciation_dict_file: Path, trim_symbols: str, folder_out: Path, overwrite: bool):
  logger = getLogger(__name__)

  if not folder_in.exists():
    raise Exception("Folder does not exist!")

  if not pronunciation_dict_file.exists():
    raise Exception("Pronunciation dictionary not found!")

  pronunciation_dict = parse_file(pronunciation_dict_file)

  all_files = get_filepaths(folder_in)
  textgrid_files = [file for file in all_files if str(file).endswith(".TextGrid")]
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  trim_symbols_set = set(trim_symbols)
  logger.info(f"Trim symbols: {' '.join(sorted(trim_symbols_set))} (#{len(trim_symbols_set)})")

  textgrid_file_in: Path
  for textgrid_file_in in tqdm(textgrid_files):
    textgrid_file_out = folder_out / textgrid_file_in.name
    if textgrid_file_out.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {textgrid_file_in.name}")
      continue

    logger.info(f"Processing {textgrid_file_in}...")

    grid = TextGrid()
    grid.read(textgrid_file_in)

    convert_original_text_to_phonemes(
      grid=grid,
      language=language,
      new_ipa_tier_name=new_ipa_tier_name,
      new_arpa_tier_name=new_arpa_tier_name,
      original_text_tier_name=original_text_tier_name,
      pronunciation_dict=pronunciation_dict,
      overwrite_existing_tiers=overwrite_existing_tiers,
      text_format=text_format,
      trim_symbols=trim_symbols_set,
    )

    folder_out.mkdir(parents=True, exist_ok=True)
    grid.write(textgrid_file_out)

  logger.info(f"Written output .TextGrid files to: {folder_out}")


def add_phonemes_from_phonemes(base_dir: Path, folder_in: Path, original_text_tier_name: str, reference_tier_name: str, new_ipa_tier_name: str, new_arpa_tier_name: str, overwrite_existing_tiers: bool, text_format: SymbolFormat, language: Language, pronunciation_dict_file: Path, trim_symbols: str, folder_out: Path, overwrite: bool):
  logger = getLogger(__name__)

  if not folder_in.exists():
    raise Exception("Folder does not exist!")

  if not pronunciation_dict_file.exists():
    raise Exception("Pronunciation dictionary not found!")

  pronunciation_dict = parse_file(pronunciation_dict_file)

  all_files = get_filepaths(folder_in)
  textgrid_files = [file for file in all_files if str(file).endswith(".TextGrid")]
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  trim_symbols_set = set(trim_symbols)
  logger.info(f"Trim symbols: {' '.join(sorted(trim_symbols_set))} (#{len(trim_symbols_set)})")

  textgrid_file_in: Path
  for textgrid_file_in in tqdm(textgrid_files):
    textgrid_file_out = folder_out / textgrid_file_in.name
    if textgrid_file_out.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {textgrid_file_in.name}")
      continue

    logger.info(f"Processing {textgrid_file_in}...")

    grid = TextGrid()
    grid.read(textgrid_file_in)

    add_phoneme_layer_containing_punctuation(
      grid=grid,
      language=language,
      new_ipa_tier_name=new_ipa_tier_name,
      new_arpa_tier_name=new_arpa_tier_name,
      reference_tier_name=reference_tier_name,
      original_text_tier_name=original_text_tier_name,
      pronunciation_dict=pronunciation_dict,
      overwrite_existing_tiers=overwrite_existing_tiers,
      text_format=text_format,
      trim_symbols=trim_symbols_set,
    )

    folder_out.mkdir(parents=True, exist_ok=True)
    grid.write(textgrid_file_out)

  logger.info(f"Written output .TextGrid files to: {folder_out}")
