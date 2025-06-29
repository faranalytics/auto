# Auto

Auto is an autonomous context window management implementation.

## Introduction

One of the challenges in running autonomous agents is the management of an ever-growing context window. This implementation gives the agent the capability to manage its context window autonomously. It provides tools for discretely deleting and updating messages.

This is an alternative approach to a more conventional function calling framework.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)

## Installation

```bash
pip install git+https://github.com/faranalytics/auto.git
```

## Usage

### Instructions

#### Create a `config.ini` file.

```ini
[DEFAULT]
OPENAI_API_KEY =
STORE_PATH = ./store
SYSTEM_MESSAGE_PATH = ./system_message.md
MODEL = gpt-4o-2024-08-06
MODEL_MAX_TOKEN_COUNT = 128000
DEFAULT_USER_MESSAGE_PATH = ./default_user_message.md
TEMPERATURE = 0
```

#### Run the script.

- Specify the location of the `config.ini` file.
- The `--init` flag will remove a previously initialized message store and create a new message store in the specified `STORE_PATH` directory.

```bash
python -m auto --config-path=./config.ini --init
```

Alternatively, if you omit the `--init` flag, you can run the script while retaining the conversation history in `STORE_PATH`.

```bash
python -m auto --config-path=./config.ini
```
