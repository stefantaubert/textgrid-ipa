from logging import getLogger
from typing import cast

from text_utils import symbols_map_arpa_to_ipa
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.utils import update_or_add_tier


def map_arpa_to_ipa(grid: TextGrid, arpa_tier_name: str, ipa_tier_name: str, overwrite_existing_tier: bool) -> None:
  logger = getLogger(__name__)

  arpa_tier: IntervalTier = grid.getFirst(arpa_tier_name)
  if arpa_tier is None:
    raise Exception("ARPA tier not found!")

  if grid.getFirst(ipa_tier_name) is not None and not overwrite_existing_tier:
    raise Exception("IPA tier already exists!")

  ipa_tier = IntervalTier(
    minTime=arpa_tier.minTime,
    maxTime=arpa_tier.maxTime,
    name=ipa_tier_name,
  )

  for interval in arpa_tier.intervals:
    arpa_str = cast(str, interval.mark)
    arpa_symbols = tuple(arpa_str.split(" "))
    new_ipa_tuple = symbols_map_arpa_to_ipa(
      arpa_symbols=arpa_symbols,
      ignore={},
      replace_unknown=False,
      replace_unknown_with=None,
    )

    new_ipa = " ".join(new_ipa_tuple)
    logger.debug(f"Mapped \"{arpa_str}\" to \"{new_ipa}\".")

    ipa_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=new_ipa,
    )
    ipa_tier.intervals.append(ipa_interval)

  if overwrite_existing_tier:
    update_or_add_tier(grid, ipa_tier)
  else:
    grid.append(ipa_tier)
