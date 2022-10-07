from textgrid import Interval

from textgrid_tools.grids.durations_labelling import filter_intervals_by_mark


def test_a_b_c_d__empty__returns_all():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 2, "b"),
    Interval(2, 3, "c"),
    Interval(3, 4, "b"),
  ]
  res = list(filter_intervals_by_mark(intervals, {}))
  assert res == [
    intervals[0],
    intervals[1],
    intervals[2],
    intervals[3],
  ]


def test_a_b_c_d__e__returns_empty():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 2, "b"),
    Interval(2, 3, "c"),
    Interval(3, 4, "b"),
  ]
  res = list(filter_intervals_by_mark(intervals, {"e"}))
  assert res == []


def test_a_b_c_d__b__returns_b():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 2, "b"),
    Interval(2, 3, "c"),
    Interval(3, 4, "d"),
    Interval(0, 1, "a"),
    Interval(1, 2, "b"),
    Interval(2, 3, "c"),
    Interval(3, 4, "d"),
  ]
  res = list(filter_intervals_by_mark(intervals, {"b"}))
  assert res == [
    intervals[1],
    intervals[5],
  ]


def test_a_b_c_d__b_d__returns_b_d():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 2, "b"),
    Interval(2, 3, "c"),
    Interval(3, 4, "d"),
    Interval(0, 1, "a"),
    Interval(1, 2, "b"),
    Interval(2, 3, "c"),
    Interval(3, 4, "d"),
  ]
  res = list(filter_intervals_by_mark(intervals, {"b", "d"}))
  assert res == [
    intervals[1],
    intervals[3],
    intervals[5],
    intervals[7],
  ]
