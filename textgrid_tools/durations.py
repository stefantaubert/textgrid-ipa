from argparse import ArgumentParser
from logging import Logger, getLogger
from textgrid_tools.utils import check_interval_has_content
from typing import List

from textgrid.textgrid import Interval, IntervalTier, TextGrid


def init_durations_parser(parser: ArgumentParser):
  parser.add_argument("-f", "--file", type=str, required=True, help="TextGrid input filepath.")
  parser.add_argument("-t", "--tier-name", type=str, default="words",
                      help="The name of the tier with the English words annotated.")
  return get_durations


def get_durations(file: str, tier_name: str) -> None:
  logger = getLogger()
  grid = TextGrid()
  grid.read(file)

  logger.info(f"Calculating durations of tier {tier_name}...")
  calc_durations(
    grid=grid,
    tier_name=tier_name,
    logger=logger,
  )

def calc_durations(grid: TextGrid, tier_name: str, logger: Logger) -> None:

  in_tier: IntervalTier = grid.getFirst(tier_name)
  in_tier_intervals: List[Interval] = in_tier.intervals

  total_content_duration = 0.0
  for interval in in_tier_intervals:
    has_content = check_interval_has_content(interval)
    if has_content:
      content_duration = interval.maxTime - interval.minTime
      total_content_duration += content_duration

  total_duration = in_tier.maxTime - in_tier.minTime
  content_percent = total_content_duration / total_duration * 100
  silence_percent = (total_duration - total_content_duration) / total_duration * 100
  logger.info(
    f"Duration content: {total_content_duration:.0f}s of {total_duration:.0f}s ({content_percent:.2f}%)")
  logger.info(f"Duration content: {total_content_duration/60:.0f}min of {total_duration/60:.0f}min")
  logger.info(
    f"Duration of silence: {total_duration - total_content_duration:.0f}s of {total_duration:.0f}s ({silence_percent:.2f}%)")
  logger.info(
    f"Duration of silence: {(total_duration - total_content_duration)/60:.0f}min of {total_duration/60:.0f}min")
