from textgrid.textgrid import Interval

from textgrid_tools.intervals.common import merge_intervals


def test_component_include_empty():
  intervals = (
    Interval(0, 1, ""),
    Interval(1, 2, "b"),
    Interval(2, 3, " "),
    Interval(3, 4, "c"),
    Interval(4, 5, "d"),
  )

  result = merge_intervals(list(intervals), "X", False)

  assert_interval = Interval(0, 5, "XbX XcXd")
  assert result.minTime == assert_interval.minTime
  assert result.maxTime == assert_interval.maxTime
  assert result.mark == assert_interval.mark


def test_component_ignore_empty():
  intervals = (
    Interval(0, 1, ""),
    Interval(1, 2, "b"),
    Interval(2, 3, " "),
    Interval(3, 4, "c"),
    Interval(4, 5, "d"),
  )

  result = merge_intervals(list(intervals), "X", True)

  assert_interval = Interval(0, 5, "bX XcXd")
  assert result.minTime == assert_interval.minTime
  assert result.maxTime == assert_interval.maxTime
  assert result.mark == assert_interval.mark
