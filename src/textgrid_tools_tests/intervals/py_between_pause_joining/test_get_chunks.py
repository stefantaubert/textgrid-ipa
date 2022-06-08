from math import inf

from textgrid import Interval

from textgrid_tools.intervals.between_pause_joining import chunk_intervals
from textgrid_tools_tests.helper import assert_intervals_are_equal


def test_empty__returns_empty():
  result = list(chunk_intervals([], 0))
  assert result == []


def test_component__min_pause_0__merges_no_pause_intervals():
  intervals = (
    Interval(0, 1, ""),
    Interval(1, 2, "text"),
    Interval(2, 3, ""),
    Interval(3, 4, ""),
    Interval(4, 5, "text"),
    Interval(5, 6, "text"),
    Interval(6, 7, ""),
  )

  result = list(chunk_intervals(intervals, pause=0))

  assert len(result) == 6
  assert_intervals_are_equal(result[0], [
    Interval(0, 1, ""),
  ])
  assert_intervals_are_equal(result[1], [
    Interval(1, 2, "text"),
  ])
  assert_intervals_are_equal(result[2], [
    Interval(2, 3, ""),
  ])
  assert_intervals_are_equal(result[3], [
    Interval(3, 4, ""),
  ])
  assert_intervals_are_equal(result[4], [
    Interval(4, 5, "text"),
    Interval(5, 6, "text"),
  ])
  assert_intervals_are_equal(result[5], [
    Interval(6, 7, ""),
  ])


def test_component__min_pause_1_1__merges_pause_intervals_smaller_than_1_1():
  intervals = (
    Interval(0, 1, ""),
    Interval(1, 2, "text"),
    Interval(2, 3, ""),
    Interval(3, 4, ""),
    Interval(4, 5, "text"),
    Interval(5, 6, "text"),
    Interval(6, 7, ""),
  )

  result = list(chunk_intervals(intervals, pause=1.1))

  assert len(result) == 4
  assert_intervals_are_equal(result[0], [
    Interval(0, 1, ""),
    Interval(1, 2, "text"),
  ])
  assert_intervals_are_equal(result[1], [
    Interval(2, 3, ""),
  ])
  assert_intervals_are_equal(result[2], [
    Interval(3, 4, ""),
  ])
  assert_intervals_are_equal(result[3], [
    Interval(4, 5, "text"),
    Interval(5, 6, "text"),
    Interval(6, 7, ""),
  ])


def test_component__min_pause_inf__merges_all_pause_intervals():
  intervals = (
    Interval(0, 1, ""),
    Interval(1, 2, "text"),
    Interval(2, 3, ""),
    Interval(3, 4, ""),
    Interval(4, 5, "text"),
    Interval(5, 6, "text"),
    Interval(6, 7, ""),
  )

  result = list(chunk_intervals(intervals, pause=inf))

  assert len(result) == 1
  assert_intervals_are_equal(result[0], [
    Interval(0, 1, ""),
    Interval(1, 2, "text"),
    Interval(2, 3, ""),
    Interval(3, 4, ""),
    Interval(4, 5, "text"),
    Interval(5, 6, "text"),
    Interval(6, 7, ""),
  ])
