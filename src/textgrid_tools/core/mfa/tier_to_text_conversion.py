from logging import getLogger

from textgrid.textgrid import IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import tier_to_text


def extract_tier_to_text(grid: TextGrid, tier_name: str) -> str:
  logger = getLogger(__name__)

  tier: IntervalTier = grid.getFirst(tier_name)
  if tier is None:
    logger.exception("Tier not found!")
    raise Exception()

  result = tier_to_text(tier, join_with=" ")
  return result
