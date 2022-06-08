from textgrid import Interval

from textgrid_tools.intervals.between_pause_joining import group_adjacent_pauses
from textgrid_tools_tests.helper import assert_interval_is_equal, assert_intervals_are_equal


def test_empty__returns_empty():
  result = list(group_adjacent_pauses([]))
  assert result == []


def test_one_text_interval__returns_text_interval():
  intervals = (
    Interval(0, 1, "text"),
  )
  result = list(group_adjacent_pauses(intervals))
  assert len(result) == 1
  assert_interval_is_equal(result[0], Interval(0, 1, "text"))


def test_one_pause_interval__returns_pause_group():
  intervals = (
    Interval(0, 1, ""),
  )
  result = list(group_adjacent_pauses(intervals))

  assert len(result) == 1
  assert_intervals_are_equal(result[0], [Interval(0, 1, "")])


def test_two_pause_intervals__returns_pause_group():
  intervals = (
    Interval(0, 1, ""),
    Interval(1, 2, ""),
  )
  result = list(group_adjacent_pauses(intervals))
  assert len(result) == 1
  assert_intervals_are_equal(result[0], [Interval(0, 1, ""), Interval(1, 2, "")])


def test_two_text_intervals__returns_two_text_intervals():
  intervals = (
    Interval(0, 1, "text"),
    Interval(1, 2, "text"),
  )
  result = list(group_adjacent_pauses(intervals))
  assert len(result) == 2
  assert_interval_is_equal(result[0], Interval(0, 1, "text"))
  assert_interval_is_equal(result[1], Interval(1, 2, "text"))


def test_text_pause_intervals__returns_text_pause_group():
  intervals = (
    Interval(0, 1, "text"),
    Interval(1, 2, ""),
  )
  result = list(group_adjacent_pauses(intervals))
  assert len(result) == 2
  assert_interval_is_equal(result[0], Interval(0, 1, "text"))
  assert_intervals_are_equal(result[1], [Interval(1, 2, "")])


def test_component():
  intervals = (
    Interval(0, 1, ""),
    Interval(1, 2, "text"),
    Interval(2, 3, ""),
    Interval(3, 4, ""),
    Interval(4, 5, "text"),
    Interval(5, 6, "text"),
    Interval(6, 7, ""),
  )

  result = list(group_adjacent_pauses(intervals))

  assert len(result) == 6
  assert_intervals_are_equal(result[0], [Interval(0, 1, "")])
  assert_interval_is_equal(result[1], Interval(1, 2, "text"))
  assert_intervals_are_equal(result[2], [Interval(2, 3, ""), Interval(3, 4, "")])
  assert_interval_is_equal(result[3], Interval(4, 5, "text"))
  assert_interval_is_equal(result[4], Interval(5, 6, "text"))
  assert_intervals_are_equal(result[5], [Interval(6, 7, "")])
