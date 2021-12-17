from logging import getLogger
from typing import Iterable, cast

from text_utils import symbols_map_arpa_to_ipa
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import get_first_tier, tier_exists
from textgrid_tools.utils import update_or_add_tier


def can_map_arpa_to_ipa(grid: TextGrid, arpa_tier_name: str, ipa_tier_name: str, overwrite_existing_tier: bool) -> None:
  logger = getLogger(__name__)

  if not tier_exists(grid, arpa_tier_name):
    logger.error("ARPA tier not found!")
    return False

  if tier_exists(grid, ipa_tier_name) and not overwrite_existing_tier:
    logger.error("IPA tier already exists!")
    return False

  return True


def map_arpa_to_ipa(grid: TextGrid, arpa_tier_name: str, ipa_tier_name: str, overwrite_existing_tier: bool) -> None:
  logger = getLogger(__name__)

  arpa_tier = get_first_tier(grid, arpa_tier_name)

  ipa_tier = IntervalTier(
    minTime=arpa_tier.minTime,
    maxTime=arpa_tier.maxTime,
    name=ipa_tier_name,
  )

  for interval in cast(Iterable[IntervalTier], arpa_tier.intervals):
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
