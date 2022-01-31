
from typing import (Collection, Generator, Iterable, List, Optional, Set,
                    Tuple, Union)

from text_utils import StringFormat
from text_utils.types import Symbol
from textgrid.textgrid import Interval, IntervalTier
from textgrid_tools.core.helper import (get_mark_symbols_intervals,
                                        interval_is_None_or_whitespace)
from textgrid_tools.core.interval_format import (IntervalFormat,
                                                 merge_interval_symbols)
from textgrid_tools.core.intervals.common import merge_intervals


def test_component():
  intervals = (
    Interval(0, 1, ""),
    Interval(1, 2, "b"),
    Interval(2, 3, " "),
    Interval(3, 4, "c"),
    Interval(4, 5, "d"),
  )

  result = merge_intervals(list(intervals), StringFormat.TEXT, IntervalFormat.SYMBOL)

  assert result
