from logging import getLogger
from typing import Iterable, Optional, cast

from text_utils import symbols_map_arpa_to_ipa
from text_utils.string_format import StringFormat
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.mfa.helper import (add_or_update_tier, get_first_tier,
                                            get_mark_symbols)
from textgrid_tools.core.validation import (ExistingTierError,
                                            InvalidGridError,
                                            NotExistingTierError)


def map_arpa_to_ipa(grid: TextGrid, tier_name: str, custom_output_tier_name: Optional[str], tier_string_format: StringFormat, overwrite_tier: bool) -> ExecutionResult:
  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NotExistingTierError.validate(grid, tier_name):
    return error, False

  output_tier_name = tier_name
  if custom_output_tier_name is not None:
    if not overwrite_tier and (error := ExistingTierError.validate(grid, custom_output_tier_name)):
      return error, False
    output_tier_name = custom_output_tier_name

  logger = getLogger(__name__)

  tier = get_first_tier(grid, tier_name)

  output_tier = IntervalTier(
    minTime=tier.minTime,
    maxTime=tier.maxTime,
    name=output_tier_name,
  )

  for interval in cast(Iterable[IntervalTier], tier.intervals):
    arpa_symbols = get_mark_symbols(interval, tier_string_format)
    ipa_symbols = symbols_map_arpa_to_ipa(
      arpa_symbols=arpa_symbols,
      ignore={},
      replace_unknown=False,
      replace_unknown_with=None,
    )

    new_ipa = tier_string_format.convert_symbols_to_string(ipa_symbols)
    logger.debug(f"Mapped \"{''.join(arpa_symbols)}\" to \"{''.join(ipa_symbols)}\".")

    ipa_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=new_ipa,
    )
    output_tier.intervals.append(ipa_interval)

  changed_anything = add_or_update_tier(grid, tier, output_tier, overwrite_tier)

  return None, changed_anything
