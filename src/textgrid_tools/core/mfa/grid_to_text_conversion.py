from logging import getLogger

from textgrid.textgrid import TextGrid
from textgrid_tools.core.mfa.helper import (check_is_valid_grid, tier_exists,
                                            tier_to_text)
from textgrid_tools.core.mfa.string_format import StringFormat


def can_convert_tier_to_text(grid: TextGrid, tier: str) -> bool:
  logger = getLogger(__name__)

  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if not tier_exists(grid, tier):
    logger.error(f"Tier \"{tier}\" not found!")
    return False

  return True


def convert_tier_to_text(grid: TextGrid, tier: str, string_format: StringFormat) -> str:
  assert can_convert_tier_to_text(grid, tier)

  result = tier_to_text(tier, join_with=string_format.get_word_separator())

  return result
