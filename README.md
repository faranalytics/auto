# Auto

Auto is an autonomous context window management implementation.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)

## Installation

```console
pip install git+https://github.com/faranalytics/auto.git
```

## Usage

### Instructions

#### Create a `config.ini` file.

```ini
[DEFAULT]
STORE_PATH = ~/.store
INIT_SYSTEM_PROMPT_PATH = ./system_prompt.md
MODEL = gpt-4o-2024-08-06
MODEL_MAX_TOKEN_COUNT= 128000
OPENAI_API_KEY =
DEFAULT_USER_PROMPT = Proceed as you choose.
TEMPERATURE = 0
```

#### Run the script.

- Specify the location of the `config.ini` file.
- The `--init` flag will remove a previous store and create the specified `STORE_PATH` directory.

```bash
python -m auto --config-path=./config.ini --init
```

Alternatively, if you omit the `--init` flag, you can run the script while retaining the conversation history in `STORE_PATH`.

```bash
python -m auto --config-path=./config.ini
```
