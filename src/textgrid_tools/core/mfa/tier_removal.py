from logging import getLogger
from typing import Set

from textgrid.textgrid import IntervalTier, TextGrid


def can_remove_tiers(grid: TextGrid, tier_names: Set[str]) -> bool:
  logger = getLogger(__name__)

  if len(tier_names) == 0:
    return False

  result = True
  for tier_name in tier_names:
    tier: IntervalTier = grid.getFirst(tier_name)
    if tier is None:
      logger.exception(f"Tier \"{tier_name}\" not found!")
      result = False

  return result


def remove_tiers(grid: TextGrid, tier_names: Set[str]) -> None:
  assert can_remove_tiers(grid, tier_names)
  for tier_name in tier_names:
    tier: IntervalTier = grid.getFirst(tier_name)
    grid.tiers.remove(tier)
