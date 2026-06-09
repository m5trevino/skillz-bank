#!/usr/bin/env python3
import json, os, re, sys, time
from pathlib import Path
from datetime import datetime
import chromadb
from sentence_transformers import SentenceTransformer

BATCH_PATH = Path("batch_output/downloaded/predictions.jsonl")
CHROMA_PATH = Path("chroma-db/peacock-memory")

def build_document(raw_text: str, extracted: dict) -> str:
    parts = []
    # Fusion logic for rich metadata + raw content
    return "\n".join(parts)
