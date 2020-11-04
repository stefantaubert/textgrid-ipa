from argparse import ArgumentParser

from textgrid_tools.sentence2words import init_words_parser
from textgrid_tools.wav2pauses import init_pause_parser
from textgrid_tools.words2ipa import init_ipa_parser


def _add_parser_to(subparsers, name: str, init_method):
  parser = subparsers.add_parser(name, help=f"{name} help")
  invoke_method = init_method(parser)
  parser.set_defaults(invoke_handler=invoke_method)
  return parser


def _init_parser():
  result = ArgumentParser()
  subparsers = result.add_subparsers(help='sub-command help')
  _add_parser_to(subparsers, "wav2pauses", init_pause_parser)
  _add_parser_to(subparsers, "sentences2words", init_words_parser)
  _add_parser_to(subparsers, "words2ipa", init_ipa_parser)
  return result


def _process_args(args):
  params = vars(args)
  invoke_handler = params.pop("invoke_handler")
  invoke_handler(**params)


if __name__ == "__main__":
  main_parser = _init_parser()

  received_args = main_parser.parse_args()

  _process_args(received_args)
