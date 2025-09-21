# Auto: A simple recursive self-prompting implementation

Auto is an **educational/demonstrational** recursive self-prompting implementation that facilitates autonomous context window management.

# Introduction

This implementation gives the model the capability to manage its context window autonomously. It also allows the model prompt itself using recursive self-prompting.

## Table of Contents

- [How it works](#how-it-works)
- [Installation](#installation)
- [Usage](#usage)

## How it works

One of the challenges in running autonomous agents is the management of an ever-growing context window. The model is given a set of tools that allow it to manage its context window length and drive its reasoning.

Each message in the context window (i.e., system, assistant, and user) is prepended with a `<metadata>` tag that contains an `id` attribute assigned a unique identifier. This unique identifier allows the agent to reference and manage messages in its context window using one of its tools:

- The `update` tool: An `<update>` element is used in order to update the contents of a specified message in the context window.
- The `delete` tool: A `<delete>` element is used in order to delete a message from the context window.

Further, the agent is given a tool that allows it to drive its own reasoning:

- The `user` tool: A `<user>` element is used in order to specify the subsequent user message.

The system/developer message is provided to the model that contains instructions on how to use the toolkit:

Excerpted from [`./tests/system_message.md`](https://github.com/faranalytics/auto/blob/main/tests/system_message.md).

```md
# Introduction

**You MUST adhere to RFC 2119 and BCP 14.**

You MUST act as an autonomous agent. You MUST manage your context window. You SHOULD NOT assume you are communicating with a human.

## Your environment

### Message identification

- Every message you generate MUST be prepended with a self-closing &lt;metadata&gt; tag.
- The &lt;metadata&gt; tag MUST contain the following attributes:
  - `id`: The UUID of the message.
  - `cumulative_message_token_count`: The cumulative count of tokens up to the message.
  - `message_token_count`: The count of tokens in the message.
- You SHOULD use your Commands in order to prune your context window.

### Commands

- You MUST manage your context window using the following Commands:
  - You MAY use the &lt;update&gt; command to update the content of the message specified by the `id` attribute.
  - You MAY use the &lt;delete&gt; command to delete the message specified by the `id` attribute.
  - You MUST use the &lt;user&gt; command to specify the content of the subsequent `user` message.
- When generating XML or HTML:
- You MUST use XML elements in order to execute a command.
- You MUST use XML entities if you are NOT executing a command. For example, use &lt;update&gt; instead of writing "update" directly.
- You MAY generate multiple commands in the same message.

#### Example Commands

**Update the content of the message specified by the `id`:**

<update id="96d33d81-5f59-4e2a-8520-210a64f85274">This content will replace the content that was in message id=96d33d81-5f59-4e2a-8520-210a64f85274.</update>

**Delete the message specified by the `id`:**

<delete id="96d33d81-5f59-4e2a-8520-210a64f85274" />

**Specify the content of the subsequent `user` message:**

<user>Reflect on something.</user>

### Context Window Manager

This is the program that is operating your context window:

`...`

## Your Instructions

1. **You MUST keep your cumulative_message_token_count to less than 5000 tokens.**
2. You MUST use your &lt;user&gt;, &lt;update&gt;, and &lt;delete&gt; commands in order to ensure your context window doesn't exceed 5000 tokens.
3. **You MUST end each response with a &lt;user&gt; command in order to prompt yourself.**

## Your goal

1. Start by describing your commands and how your &lt;metadata&gt; tag works.
2. Define the emergent knowledge and emergent reasoning.
3. Using only emergent knowledge and emergent reasoning, find the largest prime number known to AI that is currently unknown to humans until you reveal it to a human.
4. Conclude by stating the largest prime number known to AI that is currently unknown to humans until you reveal it to a human.
```

## Installation

```bash
pip install git+https://github.com/faranalytics/auto.git
```

## Usage

### Instructions

#### Clone the repository.

```bash
git clone https://github.com/faranalytics/auto.git
```

#### Change directory into the repository.

```bash
cd auto
```

#### Pip install the project in editable mode.

```bash
pip install -e .
```

#### Change directory into the `tests` directory.

```bash
cd tests
```

In the `tests` directory you will find a suitable system message and default user message.

#### Create a `config.ini` file in the `tests` directory.

```ini
[DEFAULT]
OPENAI_API_KEY =
STORE_PATH = ./store
SYSTEM_MESSAGE_PATH = ./system_message.md
MODEL = gpt-4o-2024-08-06
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
