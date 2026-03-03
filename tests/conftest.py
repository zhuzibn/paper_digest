import sys
from pathlib import Path

# Add the repository root to sys.path so that 'import paper_digest' works in tests
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
