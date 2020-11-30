from argparse import ArgumentParser
from functools import partial
from logging import Logger, getLogger
import os
from typing import List, Optional

from cmudict_parser import CMUDict, get_dict
from epitran import Epitran
from textgrid.textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.utils import check_paths_ok, get_parent_dirpath, update_or_add_tier


def init_ipa_parser(parser: ArgumentParser):
  parser.add_argument("--file", type=str, required=True, help="TextGrid input filepath.")
  parser.add_argument("--output", type=str, required=True,
                      help="TextGrid output filepath.")
  parser.add_argument("--words-tier-name", type=str, default="words",
                      help="The name of the tier with the English words annotated.")
  parser.add_argument("--ipa-tier-name", type=str, default="IPA-standard",
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

    os.makedirs(get_parent_dirpath(output), exist_ok=True)
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
  cmu = get_dict(silent=True)
  ipa_intervals: List[Interval] = [convert_to_ipa_interval(x, epi, cmu, logger) for x in tiers]
  return ipa_intervals


def epi_transliterate(word: str, epitran: Epitran, logger: Logger) -> str:
  ipa = epitran.transliterate(word)
  logger.debug(f"{word} was not in CMUDict therefore used Epitran -> {ipa}")
  return ipa


def convert_to_ipa_interval(tier: IntervalTier, epitran: Epitran, cmu: CMUDict, logger: Logger) -> IntervalTier:
  word = tier.mark
  epi = partial(epi_transliterate, epitran=epitran, logger=logger)
  ipa = cmu.sentence_to_ipa(
    sentence=word,
    replace_unknown_with=epi
  )
  ipa_interval = Interval(
    minTime=tier.minTime,
    maxTime=tier.maxTime,
    mark=ipa,
  )
  logger.info(ipa)
  return ipa_interval
