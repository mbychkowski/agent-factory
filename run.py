#!/usr/bin/env python3
import sys
from pathlib import Path

# Add the project root directory to the python search path
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

from agents.spec_deliberator.loop_agent import main

if __name__ == "__main__":
    main()
