from pathlib import Path
from typing import Optional

from text_utils import EngToIpaMode



def init(base_dir: Path, recording_name: str, audio_path: Path):
  pass

def clone(base_dir: Path, recording_name: str, in_step: str, out_step: str):
  pass

def detect_silence(base_dir: Path, recording_name: str, in_step: str, out_step: str, out_tier: str, silence_boundary: float, chunk_size_ms: int, min_silence_duration_ms: int, min_content_duration_ms: int, content_buffer_start_ms: int, content_buffer_end_ms: int):
  pass

def extract_words(base_dir: Path, recording_name: str, in_step: str, out_step: str, in_tier: str, out_tier: str):
  pass

def convert_to_ipa(base_dir: Path, in_step: str, out_step: str, in_tier: str, out_tier: str, mode: EngToIpaMode, replace_unknown_with: str, consider_ipa_annotations: bool):
  pass

def to_dataset(base_dir: Path, recording_name: str, step: str, tier: str, duration_s_max: float, remove_silence_tier: Optional[str], output_dir: Path, output_name: str, speaker_name: str, speaker_gender: str, speaker_accent: str):
  pass
