from logging import getLogger

from textgrid.textgrid import TextGrid
from textgrid_tools.core.mfa.helper import check_is_valid_grid, tier_exists

Success = bool


def validation_tier_exists_but_no_overwrite_fails(grid: TextGrid, tier_name: str, overwrite: bool) -> None:
  if tier_exists(grid, tier_name) and not overwrite:
    logger = getLogger(__name__)
    logger.error(f"Tier \"{tier_name}\" already exists!")
    return True
  return False


def validation_grid_is_valid_fails(grid: TextGrid) -> bool:
  if not check_is_valid_grid(grid):
    logger = getLogger(__name__)
    logger.error("Grid is not valid!")
    return True
  return False


def validation_tier_exists_fails(grid: TextGrid, tier_name: str) -> bool:
  if not tier_exists(grid, tier_name):
    logger = getLogger(__name__)
    logger.error(f"Tier \"{tier_name}\" does not exist!")
    return True
  return False
