from logging import getLogger
from typing import Iterable, Set, cast

from text_utils.language import Language
from text_utils.symbol_format import SymbolFormat
from text_utils.text import text_normalize
from textgrid.textgrid import Interval, TextGrid
from textgrid_tools.core.mfa.helper import (check_is_valid_grid, get_tiers,
                                            tier_exists)


def can_normalize_tiers(grid: TextGrid, tiers: Set[str]) -> bool:
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


def normalize_tiers(grid: TextGrid, tiers: Set[str], language: Language) -> None:
  assert can_normalize_tiers(grid, tiers)
  for tier in tiers:
    for target_tier in get_tiers(grid, tier):
      for interval in cast(Iterable[Interval], target_tier.intervals):
        text = str(interval.mark)
        text = text.replace("\n", " ")
        text = text.replace("\r", "")
        text = text_normalize(
          text=text,
          lang=language,
          text_format=SymbolFormat.GRAPHEMES,
        )
        interval.mark = text
