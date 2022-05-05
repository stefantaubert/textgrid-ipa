# taken from textgrid

import codecs
import re

from textgrid import Interval, IntervalTier, Point, PointTier, TextGrid


def _getMark(text, short):
  """
  Return the mark or text entry on a line. Praat escapes double-quotes
  by doubling them, so doubled double-quotes are read as single
  double-quotes. Newlines within an entry are allowed.
  """

  line = text.readline()

  # check that the line begins with a valid entry type
  if not short and not re.match(r'^\s*(text|mark) = "', line):
    raise ValueError('Bad entry: ' + line)

  # read until the number of double-quotes is even
  while line.count('"') % 2:
    next_line = text.readline()

    if not next_line:
      raise EOFError('Bad entry: ' + line[:20] + '...')

    line += next_line
  if short:
    pattern = r'^"(.*?)"\s*$'
  else:
    pattern = r'^\s*(text|mark) = "(.*?)"\s*$'
  entry = re.match(pattern, line, re.DOTALL)

  return entry.groups()[-1].replace('""', '"')


def parse_header(source):
  header = source.readline()  # header junk
  m = re.match(r'File type = "([\w ]+)"', header)
  if m is None or not m.groups()[0].startswith('ooTextFile'):
    raise Exception(
      'The file could not be parsed as a Praat text file as it is lacking a proper header.')

  short = 'short' in m.groups()[0]
  file_type = parse_line(source.readline(), short, '')  # header junk
  t = source.readline()  # header junk
  return file_type, short


def parse_line(line, short, to_round):
  line = line.strip()
  if short:
    if '"' in line:
      return line[1:-1]
    return round(float(line), to_round)
  if '"' in line:
    m = re.match(r'.+? = "(.*)"', line)
    return m.groups()[0]
  m = re.match(r'.+? = (.*)', line)
  return round(float(m.groups()[0]), to_round)


def read(f, round_digits=DEFAULT_TEXTGRID_PRECISION, encoding=None):
  """
  Read the tiers contained in the Praat-formatted TextGrid file
  indicated by string f. Times are rounded to the specified precision.
  """
  result = TextGrid()
  with codecs.open(f, 'r', encoding=encoding) as source:
    file_type, short = parse_header(source)
    if file_type != 'TextGrid':
      raise TextGridError(
        'The file could not be parsed as a TextGrid as it is lacking a proper header.')
    result.minTime = parse_line(source.readline(), short, round_digits)
    result.maxTime = parse_line(source.readline(), short, round_digits)
    source.readline()  # more header junk
    if short:
      m = int(source.readline().strip())  # will be self.n
    else:
      m = int(source.readline().strip().split()[2])  # will be self.n
    if not short:
      source.readline()
    for i in range(m):  # loop over grids
      if not short:
        source.readline()
      if parse_line(source.readline(), short, round_digits) == 'IntervalTier':
        inam = parse_line(source.readline(), short, round_digits)
        imin = parse_line(source.readline(), short, round_digits)
        imax = parse_line(source.readline(), short, round_digits)
        itie = IntervalTier(inam, imin, imax)
        itie.strict = result.strict
        n = int(parse_line(source.readline(), short, round_digits))
        for j in range(n):
          if not short:
            source.readline().rstrip().split()  # header junk
          jmin = parse_line(source.readline(), short, round_digits)
          jmax = parse_line(source.readline(), short, round_digits)
          jmrk = _getMark(source, short)
          if jmin < jmax:  # non-null
            itie.addInterval(Interval(jmin, jmax, jmrk))
        result.append(itie)
      else:  # pointTier
        inam = parse_line(source.readline(), short, round_digits)
        imin = parse_line(source.readline(), short, round_digits)
        imax = parse_line(source.readline(), short, round_digits)
        itie = PointTier(inam)
        n = int(parse_line(source.readline(), short, round_digits))
        for j in range(n):
          source.readline().rstrip()  # header junk
          jtim = parse_line(source.readline(), short, round_digits)
          jmrk = _getMark(source, short)
          itie.addPoint(Point(jtim, jmrk))
        result.append(itie)
