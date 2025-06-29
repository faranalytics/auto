import argparse
from pathlib import Path
import os
from typing import Any, Dict, List
from openai import OpenAI
import time
import bs4
import subprocess
import shutil
import pprint
import configparser
import uuid
from html import escape
import json
from .commons import num_tokens_from_messages
import re


def prepend_metadata(content: str, _id: str = None):
    metadata = bs4.Tag(name="metadata")
    metadata.attrs.update({"id": _id if _id else str(uuid.uuid4())})
    return str(metadata) + content


def update_token_count(messages: List[Dict[str, str]]):
    cummulative_message_token_count = 0
    for message in messages:
        message_token_count = num_tokens_from_messages([message])
        cummulative_message_token_count = cummulative_message_token_count + message_token_count
        soup = bs4.BeautifulSoup(message["content"], "html.parser")
        tag = soup.find(name="metadata")
        tag.attrs.update(
            {
                "message_token_count": message_token_count,
                "cummulative_message_token_count": cummulative_message_token_count,
            },
        )
        message["content"] = re.sub(
            pattern=r"<metadata.*?</metadata>",
            repl=str(tag),
            string=message["content"],
            count=1,
        )


parser = argparse.ArgumentParser(description="An algorithm for autonomous context window management.")
parser.add_argument("--config-path", type=str, required=True, help="Specify a configuration file path.")
parser.add_argument("--init", action="store_true")
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

if not memory_path.exists():
    with open(SYSTEM_MESSAGE_PATH, mode="r") as f:
        init_system_prompt = f.read()
        messages = [{"role": "system", "content": prepend_metadata(content=init_system_prompt)}]
        update_token_count(messages=messages)
        with open(memory_path, mode="w") as f:
            json.dump(messages, f)

while True:
    with open(memory_path, "r") as f:
        messages: List[Dict[str, str]] = json.load(f)

    print("\nBegin Memory\n")
    pprint.pprint(messages)
    print("\nEnd Memory")

    print("Querying API\n")
    client = OpenAI(api_key=OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
    )

    assistant_message = completion.choices[0].message.content
    print("\nBegin Content")
    print(assistant_message)
    print("End Content\n")
    messages.append({"role": "assistant", "content": prepend_metadata(content=assistant_message)})
    user_message = None
    auto_tag = bs4.BeautifulSoup(assistant_message, "html.parser").find(name="auto")
    if auto_tag:
        for update in auto_tag.find_all(name="update"):
            update_id = update.attrs.get("id")
            for index, message in enumerate(messages):
                soup = bs4.BeautifulSoup(message["content"], "html.parser")
                tag = soup.find(name="metadata", attrs={"id": update_id})
                if tag:
                    messages[index]["content"] = str(tag) + update.get_text().strip()

        for delete in auto_tag.find_all(name="delete"):
            delete_id = delete.attrs.get("id")
            for index, message in enumerate(messages):
                soup = bs4.BeautifulSoup(message["content"], "html.parser")
                tag = soup.find(name="metadata", attrs={"id": delete_id})
                if tag:
                    del messages[index]
                    break

        # for execute in auto_soup.find_all(name="execute"):
        #     command = execute.get_text().strip()
        #     try:
        #         output = subprocess.check_output(command, shell=True, text=True)
        #     except subprocess.CalledProcessError as e:
        #         output = f"Error: {e}"
        #     messages.append({"role": "system", "content": prepend_metadata(f"Executed: {command}\nOutput:\n{output}")})

        tag = auto_tag.find(name="user", recursive=False)
        if tag:
            user_message = tag.get_text().strip()
    if user_message:
        user_message = default_user_message + "\n" + user_message
    else:
        user_message = default_user_message

    message = input(
        f"""Enter a user message or press Enter to use the default user message:\n```\n{user_message}\n```\n\n> """
    )
    if message:
        user_message = message

    messages.append({"role": "user", "content": prepend_metadata(content=user_message)})
    update_token_count(messages=messages)

    with open(memory_path, "w") as f:
        json.dump(messages, f)
