from argparse import ArgumentParser
from logging import Logger, getLogger
from typing import List, Tuple

import numpy as np
from scipy.io.wavfile import read, write
from tqdm import tqdm

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.utils import check_interval_has_content, ms_to_samples


def init_remove_silence_parser(parser: ArgumentParser):
  parser.add_argument("-f", "--file", type=str, required=True, help="TextGrid input filepath.")
  parser.add_argument("-o", "--output", type=str, required=True, help="TextGrid output filepath.")
  parser.add_argument("-t", "--tier-name", type=str, default="words",
                      help="The name of the tier with the English words annotated.")
  parser.add_argument("-w", "--wav-file", type=str, required=True, help="")
  parser.add_argument("-r", "--wav-output-file", type=str, required=True, help="")
  return remove_silence


def remove_silence(file: str, output: str, tier_name: str, wav_file: str, wav_output_file: str) -> None:
  logger = getLogger()
  grid = TextGrid()
  grid.read(file)

  logger.info(f"Calculating durations of tier {tier_name}...")

  sampling_rate, wav = read(wav_file)

  out_wav = calc_durations(
    grid=grid,
    tier_name=tier_name,
    in_wav=wav,
    sr=sampling_rate,
    logger=logger,
  )

  write(wav_output_file, sampling_rate, out_wav)

  grid.write(output)
  logger.info("Success!")


def get_remove_samples(start_s: float, end_s: float, sr: int) -> List[int]:
  start_ms = start_s * 1000
  end_ms = end_s * 1000
  start_samples = ms_to_samples(start_ms, sr)
  sample_count_to_remove = ms_to_samples(end_ms - start_ms, sr)
  result = list(range(start_samples, start_samples + sample_count_to_remove))
  return result


def remove_from_wav(wav: np.ndarray, start_s: float, end_s: float, sr: int) -> np.ndarray:
  start_samples = ms_to_samples(start_s, sr)
  sample_count_to_remove = ms_to_samples(end_s - start_s, sr)
  return remove_from_array(wav, start_samples, sample_count_to_remove)


def remove_from_array(wav: np.ndarray, start_s: int, count: int) -> np.ndarray:
  wav = np.delete(wav, list(range(start_s, start_s + count)), axis=0)
  return wav


def calc_durations(grid: TextGrid, tier_name: str, in_wav, sr: int, logger: Logger) -> np.ndarray:

  in_tier: IntervalTier = grid.getFirst(tier_name)
  in_tier_intervals: List[Interval] = in_tier.intervals
  in_tier_intervals_reversed = in_tier_intervals[::-1]

  new_intervals: List[Interval] = list()
  remove_samples = list()
  for interval in tqdm(in_tier_intervals_reversed):
    has_content = check_interval_has_content(interval)
    if has_content:
      new_intervals.append(interval)
    else:
      remove = get_remove_samples(interval.minTime, interval.maxTime, sr)
      remove_samples.extend(remove)
      #in_wav = remove_from_wav(in_wav, interval.minTime, interval.maxTime, sr)

  logger.info(in_wav.shape)
  logger.info(len(remove_samples))
  out_wav = np.delete(in_wav, remove_samples, axis=0)
  logger.info(out_wav.shape)

  new_intervals = new_intervals[::-1]
  word_durations: List[Tuple[str, float]] = list()

  for interval in new_intervals:
    duration = interval.maxTime - interval.minTime
    word_durations.append((interval.mark, duration))

  start = 0

  word_tier = IntervalTier(
    name=tier_name,
    minTime=start,
    maxTime=0,
  )

  for _, word_duration in enumerate(word_durations):
    word, duration = word_duration
    end = start + duration
    word_interval = Interval(
      minTime=start,
      maxTime=end,
      mark=word,
    )
    # word_intervals.append(word_interval)
    word_tier.addInterval(word_interval)
    start = end

  word_tier.maxTime = start

  for i, t in enumerate(grid.tiers):
    if t.name == tier_name:
      grid.tiers.pop(i)
      break
  grid.append(word_tier)

  return out_wav
