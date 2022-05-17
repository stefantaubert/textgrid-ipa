from os import cpu_count
from typing import Tuple

from ordered_set import OrderedSet

from textgrid_tools.globals import ChangedAnything

DEFAULT_ENCODING = "utf-8"
DEFAULT_N_JOBS = cpu_count()
DEFAULT_N_FILE_CHUNKSIZE = 1
DEFAULT_MAXTASKSPERCHILD = None
DEFAULT_PUNCTUATION = list(OrderedSet(sorted((
  "!", "\"", "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/", ":", ";", "<", "=", ">", "?", "@", "[", "\\", "]", "{", "}", "~", "`",
  "、", "。", "？", "！", "：", "；", "।", "¿", "¡", "【", "】", "，", "…", "‥", "「", "」", "『", "』", "〝", "〟", "″", "⟨", "⟩", "♪", "・", "‹", "›", "«", "»", "～", "′", "“", "”"
))))
# ' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '`', '{', '}', '~'

# DEFAULT_MFA_IGNORE_PUNCTUATION = "、。।，@<>"(),.:;¿?¡!\\&%#*~【】，…‥「」『』〝〟″⟨⟩♪・‹›«»～′$+="  # missing: “”
# see https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner/blob/d8bddd43efa51acf3b9e71bbdd6d6f6a23d7bb79/montreal_forced_aligner/dictionary/mixins.py#L24
#print(' '.join(DEFAULT_PUNCTUATION), len(DEFAULT_PUNCTUATION))

Success = bool

ExecutionResult = Tuple[Success, ChangedAnything]
