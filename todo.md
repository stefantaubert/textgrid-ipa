# TODO

Maybe refactor commands like so:

```txt
textgrid-tools grids {create-dictionary}
textgrid-tools grid {create,synchronize-to-audio,split,print-stats}
textgrid-tools tiers {remove,remove-symbols,normalize,switch-string-format,transcribe-words-to-arpa,transcribe-arpa-to-ipa}
textgrid-tools tier {clone,move,copy,rename,map,export-to-txt}
textgrid-tools intervals {join-between-pause,join-by-boundary,join-by-duration,join-by-sentence,split,remove,fix-boundaries}
```

- provide windows and mac version
- use local dictionary for create-dict-from-grids
- make map on phoneme level word based!
  - by creating single commands like 1. words to ARPA with space separated (do not merge symbols here because one space always between symbols) 2. separate words on space considering merge symbols 3. map tier to other tier, by ignoring empty intervals (like original text addition)
- bug: "transliterated oov word to ..." shows same pronunciation multiple times
- remove old references
- make all consistent
  - refactor all sub-command parsers
  - check that custom output parameters are set to default if not defined per cli e.g. output-directory is set to input-directory
- remove start/end from textgrid
- copy textgrid directory
- add validation methods, e.g.,
  - tier contains custom symbols
  - tier contains only ARPAbet symbols
    - add this to pronunciation parser
  - tier contains non-dictionary words
