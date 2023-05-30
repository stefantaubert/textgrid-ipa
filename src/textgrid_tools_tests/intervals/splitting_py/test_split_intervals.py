from textgrid.textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.intervals.splitting import split_intervals


def test_component__words():
  grid = TextGrid(None, 0, 6)
  tier = IntervalTier(name="test", minTime=grid.minTime, maxTime=grid.maxTime)
  tier.add(0, 0.5, "")
  tier.add(0.5, 2, "\"This test\"")
  tier.add(2, 2.5, "")
  tier.add(2.5, 3, "")
  tier.add(3, 5, "Is right.")
  tier.add(5, 6, "")
  grid.append(tier)

  error, changed_anything = split_intervals(
    grid, {"test"}, " ", False, None)

  assert error is None
  assert changed_anything
  assert len(tier) == 8
  assert tier[0] == Interval(0, 0.5, "")
  assert tier[1] == Interval(0.5, 1.25, "\"This")
  assert tier[2] == Interval(1.25, 2.0, "test\"")
  assert tier[3] == Interval(2, 2.5, "")
  assert tier[4] == Interval(2.5, 3, "")
  assert tier[5] == Interval(3, 4, "Is")
  assert tier[6] == Interval(4, 5.0, "right.")
  assert tier[7] == Interval(5, 6, "")
