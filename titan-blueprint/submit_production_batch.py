#!/usr/bin/env python3
"""
THE IGNITER — Phase 3 of the Titan Pipeline
Uploads pre-shredded JSONL to GCS and fires a Vertex AI GCS Batch job.
The $2 Heist: Vertex Batch pricing at $0.075/Mtok (50% off real-time).
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from google import genai
from google.cloud import storage
from google.genai.types import BatchJobSource, BatchJobDestination, CreateBatchJobConfig

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG — Project Peacock1
# ═════════════════════════════════════════════════════════════════════════════
PROJECT = "gen-lang-client-0959424704"
LOCATION = "us-central1"
MODEL = "gemini-2.5-flash"
BUCKET = "peacock-batch-1777479303"


def log(msg: str):
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {msg}")


def upload_to_gcs(local_path: Path, dest_blob_name: str) -> str:
    """Upload local file to GCS via Python client. Returns the GCS URI."""
    gcs_uri = f"gs://{BUCKET}/{dest_blob_name}"
    log(f"Uploading {local_path} → {gcs_uri}")
    client = storage.Client(project=PROJECT)
    bucket = client.bucket(BUCKET)
    blob = bucket.blob(dest_blob_name)
    blob.upload_from_filename(str(local_path))
    log(f"✓ Uploaded to {gcs_uri}")
    return gcs_uri


def submit_batch_job(source_gcs_uri: str, dest_prefix: str, display_name: str) -> str:
    """Submit Vertex batch job. Returns job name."""
    log("Initializing Vertex AI client...")
    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)

    log(f"Submitting batch job: {display_name}")
    log(f"  Source: {source_gcs_uri}")
    log(f"  Dest:   {dest_prefix}")

    job = client.batches.create(
        model=MODEL,
        src=BatchJobSource(format="jsonl", gcs_uri=[source_gcs_uri]),
        config=CreateBatchJobConfig(
            display_name=display_name,
            dest=BatchJobDestination(format="jsonl", gcs_uri=dest_prefix),
        ),
    )
    log(f"✓ Job submitted: {job.name}")
    return job.name


def poll_job(job_name: str, timeout_hours: int = 4, interval_sec: int = 60) -> dict:
    """Poll batch job until complete or timeout."""
    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
    deadline = time.time() + (timeout_hours * 3600)

    log(f"Polling job {job_name} every {interval_sec}s...")
    while time.time() < deadline:
        job = client.batches.get(name=job_name)
        state = job.state.value if hasattr(job.state, "value") else str(job.state)
        log(f"  State: {state}")

        if state in ("JOB_STATE_SUCCEEDED", "SUCCEEDED"):
            log("✓ Job completed successfully")
            return {"status": "success", "job": job}
        if state in ("JOB_STATE_FAILED", "FAILED", "JOB_STATE_CANCELLED", "CANCELLED"):
            log(f"✗ Job failed or cancelled: {state}")
            return {"status": "failed", "state": state, "job": job}

        time.sleep(interval_sec)

    log("✗ Polling timed out")
    return {"status": "timeout", "job": None}


def download_results(output_gcs_prefix: str, local_dir: Path) -> list[Path]:
    """Download all output JSONL files from GCS prefix to local dir."""
    local_dir.mkdir(parents=True, exist_ok=True)
    log(f"Downloading results from {output_gcs_prefix} → {local_dir}")

    result = subprocess.run(
        ["gsutil", "ls", output_gcs_prefix],
        capture_output=True, text=True
    )
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not files:
        log("⚠ No output files found at destination")
        return []

    downloaded = []
    for gcs_file in files:
        local_file = local_dir / Path(gcs_file).name
        log(f"  {gcs_file} → {local_file}")
        subprocess.run(["gsutil", "cp", gcs_file, str(local_file)], check=True)
        downloaded.append(local_file)

    log(f"✓ Downloaded {len(downloaded)} result files")
    return downloaded


def merge_results(local_dir: Path, out_path: Path) -> int:
    """Merge all downloaded JSONL result files into one."""
    jsonl_files = sorted(local_dir.glob("*.jsonl"))
    if not jsonl_files:
        log("⚠ No .jsonl files to merge")
        return 0

    log(f"Merging {len(jsonl_files)} files → {out_path}")
    count = 0
    with open(out_path, "w") as out:
        for f in jsonl_files:
            with open(f) as src:
                for line in src:
                    line = line.strip()
                    if line:
                        out.write(line + "\n")
                        count += 1
    log(f"✓ Merged {count} result lines")
    return count


def main() -> int:
    ap = argparse.ArgumentParser(description="Submit Titan Vertex GCS Batch Job")
    ap.add_argument("input", type=Path, help="Local batch input JSONL file")
    ap.add_argument("--name", default="titan_prod", help="Job display name prefix")
    ap.add_argument("--bucket", default=BUCKET, help="GCS bucket for input/output")
    ap.add_argument("--poll", action="store_true", help="Poll until job completes")
    ap.add_argument("--download", action="store_true", help="Download results after success")
    ap.add_argument("--merge", action="store_true", help="Merge downloaded JSONLs into one")
    ap.add_argument("--out-dir", type=Path, default=Path("batch_output"), help="Local dir for downloads")
    ap.add_argument("--timeout", type=int, default=6, help="Polling timeout in hours")
    args = ap.parse_args()

    if not args.input.exists():
        print(f"Error: input file not found: {args.input}")
        return 1

    # ── 1. Upload ────────────────────────────────────────────────────────────
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    source_gcs = upload_to_gcs(args.input, f"{args.name}_{ts}_input.jsonl")

    # ── 2. Submit ────────────────────────────────────────────────────────────
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    display_name = f"{args.name}_{ts}"
    dest_prefix = f"gs://{BUCKET}/{args.name}_{ts}_output"
    job_name = submit_batch_job(source_gcs, dest_prefix, display_name)

    # ── 3. Save job metadata ─────────────────────────────────────────────────
    meta_path = args.out_dir / f"{args.name}_{ts}_job_info.json"
    meta = {
        "job_name": job_name,
        "display_name": display_name,
        "source_gcs": source_gcs,
        "dest_prefix": dest_prefix,
        "model": MODEL,
        "project": PROJECT,
        "location": LOCATION,
        "submitted_at": datetime.utcnow().isoformat(),
    }
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    log(f"✓ Job metadata saved: {meta_path}")

    # ── 4. Poll (optional) ───────────────────────────────────────────────────
    if args.poll:
        result = poll_job(job_name, timeout_hours=args.timeout)
        meta["result"] = result["status"]
        meta["finished_at"] = datetime.utcnow().isoformat()
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        if result["status"] != "success":
            return 1

        # ── 5. Download (optional) ───────────────────────────────────────────
        if args.download:
            dl_dir = args.out_dir / f"{args.name}_{ts}_raw"
            downloaded = download_results(dest_prefix, dl_dir)
            meta["downloaded_files"] = [str(p) for p in downloaded]
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=2)

            # ── 6. Merge (optional) ──────────────────────────────────────────
            if args.merge and downloaded:
                merged_path = args.out_dir / f"{args.name}_{ts}_merged.jsonl"
                merge_results(dl_dir, merged_path)
                meta["merged_path"] = str(merged_path)
                with open(meta_path, "w") as f:
                    json.dump(meta, f, indent=2)

    log("✓ Titan pipeline Phase 3 complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
