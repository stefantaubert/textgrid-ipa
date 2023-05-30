from textgrid.textgrid import Interval

from textgrid_tools.intervals.symbols_joining import chunk_intervals


def test_empty_empty_empty_r_returns_empty():
  result = list(chunk_intervals([], {}, {}, "right"))

  assert len(result) == 0


def test_one_interval_empty_empty_r__returns_interval_unchanged():
  interval = Interval(0.5, 2, "")

  result = list(chunk_intervals([interval], {}, {}, "right"))

  assert len(result) == 1
  assert len(result[0]) == 1
  assert result[0][0] == interval


def test_two_empty_intervals_empty_empty_r__returns_intervals_unchanged():
  int1 = Interval(0.5, 1.0, "")
  int2 = Interval(1.0, 1.5, "")

  result = list(chunk_intervals([int1, int2], {}, {}, "right"))

  assert len(result) == 2
  assert len(result[0]) == 1
  assert len(result[1]) == 1
  assert result[0][0] == int1
  assert result[1][0] == int2


def test_a__X__X_empty_r__returns_a_X():
  int1 = Interval(0.5, 1.0, "a")
  int2 = Interval(1.0, 1.5, "X")

  result = list(chunk_intervals([int1, int2], {"X"}, {}, "right"))

  assert len(result) == 1
  assert len(result[0]) == 2
  assert result[0][0] == int1
  assert result[0][1] == int2


def test_a__X__X_empty_l__returns_a__X():
  int1 = Interval(0.5, 1.0, "a")
  int2 = Interval(1.0, 1.5, "X")

  result = list(chunk_intervals([int1, int2], {"X"}, {}, "left"))

  assert len(result) == 2
  assert len(result[0]) == 1
  assert len(result[1]) == 1
  assert result[0][0] == int1
  assert result[1][0] == int2


def test_component_l():
  intervals = [
    Interval(0, 1, "\""),
    Interval(0, 1, "I"),
    Interval(0, 1, "'"),
    Interval(0, 1, "m"),
    Interval(0, 1, ","),
    Interval(0, 1, ""),
    Interval(0, 1, ""),
    Interval(0, 1, "4"),
    Interval(0, 1, "."),
    Interval(0, 1, " "),
    Interval(0, 1, "X"),
    Interval(0, 1, "!"),
    Interval(0, 1, "\""),
  ]

  result = list(chunk_intervals(intervals, {"\"", "'", ".", "!", ","}, {"", " "}, "left"))

  assert result == [
    [intervals[0], intervals[1]],
    [intervals[2], intervals[3]],
    [intervals[4]],
    [intervals[5]],
    [intervals[6]],
    [intervals[7]],
    [intervals[8]],
    [intervals[9]],
    [intervals[10]],
    [intervals[11]],
    [intervals[12]],
  ]


def test_component_r():
  intervals = [
    Interval(0, 1, "\""),
    Interval(0, 1, "I"),
    Interval(0, 1, "'"),
    Interval(0, 1, "m"),
    Interval(0, 1, ","),
    Interval(0, 1, ""),
    Interval(0, 1, ""),
    Interval(0, 1, "4"),
    Interval(0, 1, "."),
    Interval(0, 1, " "),
    Interval(0, 1, "X"),
    Interval(0, 1, "!"),
    Interval(0, 1, "\""),
  ]

  result = list(chunk_intervals(intervals, {"\"", "'", ".", "!", ","}, {"", " "}, "right"))

  assert result == [
    [intervals[0]],
    [intervals[1], intervals[2]],
    [intervals[3], intervals[4]],
    [intervals[5]],
    [intervals[6]],
    [intervals[7], intervals[8]],
    [intervals[9]],
    [intervals[10], intervals[11], intervals[12]],
  ]


def test_component_t():
  intervals = [
    Interval(0, 1, "\""),
    Interval(0, 1, "I"),
    Interval(0, 1, "'"),
    Interval(0, 1, "m"),
    Interval(0, 1, ","),
    Interval(0, 1, ""),
    Interval(0, 1, "-"),
    Interval(0, 1, "-"),
    Interval(0, 1, ""),
    Interval(0, 1, "4"),
    Interval(0, 1, "."),
    Interval(0, 1, " "),
    Interval(0, 1, "X"),
    Interval(0, 1, "!"),
    Interval(0, 1, "\""),
  ]

  result = list(chunk_intervals(intervals, {"\"", "'", ".", "!", ",", "-"}, {}, "together"))

  assert result == [
    [intervals[0]],
    [intervals[1]],
    [intervals[2]],
    [intervals[3]],
    [intervals[4]],
    [intervals[5]],
    [intervals[6], intervals[7]],
    [intervals[8]],
    [intervals[9]],
    [intervals[10]],
    [intervals[11]],
    [intervals[12]],
    [intervals[13], intervals[14]],
  ]
