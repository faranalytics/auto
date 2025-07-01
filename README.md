# Auto

Auto is an autonomous context window management implementation.

## Introduction

One of the challenges in running autonomous Agents is the management of an ever-growing context window. This implementation gives the Agent the capability to manage its context window autonomously. 

Each message in the context window (i.e., system, assistant, and user) are prepended with a `<metadata>` tag that contains an `id` attribute assigned to a unique identifier.  This unique identifier allows the Agent to reference messages in its context window using one of its tools:

- The `update` tool: An `<update>` element is used in order to update the contents of a specified message.
- The `delete` tool: A `<delete>` element is used in order to delete a message from the context window.

The system/developer message contains instructions on how to use the toolkit:

```md
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
```
