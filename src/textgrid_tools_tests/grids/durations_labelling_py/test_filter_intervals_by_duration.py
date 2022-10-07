from math import inf

from textgrid import Interval

from textgrid_tools.grids.durations_labelling import filter_intervals_by_duration


def test_component():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 3, "b"),
    Interval(3, 6, "c"),
    Interval(6, 10, "d"),
    Interval(0, 1, "aa"),
    Interval(1, 3, "bb"),
    Interval(3, 6, "cc"),
    Interval(6, 10, "dd"),
  ]

  res = list(filter_intervals_by_duration(intervals, 0, inf))
  assert res == [
    intervals[0],
    intervals[1],
    intervals[2],
    intervals[3],
    intervals[4],
    intervals[5],
    intervals[6],
    intervals[7],
  ]


def test_1_2_3_4__1_2__returns_1():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 3, "b"),
    Interval(3, 6, "c"),
    Interval(6, 10, "d"),
    Interval(0, 1, "aa"),
    Interval(1, 3, "bb"),
    Interval(3, 6, "cc"),
    Interval(6, 10, "dd"),
  ]

  res = list(filter_intervals_by_duration(intervals, 1, 2))
  assert res == [
    intervals[0],
    intervals[4],
  ]


def test_1_2_3_4__1_3__returns_1_2():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 3, "b"),
    Interval(3, 6, "c"),
    Interval(6, 10, "d"),
    Interval(0, 1, "aa"),
    Interval(1, 3, "bb"),
    Interval(3, 6, "cc"),
    Interval(6, 10, "dd"),
  ]

  res = list(filter_intervals_by_duration(intervals, 1, 3))
  assert res == [
    intervals[0],
    intervals[1],
    intervals[4],
    intervals[5],
  ]


def test_1_2_3_4__4_inf__returns_4():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 3, "b"),
    Interval(3, 6, "c"),
    Interval(6, 10, "d"),
    Interval(0, 1, "aa"),
    Interval(1, 3, "bb"),
    Interval(3, 6, "cc"),
    Interval(6, 10, "dd"),
  ]

  res = list(filter_intervals_by_duration(intervals, 4, inf))
  assert res == [
    intervals[3],
    intervals[7],
  ]


def test_1_2_3_4__2_2__returns_nothing():
  intervals = [
    Interval(0, 1, "a"),
    Interval(1, 3, "b"),
    Interval(3, 6, "c"),
    Interval(6, 10, "d"),
    Interval(0, 1, "aa"),
    Interval(1, 3, "bb"),
    Interval(3, 6, "cc"),
    Interval(6, 10, "dd"),
  ]

  res = list(filter_intervals_by_duration(intervals, 2, 2))
  assert res == []
