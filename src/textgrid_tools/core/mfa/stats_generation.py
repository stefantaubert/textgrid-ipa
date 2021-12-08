from logging import getLogger
from typing import Iterable, List, cast

from numpy.core.fromnumeric import mean
from textgrid.textgrid import Interval, IntervalTier, TextGrid


def print_stats(grid: TextGrid, duration_threshold: float) -> None:
  logger = getLogger(__name__)
  logger.info(f"Start: {grid.minTime}")
  logger.info(f"End: {grid.maxTime}")
  logger.info(f"Duration: {grid.maxTime - grid.minTime}s")
  logger.info(f"# Tiers: {len(grid.tiers)}")
  for nr, tier in enumerate(grid.tiers, start=1):
    logger.info(f"== Tier {nr} ==")
    print_stats_tier(tier, duration_threshold)


def print_stats_tier(tier: IntervalTier, duration_threshold: float) -> None:
  logger = getLogger(__name__)
  logger.info(f"Name: {tier.name}")
  logger.info(f"# Intervals: {len(tier.intervals)}")
  if len(tier.intervals) == 0:
    return
  durations = [interval.duration() for interval in cast(List[Interval], tier.intervals)]
  logger.info(f"Min duration: {min(durations)}s")
  logger.info(f"Max duration: {max(durations)}s")
  logger.info(f"Average duration: {mean(durations)}s")

  for interval in cast(Iterable[Interval], tier.intervals):
    if interval.duration() < duration_threshold:
      logger.info(
        f"Very short interval: [{interval.minTime}, {interval.maxTime}] \"{interval.mark}\" -> {interval.duration()}s")
