from textgrid import Interval

from textgrid_tools.intervals.duration_joining import split_pause_at_end
from textgrid_tools_tests.helper import assert_intervals_are_equal


def test_empty__returns_empty_lists():
  content, pause = split_pause_at_end([])
  assert_intervals_are_equal(content, [])
  assert_intervals_are_equal(pause, [])


def test_pause__returns_empty_list_and_pause():
  content, pause = split_pause_at_end([Interval(0, 1, "")])
  assert_intervals_are_equal(content, [])
  assert_intervals_are_equal(pause, [Interval(0, 1, "")])


def test_content__returns_content_and_empty_list():
  content, pause = split_pause_at_end([Interval(0, 1, "a")])
  assert_intervals_are_equal(content, [Interval(0, 1, "a")])
  assert_intervals_are_equal(pause, [])


def test_pause_content__returns_pause_with_content_and_empty_list():
  content, pause = split_pause_at_end([Interval(0, 1, ""), Interval(1, 2, "a")])
  assert_intervals_are_equal(content, [Interval(0, 1, ""), Interval(1, 2, "a")])
  assert_intervals_are_equal(pause, [])


def test_content_pause__returns_content_and_pause():
  content, pause = split_pause_at_end([Interval(0, 1, "a"), Interval(1, 2, "")])
  assert_intervals_are_equal(content, [Interval(0, 1, "a")])
  assert_intervals_are_equal(pause, [Interval(1, 2, "")])
