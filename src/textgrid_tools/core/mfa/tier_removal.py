from logging import getLogger

from textgrid.textgrid import IntervalTier, TextGrid


def remove_tier(grid: TextGrid, tier_name: str) -> None:
  logger = getLogger(__name__)

  tier: IntervalTier = grid.getFirst(tier_name)
  if tier is None:
    logger.exception("Tier not found!")
    raise Exception()

  grid.tiers.remove(tier)
