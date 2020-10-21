import os
from argparse import ArgumentParser

from convert import add_ipa_tier
from textgrid.textgrid import TextGrid


def check_paths_ok(in_path: str, out_path: str):
  if not os.path.exists(in_path):
    print("The file couldn't be found!")
    return False

  if in_path == out_path:
    print("Input and output files should be different!")
    return False

  return True


if __name__ == "__main__":
  main_parser = ArgumentParser()
  main_parser.add_argument("-f", "--file", type=str, required=True, help="TextGrid input filepath.")
  main_parser.add_argument("-o", "--output", type=str, required=True,
                           help="TextGrid output filepath.")
  main_parser.add_argument("-w", "--word-tier-name", type=str, required=True,
                           help="The name of the tier with the English words annotated.")
  main_parser.add_argument("-a", "--actual-ipa-tier-name", type=str, required=True,
                           help="The name of the tier which should contain the IPA transcriptions. If the tier exists, it will be overwritten.")
  main_parser.add_argument("-s", "--standard-ipa-tier-name", type=str, required=False,
                           help="The name of the tier which should contain the IPA transcriptions for reference. If the tier exists, it will be overwritten.")
  args = main_parser.parse_args()

  if check_paths_ok(args.file, args.output):

    grid = TextGrid()
    grid.read(args.file)

    add_ipa_tier(
      grid=grid,
      in_tier_name=args.word_tier_name,
      out_tier_name=args.standard_ipa_tier_name,
    )

    grid.write(args.output)
    print("Success!")
