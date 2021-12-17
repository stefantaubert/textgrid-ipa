from logging import getLogger

from textgrid.textgrid import IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import check_is_valid_grid, tier_exists


def can_move_tier(grid: TextGrid, tier: str, to_position: int) -> bool:
  logger = getLogger(__name__)
  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if not tier_exists(grid, tier):
    logger.info("Tier does not exist.")
    return False

  if not 0 <= to_position < len(grid.tiers):
    logger.error(f"Position {to_position} is not valid, it needs to be between [0, {len(grid)}).")
    return False

  return True


def move_tier(grid: TextGrid, tier: str, to_position: int) -> bool:
  assert can_move_tier(grid, tier, to_position)

  target_tier: IntervalTier = grid.getFirst(tier)
  if grid.tiers[to_position] == target_tier:
    return False

  grid.tiers.remove(target_tier)
  grid.tiers.insert(to_position, target_tier)
  return True
