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
USER_PROMPT = config["DEFAULT"]["USER_PROMPT"]

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
        context_window: List[Dict[str, str]] = json.load(f)

    print("\nBegin Memory\n")
    print(context_window)
    print("\nEnd Memory\n")
    input("Press Enter to continue.")

    print("\nQuerying API\n")
    client = OpenAI(api_key=OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model=MODEL,
        messages=context_window,
        temperature=0,
    )
    content = completion.choices[0].message.content

    print("\nBegin Content\n")
    print(content)
    print("\nEnd Content\n")
    input("Press Enter to continue.")

    content_soup = bs4.BeautifulSoup(content, "html.parser")
    updates: bs4.ResultSet[bs4.Tag] = content_soup.find_all(name="update")
    for update in updates:
        print("Update: ", update)
        update_string = update.get_text().strip()
        update_id = update.attrs.get("id")
        input("Press Enter to continue.")
    context_window.append({"role": "assistant", "content": prepend_metadata(content=content)})
    context_window.append({"role": "user", "content": prepend_metadata(content=USER_PROMPT)})
    with open(memory_path, "w") as f:
        json.dump(context_window, f)
    input("Press Enter to continue.")
