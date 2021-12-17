
import os
import shutil
from logging import getLogger
from pathlib import Path

from speech_dataset_parser.data import PreDataList
from speech_dataset_parser.gender import Gender
from speech_dataset_parser.language import Language
from speech_dataset_parser.text_format import TextFormat


def data_has_unique_identifiers(data: PreDataList) -> bool:
  identifiers = [entry.identifier for entry in data.items()]
  all_identifiers_are_unique = len(set(identifiers)) == len(identifiers)
  return all_identifiers_are_unique


def export_transcriptions_to_folder(data: PreDataList, target_folder: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)
  target_folder.mkdir(parents=True, exist_ok=True)

  attach_nrs = not data_has_unique_identifiers(data)
  if attach_nrs:
    logger.info(
      "The identifiers of the data are not unique therefore adding an index at the start of the entry name.")

  for entry_id, entry in enumerate(data.items()):
    prepend_str = f"{entry_id}-" if attach_nrs else ""
    target_txt_path = target_folder / f"{prepend_str}{entry.relative_audio_path.stem}.txt"
    if target_txt_path.is_file():
      if not overwrite:
        logger.info(f"Skipping existing file: {target_txt_path}")
        continue
      os.remove(target_txt_path)
    target_txt_path.write_text(entry.symbols)

  logger.info(f"Written output to: {target_folder}")
