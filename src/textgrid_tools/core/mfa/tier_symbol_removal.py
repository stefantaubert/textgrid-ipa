from logging import getLogger
from typing import Iterable, Set, cast

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import get_tiers, tier_exists


def can_remove_symbols(grid: TextGrid, tiers: Set[str], symbols: Set[str]) -> bool:
  logger = getLogger(__name__)

  if len(symbols) == 0:
    logger.error("No symbols defined!")
    return False

  if len(tiers) == 0:
    logger.error("No tiers given!")
    return False

  result = True
  for tier in tiers:
    if not tier_exists(grid, tier):
      logger.error(f"Tier \"{tier}\" not found!")
      result = False
  return result


def remove_symbols(grid: TextGrid, tiers: Set[str], symbols: Set[str]) -> bool:
  assert can_remove_symbols(grid, tiers, symbols)
  logger = getLogger(__name__)

  logger.info(f"Removing symbols: {' '.join(sorted(symbols))} ...")
  changed_anything = False

  for tier in cast(Iterable[IntervalTier], grid.tiers):
    if tier.name in tiers:
      for interval in cast(Iterable[Interval], tier.intervals):
        interval_symbols_str = str(interval.mark)
        new_symbols = (symbol for symbol in interval_symbols_str.split(" ")
                       if symbol not in symbols)
        new_interval_symbols_str = " ".join(new_symbols)
        changed_anything |= interval_symbols_str != new_interval_symbols_str
        interval.mark = new_interval_symbols_str
        # logger.debug(f"Changed \"{interval_symbols_str}\" to \"{new_interval_symbols_str}\".")
  return changed_anything
