from copy import deepcopy
from logging import getLogger
from typing import Iterable, cast

from textgrid.textgrid import IntervalTier, TextGrid


def clone_tier(grid: TextGrid, tier_name: str, new_tier_name: str) -> None:
  logger = getLogger(__name__)

  for tier in cast(Iterable[IntervalTier], grid.tiers):
    tier: IntervalTier = grid.getFirst(tier_name)
    new_tier = deepcopy(tier)
    new_tier.name = new_tier_name
    grid.append(new_tier)
