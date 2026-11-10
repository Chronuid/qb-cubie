"""Start the standalone JSONL reviewer with an explicit runtime JSON configuration."""

import argparse

from ollama_agents.reviewer.process import main

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    raise SystemExit(main(parser.parse_args().config))
