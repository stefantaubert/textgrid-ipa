""" 
# parser.add_argument("--silence_boundary", type=float, default=0.25,
#                     help="Percent of lower dB recognized as silence.")
# parser.add_argument("--chunk_size_ms", type=int, default=50)
# parser.add_argument("--min_silence_duration_ms", type=int, default=700)
# parser.add_argument("--min_content_duration_ms", type=int, default=200)
# parser.add_argument("--content_buffer_start_ms", type=int, default=50)
# parser.add_argument("--content_buffer_end_ms", type=int, default=100) """

# from logging import getLogger
# from typing import List, Optional, Tuple

# import numpy as np
# from audio_utils import get_chunks, get_duration_s_samples, ms_to_samples
# from textgrid.textgrid import TextGrid
# from textgrid_tools.utils import (durations_to_intervals, grid_contains_tier,
#                                   intervals_to_tier, update_tier)


# def add_pause_tier(grid: TextGrid, wav: np.ndarray, sr: int, out_tier_name: Optional[str], silence_boundary: float, chunk_size_ms: int, min_silence_duration_ms: int, min_content_duration_ms: int, content_buffer_start_ms: int, content_buffer_end_ms: int, silence_mark: str, content_mark: str, overwrite_tier: bool) -> None:
#   logger = getLogger(__name__)

#   if grid_contains_tier(grid, out_tier_name) and not overwrite_tier:
#     logger.error(f"Tier {out_tier_name} already exists!")
#     return

#   chunk_size = ms_to_samples(chunk_size_ms, sr)
#   min_silence_duration = ms_to_samples(min_silence_duration_ms, sr)
#   min_content_duration = ms_to_samples(min_content_duration_ms, sr)
#   content_buffer_start = ms_to_samples(content_buffer_start_ms, sr)
#   content_buffer_end = ms_to_samples(content_buffer_end_ms, sr)

#   chunks = get_chunks(
#     wav=wav,
#     silence_boundary=silence_boundary,
#     chunk_size=chunk_size,
#     content_buffer_end=content_buffer_end,
#     content_buffer_start=content_buffer_start,
#     min_content_duration=min_content_duration,
#     min_silence_duration=min_silence_duration,
#   )

#   logger.info(f"Extracted {len(chunks)} chunks.")

#   mark_duration: List[Tuple[str, float]] = list()
#   for chunk in chunks:
#     duration = get_duration_s_samples(chunk.size, sr)
#     mark = silence_mark if chunk.is_silence else content_mark
#     mark_duration.append((mark, duration))

#   intervals = durations_to_intervals(mark_duration, grid.maxTime)
#   logger.info(f"Extracted {len(intervals)} intervals.")

#   pause_tier = intervals_to_tier(intervals, out_tier_name)

#   if grid_contains_tier(grid, pause_tier.name):
#     assert overwrite_tier
#     logger.info("Overwriting tier...")
#     update_tier(grid, pause_tier)
#   else:
#     logger.info("Adding tier...")
#     grid.append(pause_tier)
