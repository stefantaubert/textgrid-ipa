# textgrid-utils

[![PyPI](https://img.shields.io/pypi/v/textgrid-utils.svg)](https://pypi.python.org/pypi/textgrid-utils)
[![PyPI](https://img.shields.io/pypi/pyversions/textgrid-utils.svg)](https://pypi.python.org/pypi/textgrid-utils)
[![MIT](https://img.shields.io/github/license/stefantaubert/textgrid-ipa.svg)](https://github.com/stefantaubert/textgrid-ipa/blob/main/LICENSE)

CLI to modify TextGrids and their corresponding audio files.

## Usage

Currently there is only linux supported.
Download the [latest release](https://github.com/stefantaubert/textgrid-ipa/releases):

```sh
wget "https://github.com/stefantaubert/textgrid-ipa/releases/latest/download/textgrid-tools-linux.zip" -N
```

Unpack it and navigate into directory:

```sh
unzip -o textgrid-tools-linux.zip -d textgrid-tools
cd textgrid-tools
```

Use it:

```sh
./textgrid-tools
```

### Commands

```txt
convert-text-to-grid                convert text files to grid files
convert-grid-to-text                convert grid files to text files
create-dict-from-grids              create pronunciation dictionary from multiple grid files
join-tier-intervals                 join tier intervals together
map-words-to-tier                   map words from one grid file to a tier in another grid file
map-arpa-tier-to-ipa                map a tier with ARPA transcriptions to IPA
remove-tiers                        remove tiers
remove-symbols-from-tiers           remove symbols from tiers
remove-intervals                    remove intervals on all tiers
rename-tier                         rename a tier
clone-tier                          clone a tier
move-tier                           move a tier to another position in the grid
transcribe-words-to-arpa            transcribe a tier containing words with help of a pronunciation dictionary to ARPA
split-grid                          split a grid file on intervals into multiple grid files (incl. audio files)
convert-text-to-symbols             convert text string format to symbol string format
fix-boundaries                      align boundaries of tiers according to a reference tier
sync-grid-to-audio                  synchronize grid minTime and maxTime according to the corresponding audio file
normalize-tiers                     normalize text of tiers
print-stats                         print statistics
```

## Troubleshooting

If recordings/audio files are not in `.wav` format they need to be converted:

```sh
sudo apt-get install ffmpeg -y
# e.g., mp3 to wav conversion
ffmpeg -i *.mp3 -acodec pcm_s16le *.wav
```

If error `ImportError: libffi.so.7: cannot open shared object file: No such file or directory` occurs, do ...

## Development

Checkout this repository:

```sh
git clone https://github.com/stefantaubert/textgrid-ipa
cd textgrid-ipa
# install `pipenv`
pip install --user pipenv --python 3.8
# install environment for this repository
pipenv install --dev
```

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
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.lintOnSave": true,
  "python.linting.flake8Enabled": false,
  "python.linting.pycodestyleEnabled": false,
  "python.linting.banditEnabled": false,
  "python.linting.mypyEnabled": false,
  "python.languageServer": "Pylance",
  "editor.formatOnSave": true,
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.autoSearchPaths": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "python.testing.autoTestDiscoverOnSaveEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.nosetestsEnabled": false,
  "python.testing.pytestEnabled": true,
}
```

### Add to another project

In the destination project run:

```sh
# if not already done:
pip install --user pipenv --python 3.8
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

### Deploy

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
  
# copy to local apps folder
mkdir -p /home/mi/apps/textgrid-tools
cp dist/* -r /home/mi/apps/textgrid-tools

# zip files
cd dist
zip textgrid-tools-linux.zip ./ -r
cd ..

# libffi.so is located at "/usr/lib/x86_64-linux-gnu/libffi.so.7"
# if not included this error occurs:
## ...
## File "/usr/lib/python3.8/ctypes/__init__.py", line 7, in <module>
## ImportError: libffi.so.7: cannot open shared object file: No such file or directory

# check filesizes
cd dist
du -h | sort -rh

# unzip
unzip textgrid-tools-linux.zip -d target_folder
```

```sh
# Convert audio files to wav
sudo apt-get install ffmpeg -y
ffmpeg -i *.mp3 -acodec pcm_s16le -ar 22050 *.wav
```
