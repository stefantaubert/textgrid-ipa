from textgrid.textgrid import Interval

from textgrid_tools.intervals.splitting import get_split_intervals


def test_empty__empty_F__returns_one_interval():
  interval = Interval(0.5, 2, "")

  intervals = list(get_split_intervals(
    interval, "", False))

  assert len(intervals) == 1
  assert intervals[0] == interval


def test_empty__empty_T__returns_one_interval():
  interval = Interval(0.5, 2, "")

  intervals = list(get_split_intervals(
    interval, "", True))

  assert len(intervals) == 1
  assert intervals[0] == interval


def test_one_symbol__empty_F__returns_one_interval():
  interval = Interval(0.5, 2, "a")

  intervals = list(get_split_intervals(
    interval, "", False))

  assert len(intervals) == 1
  assert intervals[0].mark == "a"


def test_one_symbol__empty_T__returns_one_interval():
  interval = Interval(0.5, 2, "a")

  intervals = list(get_split_intervals(
    interval, "", True))

  assert len(intervals) == 1
  assert intervals[0].mark == "a"


def test_two_symbols__empty_F__returns_two_intervals():
  interval = Interval(0.5, 1.5, "ab")

  intervals = list(get_split_intervals(
    interval, "", False))

  assert len(intervals) == 2
  assert intervals[0].minTime == 0.5
  assert intervals[0].maxTime == 1.0
  assert intervals[0].mark == "a"
  assert intervals[1].minTime == 1.0
  assert intervals[1].maxTime == 1.5
  assert intervals[1].mark == "b"


def test_two_symbols__empty_T__returns_three_intervals():
  interval = Interval(0.5, 2.0, "ab")

  intervals = list(get_split_intervals(
    interval, "", True))

  assert len(intervals) == 3
  assert intervals[0].minTime == 0.5
  assert intervals[0].maxTime == 1.0
  assert intervals[0].mark == "a"
  assert intervals[1].minTime == 1.0
  assert intervals[1].maxTime == 1.5
  assert intervals[1].mark == ""
  assert intervals[2].minTime == 1.5
  assert intervals[2].maxTime == 2.0
  assert intervals[2].mark == "b"


def test_component_F():
  interval = Interval(0.5, 2.5, "this is a test")

  intervals = list(get_split_intervals(
    interval, " ", False))

  assert len(intervals) == 4
  assert intervals[0] == Interval(0.5, 1.0, "this")
  assert intervals[1] == Interval(1.0, 1.5, "is")
  assert intervals[2] == Interval(1.5, 2.0, "a")
  assert intervals[3] == Interval(2.0, 2.5, "test")


def test_component_T():
  interval = Interval(0.5, 4, "this is a test")

  intervals = list(get_split_intervals(
    interval, " ", True))

  assert len(intervals) == 7
  assert intervals[0] == Interval(0.5, 1.0, "this")
  assert intervals[1] == Interval(1.0, 1.5, " ")
  assert intervals[2] == Interval(1.5, 2.0, "is")
  assert intervals[3] == Interval(2.0, 2.5, " ")
  assert intervals[4] == Interval(2.5, 3.0, "a")
  assert intervals[5] == Interval(3.0, 3.5, " ")
  assert intervals[6] == Interval(3.5, 4, "test")
