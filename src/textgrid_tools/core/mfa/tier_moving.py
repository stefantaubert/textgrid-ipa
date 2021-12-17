from logging import getLogger

from textgrid.textgrid import IntervalTier, TextGrid


def can_move_tier(grid: TextGrid, tier_name: str, to_position: int) -> bool:
  logger = getLogger(__name__)
  target_tier: IntervalTier = grid.getFirst(tier_name)
  if target_tier is None:
    logger.info("Tier does not exist.")
    return False

  if not 0 <= to_position < len(grid.tiers):
    logger.error(f"Position {to_position} is not valid, it needs to be between [0, {len(grid)}).")
    return False

  return True


def move_tier(grid: TextGrid, tier_name: str, to_position: int) -> bool:
  assert can_move_tier(grid, tier_name, to_position)

  logger = getLogger(__name__)
  target_tier: IntervalTier = grid.getFirst(tier_name)
  if grid.tiers[to_position] == target_tier:
    logger.info("Tier is already on the position.")
    return False

  grid.tiers.remove(target_tier)
  grid.tiers.insert(to_position, target_tier)
  return True
