from textgrid.textgrid import Interval

from textgrid_utils.intervals.common import merge_intervals_custom_symbol


def test_component():
  intervals = (
    Interval(0, 1, ""),
    Interval(1, 2, "b"),
    Interval(2, 3, " "),
    Interval(3, 4, "c"),
    Interval(4, 5, "d"),
  )

  result = merge_intervals_custom_symbol(list(intervals), "X")

  assert result == Interval(0, 5, "XbXXcXd")
