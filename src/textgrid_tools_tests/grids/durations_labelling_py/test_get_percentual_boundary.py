import math

import numpy as np

from textgrid_tools.grids.durations_labelling import get_percentual_boundary


def test_component():
  durations = np.array([1, 2, 3, 4, 5, 6, 7, 8])
  res_min, res_max = get_percentual_boundary(durations, 25, 75)
  assert res_min == 2.0
  assert res_max == 6.0


def test_max_inf__returns_max_inf():
  durations = np.array([1, 2, 3, 4, 5, 6, 7, 8])
  res_min, res_max = get_percentual_boundary(durations, 25, math.inf)
  assert res_min == 2.0
  assert res_max == math.inf


def test_min_zero__returns_zero():
  durations = np.array([1, 2, 3, 4, 5, 6, 7, 8])
  res_min, res_max = get_percentual_boundary(durations, 0, 75)
  assert res_min == 0.0
  assert res_max == 6.0


def test_one_one__returns_same():
  durations = np.array([1, 2, 3, 4, 5, 6, 7, 8])
  res_min, res_max = get_percentual_boundary(durations, 25, 25)
  assert res_min == 2.0
  assert res_max == 2.0
