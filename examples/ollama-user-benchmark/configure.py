"""Run with the Python interpreter from the environment containing Cubie."""
from pathlib import Path
import json
import sys

path = Path(__file__).with_name('agent.toml')
text = path.read_text()
lines = [f'command = [{json.dumps(sys.executable)}, "-I", "agent.py"]'
         if line.startswith('command =') else line for line in text.splitlines()]
path.write_text('\n'.join(lines) + '\n')
print(path)
