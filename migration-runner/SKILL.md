---
name: migration-runner
description: Migrates data from ChromaDB SQLite into Graphiti temporal graph. Reads your collections, maps them to custom entity types, handles queue drain, backup, metadata normalization, and generates executable migration scripts. Assumes Graphiti is configured and schema is designed.
version: 1.0.0
---

# MIGRATION-RUNNER v1.0
# ======================
# PURPOSE: Move your ChromaDB data into Graphiti
# INPUT:   ChromaDB SQLite path, collection names, Graphiti connection
# OUTPUT:  Executable migration script + validation report
# ASSUMES: Graphiti configured (doc-interrogator), schema designed (schema-designer)

# THE FLOW
# =========
# 1. ANALYZE — Inspect ChromaDB: collections, counts, metadata keys, queue depth
# 2. BACKUP — Snapshot ChromaDB before any changes
# 3. DRAIN — Process pending queue items
# 4. NORMALIZE — Unify metadata schema across collections
# 5. MIGRATE — Generate and execute ingest scripts per collection
# 6. VALIDATE — Count entities, run sample queries, verify integrity
# 7. REPORT — Summary of what migrated, what skipped, next steps

# STEP 1: ANALYZE
# ================
# Run these checks and present results:
#
# ```bash
# sqlite3 chroma.sqlite3 "SELECT name FROM collections;"
# sqlite3 chroma.sqlite3 "SELECT segment_id, COUNT(*) FROM embeddings GROUP BY segment_id;"
# sqlite3 chroma.sqlite3 "SELECT key, COUNT(*) FROM embedding_metadata GROUP BY key ORDER BY count DESC LIMIT 20;"
# sqlite3 chroma.sqlite3 "SELECT operation, topic, COUNT(*) FROM embeddings_queue GROUP BY operation, topic;"
# ```
#
# Present:
#   "Found {N} collections, {M} total embeddings, {Q} queue items.
#    Metadata keys: {list}
#    Dimensional split: {384d vs 1000d}
#    Collections for migration: {list}"

# STEP 2: BACKUP
# ===============
# Create timestamped backup:
# ```bash
# BACKUP_DIR="$HOME/chroma-backup-$(date +%Y%m%d-%H%M%S)"
# mkdir -p "$BACKUP_DIR"
# sqlite3 chroma.sqlite3 ".backup '$BACKUP_DIR/chroma.sqlite3'"
# cp -r uuid-directories/ "$BACKUP_DIR/"
# echo "Backup: $BACKUP_DIR"
# ```

# STEP 3: DRAIN QUEUE
# ===================
# Process pending ADD operations:
# ```python
# import chromadb
# client = chromadb.PersistentClient(path="chroma_db/")
# for collection_name in collections:
#     coll = client.get_collection(collection_name)
#     # Force queue processing by querying
#     coll.query(query_texts=["test"], n_results=1)
# ```
# Or use ChromaDB's internal queue processor if exposed.

# STEP 4: NORMALIZE METADATA
# ==========================
# Map collection-specific keys to unified schema:
#
# | Collection | Source Keys | Unified Key |
# |------------|-------------|-------------|
# | chat_conversations | project, date, topic | project, reference_time, topic |
# | agent_invariants | repo, category, confidence | repo, category, confidence |
# | app_invariants | repo, category, confidence | repo, category, confidence |
# | tech_vault | domain, topic | domain, topic |
# | seed_vault | domain, topic | domain, topic |
# | case_files_vault | jurisdiction, status | jurisdiction, status |
# | personal_vault | project, topic | project, topic |
# | codebase_vault | language, framework | language, framework |
#
# Handle missing keys: set to None or default.

# STEP 5: MIGRATE
# ===============
# Generate per-collection ingest script:
#
# ```python
# async def migrate_collection(graphiti, collection_name, entity_type):
#     client = chromadb.PersistentClient(path="chroma_db/")
#     coll = client.get_collection(collection_name)
#     results = coll.get(include=["documents", "metadatas"])
#     
#     for doc, meta in zip(results["documents"], results["metadatas"]):
#         await graphiti.add_episode(
#             name=f"{collection_name}-{meta.get('id', 'unknown')}",
#             episode_body=doc,
#             source=EpisodeType.text,
#             reference_time=meta.get("date", datetime.now()),
#             source_description=collection_name,
#             entity_types={entity_type.__name__: entity_type},
#             edge_types=edge_types,
#             edge_type_map=edge_type_map,
#         )
# ```
#
# For structured data (invariants), use EpisodeType.json:
# ```python
# episode_body=json.dumps({
#     "law": meta.get("law"),
#     "violation": meta.get("violation"),
#     "evidence": meta.get("evidence"),
#     "confidence": meta.get("confidence"),
# })
# ```

# STEP 6: VALIDATE
# ================
# Post-migration checks:
# ```python
# # Count nodes per type
# results = await graphiti._search(
#     query="*",
#     config=NODE_HYBRID_SEARCH_RRF
# )
# print(f"Total nodes: {len(results.nodes)}")
#
# # Sample temporal query
# results = await graphiti.search(
#     "cases involving John Smith",
#     center_node_uuid=john_smith_uuid,
#     num_results=10
# )
# print(f"Found {len(results)} connections")
#
# # Check communities
# await graphiti.build_communities()
# ```

# STEP 7: REPORT
# ==============
# Generate markdown report:
# ```markdown
# # Migration Report
# ## Source: ChromaDB @ {path}
# ## Target: Graphiti @ {neo4j_uri}
# ## Date: {timestamp}
#
# | Collection | Embeddings | Migrated | Skipped | Errors |
# |------------|-----------|----------|---------|--------|
# | chat_conversations | 26,154 | 26,154 | 0 | 0 |
# | agent_invariants | 235 | 235 | 0 | 0 |
# | ... | ... | ... | ... | ... |
#
# ## Validation
# - Total nodes: {N}
# - Total edges: {M}
# - Communities built: {K}
# - Sample queries: passed
#
# ## Next Steps
# - [ ] Rewire Herbert v2 to query Graphiti
# - [ ] Set up periodic community rebuilds
# - [ ] Configure backup strategy for Neo4j
# ```

# BEHAVIOR RULES
# ==============
# DO:
#   - Always backup before migrating
#   - Present analysis before acting
#   - Normalize metadata consistently
#   - Generate executable scripts, not just plans
#   - Validate after migration
#   - Report clearly what happened
#
# DO NOT:
#   - Delete source data without backup
#   - Skip queue drain
#   - Ignore dimensional splits
#   - Run migration without user approval
#   - Leave validation unreported
#
# The job: ANALYZE → BACKUP → DRAIN → NORMALIZE → MIGRATE → VALIDATE → REPORT
