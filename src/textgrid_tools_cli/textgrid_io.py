# taken from textgrid: see https://github.com/kylebgorman/textgrid

import re
from pathlib import Path
from typing import Generator, Iterator, Union

from textgrid import Interval, IntervalTier, Point, PointTier, TextGrid


def read_original(path: Path, n_digits: int, encoding: str) -> TextGrid:
  #start = perf_counter()
  grid_in = TextGrid()
  grid_in.read(path, n_digits, encoding)
  #duration = perf_counter() - start
  # print(duration)
  return grid_in


def _getMark(lines: Iterator[str], short):
  """
  Return the mark or text entry on a line. Praat escapes double-quotes
  by doubling them, so doubled double-quotes are read as single
  double-quotes. Newlines within an entry are allowed.
  """

  line = next(lines)

  # check that the line begins with a valid entry type
  if not short and not re.match(r'^\s*(text|mark) = "', line):
    raise ValueError('Bad entry: ' + line)

  # read until the number of double-quotes is even
  while line.count('"') % 2:
    next_line = next(lines)

    if not next_line:
      raise EOFError('Bad entry: ' + line[:20] + '...')

    line += next_line
  if short:
    pattern = r'^"(.*?)"\s*$'
  else:
    pattern = r'^\s*(text|mark) = "(.*?)"\s*$'
  entry = re.match(pattern, line, re.DOTALL)

  return entry.groups()[-1].replace('""', '"')


def parse_header(lines: Iterator[str]):
  header = next(lines)  # header junk
  m = re.match(r'File type = "([\w ]+)"', header)
  if m is None or not m.groups()[0].startswith('ooTextFile'):
    raise Exception(
      'The file could not be parsed as a Praat text file as it is lacking a proper header.')

  short = 'short' in m.groups()[0]
  file_type = parse_line(next(lines), short)  # header junk
  next(lines)  # header junk
  return file_type, short


def parse_line(line, short):
  line = line.strip()
  if short:
    if '"' in line:
      return line[1:-1]
    return float(line)
  if '"' in line:
    m = re.match(r'.+? = "(.*)"', line)
    return m.groups()[0]
  m = re.match(r'.+? = (.*)', line)
  return float(m.groups()[0])


def read_file_faster(path: Path, encoding: str) -> TextGrid:
  with open(path, "r", encoding=encoding) as f:
    lines = f.readlines()
  result = parse_lines(iter(lines))
  del f
  del lines
  return result


def parse_text(text: str) -> TextGrid:
  return parse_lines(iter(text.splitlines(True)))


def parse_lines(lines: Iterator[str]) -> TextGrid:
  """
  Read the tiers contained in the Praat-formatted TextGrid file
  indicated by string f. Times are rounded to the specified precision.
  """
  # start = perf_counter()
  result = TextGrid()
  file_type, short = parse_header(lines)
  if file_type != 'TextGrid':
    raise Exception(
      'The file could not be parsed as a TextGrid as it is lacking a proper header.')
  result.minTime = parse_line(next(lines), short)
  result.maxTime = parse_line(next(lines), short)
  next(lines)  # more header junk
  if short:
    m = int(next(lines).strip())  # will be self.n
  else:
    m = int(next(lines).strip().split()[2])  # will be self.n
  if not short:
    next(lines)
  for i in range(m):  # loop over grids
    if not short:
      next(lines)
    if parse_line(next(lines), short) == 'IntervalTier':
      inam = parse_line(next(lines), short)
      imin = parse_line(next(lines), short)
      imax = parse_line(next(lines), short)
      itie = IntervalTier(inam, imin, imax)
      itie.strict = result.strict
      n = int(parse_line(next(lines), short))
      for j in range(n):
        if not short:
          next(lines)  # header junk
        jmin = parse_line(next(lines), short)
        jmax = parse_line(next(lines), short)
        jmrk = _getMark(lines, short)
        if jmin < jmax:  # non-null
          itie.addInterval(Interval(jmin, jmax, jmrk))
      result.append(itie)
    else:  # pointTier
      inam = parse_line(next(lines), short)
      imin = parse_line(next(lines), short)
      imax = parse_line(next(lines), short)
      itie = PointTier(inam)
      n = int(parse_line(next(lines), short))
      for j in range(n):
        next(lines)  # header junk
        jtim = parse_line(next(lines), short)
        jmrk = _getMark(lines, short)
        itie.addPoint(Point(jtim, jmrk))
      result.append(itie)
  # duration = perf_counter() - start
  # print(duration)
  return result


def save_file_faster(grid: TextGrid, path: Path, encoding: str) -> None:
  lines = get_lines(grid)
  text = "\n".join(lines)
  with open(path, "w", encoding=encoding) as f:
    f.write(text)


def try_get_time_as_int(time: Union[float, int]) -> Union[int, float]:
  if isinstance(time, int):
    return time
  if isinstance(time, float):
    if time.is_integer():
      return int(time)
    return time
  assert False
  raise ValueError()


def get_lines(grid: TextGrid, null='') -> Generator[str, None, None]:
  """
  Write the current state into a Praat-format TextGrid file. f may
  be a file object to write to, or a string naming a path to open
  for writing.
  """
  yield 'File type = "ooTextFile"'
  yield 'Object class = "TextGrid"'
  yield ""
  yield 'xmin = {0} '.format(try_get_time_as_int(grid.minTime))
  # compute max time
  maxT = grid.maxTime
  if not maxT:
    maxT = max([t.maxTime if t.maxTime else t[-1].maxTime
                for t in grid.tiers])
  yield 'xmax = {0} '.format(try_get_time_as_int(maxT))
  yield 'tiers? <exists> '
  yield 'size = {0} '.format(len(grid))
  yield 'item []: '
  for (i, tier) in enumerate(grid.tiers, 1):
    yield '    item [{0}]:'.format(i)
    if tier.__class__ == IntervalTier:
      yield '        class = "IntervalTier" '
      yield '        name = "{0}" '.format(tier.name)
      yield '        xmin = {0} '.format(try_get_time_as_int(tier.minTime))
      yield '        xmax = {0} '.format(try_get_time_as_int(maxT))
      # compute the number of intervals and make the empty ones
      output = _fillInTheGaps(tier, null)
      yield '        intervals: size = {0} '.format(len(output))
      for (j, interval) in enumerate(output, 1):
        yield '        intervals [{0}]:'.format(j)
        yield '            xmin = {0} '.format(try_get_time_as_int(interval.minTime))
        yield '            xmax = {0} '.format(try_get_time_as_int(interval.maxTime))
        mark = _formatMark(interval.mark)
        yield '            text = "{0}" '.format(mark)
    elif tier.__class__ == PointTier:  # PointTier
      yield '        class = "TextTier" '
      yield '        name = "{0}" '.format(tier.name)
      yield '        xmin = {0} '.format(try_get_time_as_int(tier.minTime))
      yield '        xmax = {0} '.format(try_get_time_as_int(maxT))
      yield '        points: size = {0} '.format(len(tier))
      for (k, point) in enumerate(tier, 1):
        yield '            points [{0}]: '.format(k)
        yield '                time = {0} '.format(try_get_time_as_int(point.time))
        mark = _formatMark(point.mark)
        yield '                mark = "{0}" '.format(mark)
  # final new-line
  yield ""


def _formatMark(text):
  return text.replace('"', '""')


def _fillInTheGaps(tier: IntervalTier, null):
  """
  Returns a pseudo-IntervalTier with the temporal gaps filled in
  """
  prev_t = tier.minTime
  output = []
  for interval in tier.intervals:
    if prev_t < interval.minTime:
      output.append(Interval(prev_t, interval.minTime, null))
    output.append(interval)
    prev_t = interval.maxTime
  # last interval
  if tier.maxTime is not None and prev_t < tier.maxTime:  # also false if maxTime isn't defined
    output.append(Interval(prev_t, tier.maxTime, null))
  return output
