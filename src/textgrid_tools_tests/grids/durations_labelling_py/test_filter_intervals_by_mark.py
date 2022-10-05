from textgrid import Interval

from textgrid_tools.grids.durations_labelling import filter_intervals_by_mark


def test_component():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 2, "b"),
    Interval(2, 3, "c"),
    Interval(3, 4, "b"),
  ]
  res = list(filter_intervals_by_mark(intervals, {"b"}))
  assert res == [intervals[1], intervals[3]]
