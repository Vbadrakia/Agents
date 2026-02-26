import json
import os

MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"jobs": [], "news": []}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def is_duplicate(category, item):
    memory = load_memory()
    if item in memory[category]:
        return True
    memory[category].append(item)
    save_memory(memory)
    return False
