#!/usr/bin/env python3
"""
THE SHREDDER — Phase 2 of the Titan Pipeline
Slices raw discovery text into atomic JSONL requests for Vertex AI GCS Batch.
Zero Omission Protocol: every sentence gets a [S:GLOBAL_ID]. No skips.
"""

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# ── CONFIG ────────────────────────────────────────────────────────────────────
CHUNK_SIZE_BYTES = 800 * 1024
CHUNK_OVERLAP_SENTENCES = 3
OUTPUT_DIR = "processed_text"
BUCKET_INPUT_PATH = "gs://peacock-batch-1777479303/input/"

# ── EXTRACTION PROMPT — Zero Omission Protocol ─────────────────────────────────
EXTRACTION_PROMPT = """You are a FORENSIC EXTRACTION ENGINE operating under the ZERO OMISSION PROTOCOL.

MISSION: Process EVERY sentence in the provided discovery text. Account for ALL sentence IDs. No skips. No summaries.

INPUT FORMAT:
Each sentence is prefixed with [S:GLOBAL_ID] where GLOBAL_ID is the absolute sentence number across the entire document.

OUTPUT FORMAT — JSON array with EXACTLY one object per input sentence:
[
  {
    "sentence_idx": <the GLOBAL_ID from input>,
    "type": "EVENT" | "NO_EVENT" | "REDACTED" | "AMBIGUOUS",
    "verbatim_entity": "exact name as written, or GHOST_N for redacted, or null",
    "verbatim_time": "exact time phrase as written, or null",
    "action": "what happened — max 15 words, or null",
    "normalized_time": "ISO 8601 if possible, HH:MM for times, YYYY-MM-DD for dates, or null",
    "normalized_time_end": "for time ranges, or null",
    "is_fuzzy_time": true | false,
    "source_quote": "the EXACT full sentence text",
    "status": "fact" | "inference" | "official" | "hearsay",
    "epistemic_tier": 1 | 2 | 3 | 4,
    "action_category": "movement" | "communication" | "observation" | "forensic_action" | "emotion" | "alibi" | "null",
    "location": "location mentioned, or null",
    "doc_id": "<provided DOC_ID>",
    "page_num": <provided PAGE_NUM>,
    "global_idx": <the GLOBAL_ID>
  }
]

STATUS RULES:
- "fact" = Direct witness statement, first-person account, verbatim quote
- "inference" = Analyst interpretation, implied but not directly stated
- "official" = Police record, detective report, official document language
- "hearsay" = Second-hand report, "she said that he...", "it was reported that..."

EPISTEMIC TIER:
- 1 = Direct witness (I saw, I heard, I was there)
- 2 = Hearsay / second-hand (she told me, they said)
- 3 = Official record (detective states, report indicates)
- 4 = Speculation / inference (it appears, likely, probably)

GHOST ENTITY RULES:
- If a name is [REDACTED], blacked out, or a number like "Victim 1", use GHOST_N where N increments per document
- If a pronoun ("he", "she", "the officer") refers to a previously mentioned entity, use that entity's name/ghost_id
- If a pronoun refers to an unknown entity, create a new GHOST_ID

CRITICAL: The number of output objects MUST exactly equal the number of [S:GLOBAL_ID] prefixes in the input. Every sentence gets a result. Type "NO_EVENT" is valid for sentences with no actionable information."""

# ── SENTENCE SPLITTER ─────────────────────────────────────────────────────────
def split_into_sentences(text: str) -> List[Tuple[int, str, int]]:
    sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-Z"\'])|(?<=[.!?])\n+')
    sentences = []
    idx = 0
    offset = 0
    parts = sentence_endings.split(text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        start_offset = text.find(part, offset)
        if start_offset == -1:
            start_offset = offset
        sentences.append((idx, part, start_offset))
        idx += 1
        offset = start_offset + len(part)
    return sentences

# ── CHUNKER ───────────────────────────────────────────────────────────────────
def chunk_document(doc_path: str, doc_id: str, chunk_size: int = CHUNK_SIZE_BYTES) -> List[Dict]:
    with open(doc_path, 'r', encoding='utf-8', errors='replace') as f:
        full_text = f.read()
    sentences = split_into_sentences(full_text)
    total_sentences = len(sentences)
    chunks = []
    current_chunk_sentences = []
    current_chunk_size = 0
    global_start_idx = 0
    for i, (sent_idx, sent_text, offset) in enumerate(sentences):
        sent_size = len(sent_text.encode('utf-8'))
        if current_chunk_size + sent_size > chunk_size and current_chunk_sentences:
            chunk_text = "\n".join([f"[S:{gs}] {st}" for gs, st, _ in current_chunk_sentences])
            chunks.append({
                "doc_id": doc_id,
                "chunk_id": f"{doc_id}_chunk_{len(chunks):04d}",
                "global_start_idx": global_start_idx,
                "global_end_idx": current_chunk_sentences[-1][0],
                "sentence_count": len(current_chunk_sentences),
                "text": chunk_text,
                "char_start": current_chunk_sentences[0][2],
                "char_end": current_chunk_sentences[-1][2] + len(current_chunk_sentences[-1][1])
            })
            overlap_start = max(0, len(current_chunk_sentences) - CHUNK_OVERLAP_SENTENCES)
            current_chunk_sentences = current_chunk_sentences[overlap_start:]
            current_chunk_size = sum(len(s[1].encode('utf-8')) for s in current_chunk_sentences)
            global_start_idx = current_chunk_sentences[0][0]
        current_chunk_sentences.append((sent_idx, sent_text, offset))
        current_chunk_size += sent_size
    if current_chunk_sentences:
        chunk_text = "\n".join([f"[S:{gs}] {st}" for gs, st, _ in current_chunk_sentences])
        chunks.append({
            "doc_id": doc_id,
            "chunk_id": f"{doc_id}_chunk_{len(chunks):04d}",
            "global_start_idx": global_start_idx,
            "global_end_idx": current_chunk_sentences[-1][0],
            "sentence_count": len(current_chunk_sentences),
            "text": chunk_text,
            "char_start": current_chunk_sentences[0][2],
            "char_end": current_chunk_sentences[-1][2] + len(current_chunk_sentences[-1][1])
        })
    print(f"[✓] Chunked {doc_id}: {total_sentences} sentences → {len(chunks)} chunks")
    return chunks

# ── BATCH INPUT GENERATOR ─────────────────────────────────────────────────────
def generate_batch_input(chunks: List[Dict], output_path: str):
    with open(output_path, 'w') as f:
        for chunk in chunks:
            est_page = chunk["global_start_idx"] // 15
            request_payload = {
                "key": chunk["chunk_id"],
                "request": {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {"text": EXTRACTION_PROMPT},
                                {"text": f"DOC_ID: {chunk['doc_id']}\nPAGE_NUM: {est_page}\nCHUNK_ID: {chunk['chunk_id']}\nSENTENCE_RANGE: {chunk['global_start_idx']}-{chunk['global_end_idx']}\n\n--- START DISCOVERY TEXT ---\n{chunk['text']}\n--- END DISCOVERY TEXT ---\n\nOUTPUT JSON ARRAY:"}
                            ]
                        }
                    ],
                    "generation_config": {
                        "response_mime_type": "application/json",
                        "temperature": 0.0,
                        "max_output_tokens": 8192
                    }
                }
            }
            f.write(json.dumps(request_payload) + "\n")
    print(f"[✓] Generated batch input: {output_path} ({len(chunks)} requests)")

# ── MAIN ──────────────────────────────────────────────────────────────────────
def prep_batch(doc_path: str, doc_id: Optional[str] = None):
    doc_path = Path(doc_path)
    if not doc_id:
        doc_id = doc_path.stem
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chunks = chunk_document(str(doc_path), doc_id)
    output_file = os.path.join(OUTPUT_DIR, f"{doc_id}_batch_input.jsonl")
    generate_batch_input(chunks, output_file)
    manifest_path = os.path.join(OUTPUT_DIR, f"{doc_id}_chunk_manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump({
            "doc_id": doc_id,
            "doc_path": str(doc_path),
            "total_chunks": len(chunks),
            "total_sentences": sum(c["sentence_count"] for c in chunks),
            "chunks": chunks
        }, f, indent=2)
    print(f"[✓] Manifest saved: {manifest_path}")
    print(f"[✓] Ready for upload to {BUCKET_INPUT_PATH}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 batch_chunker.py <doc_path> [doc_id]")
        sys.exit(1)
    doc_path = sys.argv[1]
    doc_id = sys.argv[2] if len(sys.argv) > 2 else None
    prep_batch(doc_path, doc_id)
