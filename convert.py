from typing import List, Optional

import epitran

import textgrid
from textgrid.textgrid import Interval, IntervalTier, TextGrid


def set_tier(grid: TextGrid, tier: IntervalTier) -> None:
  existing_tier: Optional[IntervalTier] = grid.getFirst(tier.name)
  if existing_tier is not None:
    existing_tier.intervals.clear()
    existing_tier.intervals.extend(tier.intervals)
    existing_tier.maxTime = tier.maxTime
    existing_tier.minTime = tier.minTime
  else:
    grid.append(tier)


def main(filepath: str, outpath: str, word_tier_name: str,
         standard_name: Optional[str], actual_name: Optional[str]) -> None:
  grid = textgrid.TextGrid()
  grid.read(filepath)

  word_tier: IntervalTier = grid.getFirst(word_tier_name)
  word_intervals: List[Interval] = word_tier.intervals
  ipa_intervals = convert_to_ipa_intervall(word_intervals)

  actual_tier = IntervalTier(
    name=actual_name,
    minTime=word_tier.minTime,
    maxTime=word_tier.maxTime
  )
  actual_tier.intervals.extend(ipa_intervals)
  set_tier(grid, actual_tier)

  if standard_name is not None:
    standard_tier = IntervalTier(
      name=standard_name,
      minTime=word_tier.minTime,
      maxTime=word_tier.maxTime
    )
    standard_tier.intervals.extend(ipa_intervals)
    set_tier(grid, standard_tier)

  grid.write(outpath)
  return grid


def convert_to_ipa_intervall(tiers: List[IntervalTier]) -> List[IntervalTier]:
  epi = epitran.Epitran('eng-Latn')
  ipa_intervals: List[Interval] = list()
  for word_interval in tiers:
    ipa_interval = Interval(
      minTime=word_interval.minTime,
      maxTime=word_interval.maxTime,
      mark=epi.transliterate(word_interval.mark),
    )
    ipa_intervals.append(ipa_interval)
  return ipa_intervals


if __name__ == "__main__":
  main(
    filepath="/datasets/phil_home/downloads/test.TextGrid",
    outpath="out.TextGrid",
    word_tier_name="words",
    standard_name="IPA-standard",
    actual_name="IPA-actual",
  )
