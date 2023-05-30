from textgrid.textgrid import IntervalTier, TextGrid

from textgrid_tools.tier.moving import move_tier
from textgrid_tools.validation import InvalidGridError


def test_empty__is_not_moved():
  grid = TextGrid()

  error, changed_anything = move_tier(grid, tier_name="test", position_one_based=1, logger=None)

  assert isinstance(error, InvalidGridError)
  assert not changed_anything


def test_one_entry__is_not_moved():
  grid = TextGrid(None, 0, 1)
  tier = IntervalTier("test", 0, 1)
  grid.tiers.append(tier)

  error, changed_anything = move_tier(grid, tier_name="test", position_one_based=1, logger=None)

  assert error is None
  assert not changed_anything
  assert len(grid) == 1
  assert grid[0] == tier


def test_A_B_move_B_to_0__is_moved():
  grid = TextGrid(None, 0, 1)
  tierA = IntervalTier("testA", 0, 1)
  tierB = IntervalTier("testB", 0, 1)

  grid.tiers.append(tierA)
  grid.tiers.append(tierB)

  error, changed_anything = move_tier(grid, tier_name="testB", position_one_based=1, logger=None)

  assert error is None
  assert changed_anything
  assert len(grid) == 2
  assert grid[0] == tierB
  assert grid[1] == tierA


def test_A_B_move_A_to_1__is_moved():
  grid = TextGrid(None, 0, 1)
  tierA = IntervalTier("testA", 0, 1)
  tierB = IntervalTier("testB", 0, 1)

  grid.tiers.append(tierA)
  grid.tiers.append(tierB)

  error, changed_anything = move_tier(grid, tier_name="testA", position_one_based=2, logger=None)

  assert error is None
  assert changed_anything
  assert len(grid) == 2
  assert grid[0] == tierB
  assert grid[1] == tierA
