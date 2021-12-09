from logging import getLogger
from typing import Set

from textgrid.textgrid import IntervalTier, TextGrid


def remove_tiers(grid: TextGrid, tier_names: Set[str]) -> None:
  logger = getLogger(__name__)

  for tier_name in tier_names:
    tier: IntervalTier = grid.getFirst(tier_name)
    if tier is None:
      logger.exception(f"Tier \"{tier_name}\" not found!")
      raise Exception()

    grid.tiers.remove(tier)
