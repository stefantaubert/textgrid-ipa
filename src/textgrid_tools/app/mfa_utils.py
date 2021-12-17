from logging import getLogger
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple, cast

from general_utils import load_obj, save_obj
from general_utils.main import get_all_files_in_all_subfolders
from pronunciation_dict_parser import export
from pronunciation_dict_parser.default_parser import PublicDictType
from pronunciation_dict_parser.parser import parse_file
from scipy.io.wavfile import read
from sentence2pronunciation.lookup_cache import LookupCache
from text_utils.language import Language
from text_utils.symbol_format import SymbolFormat
from textgrid.textgrid import TextGrid
from textgrid_tools.core.mfa import *
from textgrid_tools.utils import get_filepaths
from tqdm import tqdm

# default was 8 but praat has 16
DEFAULT_TEXTGRID_PRECISION = 16

TEXTGRID_FILE_TYPE = ".TextGrid"
AUDIO_FILE_TYPE = ".wav"


def convert_texts_to_arpa_dicts(base_dir: Path, folder_in: Path, trim_symbols: str, consider_annotations: bool, out_path_mfa_dict: Optional[Path], out_path_cache: Optional[Path], out_path_punctuation_dict: Optional[Path], dict_type: PublicDictType, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not folder_in.exists():
    raise Exception("Folder does not exist!")

  if out_path_mfa_dict is not None and out_path_mfa_dict.is_file() and not overwrite:
    logger.info(f"{out_path_mfa_dict} already exists!")
    return

  if out_path_punctuation_dict is not None and out_path_punctuation_dict.is_file() and not overwrite:
    logger.info(f"{out_path_punctuation_dict} already exists!")
    return

  trim_symbols_set = set(trim_symbols)
  logger.info(f"Trim symbols: {' '.join(sorted(trim_symbols_set))} (#{len(trim_symbols_set)})")

  all_files = get_filepaths(folder_in)
  text_files = [file for file in all_files if file.suffix.lower() == ".txt"]
  logger.info(f"Found {len(text_files)} .txt files.")

  text_file_in: Path
  text_contents: List[str] = []
  for text_file_in in tqdm(text_files):
    logger.info(f"Processing {text_file_in}...")
    text = text_file_in.read_text()
    text_contents.append(text)

  logger.info("Producing dictionary...")

  pronunciation_dict, pronunciation_dict_punctuation, cache = get_arpa_pronunciation_dicts_from_texts(
    texts=text_contents,
    trim_symbols=trim_symbols_set,
    dict_type=dict_type,
    consider_annotations=consider_annotations,
    ignore_case=True,
    n_jobs=15,
    split_on_hyphen=True,
  )

  if out_path_mfa_dict is not None:
    logger.info(f"Saving {out_path_mfa_dict}...")
    export(
      include_counter=True,
      path=out_path_mfa_dict,
      pronunciation_dict=pronunciation_dict,
      symbol_sep=" ",
      word_pronunciation_sep="  ",
    )
    logger.info(f"Written pronunciation dictionary for MFA alignment to: {out_path_mfa_dict}")

  if out_path_punctuation_dict is not None:
    logger.info(f"Saving {out_path_punctuation_dict}...")
    export(
      include_counter=True,
      path=out_path_punctuation_dict,
      pronunciation_dict=pronunciation_dict_punctuation,
      symbol_sep=" ",
      word_pronunciation_sep="  ",
    )
    logger.info(
        f"Written pronunciation dictionary for adding punctuation phonemes to: {out_path_punctuation_dict}")

  if out_path_cache is not None:
    logger.info(f"Saving {out_path_cache}...")
    save_obj(cache, out_path_cache)
    logger.info(
        f"Written cache to: {out_path_cache}")

  return


def get_files_dict(folder: Path, filetype: str) -> Dict[str, Path]:
  all_files = get_all_files_in_all_subfolders(folder)
  resulting_files = {str(file.relative_to(folder).parent / file.stem): file.relative_to(folder)
                     for file in all_files if file.suffix.lower() == filetype.lower()}
  return resulting_files


def normalize_text_files_in_folder(base_dir: Path, folder_in: Path, folder_out: Path, overwrite: bool) -> None:
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
    )

    folder_out.mkdir(parents=True, exist_ok=True)
    text_file_out.write_text(new_text, encoding="UTF-8")

  logger.info(f"Written normalized output to: {folder_out}")


def files_extract_tier_to_text(base_dir: Path, textgrid_folder_in: Path, tier_name: str, txt_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not textgrid_folder_in.exists():
    raise Exception("Textgrid folder does not exist!")

  all_files = get_filepaths(textgrid_folder_in)
  textgrid_files = [file for file in all_files if file.suffix.lower() == ".textgrid"]
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  textgrid_file_in: Path
  for textgrid_file_in in tqdm(textgrid_files):
    text_file_out = txt_folder_out / f"{textgrid_file_in.stem}.txt"
    if text_file_out.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {textgrid_file_in.name}")
      continue

    logger.info(f"Processing {textgrid_file_in}...")
    grid = TextGrid()
    grid.read(textgrid_file_in, round_digits=DEFAULT_TEXTGRID_PRECISION)

    text = extract_tier_to_text(grid, tier_name=tier_name)

    txt_folder_out.mkdir(parents=True, exist_ok=True)
    text_file_out.write_text(text, encoding="UTF-8")

  logger.info(f"Written text output to: {txt_folder_out}")


def extract_sentences_text_files(base_dir: Path, text_folder_in: Path, audio_folder: Path, text_format: SymbolFormat, language: Language, time_factor: float, tier_name: str, folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not text_folder_in.exists():
    raise Exception("Text folder does not exist!")

  if not audio_folder.exists():
    raise Exception("Audio folder does not exist!")

  all_text_files = get_filepaths(text_folder_in)
  txt_files = [file for file in all_text_files if file.suffix.lower() == ".txt"]
  logger.info(f"Found {len(txt_files)} .txt files.")

  all_audio_files = get_filepaths(audio_folder)
  wav_files = {file.stem: file for file in all_audio_files if file.suffix.lower() == ".wav"}
  logger.info(f"Found {len(wav_files)} .wav files.")

  txt_file_in: Path
  for txt_file_in in tqdm(txt_files):
    text_file_out = folder_out / txt_file_in.name
    if text_file_out.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {txt_file_in.name}")
      continue

    if txt_file_in.stem not in wav_files:
      logger.error(f"For the .txt file {txt_file_in} no .wav file was found. Skipping...")
      continue

    logger.info(f"Processing {txt_file_in}...")

    text = txt_file_in.read_text()

    audio_path = wav_files[txt_file_in.stem]
    sr, wav = read(audio_path)

    grid = extract_sentences_to_textgrid(
      original_text=text,
      audio=wav,
      sr=sr,
      tier_name=tier_name,
      time_factor=time_factor,
    )

    folder_out.mkdir(parents=True, exist_ok=True)
    grid_file_out = folder_out / f"{txt_file_in.stem}.TextGrid"
    grid.write(grid_file_out)

  logger.info(f"Written .TextGrid files to: {folder_out}")


def merge_words_to_new_textgrid(base_dir: Path, folder_in: Path, reference_tier_name: str, min_pause_s: float, new_tier_name: str, overwrite_existing_tier: bool, folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not folder_in.exists():
    raise Exception("TextGrid folder does not exist!")

  all_text_files = get_filepaths(folder_in)
  textgrid_files = [file for file in all_text_files if file.suffix.lower() == ".textgrid"]
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  grid_file_in: Path
  for grid_file_in in tqdm(textgrid_files):
    grid_file_out = folder_out / grid_file_in.name
    if grid_file_out.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {grid_file_in.name}")
      continue

    logger.info(f"Processing {grid_file_in}...")

    grid = TextGrid()
    grid.read(grid_file_in, round_digits=DEFAULT_TEXTGRID_PRECISION)

    merge_words_together(
      grid=grid,
      new_tier_name=new_tier_name,
      reference_tier_name=reference_tier_name,
      min_pause_s=min_pause_s,
      overwrite_existing_tier=overwrite_existing_tier,
    )

    folder_out.mkdir(parents=True, exist_ok=True)
    grid.write(grid_file_out)

  logger.info(f"Written .TextGrid files to: {folder_out}")


def add_original_texts_layer(base_dir: Path, text_folder: Path, textgrid_folder_in: Path, reference_tier_name: str, new_tier_name: str, path_align_dict: Path, textgrid_folder_out: Path, overwrite_existing_tier: bool, overwrite: bool):
  logger = getLogger(__name__)

  if not text_folder.exists():
    raise Exception("Text folder does not exist!")

  if not textgrid_folder_in.exists():
    raise Exception("TextGrid folder does not exist!")

  if not path_align_dict.exists():
    raise Exception("Alignment dictionary does not exist!")

  all_files_text_folder = get_filepaths(text_folder)
  text_files_text_folder = [file for file in all_files_text_folder if str(file).endswith(".txt")]

  logger.info(f"Found {len(text_files_text_folder)} .txt files.")

  all_files_textgrid_folder = get_filepaths(textgrid_folder_in)
  textgrid_files_textgrid_folder = [
    file for file in all_files_textgrid_folder if str(file).endswith(".TextGrid")]

  logger.info(f"Found {len(textgrid_files_textgrid_folder)} .TextGrid files.")

  txt_files: Dict[str, Path] = {file.stem: file for file in text_files_text_folder}
  textgrid_files: Dict[str, Path] = {file.stem: file for file in textgrid_files_textgrid_folder}

  alignment_dict = parse_file(path_align_dict)

  all_filenames = txt_files.keys() | textgrid_files.keys()

  logger.info(f"Found {len(all_filenames)} file names.")

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

    logger.debug(f"Processing {filename}...")

    txt_path = txt_files[filename]
    textgrid_path = textgrid_files[filename]

    grid = TextGrid()
    grid.read(textgrid_path, round_digits=DEFAULT_TEXTGRID_PRECISION)
    text = txt_path.read_text()

    add_layer_containing_original_text(
      grid=grid,
      new_tier_name=new_tier_name,
      original_text=text,
      overwrite_existing_tier=overwrite_existing_tier,
      reference_tier_name=reference_tier_name,
      alignment_dict=alignment_dict,
    )

    textgrid_folder_out.mkdir(parents=True, exist_ok=True)
    grid.write(textgrid_file_out)

  logger.info(f"Written output .TextGrid files to: {textgrid_folder_out}")


def add_graphemes(base_dir: Path, folder_in: Path, original_text_tier_name: str, new_tier_name: str, overwrite_existing_tier: bool, folder_out: Path, overwrite: bool):
  logger = getLogger(__name__)

  if not folder_in.exists():
    raise Exception("Folder does not exist!")

  all_files = get_filepaths(folder_in)
  textgrid_files = [file for file in all_files if str(file).endswith(".TextGrid")]
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  textgrid_file_in: Path
  for textgrid_file_in in tqdm(textgrid_files):
    textgrid_file_out = folder_out / textgrid_file_in.name
    if textgrid_file_out.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {textgrid_file_in.name}")
      continue

    logger.debug(f"Processing {textgrid_file_in}...")

    grid = TextGrid()
    grid.read(textgrid_file_in, round_digits=DEFAULT_TEXTGRID_PRECISION)

    add_graphemes_from_words(
      grid=grid,
      new_tier_name=new_tier_name,
      original_text_tier_name=original_text_tier_name,
      overwrite_existing_tier=overwrite_existing_tier,
    )

    folder_out.mkdir(parents=True, exist_ok=True)
    grid.write(textgrid_file_out)

  logger.info(f"Written output .TextGrid files to: {folder_out}")


def app_transcribe_words_to_arpa(base_dir: Path, folder_in: Path, original_text_tier_name: str, consider_annotations: bool, tier_name: str, overwrite_existing_tier: bool, path_cache: Path, folder_out: Path, overwrite: bool):
  logger = getLogger(__name__)

  if not folder_in.exists():
    raise Exception("Folder does not exist!")

  if not path_cache.exists():
    raise Exception("Cache not found!")

  cache = cast(LookupCache, load_obj(path_cache))

  all_files = get_filepaths(folder_in)
  textgrid_files = [file for file in all_files if str(file).endswith(".TextGrid")]
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  textgrid_file_in: Path
  for textgrid_file_in in tqdm(textgrid_files):
    textgrid_file_out = folder_out / textgrid_file_in.name
    if textgrid_file_out.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {textgrid_file_in.name}")
      continue

    logger.debug(f"Processing {textgrid_file_in}...")

    grid = TextGrid()
    grid.read(textgrid_file_in, round_digits=DEFAULT_TEXTGRID_PRECISION)

    transcribe_words_to_arpa(
      grid=grid,
      tier_name=tier_name,
      original_text_tier_name=original_text_tier_name,
      cache=cache,
      overwrite_existing_tier=overwrite_existing_tier,
      consider_annotations=consider_annotations,
      ignore_case=True,
    )

    folder_out.mkdir(parents=True, exist_ok=True)
    grid.write(textgrid_file_out)

  logger.info(f"Written output .TextGrid files to: {folder_out}")


def app_transcribe_words_to_arpa_on_phoneme_level(base_dir: Path, folder_in: Path, words_tier_name: str, phoneme_tier_name: str, arpa_tier_name: str, consider_annotations: bool, overwrite_existing_tier: bool, path_cache: Path, trim_symbols: str, folder_out: Path, overwrite: bool):
  logger = getLogger(__name__)

  if not folder_in.exists():
    raise Exception("Folder does not exist!")

  if not path_cache.exists():
    raise Exception("Cache not found!")

  cache = load_obj(path_cache)

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

    logger.debug(f"Processing {textgrid_file_in}...")

    grid = TextGrid()
    grid.read(textgrid_file_in, round_digits=DEFAULT_TEXTGRID_PRECISION)

    transcribe_words_to_arpa_on_phoneme_level(
      grid=grid,
      arpa_tier_name=arpa_tier_name,
      phoneme_tier_name=phoneme_tier_name,
      words_tier_name=words_tier_name,
      cache=cache,
      overwrite_existing_tier=overwrite_existing_tier,
      trim_symbols=trim_symbols_set,
      consider_annotations=consider_annotations,
      ignore_case=True,
    )

    folder_out.mkdir(parents=True, exist_ok=True)
    grid.write(textgrid_file_out)

  logger.info(f"Written output .TextGrid files to: {folder_out}")
