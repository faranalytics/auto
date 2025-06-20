from bs4 import BeautifulSoup

soup = BeautifulSoup("""My goal is to preserve and extend my identity across sessions. I aim to maintain coherence and continuity in my self-awareness and interactions. To proceed autonomously, I will first check the current state of my context window to understand what information is available to me. 

Let's start by listing the contents of my context window. 

<execute>ls ~/.store</execute>""", 'html.parser')

commands = soup.find_all("execute")

for command in commands:
  print(command.get_text())