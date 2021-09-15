# Remote Dependencies

- text-utils
  - pronunciation_dict_parser
  - g2p_en
  - sentence2pronunciation
- audio_utils

## Pipfile

### Local

```Pipfile
text-utils = {editable = true, path = "./../text-utils"}
audio-utils = {editable = true, path = "./../audio-utils"}

pronunciation_dict_parser = {editable = true, path = "./../pronunciation_dict_parser"}
g2p_en = {editable = true, path = "./../g2p"}
sentence2pronunciation = {editable = true, path = "./../sentence2pronunciation"}
```

### Remote

```Pipfile
text-utils = {editable = true, ref = "master", git = "https://github.com/stefantaubert/text-utils.git"}
audio-utils = {editable = true, ref = "master", git = "https://github.com/stefantaubert/audio-utils.git"}
```

## setup.cfg

```cfg
text-utils@git+https://github.com/stefantaubert/text-utils.git
audio-utils@git+https://github.com/stefantaubert/audio-utils.git
```
