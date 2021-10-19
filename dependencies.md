# Remote Dependencies

- text-utils
  - pronunciation_dict_parser
  - g2p_en
  - sentence2pronunciation
- audio_utils
- speech_dataset_parser
  - general-utils

## Pipfile

### Local

```Pipfile
text-utils = {editable = true, path = "./../text-utils"}
audio-utils = {editable = true, path = "./../audio-utils"}
speech_dataset_parser = {editable = true, path = "./../speech_dataset_parser"}

pronunciation_dict_parser = {editable = true, path = "./../pronunciation_dict_parser"}
g2p_en = {editable = true, path = "./../g2p"}
sentence2pronunciation = {editable = true, path = "./../sentence2pronunciation"}
general-utils = {editable = true, path = "./../general-utils"}
```

### Remote

```Pipfile
text-utils = {editable = true, ref = "master", git = "https://github.com/stefantaubert/text-utils.git"}
audio-utils = {editable = true, ref = "master", git = "https://github.com/stefantaubert/audio-utils.git"}
speech_dataset_parser = {editable = true, ref = "master", git = "https://github.com/stefantaubert/speech-dataset-parser.git"}
```

## setup.cfg

```cfg
text-utils@git+https://github.com/stefantaubert/text-utils.git
audio-utils@git+https://github.com/stefantaubert/audio-utils.git
speech_dataset_parser@git+https://github.com/stefantaubert/speech_dataset_parser.git
```
