import argparse
from pathlib import Path
import os
from openai import OpenAI
import time
from bs4 import BeautifulSoup
import subprocess
import shutil
import pprint
import configparser
import re
from .num_tokens_from_messages import num_tokens_from_messages

parser = argparse.ArgumentParser(description="Auto")
parser.add_argument("--config-path", type=str, required=True, help="Specify a configuration file path.")
parser.add_argument("--init", action="store_true")
args = parser.parse_args()

config_path = Path(args.config_path).expanduser()

config = configparser.ConfigParser()
config.read(config_path)

store_path = Path(config["DEFAULT"]["STORE_PATH"]).expanduser()
init_system_prompt_path = Path(config["DEFAULT"]["INIT_SYSTEM_PROMPT_PATH"])
model = config["DEFAULT"]["MODEL"]
model_max_token_count = int(config["DEFAULT"]["MODEL_MAX_TOKEN_COUNT"])

if args.init and store_path.exists():
    shutil.rmtree(store_path)

if not store_path.exists():
    store_path.mkdir(parents=True)

system_prompt_path = store_path.joinpath("timestamp=0,role=system")

if not system_prompt_path.exists():
    with open(init_system_prompt_path, mode="r") as f:
        init_system_prompt = f.read()
        with open(store_path.joinpath("timestamp=0,role=system"), mode="w") as f:
            f.write(init_system_prompt)

HISTORY_PATTERN = re.compile(r"^timestamp=[\d.]+,role=(?:user|assistant)$", re.IGNORECASE)
while True:

    with open(store_path.joinpath("timestamp=0,role=system"), "r") as f:
        system_prompt = f.read()

    messages = []
    for file in store_path.rglob("*"):
        if HISTORY_PATTERN.search(file.name):
            message = {tup[0]: tup[1] for tup in [field.split("=") for field in file.stem.split(",")]}
            with open(file, "r") as f:
                message["content"] = f.read()
                messages.append(message)

    if len(messages) != 0:
      messages.sort(key=lambda x: int(x["timestamp"]))
      messages = [{k: v for k, v in message.items() if k in ["role", "content"]} for message in messages]
      token_count = num_tokens_from_messages(
          messages=[{"role": "system", "content": system_prompt}], model=model
      )
      if token_count > model_max_token_count:
          raise Exception("The system prompt exceeds the model's maximum token count.")
      messages = messages[::-1]
      for index, message in enumerate(messages):
        token_count = token_count + num_tokens_from_messages(messages=[message], model=model)
        if token_count > model_max_token_count:
            messages = messages[:index]
            break
      messages = messages[::-1]
      messages.insert(0, {"role": "system", "content": system_prompt})
    else:
        messages = [{"role": "system", "content": system_prompt}]

    pprint.pprint(messages)
    print(len(messages))
    print("Querying API")
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    completion = client.chat.completions.create(model=model, messages=messages, temperature=0)
    content = completion.choices[0].message.content

    print("Content:\n", content)

    with open(store_path.joinpath(f"timestamp={time.time_ns()},role=assistant"), mode="w") as f:
        f.write(content)

    soup = BeautifulSoup(content, "html.parser")
    executes = soup.find_all("execute")

    if len(executes) == 0:
        input("Press Enter to continue.")

    for execute in executes:
        expression = execute.get_text()
        print("Expression: ", expression)
        input("Press Enter to continue.")
        result = subprocess.run(expression, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            output = f"<stdout>{str(result.stdout)}</stdout>"
        else:
            output = f"<stderr>{str(result.stderr)}</stderr>"
        print("Output: ", output)
        with open(store_path.joinpath(f"timestamp={time.time_ns()},role=user"), mode="w") as f:
            f.write(output)

    with open(store_path.joinpath(f"timestamp={time.time_ns()},role=user"), mode="w") as f:
        f.write("Please proceed autonomously.")
