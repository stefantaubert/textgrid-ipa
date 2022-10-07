import math

import numpy as np

from textgrid_tools.grids.durations_labelling import get_percentile_boundary


def test_component():
  durations = np.array([1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6])
  res_min, res_max = get_percentile_boundary(durations, 20, 60)
  assert res_min == 2.0
  assert res_max == 4.0


def test_max_inf__returns_max_inf():
  durations = np.array([1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6])
  res_min, res_max = get_percentile_boundary(durations, 20, math.inf)
  assert res_min == 2.0
  assert res_max == math.inf


def test_min_zero__returns_first_entry():
  durations = np.array([1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6])
  res_min, res_max = get_percentile_boundary(durations, 0, 60)
  assert res_min == 1.0
  assert res_max == 4.0


def test_same__returns_same():
  durations = np.array([1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6])
  res_min, res_max = get_percentile_boundary(durations, 20, 20)
  assert res_min == 2.0
  assert res_max == 2.0


def test_uneven_number():
  durations = np.array([1, 2, 3, 4])
  res_min, res_max = get_percentile_boundary(durations, 5, 90)
  assert res_min == 1.15
  assert res_max == 3.7


def test_one_entry_5_90__returns_entry_twice():
  durations = np.array([3])
  res_min, res_max = get_percentile_boundary(durations, 5, 90)
  assert res_min == 3.0
  assert res_max == 3.0


def test_one_entry_0_90__returns_entry_twice():
  durations = np.array([3])
  res_min, res_max = get_percentile_boundary(durations, 0, 90)
  assert res_min == 3.0
  assert res_max == 3.0


def test_one_entry_90_inf__returns_entry_inf():
  durations = np.array([3])
  res_min, res_max = get_percentile_boundary(durations, 90, math.inf)
  assert res_min == 3.0
  assert res_max == math.inf


def test_two_entries__returns_entry_twice():
  durations = np.array([3, 4])
  res_min, res_max = get_percentile_boundary(durations, 5, 90)
  assert res_min == 3.05
  assert res_max == 3.9
