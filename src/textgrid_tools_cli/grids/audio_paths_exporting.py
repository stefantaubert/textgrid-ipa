from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import List

from tqdm import tqdm

from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       get_audio_files, parse_txt_path)
from textgrid_tools_cli.logging_configuration import init_and_get_console_logger


def get_audio_paths_exporting_parser(parser: ArgumentParser):
  parser.description = "This command exports all paths of all audio into one text file."
  add_directory_argument(parser)
  parser.add_argument("output", type=parse_txt_path, metavar="OUTPUT",
                      help="path to output the paths (*.txt)")
  add_encoding_argument(parser, "OUTPUT encoding")
  return export_audio_paths_ns


def export_audio_paths_ns(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)

  grid_files = get_audio_files(ns.directory)

  paths: List[str] = []
  for file_nr, (file_stem, rel_path) in enumerate(tqdm(grid_files.items()), start=1):
    audio_file_in_abs: Path = ns.directory / rel_path
    paths.append(str(audio_file_in_abs.absolute()))

  txt = "\n".join(paths)

  ns.output.parent.mkdir(parents=True, exist_ok=True)
  ns.output.write_text(txt, ns.encoding)
  logger.info(f"Exported {len(paths)} path(s) to: \"{ns.output.absolute()}\".")

  return True, True
