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

def generate_uuid():
    return str(uuid.uuid4())

def prepend_metadata(content: str, id: str = None):
    metadata = bs4.Tag(name="metadata")
    metadata.attrs.update({"id": id if id else generate_uuid()})
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
TEMPERATURE = float(config["DEFAULT"]["TEMPERATURE"])

memory_path = STORE_PATH.joinpath("memory.json")
transcript_path = STORE_PATH.joinpath("transcript.log")

if args.init and STORE_PATH.exists():
    shutil.rmtree(STORE_PATH)

if not STORE_PATH.exists():
    STORE_PATH.mkdir(parents=True)

if not memory_path.exists():
    with open(INIT_SYSTEM_PROMPT_PATH, mode="r") as f:
        init_system_prompt = f.read()
        memory = [
            {"role": "system", "content": prepend_metadata(content=init_system_prompt)}
        ]
        with open(memory_path, mode="w") as f:
            json.dump(memory, f)

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

    autonomy_soup = bs4.BeautifulSoup(content, "html.parser").find(name="autonomy")
    if autonomy_soup:
      for update in autonomy_soup.find_all(name="update"):
          update_id = update.attrs.get("id")
          for index, message in enumerate(messages):
              soup = bs4.BeautifulSoup(message["content"], "html.parser")
              tag = soup.find(name="metadata", attrs={"id": update_id})
              if tag:
                  messages[index]["content"] = str(tag) + update.get_text().strip()

      for delete in autonomy_soup.find_all(name="delete"):
          delete_id = delete.attrs.get("id")
          messages = [m for m in messages if not bs4.BeautifulSoup(m["content"], "html.parser").find(name="metadata", attrs={"id": delete_id})]

      for execute in autonomy_soup.find_all(name="execute"):
          command = execute.get_text().strip()
          try:
              output = subprocess.check_output(command, shell=True, text=True)
          except subprocess.CalledProcessError as e:
              output = f"Error: {e}"
          messages.append({"role": "system", "content": prepend_metadata(f"Executed: {command}\nOutput:\n{output}")})

      user_override = None
      user_tag = autonomy_soup.find(name="user", recursive=False)
      if user_tag:
          user_override = user_tag.get_text().strip()

      messages.append({"role": "assistant", "content": content})
    else:
        user_override = None

    if user_override:
        user_prompt = user_override
        print(f"User prompt overridden by assistant: {user_prompt}")
        input("Press Enter to continue.")
    else:
        user_prompt = input(f"Enter a user message or press Enter to use the default user message: \"{DEFAULT_USER_PROMPT}\"\n> ")
        if not user_prompt:
            user_prompt = DEFAULT_USER_PROMPT

    messages.append({"role": "user", "content": prepend_metadata(content=user_prompt)})

    with open(memory_path, "w") as f:
        json.dump(messages, f)

    with open(transcript_path, "a") as f:
        f.write(f"{content}\n\n")
