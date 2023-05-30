import re
from logging import getLogger

from textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.intervals.text_replacement import replace_text


def test_component():
  grid1 = TextGrid("test", 0, 5)
  grid1_tier1 = IntervalTier("tier1", 0, 5)
  grid1_tier2 = IntervalTier("tier2", 0, 5)
  grid1_tier1.intervals = [
    Interval(0, 0.5, "a"),  # 0.5s
    Interval(0.5, 1.5, "a"),  # 1s
    Interval(1.5, 2, "b"),  # 0.5s
    Interval(2, 3, ""),  # 1s
    Interval(3, 5, "a"),  # 2s
  ]

  grid1_tier2.intervals = [
    Interval(0, 0.5, "-"),
    Interval(0.5, 1.5, "b"),
    Interval(1.5, 2, "a"),
    Interval(2, 3, "X"),
    Interval(3, 5, "REPLACED"), # will be matched but unchanged
  ]

  grid1.tiers = [
    grid1_tier1,
    grid1_tier2
  ]

  error, changed_anything = replace_text(grid1, {"tier1", "tier2"}, re.compile(
    "^(a|-|REPLACED)$"), "REPLACED", mode="both", logger=getLogger())

  assert error is None
  assert changed_anything
  assert grid1_tier1.intervals == [
    Interval(0, 0.5, "REPLACED"),
    Interval(0.5, 1.5, "REPLACED"),
    Interval(1.5, 2, "b"),
    Interval(2, 3, ""),
    Interval(3, 5, "REPLACED"),
  ]

  assert grid1_tier2.intervals == [
    Interval(0, 0.5, "REPLACED"),
    Interval(0.5, 1.5, "b"),
    Interval(1.5, 2, "a"),
    Interval(2, 3, "X"),
    Interval(3, 5, "REPLACED"),
  ]
