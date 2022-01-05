from logging import getLogger

from textgrid.textgrid import TextGrid
from textgrid_tools.core.mfa.helper import (check_is_valid_grid,
                                            get_first_tier, tier_exists)
from textgrid_tools.utils import update_or_add_tier


def can_copy(grid: TextGrid, reference_grid: TextGrid, reference_tier_name: str, new_tier: str, overwrite_tier: bool) -> bool:
  logger = getLogger(__name__)

  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if not check_is_valid_grid(reference_grid):
    logger.error("Reference grid is invalid!")
    return False

  if grid.minTime != reference_grid.minTime or grid.maxTime != reference_grid.maxTime:
    logger.error("Both grids need to have the same minTime and maxTime!")
    return False

  if not tier_exists(reference_grid, reference_tier_name):
    logger.error(f"Tier \"{reference_tier_name}\" not found!")
    return False

  if tier_exists(grid, new_tier) and not overwrite_tier:
    logger.error(f"Tier \"{new_tier}\" already exists!")
    return False

  return True


def copy_tier_to_grid(grid: TextGrid, reference_grid: TextGrid, reference_tier_name: str, new_tier: str, overwrite_tier: bool) -> None:
  assert can_copy(grid, reference_grid, reference_tier_name, new_tier, overwrite_tier)
  reference_tier = get_first_tier(reference_grid, reference_tier_name)

  if overwrite_tier:
    update_or_add_tier(grid, reference_tier)
  else:
    grid.append(reference_tier)
