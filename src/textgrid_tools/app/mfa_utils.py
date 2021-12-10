from logging import getLogger
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple, cast

from general_utils import load_obj, save_obj
from general_utils.main import get_all_files_in_all_subfolders
from pronunciation_dict_parser import export
from pronunciation_dict_parser.default_parser import PublicDictType
from pronunciation_dict_parser.parser import parse_file
from scipy.io.wavfile import read, write
from sentence2pronunciation.lookup_cache import LookupCache
from text_utils.language import Language
from text_utils.symbol_format import SymbolFormat
from textgrid.textgrid import TextGrid
from textgrid_tools.core.mfa import *
from textgrid_tools.core.mfa.audio_grid_syncing import sync_grid_to_audio
from textgrid_tools.core.mfa.symbol_removal import remove_symbols
from textgrid_tools.core.mfa.tier_cloning import clone_tier
from textgrid_tools.core.mfa.tier_moving import move_tier
from textgrid_tools.core.mfa.tier_renaming import rename_tier
from textgrid_tools.utils import get_filepaths
from tqdm import tqdm

# default was 8 but praat has 15
DEFAULT_TEXTGRID_PRECISION = 15

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


def files_remove_tiers(base_dir: Path, folder_in: Path, tier_names: List[str], folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  tier_names_set = set(tier_names)
  if len(tier_names_set) == 0:
    logger.error("Please specify at least one tier!")
    return

  textgrid_files = get_files_dict(folder_in, filetype=TEXTGRID_FILE_TYPE)
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  logger.info("Reading files...")
  textgrid_file_in_rel: Path
  for _, textgrid_file_in_rel in cast(Iterable[Tuple[str, Path]], tqdm(textgrid_files.items())):
    textgrid_file_out_abs = folder_out / textgrid_file_in_rel
    if textgrid_file_out_abs.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {textgrid_file_in_rel.name}")
      continue

    grid = TextGrid()
    grid.read(folder_in / textgrid_file_in_rel, round_digits=DEFAULT_TEXTGRID_PRECISION)
    remove_tiers(grid, tier_names_set)
    textgrid_file_out_abs.parent.mkdir(parents=True, exist_ok=True)
    grid.write(textgrid_file_out_abs)

  logger.info(f"Done. Written output to: {folder_out}")
  return


def files_remove_symbols(base_dir: Path, folder_in: Path, tier_names: List[str], symbols: List[str], folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  tier_names_set = set(tier_names)
  if len(tier_names_set) == 0:
    logger.error("Please specify at least one tier!")
    return

  symbols_set = set(symbols)
  if len(symbols_set) == 0:
    logger.error("Please specify at least one symbol!")
    return

  textgrid_files = get_files_dict(folder_in, filetype=TEXTGRID_FILE_TYPE)
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  logger.info("Reading files...")
  textgrid_file_in_rel: Path
  for _, textgrid_file_in_rel in cast(Iterable[Tuple[str, Path]], tqdm(textgrid_files.items())):
    textgrid_file_out_abs = folder_out / textgrid_file_in_rel
    if textgrid_file_out_abs.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {textgrid_file_in_rel.name}")
      continue

    grid = TextGrid()
    grid.read(folder_in / textgrid_file_in_rel, round_digits=DEFAULT_TEXTGRID_PRECISION)
    remove_symbols(grid, tier_names_set, symbols)
    textgrid_file_out_abs.parent.mkdir(parents=True, exist_ok=True)
    grid.write(textgrid_file_out_abs)

  logger.info(f"Done. Written output to: {folder_out}")
  return


def get_files_dict(folder: Path, filetype: str) -> Dict[str, Path]:
  all_files = get_all_files_in_all_subfolders(folder)
  resulting_files = {str(file.relative_to(folder).parent / file.stem): file.relative_to(folder)
                     for file in all_files if file.suffix.lower() == filetype.lower()}
  return resulting_files


def files_rename_tier(base_dir: Path, folder_in: Path, tier_name: str, new_tier_name: str, folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  textgrid_files = get_files_dict(folder_in, filetype=TEXTGRID_FILE_TYPE)
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  logger.info("Reading files...")
  textgrid_file_in_rel: Path
  for _, textgrid_file_in_rel in cast(Iterable[Tuple[str, Path]], tqdm(textgrid_files.items())):
    textgrid_file_out_abs = folder_out / textgrid_file_in_rel
    if textgrid_file_out_abs.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {textgrid_file_in_rel.name}")
      continue

    grid = TextGrid()
    grid.read(folder_in / textgrid_file_in_rel, round_digits=DEFAULT_TEXTGRID_PRECISION)
    rename_tier(grid, tier_name, new_tier_name)
    textgrid_file_out_abs.parent.mkdir(parents=True, exist_ok=True)
    grid.write(textgrid_file_out_abs)

  logger.info(f"Done. Written output to: {folder_out}")
  return


def files_clone_tier(base_dir: Path, folder_in: Path, tier_name: str, new_tier_name: str, folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  textgrid_files = get_files_dict(folder_in, filetype=TEXTGRID_FILE_TYPE)
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  logger.info("Reading files...")
  for file_path, textgrid_file_in_rel in cast(Iterable[Tuple[str, Path]], tqdm(textgrid_files.items())):
    textgrid_file_out_abs = folder_out / textgrid_file_in_rel
    if textgrid_file_out_abs.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {textgrid_file_in_rel.name}")
      continue

    grid = TextGrid()
    grid.read(folder_in / textgrid_file_in_rel, round_digits=DEFAULT_TEXTGRID_PRECISION)
    logger.info(f"Cloning tier \"{tier_name}\" in file \"{file_path}\"...")
    clone_tier(grid, tier_name, new_tier_name)
    textgrid_file_out_abs.parent.mkdir(parents=True, exist_ok=True)
    grid.write(textgrid_file_out_abs)

  logger.info(f"Done. Written output to: {folder_out}")
  return


def files_move_tier(base_dir: Path, folder_in: Path, tier_name: str, position: int, folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  textgrid_files = get_files_dict(folder_in, filetype=TEXTGRID_FILE_TYPE)
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  logger.info("Reading files...")
  for _, textgrid_file_in_rel in cast(Iterable[Tuple[str, Path]], tqdm(textgrid_files.items())):
    textgrid_file_out_abs = folder_out / textgrid_file_in_rel
    if textgrid_file_out_abs.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {textgrid_file_in_rel.name}")
      continue

    grid = TextGrid()
    grid.read(folder_in / textgrid_file_in_rel, round_digits=DEFAULT_TEXTGRID_PRECISION)
    move_tier(grid, tier_name, position)
    textgrid_file_out_abs.parent.mkdir(parents=True, exist_ok=True)
    grid.write(textgrid_file_out_abs)

  logger.info(f"Done. Written output to: {folder_out}")
  return


def files_split_intervals(base_dir: Path, folder_in: Path, audio_folder_in: Path, reference_tier_name: str, split_marks: str, folder_out: Path, audio_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not folder_in.exists():
    raise Exception("Textgrid folder does not exist!")

  if not audio_folder_in.exists():
    raise Exception("Audio folder does not exist!")

  split_marks_set = set(split_marks.split(" "))
  if len(split_marks_set) == 0:
    return

  all_files = get_filepaths(folder_in)
  textgrid_files = [file for file in all_files if file.suffix.lower() == ".textgrid"]
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  all_audio_files = get_filepaths(audio_folder_in)
  wav_files = {file.stem: file for file in all_audio_files if file.suffix.lower() == ".wav"}
  logger.info(f"Found {len(wav_files)} .wav files.")

  logger.info("Reading files...")
  textgrid_file_in: Path
  for textgrid_file_in in tqdm(textgrid_files):
    logger.info(f"Processing {textgrid_file_in.stem}...")
    textgrid_files_out = folder_out / textgrid_file_in.stem
    wav_files_out = audio_folder_out / f"{textgrid_file_in.stem}"
    if (textgrid_files_out.exists() or wav_files_out.exists()) and not overwrite:
      logger.info(f"Skipped already existing file (.TextGrid or .wav): {textgrid_file_in.name}")
      continue

    if textgrid_file_in.stem not in wav_files:
      logger.error(f"For the .TextGrid file {textgrid_file_in} no .wav file was found. Skipping...")
      continue

    grid = TextGrid()
    grid.read(textgrid_file_in, round_digits=DEFAULT_TEXTGRID_PRECISION)

    audio_path = wav_files[textgrid_file_in.stem]
    sr, wav = read(audio_path)
    success, grids_wavs = split_grid(
      grid, wav, sr, reference_tier_name, split_marks_set, n_digits=DEFAULT_TEXTGRID_PRECISION)

    if success:
      assert grids_wavs is not None
      logger.info("Saving...")
      textgrid_files_out.mkdir(parents=True, exist_ok=True)
      wav_files_out.mkdir(parents=True, exist_ok=True)
      for i, (new_grid, new_wav) in enumerate(tqdm(grids_wavs)):
        grid_out_path = textgrid_files_out / f"{i}.TextGrid"
        wav_out_path = wav_files_out / f"{i}.wav"
        new_grid.write(grid_out_path)
        write(wav_out_path, sr, new_wav)

  logger.info(f"Done. Written output to: {folder_out}")


def files_remove_intervals(base_dir: Path, folder_in: Path, audio_folder_in: Path, reference_tier_name: str, remove_marks: Optional[List[str]], remove_empty: bool, folder_out: Path, audio_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not folder_in.exists():
    raise Exception("Textgrid folder does not exist!")

  if not audio_folder_in.exists():
    raise Exception("Audio folder does not exist!")

  remove_marks_set = set(remove_marks) if remove_marks is not None else set()

  if len(remove_marks_set) == 0 and not remove_empty:
    logger.info("Please set marks and/or remove_empty!")
    return

  logger.info(f"Marks: {remove_marks_set} and empty: {'yes' if remove_empty else 'no'}")

  all_files = get_filepaths(folder_in)
  textgrid_files = [file for file in all_files if file.suffix.lower() == ".textgrid"]
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  all_audio_files = get_filepaths(audio_folder_in)
  wav_files = {file.stem: file for file in all_audio_files if file.suffix.lower() == ".wav"}
  logger.info(f"Found {len(wav_files)} .wav files.")

  logger.info("Reading files...")
  textgrid_file_in: Path
  for textgrid_file_in in tqdm(textgrid_files):
    logger.info(f"Processing {textgrid_file_in.stem}...")
    textgrid_file_out = folder_out / textgrid_file_in.name
    wav_file_out = audio_folder_out / f"{textgrid_file_in.stem}.wav"
    if (textgrid_file_out.exists() or wav_file_out.exists()) and not overwrite:
      logger.info(f"Skipped already existing file (.TextGrid or .wav): {textgrid_file_in.name}")
      continue

    if textgrid_file_in.stem not in wav_files:
      logger.error(f"For the .TextGrid file {textgrid_file_in} no .wav file was found. Skipping...")
      continue

    logger.info(f"Removing intervals with: {remove_marks}")

    grid = TextGrid()
    grid.read(textgrid_file_in, round_digits=DEFAULT_TEXTGRID_PRECISION)

    audio_path = wav_files[textgrid_file_in.stem]
    sr, wav = read(audio_path)
    logger.info("Removing intervals...")
    success, new_wav = remove_intervals(grid, wav, sr, reference_tier_name,
                                        remove_marks_set, remove_empty,
                                        n_digits=DEFAULT_TEXTGRID_PRECISION)
    if success:
      assert new_wav is not None
      textgrid_file_out.parent.mkdir(parents=True, exist_ok=True)
      grid.write(textgrid_file_out)

      wav_file_out.parent.mkdir(parents=True, exist_ok=True)
      write(wav_file_out, sr, new_wav)

  logger.info(f"Done. Written output to: {folder_out}")


def files_sync_grids(base_dir: Path, folder: Path, audio_folder: Path, folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not folder.exists():
    raise Exception("Textgrid folder does not exist!")

  if not audio_folder.exists():
    raise Exception("Audio folder does not exist!")

  textgrid_files = get_files_dict(folder, filetype=TEXTGRID_FILE_TYPE)
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  audio_files = get_files_dict(audio_folder, filetype=AUDIO_FILE_TYPE)
  logger.info(f"Found {len(audio_files)} audio files.")

  logger.info("Reading files...")
  textgrid_file_in_rel: Path
  # changed_anything = False
  all_successfull = True
  for path, textgrid_file_in_rel in cast(Iterable[Tuple[str, Path]], tqdm(textgrid_files.items())):
    if path not in audio_files:
      logger.info(f"No corresponding audio file found for {str(textgrid_file_in_rel)}!")
      continue

    textgrid_file_out_abs = folder_out / textgrid_file_in_rel
    audio_file_out_abs = folder_out / audio_files[path]
    if (textgrid_file_out_abs.exists() or audio_file_out_abs.exists()) and not overwrite:
      logger.info(f"Skipped already existing file: {path}")
      continue

    grid = TextGrid()
    grid.read(folder / textgrid_file_in_rel, round_digits=DEFAULT_TEXTGRID_PRECISION)
    audio_file_in_abs = audio_folder / audio_files[path]
    sr, wav = read(audio_file_in_abs)

    success = sync_grid_to_audio(
      grid, wav, sr, ndigits=DEFAULT_TEXTGRID_PRECISION)
    # changed_anything |= changed_something
    all_successfull &= success

    if success:
      textgrid_file_out_abs.parent.mkdir(parents=True, exist_ok=True)
      grid.write(textgrid_file_out_abs)

  if not all_successfull:
    logger.info("Not all was successfull!")
  else:
    logger.info("All was successfull!")
  # if not changed_anything:
  #   logger.info("Didn't changed anything.")
  logger.info(f"Done. Written output to: {folder_out}")


def files_fix_boundaries(base_dir: Path, folder_in: Path, reference_tier_name: str, difference_threshold: Optional[float], folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not folder_in.exists():
    raise Exception("Textgrid folder does not exist!")

  all_files = get_filepaths(folder_in)
  textgrid_files = [file for file in all_files if file.suffix.lower() == ".textgrid"]
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")
  success = True
  logger.info("Reading files...")
  textgrid_file_in: Path
  for textgrid_file_in in tqdm(textgrid_files):
    textgrid_file_out = folder_out / textgrid_file_in.name
    if textgrid_file_out.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {textgrid_file_in.name}")
      continue

    grid = TextGrid()
    grid.read(textgrid_file_in, round_digits=DEFAULT_TEXTGRID_PRECISION)
    logger.info("Fixing interval boundaries...")
    success &= fix_interval_boundaries_grid(grid, reference_tier_name, difference_threshold)
    logger.info("Saving output...")
    textgrid_file_out.parent.mkdir(parents=True, exist_ok=True)
    grid.write(textgrid_file_out)
    logger.info(f"Written grid to: {textgrid_file_out}")

  if success:
    logger.info(f"Done. Everything was successfully fixed!")
  else:
    logger.info(f"Done. Not everything was successfully fixed!")
  logger.info(f"Written output to: {folder_out}")


def files_print_stats(base_dir: Path, folder: Path, duration_threshold: float, print_symbols_tier_names: List[str]) -> None:
  logger = getLogger(__name__)

  if not folder.exists():
    raise Exception("Textgrid folder does not exist!")

  all_files = get_filepaths(folder)
  textgrid_files = [file for file in all_files if file.suffix.lower() == ".textgrid"]
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  for textgrid_file_in in textgrid_files:
    grid = TextGrid()
    grid.read(textgrid_file_in, round_digits=DEFAULT_TEXTGRID_PRECISION)
    logger.info(f"Statistics for file {textgrid_file_in.relative_to(folder)}")
    print_stats(grid, duration_threshold, set(print_symbols_tier_names))
    logger.info("")


def files_map_arpa_to_ipa(base_dir: Path, folder_in: Path, arpa_tier_name: str, folder_out: Path, ipa_tier_name: str, overwrite_existing_tier: bool, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not folder_in.exists():
    raise Exception("Textgrid folder does not exist!")

  all_files = get_filepaths(folder_in)
  textgrid_files = [file for file in all_files if file.suffix.lower() == ".textgrid"]
  logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

  logger.info("Reading files...")
  for textgrid_file_in in cast(Iterator[Path], tqdm(textgrid_files)):
    textgrid_file_out = folder_out / textgrid_file_in.name
    if textgrid_file_out.exists() and not overwrite:
      logger.info(f"Skipped already existing file: {textgrid_file_in.name}")
      continue

    grid = TextGrid()
    grid.read(textgrid_file_in, round_digits=DEFAULT_TEXTGRID_PRECISION)

    logger.info("Mapping ARPA to IPA...")
    map_arpa_to_ipa(
      grid=grid,
      arpa_tier_name=arpa_tier_name,
      ipa_tier_name=ipa_tier_name,
      overwrite_existing_tier=overwrite_existing_tier,
    )

    textgrid_file_out.parent.mkdir(parents=True, exist_ok=True)
    grid.write(textgrid_file_out)

  logger.info(f"Done. Written output to: {folder_out}")


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


def add_marker(base_dir: Path, folder_in: Path, reference_tier_name: str, new_tier_name: str, overwrite_existing_tier: bool, folder_out: Path, overwrite: bool):
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

    add_marker_tier(
      grid=grid,
      reference_tier_name=reference_tier_name,
      new_tier_name=new_tier_name,
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
