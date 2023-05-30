from textgrid import Interval

from textgrid_tools.intervals.common import group_adjacent_content_and_pauses
from textgrid_tools_tests.helper import assert_intervals_are_equal


def test_empty__returns_empty():
  result = list(group_adjacent_content_and_pauses(()))

  assert len(result) == 0


def test_one_pause__returns_pause():
  result = list(group_adjacent_content_and_pauses((
    Interval(0, 1, ""),
  )))

  assert len(result) == 1
  assert_intervals_are_equal(result[0][0], [Interval(0, 1, "")])
  assert result[0][1] is True


def test_one_content__returns_content():
  result = list(group_adjacent_content_and_pauses((
    Interval(0, 1, "a"),
  )))

  assert len(result) == 1
  assert_intervals_are_equal(result[0][0], [Interval(0, 1, "a")])
  assert result[0][1] is False


def test_content_pause__returns_content_pause():
  result = list(group_adjacent_content_and_pauses((
    Interval(0, 1, "a"),
    Interval(1, 2, ""),
  )))

  assert len(result) == 2
  assert_intervals_are_equal(result[0][0], [Interval(0, 1, "a")])
  assert result[0][1] is False
  assert_intervals_are_equal(result[1][0], [Interval(1, 2, "")])
  assert result[1][1] is True


def test_pause_content__returns_pause_content():
  result = list(group_adjacent_content_and_pauses((
    Interval(0, 1, ""),
    Interval(1, 2, "a"),
  )))

  assert len(result) == 2
  assert_intervals_are_equal(result[0][0], [Interval(0, 1, "")])
  assert result[0][1] is True
  assert_intervals_are_equal(result[1][0], [Interval(1, 2, "a")])
  assert result[1][1] is False


def test_content_content__returns_grouped_content():
  result = list(group_adjacent_content_and_pauses((
    Interval(0, 1, "a"),
    Interval(1, 2, "b"),
  )))

  assert len(result) == 1
  assert_intervals_are_equal(result[0][0], [Interval(0, 1, "a"), Interval(1, 2, "b")])
  assert result[0][1] is False


def test_pause_pause__returns_grouped_pause():
  result = list(group_adjacent_content_and_pauses((
    Interval(0, 1, ""),
    Interval(1, 2, ""),
  )))

  assert len(result) == 1
  assert_intervals_are_equal(result[0][0], [Interval(0, 1, ""), Interval(1, 2, "")])
  assert result[0][1] is True


def test_component():
  result = list(group_adjacent_content_and_pauses((
    Interval(0, 1, ""),
    Interval(1, 2, "a"),
    Interval(2, 3, "a"),
    Interval(4, 5, ""),
    Interval(6, 7, ""),
    Interval(8, 9, "a"),
  )))

  assert len(result) == 4
  assert_intervals_are_equal(result[0][0], [Interval(0, 1, "")])
  assert result[0][1] is True

  assert_intervals_are_equal(result[1][0], [Interval(1, 2, "a"), Interval(2, 3, "a")])
  assert result[1][1] is False

  assert_intervals_are_equal(result[2][0], [Interval(4, 5, ""), Interval(6, 7, "")])
  assert result[2][1] is True

  assert_intervals_are_equal(result[3][0], [Interval(8, 9, "a")])
  assert result[3][1] is False
