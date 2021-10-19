import os
import shutil
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from shutil import copy2
from typing import Dict, List

from general_utils import save_obj
from general_utils.main import cast_as, load_obj
from sentence2pronunciation.core import symbols_join
from speech_dataset_parser import (Gender, Language, PreData, PreDataList,
                                   Recording, Symbols, TextFormat, data,
                                   parse_custom, parse_ljs, save_custom)
from text_utils import text_to_symbols
from textgrid import TextGrid
from textgrid.textgrid import Interval, IntervalTier
from textgrid_tools.core.mfa_utils import interval_is_empty, tier_to_text
from tqdm import tqdm


@dataclass()
class TemporaryRecording:
  basename: str
  symbols_language: Language
  speaker_name: str
  speaker_accent: str
  speaker_gender: Gender
  relative_audio_path: Path


def data_has_unique_identifiers(data: PreDataList) -> bool:
  identifiers = [entry.identifier for entry in data.items()]
  all_identifiers_are_unique = len(set(identifiers)) == len(identifiers)
  return all_identifiers_are_unique


DATA_NAME = "data.pkl"
AUDIO_DIR_NAME = "audio"


def export_transcriptions_to_folder(dir_path: Path, data: PreDataList, target_folder: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)
  target_folder.mkdir(parents=True, exist_ok=True)

  assert data_has_unique_identifiers(data)

  temp_recordings = {}
  entry: PreData
  for entry in tqdm(data.items()):
    target_txt_path = target_folder / "txt_transcript" / f"{entry.relative_audio_path.stem}.txt"
    target_audio_path = target_folder / AUDIO_DIR_NAME / entry.relative_audio_path.name

    if target_txt_path.is_file():
      if not overwrite:
        logger.info(f"Skipping existing file: {target_txt_path}")
        continue
      os.remove(target_txt_path)
    if target_audio_path.is_file():
      if not overwrite:
        logger.info(f"Skipping existing file: {target_audio_path}")
        continue
      os.remove(target_audio_path)

    target_txt_path.parent.mkdir(exist_ok=True, parents=True)
    target_audio_path.parent.mkdir(exist_ok=True, parents=True)

    origin_audio_path = dir_path / entry.relative_audio_path
    copy2(origin_audio_path, target_audio_path)
    target_txt_path.write_text(''.join(entry.symbols))
    tmp_recording = TemporaryRecording(
      basename=entry.basename,
      speaker_accent=entry.speaker_accent,
      speaker_gender=entry.speaker_gender,
      speaker_name=entry.speaker_name,
      symbols_language=entry.symbols_language,
      relative_audio_path=target_audio_path.relative_to(target_folder),
    )
    temp_recordings[entry.identifier] = tmp_recording

  save_obj(temp_recordings, target_folder / DATA_NAME)
  logger.info(f"Written output to: {target_folder}")


def convert_to_dataset(folder: Path, textgrid_folder_name: str, tier_name: str, symbols_format: TextFormat, target_dir: Path) -> None:
  logger = getLogger(__name__)
  data_path = folder / DATA_NAME
  data = cast_as(load_obj(data_path), Dict[int, TemporaryRecording])
  result: List[Recording] = []
  entry: TemporaryRecording
  for identifier, entry in data.items():
    audio_path = folder / entry.relative_audio_path
    textgrid_path = folder / textgrid_folder_name / f"{identifier}.TextGrid"
    grid = TextGrid()
    grid.read(textgrid_path)
    tier = cast_as(grid.getFirst(tier_name), IntervalTier)
    if tier is None:
      logger.error(f"Tier {tier_name} not found!")
      raise Exception()

    content = []
    interval: Interval
    for interval in tier.intervals:
      if not interval_is_empty(interval):
        # only word layers are supported so far
        interval_symbols = text_to_symbols(
          text=interval.mark,
          text_format=symbols_format,
          lang=entry.symbols_language,
        )
        content.append(interval_symbols)

    symbols = symbols_join(content, join_symbol=" ")

    recording = Recording(
      basename=entry.basename,
      absolute_audio_path=audio_path,
      speaker_accent=entry.speaker_accent,
      speaker_gender=entry.speaker_gender,
      speaker_name=entry.speaker_name,
      symbols=symbols,
      symbols_format=symbols_format,
      symbols_language=entry.symbols_language,
    )

    result.append(recording)

  save_custom(result, target_dir)


def main():
  dir_path = Path("/data/datasets/LJSpeech-1.1")
  target_folder = Path("/home/mi/data/MFA/ljs")

  if False:
    res = parse_ljs(
      dir_path=dir_path,
    )

    export_transcriptions_to_folder(
      dir_path=dir_path,
      data=res,
      target_folder=target_folder,
      overwrite=True,
    )

    # TODO align via MFA here
  else:
    convert_to_dataset(
      folder=target_folder,
      target_dir="/tmp/out_ds",
      symbols_format=TextFormat.PHONEMES_IPA,
      textgrid_folder_name="texgrid_transcript",
      tier_name="words-ipa",
    )


if __name__ == "__main__":
  main()
