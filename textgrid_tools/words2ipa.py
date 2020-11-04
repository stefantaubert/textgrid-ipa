from argparse import ArgumentParser
from logging import Logger, getLogger
from typing import List, Optional

from epitran import Epitran

from cmudict_parser import CMUDict, get_dict
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.utils import check_paths_ok, update_or_add_tier


def init_ipa_parser(parser: ArgumentParser):
  parser.add_argument("-f", "--file", type=str, required=True, help="TextGrid input filepath.")
  parser.add_argument("-o", "--output", type=str, required=True,
                      help="TextGrid output filepath.")
  parser.add_argument("-w", "--words-tier-name", type=str, default="words",
                      help="The name of the tier with the English words annotated.")
  parser.add_argument("-i", "--ipa-tier-name", type=str, default="IPA-standard",
                      help="The name of the tier which should contain the IPA transcriptions for reference. If the tier exists, it will be overwritten.")
  return add_ipa


def add_ipa(file: str, output: str, words_tier_name: str, ipa_tier_name: str) -> None:
  logger = getLogger()
  if check_paths_ok(file, output, logger):
    grid = TextGrid()
    grid.read(file)

    logger.info("Converting words to IPA...")

    add_ipa_tier(
      grid=grid,
      in_tier_name=words_tier_name,
      out_tier_name=ipa_tier_name,
      logger=logger,
    )

    grid.write(output)
    logger.info("Success!")


def add_ipa_tier(grid: TextGrid, in_tier_name: str,
                 out_tier_name: Optional[str], logger: Logger) -> None:

  in_tier: IntervalTier = grid.getFirst(in_tier_name)
  in_tier_intervals: List[Interval] = in_tier.intervals
  ipa_intervals = convert_to_ipa_intervals(in_tier_intervals, logger)

  out_tier = IntervalTier(
    name=out_tier_name,
    minTime=in_tier.minTime,
    maxTime=in_tier.maxTime
  )
  out_tier.intervals.extend(ipa_intervals)

  update_or_add_tier(grid, out_tier)


def convert_to_ipa_intervals(tiers: List[IntervalTier], logger: Logger) -> List[IntervalTier]:
  epi = Epitran('eng-Latn')
  cmu = get_dict()
  ipa_intervals: List[Interval] = [convert_to_ipa_interval(x, epi, cmu, logger) for x in tiers]
  return ipa_intervals


def convert_to_ipa_interval(tier: IntervalTier, epitran: Epitran, cmu: CMUDict, logger: Logger) -> IntervalTier:
  word = tier.mark
  is_silence = word == ""
  if is_silence:
    ipa = ""
  else:
    use_cmu = cmu.contains(word)
    if use_cmu:
      ipa = cmu.get_first_ipa(word)
    else:
      ipa = epitran.transliterate(word)
      logger.debug(f"{word} was not in CMUDict therefore used Epitran -> {ipa}")
  ipa_interval = Interval(
    minTime=tier.minTime,
    maxTime=tier.maxTime,
    mark=ipa,
  )
  return ipa_interval
