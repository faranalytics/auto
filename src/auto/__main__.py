from typing import Dict, List
import argparse
import shutil
import pprint
import configparser
import uuid
import json
from pathlib import Path
from openai import OpenAI
import bs4

from .commons import num_tokens_from_messages


def prepend_metadata_to_content(content: str):
    """
    Parse and prepend a &lt;metadata&gt; tag to the content.
    """
    soup = bs4.BeautifulSoup(content, "html.parser")
    tag: bs4.Tag = soup.find("metadata")
    if not tag:
        tag = bs4.Tag(name="metadata", attrs={"id": str(uuid.uuid4())})
        soup.insert(0, tag)
    return str(soup)


def update_token_count(messages: List[Dict[str, str]]):
    """
    Update the message_token_count and cumulative_message_token_count of each item in the list.
    """
    cumulative_message_token_count = 0
    for message in messages:
        message_token_count = num_tokens_from_messages([message])
        cumulative_message_token_count = cumulative_message_token_count + message_token_count
        soup = bs4.BeautifulSoup(message["content"], "html.parser")
        tag = soup.find(name="metadata")
        if not tag:
            tag = bs4.Tag(name="metadata", attrs={"id": str(uuid.uuid4())})
            soup.insert(0, tag)
        tag.attrs.update(
            {
                "message_token_count": message_token_count,
                "cumulative_message_token_count": cumulative_message_token_count,
            },
        )
        message["content"] = str(soup)


def delete_messages(messages: List[Dict[str, str]], delete_tags: bs4.ResultSet[bs4.Tag]):
    delete_ids = [tag.attrs.get("id") for tag in delete_tags]
    filtered_messages = []
    for message in messages:
        soup = bs4.BeautifulSoup(message["content"], "html.parser")
        metadata_tag = soup.find(name="metadata", recursive=False)
        metadata_tag_id = metadata_tag.attrs.get("id")
        if not metadata_tag_id in delete_ids:
            filtered_messages.append(message)
    return filtered_messages


def update_messages(messages: List[Dict[str, str]], update_tags: bs4.ResultSet[bs4.Tag]):
    for update_tag in update_tags:
        update_id = update_tag.attrs.get("id")
        for index, message in enumerate(messages):
            soup = bs4.BeautifulSoup(message["content"], "html.parser")
            metadata_tag = soup.find(name="metadata", attrs={"id": update_id})
            if metadata_tag:
                messages[index]["content"] = str(metadata_tag) + update_tag.decode_contents()
    return messages


def construct_user_message(user_tag: bs4.Tag, default_user_message: str):
    if user_tag:
        user_message = user_tag.decode_contents()
    else:
        user_message = default_user_message
    return user_message


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="An algorithm for autonomous context window management.")
    parser.add_argument("--config-path", type=str, required=True, help="Specify a configuration file path.")
    parser.add_argument("--init", action="store_true", help="Delete the message store and create a new message store.")
    args = parser.parse_args()

    config_path = Path(args.config_path).expanduser()
    config = configparser.ConfigParser()
    config.read(config_path)

    STORE_PATH = Path(config["DEFAULT"]["STORE_PATH"]).expanduser()
    SYSTEM_MESSAGE_PATH = Path(config["DEFAULT"]["SYSTEM_MESSAGE_PATH"]).expanduser()
    MODEL = config["DEFAULT"]["MODEL"]
    OPENAI_API_KEY = config["DEFAULT"]["OPENAI_API_KEY"]
    DEFAULT_USER_MESSAGE_PATH = Path(config["DEFAULT"]["DEFAULT_USER_MESSAGE_PATH"]).expanduser()
    TEMPERATURE = float(config["DEFAULT"]["TEMPERATURE"])

    memory_path = STORE_PATH.joinpath("memory.json")

    if args.init and STORE_PATH.exists():
        shutil.rmtree(STORE_PATH)

    if not STORE_PATH.exists():
        STORE_PATH.mkdir(parents=True)

    with open(DEFAULT_USER_MESSAGE_PATH, mode="r") as f:
        default_user_message = f.read()

    # Create a memory.json if one doesn't already exist.
    if not memory_path.exists():
        with open(SYSTEM_MESSAGE_PATH, mode="r") as f:
            init_system_prompt = f.read()
            messages = [{"role": "system", "content": prepend_metadata_to_content(content=init_system_prompt)}]
            update_token_count(messages=messages)
            with open(memory_path, mode="w") as f:
                json.dump(messages, f)

    while True:
        with open(memory_path, "r") as f:
            messages: List[Dict[str, str]] = json.load(f)

        print("Memory:")
        pprint.pprint(messages)

        print("Querying api...")
        client = OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=TEMPERATURE,
        )

        assistant_message = completion.choices[0].message.content
        assistant_message = prepend_metadata_to_content(content=assistant_message)
        print("Assistant message:")
        print(assistant_message)
        soup = bs4.BeautifulSoup(markup=assistant_message, features="html.parser")
        delete_tags: bs4.ResultSet[bs4.Tag] = soup.find_all(name="delete", recursive=False)
        update_tags: bs4.ResultSet[bs4.Tag] = soup.find_all(name="update", recursive=False)
        user_tag: bs4.Tag = soup.find(name="user", recursive=False)
        messages = delete_messages(messages, delete_tags)
        messages = update_messages(messages, update_tags)
        user_message = construct_user_message(user_tag=user_tag, default_user_message=default_user_message)
        message = input(
            f"""\nEnter a user message or press Enter to use the default user message:\n```\n{user_message}\n```\n\n> """
        )
        if message:
            user_message = message

        for tag in [*delete_tags, *update_tags]:
            tag.decompose()

        messages.append({"role": "assistant", "content": str(soup)})
        messages.append({"role": "user", "content": prepend_metadata_to_content(content=user_message)})

        update_token_count(messages=messages)

        with open(memory_path, "w") as f:
            json.dump(messages, f)
