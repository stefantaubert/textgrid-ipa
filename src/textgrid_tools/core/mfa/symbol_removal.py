from logging import getLogger
from typing import Iterable, Set, cast

from textgrid.textgrid import Interval, IntervalTier, TextGrid


def remove_symbols(grid: TextGrid, tier_names: Set[str], symbols: Set[str]) -> None:
  logger = getLogger(__name__)

  if len(symbols) == 0:
    logger.error("No symbols defined!")
    return
  logger.info(f"Removing symbols: {' '.join(sorted(symbols))}...")

  for tier in cast(Iterable[IntervalTier], grid.tiers):
    if tier.name in tier_names:
      for interval in cast(Iterable[Interval], tier.intervals):
        interval_symbols_str = str(interval.mark)
        new_symbols = (symbol for symbol in interval_symbols_str.split(" ")
                       if symbol not in symbols)
        new_interval_symbols_str = " ".join(new_symbols)
        interval.mark = new_interval_symbols_str
        # logger.debug(f"Changed \"{interval_symbols_str}\" to \"{new_interval_symbols_str}\".")

  return
