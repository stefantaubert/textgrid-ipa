from textgrid.textgrid import TextGrid
from textgrid_tools.core.mfa.helper import check_is_valid_grid, tier_exists


class ValidationError():
  # pylint: disable=no-self-use
  @property
  def default_message(self) -> str:
    return ""


class NotExistingTierError(ValidationError):
  def __init__(self, grid: TextGrid, tier_name: str) -> None:
    super().__init__()
    self.grid = grid
    self.tier_name = tier_name

  @classmethod
  def validate(cls, grid: TextGrid, tier_name: str):
    if not tier_exists(grid, tier_name):
      return cls(grid, tier_name)
    return None

  @property
  def default_message(self) -> str:
    return f"Tier \"{self.tier_name}\" does not exist!"


class ExistingTierError(ValidationError):
  def __init__(self, grid: TextGrid, tier_name: str) -> None:
    super().__init__()
    self.grid = grid
    self.tier_name = tier_name

  @classmethod
  def validate(cls, grid: TextGrid, tier_name: str):
    if tier_exists(grid, tier_name):
      return cls(grid, tier_name)
    return None

  @property
  def default_message(self) -> str:
    return f"Tier \"{self.tier_name}\" already exists!"


class InvalidGridError(ValidationError):
  def __init__(self, grid: TextGrid) -> None:
    super().__init__()
    self.grid = grid

  @classmethod
  def validate(cls, grid: TextGrid):
    if not check_is_valid_grid(grid):
      return cls(grid)
    return None

  @property
  def default_message(self) -> str:
    return "Grid is not valid!"
