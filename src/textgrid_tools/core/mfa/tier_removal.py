from logging import getLogger
from typing import Set

from textgrid.textgrid import TextGrid
from textgrid_tools.core.mfa.helper import check_is_valid_grid, get_tiers, tier_exists


def can_remove_tiers(grid: TextGrid, tiers: Set[str]) -> bool:
  logger = getLogger(__name__)

  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if len(tiers) == 0:
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


def remove_tiers(grid: TextGrid, tiers: Set[str]) -> None:
  assert can_remove_tiers(grid, tiers)
  for tier in tiers:
    remove_tiers_list = list(get_tiers(grid, tier))
    for remove_tier in remove_tiers_list:
      grid.tiers.remove(remove_tier)
