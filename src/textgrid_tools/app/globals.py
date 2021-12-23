from os import cpu_count

DEFAULT_N_DIGITS = 16
DEFAULT_N_JOBS = cpu_count()
DEFAULT_PUNCTUATION = {
  "!", "\"", "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/", ":", ";", "<", "=", ">", "?", "@", "[", "\\", "]", "{", "}", "~", "`",
  "、", "。", "।", "¿", "¡", "【", "】", "，", "…", "‥", "「", "」", "『", "』", "〝", "〟", "″", "⟨", "⟩", "♪", "・", "‹", "›", "«", "»", "～", "′", "“", "”"
}

# DEFAULT_MFA_IGNORE_PUNCTUATION = "、。।，@<>"(),.:;¿?¡!\\&%#*~【】，…‥「」『』〝〟″⟨⟩♪・‹›«»～′$+="  # missing: “”
# see https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner/blob/d8bddd43efa51acf3b9e71bbdd6d6f6a23d7bb79/montreal_forced_aligner/dictionary/mixins.py#L24
# print(' '.join(sorted(DEFAULT_PUNCTUATION)))
