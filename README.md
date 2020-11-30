# textgrid-tools

![Python](https://img.shields.io/github/license/stefantaubert/textgrid-ipa)
![Python](https://img.shields.io/badge/python-3.7.9-green.svg)

A python tool which is able:

- to detect pauses in recordings (.wav),
- to extract words from annotated sentences and
- to convert English words to IPA transcription based on CMUDict (and Epitran for out-of-vocabulary words).

## Workflow

The workflow is usually first to detect the silence boundaries of a recording with `wav2pauses`. Then you transcribe the contained sentences in praat to English. After that you extract the words from the sentences with `sentences2words` and adjust the word boundaries manually via praat. In the next step you convert the English words to IPA with `words2ipa`. Then you make a copy the tier in praat to have a reference to the standard-IPA transcription and adjust in the copied tier the actual-IPA transcription. As result you have at least the following tiers:

- pauses
- sentences
- words
- standard-IPA
- actual-IPA

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
pip install --user pipenv --python 3.7
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

# wav2pauses
pipenv run python -m cli wav2pauses \
  -o="/datasets/pauses.TextGrid" \
  -w="/datasets/audio.wav" \
  -p="pauses" \
  -c=50 \
  -s=0.25 \
  -m=1000

# plot_durations
pipenv run python -m cli plot-durations \
  -f="/datasets/pauses_sentences.TextGrid" \
  -t="sentences"

# remove_empty_intervals
pipenv run python -m cli remove-empty-intervals \
  -f="/datasets/pauses_sentences.TextGrid" \
  -o="/datasets/pauses_sentences_clean.TextGrid" \
  -t="sentences" \
  -w="/datasets/audio.wav" \
  -r="/datasets/audio_clean.wav" \

# sentences2words
pipenv run python -m cli sentences2words \
  -f="/datasets/pauses_sentences_clean.TextGrid" \
  -o="/datasets/pauses_sentences_words.TextGrid" \
  -s="sentences" \
  -w="words"

# words2ipa
pipenv run python -m cli words2ipa \
  -f="/datasets/pauses_sentences_words.TextGrid" \
  -o="/datasets/pauses_sentences_words_ipa.TextGrid" \
  -w="words" \
  -i="IPA-standard"
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