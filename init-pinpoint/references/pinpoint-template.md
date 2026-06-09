# PINPOINT: [Feature Name] Implementation Map

> **Feature**: [Concise Name]  
> **Trace Level**: Surgical  
> **Status**: [Operational/Buggy/Legacy]

---

## 🏗️ Feature Overview
[What this feature does and why it exists.]

## 🚀 The Execution Path (Trigger to Finish)

1. **Trigger**: `[File:Path]` → `[Function/Route]`
2. **Analysis**: Logic flows to `[File:Path]` for [Purpose]
3. **Core Processing**: Handled in `[File:Path]` via `[Class/Method]`
4. **Data Interaction**: Reads/Writes to `[Table/External API]`
5. **Completion**: Returns `[Format]` to `[Recipient]`

## 📁 Related File Index

| File Path | Role | Key Symbols |
|-----------|------|-------------|
| `app/routes/feature.py` | Entry Point | `POST /v1/feature` |
| `app/core/logic.py` | Business Logic | `process_feature()` |
| `app/models/data.py` | Schema | `FeatureRequest` |
| `app/db/crud.py` | DB Access | `save_feature()` |

## ⚙️ Configuration & Environment
- **Env Var**: `ENABLE_FEATURE_X=true`
- **Config**: `settings.json` → `feature_params`

## 🛠️ Modification Guide
- **To change logic**: Edit `process_feature()` in `app/core/logic.py`.
- **To add a field**: Update `FeatureRequest` in `app/models/data.py`.
- **To test changes**: Run `pytest tests/test_feature.py`.

## 🧠 Logic Gaps & Technical Debt
- [Note any known issues, confusing code, or missing tests.]

---

**END OF PINPOINT**
