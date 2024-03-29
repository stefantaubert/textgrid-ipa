from argparse import ArgumentParser, Namespace
from pathlib import Path
from shutil import copy
from typing import cast

from ordered_set import OrderedSet
from tqdm import tqdm

from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_encoding_argument, get_optional, parse_path,
                                       parse_txt_path)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_audio_paths_importing_parser(parser: ArgumentParser):
  parser.description = "This command imports all files from one text file containing paths."
  parser.add_argument("path", type=parse_txt_path, metavar="PATH",
                      help="path to import the paths (*.txt)")
  parser.add_argument("output_directory", metavar='OUTPUT-PATH', type=parse_path,
                      help="directory where to copy the audio files")
  parser.add_argument("--relative-to", type=get_optional(parse_path), metavar="REL-PATH",
                      help="parse paths in PATHS relative to REL-PATH to import files with the same folder structure", default=None)
  add_encoding_argument(parser, "PATHS encoding")
  parser.add_argument("-s", "--symlink", action="store_true",
                      help="create symbolic links instead of copying")
  return import_audio_paths_ns


def import_audio_paths_ns(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  try:
    text: str = ns.path.read_text(ns.encoding)
  except Exception as ex:
    logger.error("PATH couldn't be loaded.")
    logger.exception(ex)
    return False, False

  try:
    paths: OrderedSet[Path] = OrderedSet(Path(path) for path in text.split("\n"))
  except Exception as ex:
    logger.error("PATHS couldn't be parsed.")
    logger.exception(ex)
    return False, False

  logger.info(f"Parsed {len(paths)} unique paths.")

  path: Path
  for path in tqdm(paths, desc="Importing", unit=" audio(s)"):
    target_dir = cast(Path, ns.output_directory)
    if not path.is_file():
      logger.error(f"Path \"{path}\" is no file.")
      logger.exception(ex)
      return False, False

    if ns.relative_to is None:
      target_path = target_dir / path.name
    else:
      try:
        target_path = target_dir / path.relative_to(ns.relative_to)
      except ValueError as error:
        logger.error(f"Path \"{ns.relative_to}\" is not relative to \"{path}\"!")
        logger.exception(error)
        return False, False

    try:
      target_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as ex:
      logger.error(f"Target directory \"{target_path.parent.absolute()}\" couldn't be created!")
      logger.exception(ex)
      return False, False

    if ns.symlink:
      try:
        flogger.info(
          f"Creating symbolic link of \"{path.absolute()}\" at \"{target_path.absolute()}\"")
        target_path.symlink_to(path, target_is_directory=False)
      except Exception as ex:
        logger.error(
          f"Couldn't create symbolic link from \"{path.absolute()}\" to \"{target_path.absolute()}\"!")
        logger.exception(ex)
        return False, False
    else:
      try:
        flogger.info(f"Copying \"{path.absolute()}\" to \"{target_path.absolute()}\"")
        copy(path, target_path)
      except Exception as ex:
        logger.error(f"Couldn't copy \"{path.absolute()}\" to \"{target_path.absolute()}\"!")
        logger.exception(ex)
        return False, False

  logger.info(f"Imported {len(paths)} path(s) to: \"{ns.output_directory.absolute()}\".")

  return True, True
