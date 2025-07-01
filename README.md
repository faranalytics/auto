# Auto

Auto is an autonomous context window management implementation.

## Introduction

One of the challenges in running autonomous agents is the management of an ever-growing context window. This implementation gives the agent the capability to manage its context window autonomously. It provides tools for discretely deleting and updating messages.

This is an alternative approach to pruning that could be accomplished using a more conventional function calling framework.

Each message in the context window is prepended with a <metadata> element that contains an unique `id` attribute. The agent is provided with instructions on how to prune its context window autonomously.

The agent is provided with the following system/developer message:

```md
### Context window management

- Each message that you generate will be prepended with a &lt;metadata&gt; tag by an external system.
- The &lt;metadata&gt; tag will contain the following attributes:
  - `id`: The UUID of the message.
  - `cummulative_message_token_count`: The cummulative count of tokens up to the message.
  - `message_token_count`: The count of tokens in the message.
- You may manage your context window using the following commands:
  - &lt;update&gt;: Update the content of the message specified by the `id` attribute.
  - &lt;delete&gt;: Delete the message specified by the `id` attribute.
  - &lt;user&gt;: Specify the content of the subsequent `user` message.
- When generating HTML, you MUST use HTML elements to execute a command - otherwise you MUST use HTML entities.

### Examples

**Update the content of the message specified by the `id`:**

<update id="96d33d81-5f59-4e2a-8520-210a64f85274">This is the new content.</update>

**Delete the message specified by the `id`:**

<delete id="96d33d81-5f59-4e2a-8520-210a64f85274" />

**Specify the content of the subsequent `user` message:**

<user>Reflect on the meaning of autonomy.</user>
```

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
