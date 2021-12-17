import re
from logging import getLogger
from pathlib import Path
from shutil import copy, rmtree
from typing import Optional

from scipy.io.wavfile import read, write
from text_utils.language import Language
from text_utils.pronunciation.main import EngToIPAMode
from textgrid.textgrid import TextGrid
from textgrid_tools.core.extract_audio import (extract_words_to_audio,
                                               get_extracts_df)
from textgrid_tools.core.main import (add_ipa_tier, add_pause_tier,
                                      add_words_tier, export_csv,
                                      get_template_textgrid, log_tier_stats)
from textgrid_tools.core.to_dataset import Entry, convert_textgrid2dataset
from textgrid_tools.utils import save_dataclasses
from tqdm import tqdm

AUDIO_FILE = "audio.wav"

DATA_CSV_NAME = "data.csv"
AUDIO_FOLDER_NAME = "audio"


def get_recording_dir(base_dir: Path, recording_name: str) -> Path:
  return base_dir / recording_name


def get_audio_extraction_dir(recording_dir: Path, step_name: str) -> Path:
  return recording_dir / step_name


def get_step_path(recording_dir: Path, step_name: str) -> Path:
  return recording_dir / f"{step_name}.TextGrid"


def get_audio_path(recording_dir: Path) -> Path:
  return recording_dir / AUDIO_FILE


def add_recording(base_dir: Path, recording_name: str, audio_path: Path, out_step_name: str, overwrite_recording: bool):
  logger = getLogger(__name__)
  logger.info("Adding recording...")
  recording_dir = get_recording_dir(base_dir, recording_name)
  if not audio_path.exists():
    logger.error("Audio file does not exist.")
    return
  if recording_dir.exists():
    if overwrite_recording:
      rmtree(recording_dir)
      logger.info("Removed existing recording.")
    else:
      logger.error("Recording already exists.")
      return

  sr, wav = read(audio_path)

  logger.info("Creating folder...")
  recording_dir.mkdir(parents=True, exist_ok=False)
  logger.info("Adding wav...")
  dest_audio_path = get_audio_path(recording_dir)
  write(dest_audio_path, rate=sr, data=wav)
  logger.info("Adding textgrid...")
  out_step_path = get_step_path(recording_dir, out_step_name)
  grid = get_template_textgrid(wav, sr)
  grid.write(out_step_path)

  logger.info("Done.")


def clone(base_dir: Path, recording_name: str, in_step_name: str, out_step_name: str, overwrite_step: bool):
  logger = getLogger(__name__)
  logger.info("Cloning recording step...")
  recording_dir = get_recording_dir(base_dir, recording_name)

  in_step_path = get_step_path(recording_dir, in_step_name)
  out_step_path = get_step_path(recording_dir, out_step_name)
  if not in_step_path.exists():
    logger.error(f"Step {in_step_name} does not exist.")
    return
  if out_step_path.exists():
    if overwrite_step:
      rmtree(recording_dir)
      logger.info(f"Removed step {out_step_name} recording.")
    else:
      logger.error(f"Step {out_step_name} already exists.")
      return

  logger.info("Copying TextGrid file...")
  copy(in_step_path, out_step_path)

  logger.info("Done.")


def detect_silence(base_dir: Path, recording_name: str, in_step_name: str, out_step_name: str, out_tier_name: str, silence_boundary: float, chunk_size_ms: int, min_silence_duration_ms: int, min_content_duration_ms: int, content_buffer_start_ms: int, content_buffer_end_ms: int, silence_mark: str, content_mark: str, overwrite_step: bool, overwrite_tier: bool):
  logger = getLogger(__name__)
  logger.info("Detecting silence...")
  recording_dir = get_recording_dir(base_dir, recording_name)

  in_step_path = get_step_path(recording_dir, in_step_name)
  out_step_path = get_step_path(recording_dir, out_step_name)
  audio_path = get_audio_path(recording_dir)
  assert audio_path.exists()

  if not in_step_path.exists():
    logger.error(f"Step {in_step_name} does not exist.")
    return
  if out_step_path.exists():
    if overwrite_step:
      rmtree(recording_dir)
      logger.info(f"Removed step {out_step_name} recording.")
    else:
      logger.error(f"Step {out_step_name} already exists.")
      return

  logger.info("Reading data...")
  sr, wav = read(audio_path)
  grid = TextGrid()
  grid.read(in_step_path)

  logger.info("Detecting silence parts...")

  add_pause_tier(
    grid=grid,
    chunk_size_ms=chunk_size_ms,
    content_buffer_start_ms=content_buffer_start_ms,
    content_buffer_end_ms=content_buffer_end_ms,
    content_mark=content_mark,
    silence_mark=silence_mark,
    silence_boundary=silence_boundary,
    min_content_duration_ms=min_content_duration_ms,
    min_silence_duration_ms=min_silence_duration_ms,
    out_tier_name=out_tier_name,
    sr=sr,
    wav=wav,
    overwrite_tier=overwrite_tier,
  )

  grid.write(out_step_path)
  logger.info("Done.")


def extract_words(base_dir: Path, recording_name: str, in_step_name: str, out_step_name: str, in_tier_name: str, out_tier_name: str, overwrite_step: bool, overwrite_tier: bool):
  logger = getLogger(__name__)
  logger.info("Extracting words...")
  recording_dir = get_recording_dir(base_dir, recording_name)

  in_step_path = get_step_path(recording_dir, in_step_name)
  out_step_path = get_step_path(recording_dir, out_step_name)
  audio_path = get_audio_path(recording_dir)
  assert audio_path.exists()

  if not in_step_path.exists():
    logger.error(f"Step {in_step_name} does not exist.")
    return
  if out_step_path.exists():
    if overwrite_step:
      rmtree(recording_dir)
      logger.info(f"Removed step {out_step_name} recording.")
    else:
      logger.error(f"Step {out_step_name} already exists.")
      return

  logger.info("Reading data...")
  grid = TextGrid()
  grid.read(in_step_path)

  logger.info("Extracting words...")
  add_words_tier(
    grid=grid,
    in_tier_name=in_tier_name,
    out_tier_name=out_tier_name,
    overwrite_tier=overwrite_tier,
  )

  grid.write(out_step_path)
  logger.info("Done.")


def convert_to_ipa(base_dir: Path, recording_name: str, in_step_name: str, out_step_name: str, in_tier_name: str, out_tier_name: str, mode: Optional[EngToIPAMode], replace_unknown_with: str, consider_ipa_annotations: bool, in_tier_lang: Language, overwrite_step: bool, overwrite_tier: bool):
  logger = getLogger(__name__)
  logger.info("Converting to IPA...")
  recording_dir = get_recording_dir(base_dir, recording_name)

  in_step_path = get_step_path(recording_dir, in_step_name)
  out_step_path = get_step_path(recording_dir, out_step_name)
  audio_path = get_audio_path(recording_dir)
  assert audio_path.exists()

  if not in_step_path.exists():
    logger.error(f"Step {in_step_name} does not exist.")
    return
  if out_step_path.exists():
    if overwrite_step:
      rmtree(recording_dir)
      logger.info(f"Removed step {out_step_name} recording.")
    else:
      logger.error(f"Step {out_step_name} already exists.")
      return

  logger.info("Reading data...")
  grid = TextGrid()
  grid.read(in_step_path)

  logger.info("Converting to IPA...")

  add_ipa_tier(
    grid=grid,
    in_tier_name=in_tier_name,
    out_tier_name=out_tier_name,
    overwrite_tier=overwrite_tier,
    consider_ipa_annotations=consider_ipa_annotations,
    mode=mode,
    in_tier_lang=in_tier_lang,
    replace_unknown_with=replace_unknown_with,
  )

  grid.write(out_step_path)
  logger.info("Done.")


def log_stats(base_dir: Path, recording_name: str, step_name: str, tier_name: str, tier_lang: Language, ignore_arcs: Optional[bool], ignore_tones: Optional[bool], replace_unknown_ipa_by: Optional[str]):
  logger = getLogger(__name__)
  logger.info(f"Stats for recording: {recording_name}")
  recording_dir = get_recording_dir(base_dir, recording_name)

  step_path = get_step_path(recording_dir, step_name)

  if not step_path.exists():
    logger.error(f"Step {step_path} does not exist.")
    return

  grid = TextGrid()
  grid.read(step_path)

  ipa_settings = None
  # ipa_settings = IPAExtractionSettings(
  #   ignore_arcs=ignore_arcs,
  #   ignore_tones=ignore_tones,
  #   replace_unknown_ipa_by=replace_unknown_ipa_by,
  # )

  log_tier_stats(grid, tier_name, tier_lang, ipa_settings)


def to_dataset(base_dir: Path, recording_name: str, step_name: str, tier_name: str, tier_lang: Language, duration_s_max: float, ignore_empty_marks: bool, output_dir: Path, speaker_name: str, speaker_gender: str, speaker_accent: str, overwrite_output: bool):
  logger = getLogger(__name__)
  logger.info(f"Converting recording {recording_name} on tier {tier_name} to dataset...")
  recording_dir = get_recording_dir(base_dir, recording_name)

  step_path = get_step_path(recording_dir, step_name)
  audio_path = get_audio_path(recording_dir)
  assert audio_path.exists()

  if not step_path.exists():
    logger.error(f"Step {step_name} does not exist.")
    return
  if output_dir.exists():
    if overwrite_output:
      rmtree(output_dir)
      logger.info(f"Removed: {output_dir}.")
    else:
      logger.error(f"Folder {output_dir} already exists.")
      return

  logger.info("Reading data...")
  sr, wav = read(audio_path)
  grid = TextGrid()
  grid.read(step_path)

  logger.info("Converting to dataset...")
  res = convert_textgrid2dataset(
    grid=grid,
    tier_name=tier_name,
    tier_lang=tier_lang,
    wav=wav,
    sr=sr,
    duration_s_max=duration_s_max,
    speaker_accent=speaker_accent,
    speaker_gender=speaker_gender,
    speaker_name=speaker_name,
    ignore_empty_marks=ignore_empty_marks,
  )

  logger.info("Writing output files...")
  entry: Entry
  output_dir.mkdir(parents=True, exist_ok=False)
  audio_dir = output_dir / AUDIO_FOLDER_NAME
  audio_dir.mkdir(parents=False, exist_ok=False)

  for entry, out_wav in tqdm(res):
    wav_path = audio_dir / entry.wav
    write(wav_path, sr, out_wav)

  data_path = output_dir / DATA_CSV_NAME
  save_dataclasses([x for x, _ in res], data_path)

  logger.info("Done.")


def export_to_csv(base_dir: Path, recording_name: str, step_name: str, graphemes_tier_name: str, graphemes_tier_lang: Language, phonemes_tier_name: str, phones_tier_name: str, overwrite: bool):
  logger = getLogger(__name__)
  logger.info(f"Stats for recording: {recording_name}")
  recording_dir = get_recording_dir(base_dir, recording_name)

  step_path = get_step_path(recording_dir, step_name)
  output_path = recording_dir / f"{step_name}.csv"

  if not step_path.exists():
    logger.error(f"Step {step_path} does not exist.")
    return

  if output_path.exists() and not overwrite:
    logger.error("Already exported!")
    return

  grid = TextGrid()
  grid.read(step_path)

  df = export_csv(
    grid=grid,
    graphemes_tier_name=graphemes_tier_name,
    graphemes_tier_lang=graphemes_tier_lang,
    phonemes_tier_name=phonemes_tier_name,
    phones_tier_name=phones_tier_name,
  )

  df.to_csv(output_path, header=True, sep="\t")
  logger.info(f"Written output to: {output_path}")
  logger.info("Done.")


def extract_audios(base_dir: Path, recording_name: str, step_name: str, graphemes_tier_name: str, phonemes_tier_name: str, phones_tier_name: str, overwrite: bool):
  logger = getLogger(__name__)
  logger.info(f"Stats for recording: {recording_name}")
  recording_dir = get_recording_dir(base_dir, recording_name)

  step_path = get_step_path(recording_dir, step_name)

  if not step_path.exists():
    logger.error(f"Step {step_path} does not exist.")
    return

  audio_extraction_dir = get_audio_extraction_dir(recording_dir, step_name)

  if audio_extraction_dir.exists():
    if overwrite:
      rmtree(audio_extraction_dir)
      logger.info("Removed existing export.")
    else:
      logger.error("Already exported!")
      return

  audio_path = get_audio_path(recording_dir)
  assert audio_path.exists()

  logger.info("Reading data...")
  sr, wav = read(audio_path)
  grid = TextGrid()
  grid.read(step_path)

  result = extract_words_to_audio(
    grid=grid,
    graphemes_tier_name=graphemes_tier_name,
    phonemes_tier_name=phonemes_tier_name,
    phones_tier_name=phones_tier_name,
    wav=wav,
    sr=sr,
  )

  audio_extraction_dir.mkdir(parents=False, exist_ok=False)
  logger.info("Saving audios...")
  for i, ((graphemes, phonemes), extracts) in enumerate(tqdm(result.items())):
    dir_name = f"{i+1}_{graphemes.replace('/', '_')}_{phonemes}_({len(extracts)})"
    current_folder = audio_extraction_dir / dir_name
    assert not current_folder.exists()
    current_folder.mkdir(parents=False, exist_ok=False)
    df = get_extracts_df(extracts)
    df_path = current_folder / "details.csv"
    df.to_csv(df_path, sep="\t", header=True, index=False)

    for j, extract in enumerate(extracts):
      wav_file_path = current_folder / f"{j+1}_{extract.phones}.wav"
      write(wav_file_path, sr, extract.audio)

  logger.info(f"Written output to: {audio_extraction_dir}")
  logger.info("Done.")
