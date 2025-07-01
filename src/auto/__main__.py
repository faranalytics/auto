import argparse
from pathlib import Path
import os
from typing import Any, Dict, List
from openai import OpenAI
import bs4
import shutil
import pprint
import configparser
import uuid
from html import escape
import json
from .commons import num_tokens_from_messages


def prepend_metadata_to_content(content: str):
    """
    Parse and prepend a <metadata> tag to the content.
    """
    soup = bs4.BeautifulSoup(content, "html.parser")
    tag: bs4.ResultSet[bs4.Tag] = soup.find("metadata")
    if not tag:  
      tag = bs4.Tag(name="metadata", attrs={"id": uuid.uuid4()})
      soup.insert(0, tag)
    return str(soup)


def update_token_count(messages: List[Dict[str, str]]):
    """
    Update the message_token_count and cummulative_message_token_count of each item in the list.
    """
    cummulative_message_token_count = 0
    for message in messages:
        message_token_count = num_tokens_from_messages([message])
        cummulative_message_token_count = cummulative_message_token_count + message_token_count
        soup = bs4.BeautifulSoup(message["content"], "html.parser")
        tag = soup.find(name="metadata")
        if not tag:
            tag = bs4.Tag(name="metadata", attrs={"id": uuid.uuid4()})
            soup.insert(0, tag)
        tag.attrs.update(
            {
                "message_token_count": message_token_count,
                "cummulative_message_token_count": cummulative_message_token_count,
            },
        )
        message["content"] = str(soup)


parser = argparse.ArgumentParser(description="An algorithm for autonomous context window management.")
parser.add_argument("--config-path", type=str, required=True, help="Specify a configuration file path.")
parser.add_argument("--init", action="store_true", help="Delete the message store and create a new message store.")
args = parser.parse_args()

config_path = Path(args.config_path).expanduser()
config = configparser.ConfigParser()
config.read(config_path)

STORE_PATH = Path(config["DEFAULT"]["STORE_PATH"]).expanduser()
SYSTEM_MESSAGE_PATH = Path(config["DEFAULT"]["SYSTEM_MESSAGE_PATH"])
MODEL = config["DEFAULT"]["MODEL"]
MODEL_MAX_TOKEN_COUNT = int(config["DEFAULT"]["MODEL_MAX_TOKEN_COUNT"])
OPENAI_API_KEY = config["DEFAULT"]["OPENAI_API_KEY"]
DEFAULT_USER_MESSAGE_PATH = config["DEFAULT"]["DEFAULT_USER_MESSAGE_PATH"]
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

    user_message = None
    soup = bs4.BeautifulSoup(assistant_message, "html.parser")
    tags: bs4.ResultSet[bs4.Tag] = soup.find_all(name="update", recursive=False)
    for update in tags:
        update_id = update.attrs.get("id")
        for index, message in enumerate(messages):
            soup = bs4.BeautifulSoup(message["content"], "html.parser")
            tag = soup.find(name="metadata", attrs={"id": update_id})
            if tag:
                messages[index]["content"] = str(tag) + update.get_text().strip()

    tags: bs4.ResultSet[bs4.Tag] = soup.find_all(name="delete", recursive=False)
    for delete in tags:
        delete_id = delete.attrs.get("id")
        for index, message in enumerate(messages):
            soup = bs4.BeautifulSoup(message["content"], "html.parser")
            tag = soup.find(name="metadata", attrs={"id": delete_id})
            if tag:
                del messages[index]
                break

    tag = soup.find(name="user", recursive=False)
    if tag:
        user_message = tag.get_text().strip()
    else:
        user_message = default_user_message

    message = input(
        f"""Enter a user message or press Enter to use the default user message:\n```\n{user_message}\n```\n\n> """
    )
    if message:
        user_message = message
    
    messages.append({"role": "assistant", "content": str(soup)})
    messages.append({"role": "user", "content": prepend_metadata_to_content(content=user_message)})

    update_token_count(messages=messages)

    with open(memory_path, "w") as f:
        json.dump(messages, f)
