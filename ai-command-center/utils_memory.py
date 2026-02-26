"""
utils_memory.py - Simple memory utility for duplicate detection.
Stores seen items in memory.json to avoid showing the same news/data twice.
"""

import json
import os
from datetime import datetime, timedelta

MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")


def _load_memory():
    """Load memory from JSON file."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"news": [], "stocks": [], "last_cleanup": None}


def _save_memory(memory):
    """Save memory to JSON file."""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2, default=str)
    except IOError as e:
        print(f"Error saving memory: {e}")


def is_duplicate(category, identifier):
    """
    Check if an item has been seen before.
    Returns True if duplicate, False if new (and records it).
    """
    memory = _load_memory()

    if category not in memory:
        memory[category] = []

    # Check if already seen
    if identifier in memory[category]:
        return True

    # Record as seen
    memory[category].append(identifier)

    # Keep only last 500 items per category to avoid bloating
    memory[category] = memory[category][-500:]

    # Cleanup old data periodically
    today = datetime.now().strftime("%Y-%m-%d")
    if memory.get("last_cleanup") != today:
        memory["last_cleanup"] = today
        # Keep only recent entries
        for cat in memory:
            if isinstance(memory[cat], list) and cat != "last_cleanup":
                memory[cat] = memory[cat][-200:]

    _save_memory(memory)
    return False
