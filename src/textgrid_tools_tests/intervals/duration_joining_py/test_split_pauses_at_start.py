from textgrid import Interval

from textgrid_tools.intervals.duration_joining import split_pause_at_start
from textgrid_tools_tests.helper import assert_intervals_are_equal


def test_empty__returns_empty_lists():
  pause, content = split_pause_at_start([])
  assert_intervals_are_equal(pause, [])
  assert_intervals_are_equal(content, [])


def test_pause__returns_pause_and_empty_list():
  pause, content = split_pause_at_start([Interval(0, 1, "")])
  assert_intervals_are_equal(pause, [Interval(0, 1, "")])
  assert_intervals_are_equal(content, [])


def test_content__returns_empty_list_and_content():
  pause, content = split_pause_at_start([Interval(0, 1, "a")])
  assert_intervals_are_equal(pause, [])
  assert_intervals_are_equal(content, [Interval(0, 1, "a")])


def test_pause_content__returns_pause_and_content():
  pause, content = split_pause_at_start([Interval(0, 1, ""), Interval(1, 2, "a")])
  assert_intervals_are_equal(pause, [Interval(0, 1, "")])
  assert_intervals_are_equal(content, [Interval(1, 2, "a")])


def test_content_pause__returns_empty_and_content_with_pause():
  pause, content = split_pause_at_start([Interval(0, 1, "a"), Interval(1, 2, "")])
  assert_intervals_are_equal(pause, [])
  assert_intervals_are_equal(content, [Interval(0, 1, "a"), Interval(1, 2, "")])
