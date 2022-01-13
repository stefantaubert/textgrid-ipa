from textgrid_tools.core.intervals.duration_joining import chunk_intervals
from textgrid import Interval

def test_component():
  res = list(chunk_intervals(
    intervals=(
      Interval(0,1,""),
      Interval(1,2,"a"),
      Interval(3,4,"b"),
      Interval(5,7,""),
      Interval(8,9,"c"),
      Interval(9,10,""),
    ),
    include_pauses=False,
    max_duration_s=4,
  ))
  
  assert res == []