from textgrid import Interval

from textgrid_tools.intervals.duration_joining import split_pauses
from textgrid_tools_tests.helper import assert_intervals_are_equal


def test_empty__returns_empty_lists():
  start, content, end = split_pauses([])
  assert_intervals_are_equal(start, [])
  assert_intervals_are_equal(content, [])
  assert_intervals_are_equal(end, [])


def test_pause__returns_pause_empty_empty():
  start, content, end = split_pauses([Interval(0, 1, "")])
  assert_intervals_are_equal(start, [Interval(0, 1, "")])
  assert_intervals_are_equal(content, [])
  assert_intervals_are_equal(end, [])


def test_pause_pause__returns_pauses_empty_empty():
  start, content, end = split_pauses([Interval(0, 1, ""), Interval(1, 2, "")])
  assert_intervals_are_equal(start, [Interval(0, 1, ""), Interval(1, 2, "")])
  assert_intervals_are_equal(content, [])
  assert_intervals_are_equal(end, [])


def test_content__returns_empty_content_empty():
  start, content, end = split_pauses([Interval(0, 1, "a")])
  assert_intervals_are_equal(start, [])
  assert_intervals_are_equal(content, [Interval(0, 1, "a")])
  assert_intervals_are_equal(end, [])


def test_content_pause__returns_empty_content_pause():
  start, content, end = split_pauses([Interval(0, 1, "a"), Interval(1, 2, "")])
  assert_intervals_are_equal(start, [])
  assert_intervals_are_equal(content, [Interval(0, 1, "a")])
  assert_intervals_are_equal(end, [Interval(1, 2, "")])


def test_pause_content__returns_pause_content_empty():
  start, content, end = split_pauses([Interval(0, 1, ""), Interval(1, 2, "a")])
  assert_intervals_are_equal(start, [Interval(0, 1, "")])
  assert_intervals_are_equal(content, [Interval(1, 2, "a")])
  assert_intervals_are_equal(end, [])


def test_pause_content_pause__returns_pause_content_pause():
  start, content, end = split_pauses([Interval(0, 1, ""), Interval(1, 2, "a"), Interval(2, 3, "")])
  assert_intervals_are_equal(start, [Interval(0, 1, "")])
  assert_intervals_are_equal(content, [Interval(1, 2, "a")])
  assert_intervals_are_equal(end, [Interval(2, 3, "")])


def test_pause_pause_content_content_pause_pause__returns_pauses_contents_pauses():
  start, content, end = split_pauses([
    Interval(0, 1, ""), Interval(1, 2, ""),
    Interval(2, 3, "a"), Interval(3, 4, "b"),
    Interval(4, 5, ""), Interval(5, 6, ""),
  ])
  assert_intervals_are_equal(start, [Interval(0, 1, ""), Interval(1, 2, "")])
  assert_intervals_are_equal(content, [Interval(2, 3, "a"), Interval(3, 4, "b")])
  assert_intervals_are_equal(end, [Interval(4, 5, ""), Interval(5, 6, "")])
