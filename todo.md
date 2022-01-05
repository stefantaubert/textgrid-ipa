# TODO

Maybe refactor commands like so:

```txt
textgrid-tools grids {create-dictionary}
textgrid-tools grid {create,synchronize-to-audio,split,print-stats}
textgrid-tools tiers {remove,normalize,remove-symbols,fix-boundaries,convert-to-symbols}
textgrid-tools tier {clone,move,rename,transcribe-words-to-arpa}
textgrid-tools intervals {join}
```

- add insert tiers from other grids
- add map one tier to another while ignoring spaces
- join on sentences
- refactor all sub-command parsers
- improve logging
- check that custom output parameters are set to default if not defined per cli e.g. output-directory is set to input-directory
- provide windows and mac version
- use local dictionary for create-dict-from-grids
- make map on phoneme level word based!
  - by creating single commands like 1. words to ARPA with space separated (do not merge symbols here because one space always between symbols) 2. separate words on space considering merge symbols 3. map tier to other tier, by ignoring empty intervals (like original text addition)
- bug transliterated oov word to ... shows same pronunciation multiple times
- remove old references
- add merge sentences from words
- overwrite tier at all places
- remove start/end from textgrid
- copy textgrid directory
- add validation methods, e.g.,
  - tier contains custom symbols
  - tier contains only ARPAbet symbols
  - tier contains non-dictionary words
