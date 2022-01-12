from text_utils import StringFormat
from textgrid.textgrid import Interval
from textgrid_tools.core.interval_format import IntervalFormat
from textgrid_tools.core.intervals.splitting import get_split_intervals


def test_no_space__returns_one_intervals():
  interval = Interval(0.5, 2, "\"Thistest\"")

  intervals = list(get_split_intervals(
    interval, StringFormat.TEXT,
      IntervalFormat.WORDS, {}, {}))

  assert len(intervals) == 1
  assert intervals[0] == Interval(0.5, 2, "\"Thistest\"")


def test_one_space__returns_two_intervals():
  interval = Interval(0.5, 2, "\"This test\"")

  intervals = list(get_split_intervals(
    interval, StringFormat.TEXT,
      IntervalFormat.WORDS, {}, {}))

  assert len(intervals) == 2
  assert intervals[0] == Interval(0.5, 1.25, "\"This")
  assert intervals[1] == Interval(1.25, 2.0, "test\"")


def test_double_space__returns_two_intervals():
  interval = Interval(3, 5, "Is  right.")

  intervals = list(get_split_intervals(
    interval, StringFormat.TEXT,
      IntervalFormat.WORDS, {}, {}))

  assert len(intervals) == 2
  assert intervals[0] == Interval(3, 3.5, "Is")
  assert intervals[1] == Interval(3.5, 5.0, "right.")
