#!/usr/bin/env python3
import os, sys, time
from google import genai
PROJECT = "gen-lang-client-0959424704"
client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
# ... (rest of monitor_batch_loop.py)
