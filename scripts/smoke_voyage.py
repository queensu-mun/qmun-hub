"""Verify Voyage embeddings work."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import toml
import voyageai

secrets = toml.load(ROOT / ".streamlit" / "secrets.toml")
client = voyageai.Client(api_key=secrets["voyage"]["api_key"])

result = client.embed(
    ["The Queen's Model UN team competes on the North American collegiate circuit.",
     "Brazil's position on climate financing is shaped by BASIC bloc politics."],
    model="voyage-3",
    input_type="document",
)
print(f"Got {len(result.embeddings)} embeddings, dim={len(result.embeddings[0])}")
print(f"Total tokens: {result.total_tokens}")
print("OK")
