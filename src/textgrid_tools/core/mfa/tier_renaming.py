from logging import getLogger

from textgrid.textgrid import TextGrid
from textgrid_tools.core.mfa.helper import get_tiers, tier_exists


def can_rename_tier(grid: TextGrid, tier: str) -> bool:
  logger = getLogger(__name__)

  if not tier_exists(grid, tier):
    logger.error(f"Tier \"{tier}\" not found!")
    return False

  return True


def rename_tier(grid: TextGrid, tier: str, new_name: str) -> None:
  assert can_rename_tier(grid, tier)

  logger = getLogger(__name__)
  tiers = list(get_tiers(grid, {tier}))

  if len(tiers) > 1:
    logger.warning(
      f"Found multiple tiers with name \"{tier}\", therefore renaming only the first one.")
  first_tier = tiers[0]
  first_tier.name = new_name
