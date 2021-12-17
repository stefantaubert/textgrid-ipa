from logging import getLogger

from textgrid.textgrid import TextGrid
from textgrid_tools.core.mfa.helper import get_tiers


def can_rename_tier(grid: TextGrid, tier_name: str) -> bool:
  logger = getLogger(__name__)

  tiers = list(get_tiers(grid, {tier_name}))
  if len(tiers) == 0:
    logger.error(f"Tier \"{tier_name}\" not found!")
    return False

  return True


def rename_tier(grid: TextGrid, tier_name: str, new_tier_name: str) -> None:
  assert can_rename_tier(grid, tier_name)

  logger = getLogger(__name__)
  tiers = list(get_tiers(grid, {tier_name}))

  if len(tiers) > 1:
    logger.warning(
      f"Found multiple tiers with name \"{tier_name}\", therefore renaming only the first one.")
  first_tier = tiers[0]
  first_tier.name = new_tier_name
