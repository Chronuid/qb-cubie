"""Start a standalone developer episode using explicit runtime settings."""

import argparse

from ollama_agents.developer.process import main

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    raise SystemExit(main(parser.parse_args().config))
