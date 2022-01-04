from logging import getLogger

from text_utils import StringFormat
from textgrid.textgrid import TextGrid
from textgrid_tools.core.mfa.helper import (check_is_valid_grid,
                                            get_first_tier, tier_exists,
                                            tier_to_text)


def can_convert_tier_to_text(grid: TextGrid, tier_name: str) -> bool:
  logger = getLogger(__name__)

  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if not tier_exists(grid, tier_name):
    logger.error(f"Tier \"{tier_name}\" not found!")
    return False

  return True


def convert_tier_to_text(grid: TextGrid, tier_name: str, string_format: StringFormat) -> str:
  assert can_convert_tier_to_text(grid, tier_name)

  tier = get_first_tier(grid, tier_name)
  result = tier_to_text(tier, join_with=string_format.get_word_separator())

  return result
