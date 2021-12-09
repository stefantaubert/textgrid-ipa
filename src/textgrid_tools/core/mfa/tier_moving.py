from logging import getLogger

from textgrid.textgrid import IntervalTier, TextGrid


def move_tier(grid: TextGrid, tier_name: str, to_position: int) -> bool:
  logger = getLogger(__name__)

  if len(grid.tiers) == 0:
    logger.info("No tiers to move exist.")
    return False

  if not (0 <= to_position < len(grid.tiers)):
    logger.error(f"Position {to_position} is not valid, it needs to be between [0, {len(grid)}).")
    return False

  target_tier: IntervalTier = grid.getFirst(tier_name)
  if grid.tiers[to_position] == target_tier:
    logger.info("Tier is already on the position.")
    return False

  grid.tiers.remove(target_tier)
  grid.tiers.insert(to_position, target_tier)
  return True
