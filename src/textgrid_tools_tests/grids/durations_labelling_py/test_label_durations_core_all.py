from math import inf

from textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.grids.durations_labelling import label_durations_core_all


def test_component():
  grid1 = TextGrid("test", 0, 5)
  grid1_tier1 = IntervalTier("tier1", 0, 5)
  grid1_tier2 = IntervalTier("tier2", 0, 5)
  grid1_tier1.intervals = [
    Interval(0, 0.5, "a"),  # 0.5s
    Interval(0.5, 1.5, "b"),  # 1s
    Interval(1.5, 2, ""),  # 0.5s
    Interval(2, 3, "a"),  # 1s
    Interval(3, 5, "a"),  # 2s
  ]

  grid1_tier2.intervals = [
    Interval(0, 0.5, "-"),
    Interval(0.5, 1.5, "-"),
    Interval(1.5, 2, "-"),
    Interval(2, 3, "X"),  # will not be changed because it is already X
    Interval(3, 5, "-"),  # will be changed
  ]
  grid1.tiers = [
    grid1_tier1,
    grid1_tier2
  ]
  grids = [
    grid1,
  ]

  grids_changed, total_intervals, considered_intervals, count_matching_intervals, duration_matching_intervals, changed_intervals = label_durations_core_all(grids, "tier1", "tier2", "X", only_consider_marks={
      "a"}, range_mode="percentile", range_min=40, range_max=inf, min_count=1)

  assert grids_changed == [True]
  assert total_intervals == 5
  assert considered_intervals == 3
  assert count_matching_intervals == 3  # 0-0.5, 2-3, 3-5 tier1
  assert duration_matching_intervals == 2  # 2-3 & 3-5 tier1
  assert changed_intervals == 1  # 3-5 tier2
  # tier 1 has not changed
  assert grid1_tier1.intervals[0].mark == "a"
  assert grid1_tier1.intervals[1].mark == "b"
  assert grid1_tier1.intervals[2].mark == ""
  assert grid1_tier1.intervals[3].mark == "a"
  assert grid1_tier1.intervals[4].mark == "a"
  # tier 2 has changed
  assert grid1_tier2.intervals[0].mark == "-"
  assert grid1_tier2.intervals[1].mark == "-"
  assert grid1_tier2.intervals[2].mark == "-"
  assert grid1_tier2.intervals[3].mark == "X"
  assert grid1_tier2.intervals[4].mark == "X"
