import argparse
from pathlib import Path
import os
from openai import OpenAI
import time
from bs4 import BeautifulSoup
import subprocess
import shutil
import pprint

parser = argparse.ArgumentParser(description="Auto")
parser.add_argument("--store-path", type=str, help="Specify a conversation history store.")
parser.add_argument("--system-prompt-path", type=str, help="Specify a path to the system prompt.")
args = parser.parse_args()
if args.store_path is None:
    print("""Specify a path to the conversation history store with `--store-path="<the-store-path>"`.""")
    exit()

store_path = Path(args.store_path).expanduser()

if store_path.exists():
    shutil.rmtree(store_path)


if not store_path.exists():
    store_path.mkdir(parents=True)

if not args.system_prompt_path is None:
    system_prompt_path = Path(args.system_prompt_path)
    with open(system_prompt_path, mode="r") as f:
        system_prompt = f.read()
        with open(store_path.joinpath("timestamp=0-role=system"), mode="w") as f:
            f.write(system_prompt)

while True:

    files = list(store_path.rglob("*"))
    messages = []
    for file in files:
        message = {tup[0]: tup[1] for tup in [field.split("=") for field in file.stem.split("-")]}
        with open(file, "r") as f:
            data = f.read()
            message["content"] = data
            messages.append(message)

    messages.sort(key=lambda x: int(x["timestamp"]))

    messages = [{k: v for k, v in message.items() if k in ["role", "content"]} for message in messages]

    pprint.pprint(messages)

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    completion = client.chat.completions.create(model="gpt-4o-2024-08-06", messages=messages, temperature=0)

    content = completion.choices[0].message.content

    print("Content: ", content)

    with open(store_path.joinpath(f"timestamp={time.time_ns()}-role=assistant"), mode="w") as f:
        f.write(content)

    soup = BeautifulSoup(content, "html.parser")

    executes = soup.find_all("execute")

    if len(executes) == 0:
        break

    for execute in executes:
        expression = execute.get_text()
        print("Expression: ", expression)
        input()
        result = subprocess.run(expression, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            output = f"<stdout>{str(result.stdout)}</stdout>"
        else:
            output = f"<stderr>{str(result.stderr)}</stderr>"
        print("Output: ", output)
        with open(store_path.joinpath(f"timestamp={time.time_ns()}-role=user"), mode="w") as f:
            f.write(output)

    with open(store_path.joinpath(f"timestamp={time.time_ns()}-role=user"), mode="w") as f:
        f.write("Please proceed autonomously.")
