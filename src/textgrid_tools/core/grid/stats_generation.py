from logging import getLogger
from typing import Iterable, List, Set, cast

from numpy.core.fromnumeric import mean
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.validation import (InvalidGridError,
                                            NotExistingTierError)


def print_stats(grid: TextGrid, duration_threshold: float, print_symbols_tier_names: Set[str]) -> ExecutionResult:
  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in print_symbols_tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  logger = getLogger(__name__)
  logger.info(f"Start: {grid.minTime}")
  logger.info(f"End: {grid.maxTime}")
  logger.info(f"Duration: {grid.maxTime - grid.minTime}s")
  logger.info(f"# Tiers: {len(grid.tiers)}")
  for nr, tier in enumerate(cast(Iterable[IntervalTier], grid.tiers), start=1):
    print_symbols = tier.name in print_symbols_tier_names
    logger.info(f"== Tier {nr} ==")
    print_stats_tier(tier, duration_threshold, print_symbols)
  return None, False


def print_stats_tier(tier: IntervalTier, duration_threshold: float, print_symbols: bool) -> None:
  logger = getLogger(__name__)
  logger.info(f"Name: {tier.name}")
  logger.info(f"# Intervals: {len(tier.intervals)}")
  if len(tier.intervals) == 0:
    return
  durations = [interval.duration() for interval in cast(List[Interval], tier.intervals)]
  marks = list(str(interval.mark) for interval in cast(List[Interval], tier.intervals))
  if print_symbols:
    unique_words_or_symbols = {x for mark in marks for x in mark.split()}
    logger.info(
      f"Symbols: {' '.join(sorted(unique_words_or_symbols))} (# {len(unique_words_or_symbols)})")

  logger.info(f"Min duration: {min(durations)}s")
  logger.info(f"Max duration: {max(durations)}s")
  logger.info(f"Average duration: {mean(durations)}s")

  for interval in cast(Iterable[Interval], tier.intervals):
    if interval.duration() < duration_threshold:
      logger.info(
        f"Very short interval: [{interval.minTime}, {interval.maxTime}] \"{interval.mark}\" -> {interval.duration()}s")
