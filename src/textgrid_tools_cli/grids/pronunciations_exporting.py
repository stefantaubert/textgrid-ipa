from argparse import ArgumentParser, Namespace
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Optional
from typing import OrderedDict as OrderedDictType

from ordered_set import OrderedSet
from pronunciation_dictionary import PronunciationDict, SerializationOptions, save_dict
from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools.grids.dictionary_exporting import create_dictionaries
from textgrid_tools.validation import ValidationError
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (GRID_FILE_TYPE, ConvertToOrderedSetAction,
                                       add_directory_argument, add_encoding_argument,
                                       get_files_in_folder, get_grid_files, get_subfolders,
                                       parse_non_empty_or_whitespace, try_load_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_pronunciations_exporting_parser(parser: ArgumentParser):
  parser.description = "This command assigns a mark for each interval having a specific duration."
  add_directory_argument(parser)
  parser.add_argument("words_tier", type=parse_non_empty_or_whitespace, metavar="WORDS-TIER",
                      help="tier containing the words in the intervals")
  parser.add_argument("pronunciations_tier", type=parse_non_empty_or_whitespace, metavar="PRONUNCIATIONS-TIER",
                      help="tier containing the pronunciations in the intervals")
  parser.add_argument("output_name", type=parse_non_empty_or_whitespace, metavar="OUTPUT-NAME",
                      help="name of the dictionary file exported relative to DIRECTORY")
  parser.add_argument("--scope", type=str, choices=["folder", "all"],
                      metavar="SCOPE", help="scope for creation of dictionary file(s): folder -> consider all files of the subfolders together; all -> consider all files together", default="all")
  parser.add_argument("--ignore", type=str, metavar="MARK", nargs="*",
                      help="ignore intervals in the WORDS-TIER containing these marks", default=OrderedSet(("",)), action=ConvertToOrderedSetAction)
  add_encoding_argument(parser)
  return app_create_dictionary


def app_create_dictionary(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  resulting_files = (f for f in get_files_in_folder(
    ns.directory) if f.suffix.lower() == GRID_FILE_TYPE.lower())
  resulting_files = OrderedDict(sorted(
    (str(file.relative_to(ns.directory).parent / file.stem), file.relative_to(ns.directory))
      for file in resulting_files
  ))

  grids_to_groups: Dict[str, OrderedDictType[str, Path]] = {}
  if len(resulting_files) > 0:
    grids_to_groups[None] = resulting_files

  for subfolder in get_subfolders(ns.directory):
    subfolder_name = subfolder.relative_to(ns.directory)
    assert subfolder_name not in grids_to_groups
    grids_to_groups[subfolder_name] = get_grid_files(subfolder)

  loaded_grids: Dict[str, List[TextGrid]] = {}
  loaded_successful = True
  logger.info("Reading files...")
  for group_name, grids in tqdm(grids_to_groups.items()):
    for file_nr, (file_stem, rel_path) in enumerate(grids.items(), start=1):
      flogger.info(f"Processing {file_stem}")
      if group_name is None:
        grid_file_in_abs = ns.directory / rel_path
      else:
        grid_file_in_abs = ns.directory / group_name / rel_path
      error, grid = try_load_grid(grid_file_in_abs, ns.encoding)

      if error:
        flogger.debug(error.exception)
        flogger.error(error.default_message)
        flogger.info("Skipped.")
        loaded_successful = False
        continue
      assert grid is not None

      if group_name not in loaded_grids:
        loaded_grids[group_name] = []

      loaded_grids[group_name].append(grid)

  if len(loaded_grids) == 0:
    return loaded_successful, False

  error, result = create_dictionaries(
    loaded_grids, ns.words_tier, ns.pronunciations_tier, ns.scope, ns.ignore, flogger)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  logger.info("Applied operations successfully.")

  all_successful = True
  if ns.scope == "all":
    assert isinstance(result, OrderedDict)
    output_path = ns.directory / ns.output_name
    error = try_save_dict(result, output_path, ns.encoding)
    if error:
      logger.debug(error.exception)
      logger.error(error.default_message)
      all_successful = False
    logger.info(f"Saved pronunciation dictionary to: '{output_path.absolute()}'")
  elif ns.scope == "folder":
    for group_name, pronunciation_dict in result.items():
      if group_name is None:
        output_path = ns.directory / ns.output_name
      else:
        output_path = ns.directory / group_name / ns.output_name
      error = try_save_dict(pronunciation_dict, output_path, ns.encoding)
      if error:
        logger.debug(error.exception)
        logger.error(error.default_message)
        all_successful = False
        continue
      logger.info(f"Saved pronunciation dictionary to: '{output_path.absolute()}'")
  else:
    assert False

  return all_successful, True


class DictionaryCouldNotBeSavedError(ValidationError):
  def __init__(self, path: Path, exception: Exception) -> None:
    super().__init__()
    self.path = path
    self.exception = exception

  @property
  def default_message(self) -> str:
    return "Dictionary couldn't be saved!"


def try_save_dict(dictionary: PronunciationDict, path: Path, encoding: str) -> Optional[DictionaryCouldNotBeSavedError]:
  try:
    save_dict(dictionary, path, encoding, SerializationOptions("DOUBLE-SPACE", False, True))
  except Exception as ex:
    return DictionaryCouldNotBeSavedError(path, ex)
  return None
