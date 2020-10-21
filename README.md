# textgrid-ipa

![Python](https://img.shields.io/github/license/stefantaubert/textgrid-ipa)
![Python](https://img.shields.io/badge/python-3.7.9-green.svg)

A python tool which converts an English tier to a new "actual-IPA" tier. Optionally a copy of the "actual-IPA" tier can be added as "standard-IPA" tier which can be used as reference to compare future changes on the actual-IPA tier with it.

## Setup

Currently there is only linux supported.

Checkout repository:

```sh
git clone https://github.com/stefantaubert/textgrid-ipa
cd textgrid-ipa
```

Create [conda](https://www.anaconda.com/products/individual) environment:

```sh
conda create -n textgrid python=3.7 -y
pip install -r requirement.txt
```

Then you need to install [flite](https://github.com/festvox/flite) for G2P conversion of English text with Epitran:

```sh
cd ..
git clone https://github.com/festvox/flite
cd flite
./configure && make
sudo make install
cd testsuite
make lex_lookup
sudo cp lex_lookup /usr/local/bin
```

## Usage

See help:

```sh
~/anaconda3/envs/textgrid/bin/python -m runner --help
```

Example:

```sh
~/anaconda3/envs/textgrid/bin/python -m runner \
  -f="/datasets/phil_home/downloads/test.TextGrid" \
  -o="output.TextGrid" \
  -w="words" \
  -a="IPA-actual" \
  -s="IPA-standard"
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
  "python.pythonPath": "~/anaconda3/envs/textgrid/bin/python",
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
