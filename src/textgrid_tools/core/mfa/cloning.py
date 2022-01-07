from textgrid.textgrid import Interval, IntervalTier


def copy_tier(tier: IntervalTier, ignore_marks: bool) -> IntervalTier:
  result = IntervalTier(
    name=tier.name,
    maxTime=tier.maxTime,
    minTime=tier.minTime,
  )

  for interval in tier.intervals:
    cloned_interval = copy_interval(interval, ignore_marks)
    result.intervals.append(cloned_interval)

  return result


def copy_interval(interval: Interval, ignore_marks: bool) -> Interval:
  new_mark = "" if ignore_marks else interval.mark
  result = Interval(
    minTime=interval.minTime,
    maxTime=interval.maxTime,
    mark=new_mark,
  )
  return result
