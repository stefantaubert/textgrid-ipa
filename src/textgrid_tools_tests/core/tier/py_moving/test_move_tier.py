from textgrid.textgrid import IntervalTier, TextGrid
from textgrid_tools.core.tier.moving import move_tier


def test_empty__is_not_moved():
  grid = TextGrid()

  moved = move_tier(grid, tier_name="test", position=1)

  assert len(grid) == 0
  assert not moved


def test_one_entry__is_not_moved():
  grid = TextGrid()
  tier = IntervalTier(name="test")
  grid.tiers.append(tier)

  moved = move_tier(grid, tier_name="test", position=0)

  assert len(grid) == 1
  assert grid[0] == tier
  assert not moved


def test_A_B_move_B_to_0__is_moved():
  grid = TextGrid()
  tierA = IntervalTier(name="testA")
  tierB = IntervalTier(name="testB")

  grid.tiers.append(tierA)
  grid.tiers.append(tierB)

  moved = move_tier(grid, tier_name="testB", position=0)

  assert len(grid) == 2
  assert grid[0] == tierB
  assert grid[1] == tierA
  assert moved


def test_A_B_move_A_to_1__is_moved():
  grid = TextGrid()
  tierA = IntervalTier(name="testA")
  tierB = IntervalTier(name="testB")

  grid.tiers.append(tierA)
  grid.tiers.append(tierB)

  moved = move_tier(grid, tier_name="testA", position=1)

  assert len(grid) == 2
  assert grid[0] == tierB
  assert grid[1] == tierA
  assert moved
