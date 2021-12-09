from logging import getLogger
from typing import Iterable, cast

from textgrid.textgrid import IntervalTier, TextGrid


def rename_tier(grid: TextGrid, tier_name: str, new_tier_name: str) -> None:
  logger = getLogger(__name__)

  for tier in cast(Iterable[IntervalTier], grid.tiers):
    if tier.name == tier_name:
      #logger.info(f"Renaming {tier.name} to {new_tier_name}...")
      tier.name = new_tier_name
