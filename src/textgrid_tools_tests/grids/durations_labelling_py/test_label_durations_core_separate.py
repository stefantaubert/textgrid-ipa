from math import inf

from textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.grids.durations_labelling import label_durations_core_separate


def test_component():
  grid1 = TextGrid("test", 0, 6)
  grid1_tier1 = IntervalTier("tier1", 0, 6)
  grid1_tier2 = IntervalTier("tier2", 0, 6)
  grid1_tier1.intervals = [
    Interval(0, 0.5, "a"),  # 0.5s
    Interval(0.5, 1.5, "b"),  # 1s
    Interval(1.5, 2, ""),  # 0.5s
    Interval(2, 3, "a"),  # 1s
    Interval(3, 5, "a"),  # 2s
    Interval(5, 6, "c"),  # 1s
  ]

  grid1_tier2.intervals = [
    Interval(0, 0.5, "-"),
    Interval(0.5, 1.5, "-"),
    Interval(1.5, 2, "-"),
    Interval(2, 3, "X"),
    Interval(3, 5, "-"),
    Interval(5, 6, "-"),
  ]
  grid1.tiers = [
    grid1_tier1,
    grid1_tier2
  ]
  grids = [
    grid1,
  ]

  grids_changed, total_intervals, considered_intervals, count_matching_intervals, duration_matching_intervals, changed_intervals = label_durations_core_separate(grids, "tier1", "tier2", "X", only_consider_marks={
      "a", "c"}, range_mode="percentile", range_min=40, range_max=inf, min_count=2)

  assert grids_changed == [True]
  assert total_intervals == 6
  assert considered_intervals == 4  # 3x "a" + 1x "c"
  assert count_matching_intervals == 3  # 3x "a"; 1x "c" is ignored because min_count >= 2
  assert duration_matching_intervals == 2  # 2x "a" -> 1s, 2s; 0.5s is ignored
  assert changed_intervals == 1  # 1x "a" @(3, 5)
  # tier 1 has not changed
  assert grid1_tier1.intervals[0].mark == "a"
  assert grid1_tier1.intervals[1].mark == "b"
  assert grid1_tier1.intervals[2].mark == ""
  assert grid1_tier1.intervals[3].mark == "a"
  assert grid1_tier1.intervals[4].mark == "a"
  assert grid1_tier1.intervals[5].mark == "c"
  # tier 2 has changed
  assert grid1_tier2.intervals[0].mark == "-"
  assert grid1_tier2.intervals[1].mark == "-"
  assert grid1_tier2.intervals[2].mark == "-"
  assert grid1_tier2.intervals[3].mark == "X"
  assert grid1_tier2.intervals[4].mark == "X"
  assert grid1_tier2.intervals[5].mark == "-"  # unchanged because of min_count=2
