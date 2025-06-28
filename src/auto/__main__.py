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


def prepend_metadata(content: str):
    metadata = bs4.Tag(name="metadata")
    metadata.attrs.update({"id": uuid.uuid4()})
    return str(metadata) + content


parser = argparse.ArgumentParser(description="An algorithm for autonomous context window management.")
parser.add_argument("--config-path", type=str, required=True, help="Specify a configuration file path.")
parser.add_argument("--init", action="store_true")
args = parser.parse_args()

config_path = Path(args.config_path).expanduser()

config = configparser.ConfigParser()
config.read(config_path)

STORE_PATH = Path(config["DEFAULT"]["STORE_PATH"]).expanduser()
INIT_SYSTEM_PROMPT_PATH = Path(config["DEFAULT"]["INIT_SYSTEM_PROMPT_PATH"])
MODEL = config["DEFAULT"]["MODEL"]
MODEL_MAX_TOKEN_COUNT = int(config["DEFAULT"]["MODEL_MAX_TOKEN_COUNT"])
OPENAI_API_KEY = config["DEFAULT"]["OPENAI_API_KEY"]
DEFAULT_USER_PROMPT = config["DEFAULT"]["DEFAULT_USER_PROMPT"]
TEMPERATURE = config["DEFAULT"]["TEMPERATURE"]

memory_path = STORE_PATH.joinpath("memory.json")
transcript_path = STORE_PATH.joinpath("transcript.log")

if args.init and STORE_PATH.exists():
    shutil.rmtree(STORE_PATH)

if not STORE_PATH.exists():
    STORE_PATH.mkdir(parents=True)

# Initialize system prompt if not present
if not memory_path.exists():
    with open(INIT_SYSTEM_PROMPT_PATH, mode="r") as f:
        init_system_prompt = f.read()
        memory = json.dumps(
            [
                {
                    "role": "system",
                    "content": prepend_metadata(content=init_system_prompt),
                },
            ]
        )
        with open(memory_path, mode="w") as f:
            f.write(memory)

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
    content = completion.choices[0].message.content

    print("\nBegin Content")
    print(content)
    print("End Content\n")

    content_soup = bs4.BeautifulSoup(content, "html.parser")
    updates: bs4.ResultSet[bs4.Tag] = content_soup.find_all(name="update")
    for update in updates:
        update_string = update.get_text().strip()
        update_id = update.attrs.get("id")
        for index, message in enumerate(messages):
            soup = bs4.BeautifulSoup(message["content"], "html.parser")
            tag = soup.find(name="metadata", attrs={"id": update_id})
            if tag:
                messages[index]["content"] = str(tag) + update_string
    deletes: bs4.ResultSet[bs4.Tag] = content_soup.find_all(name="delete")
    for delete in deletes:
        delete_id = delete.attrs.get("id")
        for index, message in enumerate(messages):
            soup = bs4.BeautifulSoup(message["content"], "html.parser")
            tag = soup.find(name="metadata", attrs={"id": delete_id})
            if tag:
                del messages[index]
    messages.append({"role": "assistant", "content": content})
    user_prompt = input(f"""Enter a user message or press Enter to use the default user message: "{DEFAULT_USER_PROMPT}"\n> """)
    if user_prompt == "":
        messages.append({"role": "user", "content": prepend_metadata(content=DEFAULT_USER_PROMPT)})
    else:
        messages.append({"role": "user", "content": prepend_metadata(content=user_prompt)})
    with open(memory_path, "w") as f:
        json.dump(messages, f)
