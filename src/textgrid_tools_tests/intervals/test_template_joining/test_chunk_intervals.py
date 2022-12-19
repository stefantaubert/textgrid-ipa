from textgrid import Interval

from textgrid_tools.intervals.template_joining import chunk_intervals


def test_component():
  intervals = [
    Interval(0, 1, "a"),
    Interval(0, 1, ""),
    Interval(0, 1, "c"),
    Interval(0, 1, "a"),
    Interval(0, 1, ""),
    Interval(0, 1, "x"),
    Interval(0, 1, "y"),
    Interval(0, 1, "b"),
    Interval(0, 1, "a"),
    Interval(0, 1, "a"),
    Interval(0, 1, ""),
    Interval(0, 1, "c"),
    Interval(0, 1, ""),
  ]

  result = list(chunk_intervals(intervals, ["a", "", "c"]))

  assert result == [
    [intervals[0], intervals[1], intervals[2]],
    [intervals[3]],
    [intervals[4]],
    [intervals[5]],
    [intervals[6]],
    [intervals[7]],
    [intervals[8]],
    [intervals[9], intervals[10], intervals[11]],
    [intervals[12]],
  ]


def test_fulfill():
  intervals = [
    Interval(0, 1, "a"),
    Interval(0, 1, "b"),
  ]

  result = list(chunk_intervals(intervals, ["a", "b"]))

  assert result == [
    [intervals[0], intervals[1]],
  ]


def test_fulfill_single():
  intervals = [
    Interval(0, 1, "a"),
    Interval(0, 1, "b"),
    Interval(0, 1, "a"),
  ]

  result = list(chunk_intervals(intervals, ["a"]))

  assert result == [
    [intervals[0]],
    [intervals[1]],
    [intervals[2]],
  ]


def test_a_fulfill():
  intervals = [
    Interval(0, 1, "a"),
    Interval(0, 1, "a"),
    Interval(0, 1, "b"),
  ]

  result = list(chunk_intervals(intervals, ["a", "b"]))

  assert result == [
    [intervals[0]],
    [intervals[1], intervals[2]],
  ]


def test_a_a_fulfill():
  intervals = [
    Interval(0, 1, "a"),
    Interval(0, 1, "a"),
    Interval(0, 1, "a"),
    Interval(0, 1, "b"),
  ]

  result = list(chunk_intervals(intervals, ["a", "b"]))

  assert result == [
    [intervals[0]],
    [intervals[1]],
    [intervals[2], intervals[3]],
  ]


def test_fulfill_b():
  intervals = [
    Interval(0, 1, "a"),
    Interval(0, 1, "b"),
    Interval(0, 1, "b"),
  ]

  result = list(chunk_intervals(intervals, ["a", "b"]))

  assert result == [
    [intervals[0], intervals[1]],
    [intervals[2]],
  ]


def test_fulfill_X():
  intervals = [
    Interval(0, 1, "a"),
    Interval(0, 1, "b"),
    Interval(0, 1, "X"),
  ]

  result = list(chunk_intervals(intervals, ["a", "b"]))

  assert result == [
    [intervals[0], intervals[1]],
    [intervals[2]],
  ]


def test_X_fulfill():
  intervals = [
    Interval(0, 1, "X"),
    Interval(0, 1, "a"),
    Interval(0, 1, "b"),
  ]

  result = list(chunk_intervals(intervals, ["a", "b"]))

  assert result == [
    [intervals[0]],
    [intervals[1], intervals[2]],
  ]


def test_X_fulfill_X():
  intervals = [
    Interval(0, 1, "X"),
    Interval(0, 1, "a"),
    Interval(0, 1, "b"),
    Interval(0, 1, "X"),
  ]

  result = list(chunk_intervals(intervals, ["a", "b"]))

  assert result == [
    [intervals[0]],
    [intervals[1], intervals[2]],
    [intervals[3]],
  ]


def test_X():
  intervals = [
    Interval(0, 1, "X"),
  ]

  result = list(chunk_intervals(intervals, ["a", "b"]))

  assert result == [
    [intervals[0]],
  ]
