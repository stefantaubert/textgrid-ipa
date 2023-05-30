
from logging import getLogger

from textgrid.textgrid import Interval, IntervalTier

from textgrid_tools.intervals.removing import remove_intervals_from_tiers


def test_component():
  tier1 = IntervalTier("A", 0, 9)
  tier1.intervals = [
    Interval(0, 3, mark="A1"),  # rem
    Interval(3, 4, mark="A2"),
    Interval(4, 4.5, mark="A3"),  # rem
    Interval(4.5, 5, mark="A4"),  # rem
    Interval(5, 6, mark="A5"),
    Interval(6, 7, mark="A6"),  # rem
    Interval(7, 8, mark="A7"),  # rem
    Interval(8, 9, mark="A8"),  # rem
  ]

  tier2 = IntervalTier("B", 0, 9)
  tier2.intervals = [
    Interval(0, 1, mark="B1"),  # rem
    Interval(1, 2, mark="B5"),  # rem
    Interval(2, 3, mark="B3"),  # rem
    Interval(3, 4, mark="B4"),
    Interval(4, 5, mark="B5"),  # rem
    Interval(5, 6, mark="B6"),
    Interval(6, 9, mark="B7"),  # rem
  ]

  intervals = [
    Interval(0, 1, mark=""),
    Interval(1, 2, mark=""),
    Interval(2, 3, mark=""),
    Interval(4, 4.5, mark=""),
    Interval(4.5, 5, mark=""),
    Interval(6, 9, mark=""),
  ]

  success = remove_intervals_from_tiers(intervals, [tier1, tier2], getLogger())

  assert success
  assert tier1.intervals == [
    Interval(0, 1, mark="A2"),
    Interval(1, 2, mark="A5"),
  ]
  assert tier1.minTime == 0
  assert tier1.maxTime == 2

  assert tier2.intervals == [
    Interval(0, 1, mark="B4"),
    Interval(1, 2, mark="B6"),
  ]
  assert tier2.minTime == 0
  assert tier2.maxTime == 2


def test_component_not_first_interval_removed():
  tier1 = IntervalTier("A", 2, 6)
  tier1.intervals = [
    Interval(2, 4, mark="A1"),
    Interval(4, 4.5, mark="A2"),  # rem
    Interval(4.5, 5, mark="A3"),  # rem
    Interval(5, 6, mark="A4"),
  ]

  tier2 = IntervalTier("B", 2, 6)
  tier2.intervals = [
    Interval(2, 2.3, mark="B1"),
    Interval(2.3, 2.6, mark="B2"),
    Interval(2.6, 3.8, mark="B3"),
    Interval(3.8, 4, mark="B4"),
    Interval(4, 5, mark="B5"),  # rem
    Interval(5, 6, mark="B6"),
  ]

  intervals = [
    Interval(4, 5, mark=""),
  ]

  success = remove_intervals_from_tiers(intervals, [tier1, tier2], getLogger())

  assert success
  assert tier1.intervals == [
    Interval(2, 4, mark="A1"),
    Interval(4, 5, mark="A4"),  # rem
  ]
  assert tier1.minTime == 2
  assert tier1.maxTime == 5

  assert tier2.intervals == [
    Interval(2, 2.3, mark="B1"),
    Interval(2.3, 2.6, mark="B2"),
    Interval(2.6, 3.8, mark="B3"),
    Interval(3.8, 4, mark="B4"),
    Interval(4, 5, mark="B6"),
  ]
  assert tier2.minTime == 2
  assert tier2.maxTime == 5
