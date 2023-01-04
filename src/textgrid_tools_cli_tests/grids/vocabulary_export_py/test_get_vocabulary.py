
from logging import getLogger

from ordered_set import OrderedSet
from textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools_cli.grids.vocabulary_export import get_vocabulary


def test_component():
  grid1 = TextGrid("test", 0, 5)
  grid1_tier1 = IntervalTier("tier1", 0, 5)
  grid1_tier2 = IntervalTier("tier2", 0, 5)
  grid1_tier1.intervals = [
    Interval(0, 0.5, "a"),  # 0.5s
    Interval(0.5, 1.5, "b"),  # 1s
    Interval(1.5, 2, ""),  # 0.5s
    Interval(2, 3, "c"),  # 1s
    Interval(3, 5, "a"),  # 2s
  ]

  grid1_tier2.intervals = [
    Interval(0, 0.5, "-"),
    Interval(0.5, 1.5, "-"),
    Interval(1.5, 2, "-"),
    Interval(2, 3, "X"),
    Interval(3, 5, "-"),
  ]
  grid1.tiers = [
    grid1_tier1,
    grid1_tier2
  ]

  grid2 = TextGrid("test", 0, 5)
  grid2_tier1 = IntervalTier("tier1", 0, 5)
  grid2_tier1.intervals = [
    Interval(0, 5, "xyz"),
  ]
  grid2_tier2 = IntervalTier("tier2", 0, 5)
  grid2_tier2.intervals = [
    Interval(0, 5, "XZ"),
  ]

  grid2.tiers = [
    grid2_tier1,
    grid2_tier2
  ]

  error, res = get_vocabulary([grid1, grid2], {"tier1", "tier2"}, ignore={
      "", "Z", "b"}, logger=getLogger())

  assert error is None
  assert res == OrderedSet(['-', 'X', 'XZ', 'a', 'c', 'xyz'])
