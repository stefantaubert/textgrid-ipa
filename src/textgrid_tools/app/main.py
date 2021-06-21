from logging import getLogger
from pathlib import Path
from shutil import copy, rmtree

from scipy.io.wavfile import read, write
from text_utils import EngToIpaMode
from textgrid.textgrid import TextGrid
from textgrid_tools.core.main import (add_ipa_tier, add_pause_tier,
                                      add_words_tier, get_template_textgrid,
                                      log_tier_stats)

AUDIO_FILE = "audio.wav"


def get_recording_dir(base_dir: Path, recording_name: str) -> Path:
  return base_dir / recording_name


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


def convert_to_ipa(base_dir: Path, recording_name: str, in_step_name: str, out_step_name: str, in_tier_name: str, out_tier_name: str, mode: EngToIpaMode, replace_unknown_with: str, consider_ipa_annotations: bool, overwrite_step: bool, overwrite_tier: bool):
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
    replace_unknown_with=replace_unknown_with,
  )

  grid.write(out_step_path)
  logger.info("Done.")


def log_stats(base_dir: Path, recording_name: str, step_name: str, tier_name: str):
  logger = getLogger(__name__)
  logger.info("Stats")
  recording_dir = get_recording_dir(base_dir, recording_name)

  step_path = get_step_path(recording_dir, step_name)

  if not step_path.exists():
    logger.error(f"Step {step_path} does not exist.")
    return

  grid = TextGrid()
  grid.read(step_path)

  log_tier_stats(grid, tier_name)
