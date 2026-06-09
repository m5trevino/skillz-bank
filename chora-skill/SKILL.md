# CHORA — PEACOCK ARCHIVE ENGINE SKILL

**Zero-Dependency AI Chat Archive System**  
**Wired to Devwater PreCompact Hooks**

**Version:** 1.0  
**Status:** Production

---

## 00 — MISSION

Chora parses AI chat exports from 6 platforms into clean, numbered-Set markdown (`_chat.md` + `_think.md`). It runs automatically via devwater hooks on every Kimi CLI PreCompact and can be driven manually or in batch.

**Output (Hook Mode):**  
`devwater-data/$SESSION_ID/{basename}-chat.md`  
`devwater-data/$SESSION_ID/{basename}-think.md`

**Output (Manual Mode):**  
`~/peacock/aichats/{platform}/YYYY-MM-DD_slug/`

---

## 01 — REAL ARCHITECTURE

Kimi CLI PreCompact → devwater hook → `devwater_kimi_wrapper.py` → `parsers/kimi_code_parser.py` → clean Set files in `devwater-data/`

Only Kimi-Code is currently auto-wired. The other 5 parsers are manual but fully functional.

**Set Format**
```markdown
# Title
> N sets · YYYY-MM-DD
============================================================
=== Set 1 ===
user: ...
assistant: ...
-=-=-==--=--=
```

---

## 02 — OPERATOR PROCEDURES

**Manual Parse (Kimi-Code)**
```bash
python3 /home/flintx/chora/parsers/kimi_code_parser.py ~/.kimi-code/sessions/.../ses_xxx
```

**Devwater Automatic**  
Just work. Files appear in `devwater-data/` on PreCompact.

**Batch / Project Manager**
```bash
python3 project_session_manager.py --list
python3 project_session_manager.py --export-project myproject --devwater
python3 project_session_manager.py --export-all --merge
```

---

## 03 — KEY COMPONENTS

| Component                    | Purpose                              | Location |
|-----------------------------|--------------------------------------|----------|
| `kimi_code_parser.py`       | Main parser (devwater wired)         | `parsers/` |
| `devwater_kimi_wrapper.py`  | Hook bridge                          | root     |
| `project_session_manager.py`| Batch export + devwater backfill     | root     |
| 5 other platform parsers    | Manual use for non-Kimi-Code         | `parsers/` |
| `howto/` + `info/`          | Platform guides + forensic notes     | root     |

---

## 04 — JUNK SESSION FILTERS

All parsers skip empty/noise sessions:
- Kimi-Code: `is_meaningful_session()` (min lines + tool activity)
- Kimi-OG: `is_worth_parsing()` (requires ≥1 assistant message)
- Gemini CLI: equivalent content + response count filter

~25% of sessions are filtered by default.

---

## 05 — PARSER REFERENCE

See individual files in `parsers/` and guides in `howto/` for each platform’s input format, edge cases, and output rules.

All parsers produce the same strict Set format and correlated think files.

---

## 06 — ROADMAP

1. Wire remaining 5 parsers to devwater (auto-detect)
2. Extract shared utils into `parsers/common.py`
3. Add test suite
4. Unified CLI entrypoint
5. Consolidated root docs

---

## 07 — INVARIANTS

- Pure stdlib. Zero external dependencies.
- Cold-start ready. One file + howto/ is enough.
- No noise. Junk sessions are filtered, not archived.
- Blueprint before code. Deconstruct first.

**Chora is locked. Use it.**
