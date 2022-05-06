from logging import Logger, getLogger
from typing import List, Optional, Set

from textgrid.textgrid import IntervalTier, TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_all_tiers
from textgrid_tools.validation import InvalidGridError, NotExistingTierError, ValidationError


class AllTiersRemoveError(ValidationError):
  def __init__(self, grid: TextGrid, tiers: List[IntervalTier]) -> None:
    super().__init__()
    self.grid = grid
    self.tiers = tiers

  @classmethod
  def validate(cls, grid: TextGrid, tiers: List[IntervalTier]):
    if len(tiers) == len(grid.tiers):
      return cls(grid, tiers)
    return None

  @property
  def default_message(self) -> str:
    return "Removing all tiers is not possible!"


def remove_tiers(grid: TextGrid, tier_names: Set[str], logger: Optional[Logger]) -> ExecutionResult:
  assert len(tier_names) > 0
  
  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  tiers_to_remove = list(get_all_tiers(grid, tier_names))

  if error := AllTiersRemoveError.validate(grid, tiers_to_remove):
    return error, False

  for tier in tiers_to_remove:
    grid.tiers.remove(tier)

  return None, True
