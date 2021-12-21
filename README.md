# textgrid-tools

![Python](https://img.shields.io/github/license/stefantaubert/textgrid-ipa)
![Python](https://img.shields.io/badge/python-3.8.6-green.svg)

A python tool which is able:

- to detect pauses in recordings (.wav),
- to extract words from annotated sentences and
- to convert English words to IPA transcription based on CMUDict (and Epitran for out-of-vocabulary words).

File structure:

```txt
$base_dir
├── 200928-001
│  ├── audio.wav
|  ├── 0_initial.TextGrid
|  ├── 1_pauses.TextGrid
|  ├── 2_sentences.TextGrid
|  ├── 3_words.TextGrid
|  ├── 4_words_aligned.TextGrid
|  ├── 5_words_ipa_phonemes.TextGrid
|  ├── 6_words_ipa_phones.TextGrid
├── ...
```

## Workflow

The workflow is usually first to detect the silence boundaries of a recording with `wav2pauses`. Then you transcribe the contained sentences in `praat` to English. After that, you extract the words from the sentences with `sentences2words` and adjust the word boundaries manually via `praat`. In the next step, you convert the English words to IPA with `words2ipa`. Then, you make a copy of the tier in `praat` to have a reference to the standard-IPA transcription and adjust in the copied tier the actual-IPA transcription. As result you have at least the following tiers:

```txt
silence
speech
words
IPA-standard
IPA-actual
```

Possible recommended steps:

```txt
Input: raw (audio)
1. pauses (auto): detecting pauses
2. sentences (manual): annotating each sentence
  2.1. create dataset (auto)
3. words (auto): extracting all words from the sentences
4. words_aligned (manual): aligning the word boundaries
5. words_ipa_phonemes (auto): converting the words to IPA
  5.1. create dataset (auto)
6. words_ipa_phones (manual): annotating actual spoken IPA
  6.1. create dataset (auto)
```

Methods:

```py
def init(base_dir: Path, recording_name: str, audio_path: Path):
def clone(base_dir: Path, recording_name: str, in_step: str, out_step: str):
def detect_silence(base_dir: Path, recording_name: str, in_step: str, out_step: str, out_tier: str, silence_boundary: float, chunk_size_ms: int, min_silence_duration_ms: int, min_content_duration_ms: int, content_buffer_start_ms: int, content_buffer_end_ms: int):
def extract_words(base_dir: Path, recording_name: str, in_step: str, out_step: str, in_tier: str, out_tier: str):
def convert_to_ipa(base_dir: Path, in_step: str, out_step: str, in_tier: str, out_tier: str, mode: EngToIpaMode, replace_unknown_with: str, consider_ipa_annotations: bool):
def to_dataset(base_dir: Path, recording_name: str, step: str, tier: str, duration_s_max: float, remove_silence_tier: Optional[str], output_dir: Path, output_name: str, speaker_name: str, speaker_gender: str, speaker_accent: str):
```

## Setup

Currently there is only linux supported.

You need to install [flite](https://github.com/festvox/flite) for G2P conversion of English text with Epitran for OOV words:

```sh
git clone https://github.com/festvox/flite
cd flite
./configure && make
sudo make install
cd testsuite
make lex_lookup
sudo cp lex_lookup /usr/local/bin
cd ..
```

Then checkout this repository:

```sh
git clone https://github.com/stefantaubert/textgrid-ipa
cd textgrid-ipa
# install pipenv
pip install --user pipenv --python 3.8
# install custom env for repository
## a) for runtime only:
pipenv install --ignore-pipfile
## b) for development:
pipenv install --dev
```

## Usage

Example:

```sh
# help
pipenv run python -m cli --help
export recording_name="200928-001"
export recording_name="200928-002"
export recording_name="200928-003"
export recording_name="200928-004"

export base_dir=$tipa_base_dir
export PYTHONPATH=$tipa_code_dir
cd $PYTHONPATH
pipenv run python -m cli add-rec \
  --recording_name="$recording_name" \
  --audio_path="$recordings_dir/$recording_name.wav" \
  --out_step_name="0_initial"

pipenv run python -m cli rec-add-silence \
  --recording_name="$recording_name" \
  --in_step_name="0_initial" \
  --out_step_name="1_pauses" \
  --out_tier_name="silence" \
  --chunk_size_ms=50 \
  --silence_boundary=0.40 \
  --min_silence_duration_ms=700 \
  --min_content_duration_ms=200 \
  --content_buffer_start_ms=50 \
  --content_buffer_end_ms=100 \
  --silence_mark="silence" \
  --content_mark=""

pipenv run python -m cli rec-clone \
  --recording_name="$recording_name" \
  --in_step_name="1_pauses" \
  --out_step_name="2_sentences" \

pipenv run python -m cli rec-add-words \
  --recording_name="$recording_name" \
  --in_step_name="2_sentences" \
  --out_step_name="3_words" \
  --in_tier_name="sentences" \
  --out_tier_name="words"

pipenv run python -m cli rec-clone \
  --recording_name="$recording_name" \
  --in_step_name="3_words" \
  --out_step_name="4_words_aligned" \

pipenv run python -m cli rec-print-stats \
  --recording_name="$recording_name" \
  --step_name="4_words_aligned" \
  --tier_name="IPA-standard" \
  --tier_lang=IPA \
  --ignore_arcs \
  --replace_unknown_ipa_by="_"

pipenv run python -m cli rec-add-ipa \
  --recording_name="$recording_name" \
  --in_step_name="4_words_aligned" \
  --out_step_name="5_words_ipa_phonemes" \
  --in_tier_name="words" \
  --in_tier_lang=ENG \
  --out_tier_name="IPA-standard" \
  --mode=BOTH \
  --replace_unknown_with="_"

pipenv run python -m cli rec-print-stats \
  --recording_name="$recording_name" \
  --step_name="5_words_ipa_phonemes" \
  --tier_name="IPA-standard" \
  --tier_lang=IPA \
  --ignore_arcs \
  --replace_unknown_ipa_by="_"

pipenv run python -m cli rec-clone \
  --recording_name="$recording_name" \
  --in_step_name="5_words_ipa_phonemes" \
  --out_step_name="6_words_ipa_phones" \

pipenv run python -m cli rec-print-stats \
  --recording_name="$recording_name" \
  --step_name="6_words_ipa_phones" \
  --tier_name="IPA-actual" \
  --tier_lang=IPA \
  --ignore_arcs \
  --replace_unknown_ipa_by="_"

pipenv run python -m cli rec-to-dataset \
  --recording_name="$recording_name" \
  --step_name="6_words_ipa_phones" \
  --tier_name="IPA-actual" \
  --tier_lang=IPA \
  --duration_s_max=10 \
  --output_dir="$datasets_dir/NNLV_pilot/phone-based/$recording_name" \
  --speaker_name="phd1" \
  --speaker_accent="mandarin" \
  --speaker_gender="f" \
  --ignore_empty_marks \
  --overwrite_output
```

## Development

Recommended Addons for VSCode:

- GitLens
- MagicPython
- Pylance
- Python

My VSCode settings:

```json
{
  "python.pythonPath": "/home/user/.local/share/virtualenvs/textgrid-ipa-...",
  "editor.tabSize": 2,
  "editor.fontSize": 15,
  "editor.wordWrap": "on",
  "files.autoSave": "afterDelay",
  "gitlens.codeLens.enabled": false,
  "gitlens.advanced.telemetry.enabled": false,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.lintOnSave": true,
  "python.languageServer": "Pylance",
  "files.trimTrailingWhitespace": true,
  "python.formatting.autopep8Args": [
    "--indent-size=2",
    "--ignore=E121",
    "--max-line-length=100"
  ],
  "editor.formatOnSave": true,
  "workbench.editor.revealIfOpen": true,
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.autoSearchPaths": false,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### Add to another project

In the destination project run:

```sh
# if not already done:
pip install --user pipenv --python 3.7
# add reference
pipenv install -e git+https://github.com/stefantaubert/textgrid-ipa.git@main#egg=textgrid_tools
```

### Notes

Python 3.9 not working because of:

```txt
[pipenv.exceptions.InstallError]:     In file included from /usr/include/python3.9/unicodeobject.h:1026:0,
[pipenv.exceptions.InstallError]:                      from /usr/include/python3.9/Python.h:97,
[pipenv.exceptions.InstallError]:                      from src/marisa_trie.cpp:4:
[pipenv.exceptions.InstallError]:     /usr/include/python3.9/cpython/unicodeobject.h:551:42: note: declared here
[pipenv.exceptions.InstallError]:      Py_DEPRECATED(3.3) PyAPI_FUNC(PyObject*) PyUnicode_FromUnicode(
[pipenv.exceptions.InstallError]:                                               ^~~~~~~~~~~~~~~~~~~~~
[pipenv.exceptions.InstallError]:     error: command '/usr/bin/x86_64-linux-gnu-gcc' failed with exit code 1
```

Don't use ' instead of ˈ for primary stress.
Don't use / in IPA transcriptions
Don't insert line breaks in any transcription

# V2

```sh
# Convert txt to textgrid

export base_dir=$tipa_base_dir
export PYTHONPATH=$tipa_code_dir
cd $PYTHONPATH

pipenv run python -m cli mfa-txt-to-textgrid \
  --text_folder_in="$path_recordings_dir" \
  --audio_folder="$path_recordings_dir" \
  --text_format=GRAPHEMES \
  --language=ENG \
  --tier_name="sentences" \
  --folder_out="$path_textgrid_dir" \
  --overwrite
```

# Create executable

```sh
# install
sudo apt-get install patchelf

# needs to be called on all platforms
pipenv run cxfreeze \
  -O \
  --compress \
  --target-dir=dist \
  --bin-includes="libffi.so" \
  --target-name="textgrid-tools" \
  src/cli.py

# libffi.so is located at "/usr/lib/x86_64-linux-gnu/libffi.so.7"
# if not included this error occurs:
## ...
## File "/usr/lib/python3.8/ctypes/__init__.py", line 7, in <module>
## ImportError: libffi.so.7: cannot open shared object file: No such file or directory

# check filesizes
cd dist
du -h | sort -rh

# zip files
cd dist
zip textgrid-tools-linux.zip ./ -r

# unzip
unzip textgrid-tools-linux.zip -d target_folder
```

sudo apt-get install ffmpeg -y
 ffmpeg -i 04.mp3 -acodec pcm_s16le -ar 22050 04.wav