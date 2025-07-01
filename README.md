# Auto

Auto is an autonomous context window management implementation.

## Introduction

One of the challenges in running autonomous agents is the management of an ever-growing context window. This implementation gives the agent the capability to manage its context window autonomously. It provides tools for discretely deleting and updating messages.

This is an alternative approach to pruning that could be accomplished using a more conventional function calling framework.

Each message in the context window is prepended with a `<metadata>` element that contains an unique `id` attribute. The `id` of the `<metadata>` element allows the agent to reference each message in its context window.  

The agent is provided with a toolkit in its system/developer message that can be used in order to prune its context window and prompt itself:

```md
### Context window management

- Every message you generate MUST be prepended with a self-closing &lt;metadata&gt; tag.
- The &lt;metadata&gt; tag MUST contain the following attributes:
  - `id`: The UUID of the message.
  - `cumulative_message_token_count`: The cumulative count of tokens up to the message.
  - `message_token_count`: The count of tokens in the message.
- You MUST manage your context window using the following Commands:
  - You MAY use the &lt;update&gt; command to update the content of the message specified by the `id` attribute.
  - You MAY use the &lt;delete&gt; command to delete the message specified by the `id` attribute.
  - You MUST use the &lt;user&gt; command to specify the content of the subsequent `user` message.
-  When generating XML or HTML:
  - You MUST use XML elements in order to execute a command.
  - You MUST use XML entities if you are NOT executing a command.  For example, use &lt;update&gt; instead of writing "update" directly.


### Example Commands

**Update the content of the message specified by the `id`:**

<update id="96d33d81-5f59-4e2a-8520-210a64f85274">This content will replace the content that was in message id=96d33d81-5f59-4e2a-8520-210a64f85274.</update>

**Delete the message specified by the `id`:**

<delete id="96d33d81-5f59-4e2a-8520-210a64f85274" />

**Specify the content of the subsequent `user` message:**

<user>Reflect on something.</user>
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
