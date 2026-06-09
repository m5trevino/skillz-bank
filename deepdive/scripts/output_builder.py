#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

class DocumentationBuilder:
    def __init__(self, project_root, chat_data=None):
        self.root = Path(project_root)
        self.docs_dir = self.root / 'docs'
        self.analysis = self._load_analysis()
        self.chat_data = chat_data
        
    def _load_analysis(self):
        analysis_file = self.docs_dir / '.deepdive_analysis.json'
        if analysis_file.exists():
            with open(analysis_file) as f:
                return json.load(f)
        return {}
    
    def build_all(self):
        self.docs_dir.mkdir(exist_ok=True)
        (self.docs_dir / 'diagrams').mkdir(exist_ok=True)
        if self.chat_data:
            (self.docs_dir / 'chatlogs').mkdir(exist_ok=True)
        
        print("Building documentation tiers...")
        self._build_executive_overview()
        self._build_basic_overview()
        self._build_detailed_overview()
        self._build_extensive_overview()
        self._build_ai_handoff()
        self._build_legacy_placeholder()
        self._build_decision_log()
        self._build_risk_heatmap()
        self._build_test_coverage()
        self._build_api_contract()
        self._build_onboarding()
        
        if self.chat_data:
            self._build_conversation_log()
            self._build_discussion_synthesis()
            self._build_implementation_state()
            self._build_project_narrative()
        
        self._save_diagrams()
        self._save_manifest()
        print(f"Complete documentation in {self.docs_dir}")
    
    def _build_executive_overview(self):
        content = f"""# Executive Overview

**Project:** {self.root.name}
**Analyzed:** {datetime.now().isoformat()}
**Confidence Score:** {self.analysis.get('confidence', {}).get('file_scan', 0)}%

## What This Is
[AUTO_DETECTED] A software project with {len(self.analysis.get('files', []))} source files.

## Core Mission
[USER_INPUT_NEEDED] What problem does this solve?

## Current State
- **Maturity:** {'Legacy' if len(self.analysis.get('git_history', [])) > 100 else 'Active' if self.analysis.get('git_history') else 'Unknown'}
- **Risk Level:** {self._calculate_overall_risk()}
- **Test Coverage:** {'Unknown' if not self._has_tests() else 'Present'}
- **Chat Context:** {'Yes - see 11-14' if self.chat_data else 'No chat logs provided'}

## Critical Insight
{self._generate_insight()}

## Next Actions
1. Review 07-RISK_HEATMAP.md for immediate concerns
2. Read 04-AI_HANDOFF_KEY.md before any modifications
3. Check 05-LEGACY_TIMELINE.md for historical context
{'4. Review 13-IMPLEMENTATION_STATE.md for pending tasks from discussions' if self.chat_data else ''}
"""
        self._write('00-EXECUTIVE_OVERVIEW.md', content)
    
    def _build_basic_overview(self):
        files = self.analysis.get('files', [])
        exts = {}
        for f in files:
            ext = f['ext'] or 'no_extension'
            exts[ext] = exts.get(ext, 0) + 1
        
        content = f"""# Basic Overview

## Technology Profile
{chr(10).join(f"- **{ext}**: {count} files" for ext, count in sorted(exts.items(), key=lambda x: -x[1]))}

## Entry Points
{chr(10).join(f"- `{ep}`" for ep in self.analysis.get('entry_points', [])[:5])}

## Directory Structure
{self._generate_tree()}

## Build/Run Commands
[DETECTED] Check for: package.json scripts, Makefile, Dockerfile, README.md
"""
        self._write('01-BASIC_OVERVIEW.md', content)
    
    def _build_detailed_overview(self):
        content = ["# Detailed Overview", ""]
        for file_info in self.analysis.get('files', [])[:20]:
            path = file_info['path']
            funcs = self.analysis.get('functions', {}).get(str(self.root / path), [])
            content.append(f"## {path}")
            content.append(f"- **Lines:** {file_info['lines']}")
            content.append(f"- **Size:** {file_info['size']} bytes")
            content.append(f"- **Functions:** {len(funcs)}")
            if funcs:
                content.append("### Functions")
                for fn in funcs[:5]:
                    content.append(f"- `{fn['name']}()` (line {fn['line']}, complexity: {fn['complexity']})")
            risk = self.analysis.get('risk_scores', {}).get(path, {})
            if risk.get('score', 0) > 70:
                content.append(f"⚠️ **RISK SCORE: {risk['score']}/100** - High complexity/churn")
            content.append("")
        self._write('02-DETAILED_OVERVIEW.md', '\n'.join(content))
    
    def _build_extensive_overview(self):
        content = f"""# Extensive Overview

## Data Flow Architecture
[INFERRED FROM IMPORTS]
See diagrams/function_map.mmd for visual representation.

## State Management
[DETECTED PATTERNS]
- Look for: Redux, Context, useState, global variables, singletons

## Security Critical Paths
[AUTO_FLAGGED]
- Authentication entry points
- Database query builders
- External API calls

## Performance Critical Paths
[AUTO_FLAGGED] 
- Files > 500 lines
- Functions with complexity > 10
- High churn areas

## Architecture Drift
[COMPARE: README claims vs actual code structure]
"""
        self._write('03-EXTENSIVE_OVERVIEW.md', content)
    
    def _build_ai_handoff(self):
        high_risk = [f for f, r in self.analysis.get('risk_scores', {}).items() if r.get('score', 0) > 80]
        content = f"""# AI Handoff Key

## 2-Minute Drop-In Protocol

1. **READ FIRST:** 00-EXECUTIVE_OVERVIEW.md (2 min)
2. **ORIENT:** diagrams/cognitive_load.mmd (30 sec)
3. **TARGET:** 02-DETAILED_OVERVIEW.md → find your file
4. **CHECK:** 07-RISK_HEATMAP.md before modifying
{'5. **CONTEXT:** 12-DISCUSSION_SYNTHESIS.md for recent decisions' if self.chat_data else ''}

## Forbidden Zones 🔴
{chr(10).join(f"- `{f}` (Risk: {self.analysis.get('risk_scores', {{}}).get(f, {{}}).get('score', 'N/A')})" for f in high_risk[:5])}

## Safe Modification Targets 🟢
- Files with < 100 lines
- Files with tests
- Files not in 🔴 zones

## Testing Requirements
- 🔴 Zones: Write tests BEFORE modifying
- 🟡 Zones: Run existing tests after
- 🟢 Zones: Standard TDD

## Common Patterns
[DETECTED FROM CODE]
- Error handling pattern: [scan for try/catch, if err != nil, etc.]
- Logging pattern: [scan for console.log, logger, etc.]
- Naming conventions: [detected from file names]
"""
        self._write('04-AI_HANDOFF_KEY.md', content)
    
    def _build_legacy_placeholder(self):
        placeholder = """# Legacy Timeline

Generated by git_archaeologist.py. Run separately for full narrative.

## Quick Stats
- Total commits: [RUN git_archaeologist.py]
- Active authors: [RUN git_archaeologist.py]
- Major epochs: [RUN git_archaeologist.py]

See diagrams/git_timeline.mmd for visual timeline.
"""
        self._write('05-LEGACY_TIMELINE.md', placeholder)
    
    def _build_decision_log(self):
        content = """# Decision Log

| Decision | Context | Date | Status | Confidence |
|----------|---------|------|--------|------------|
| [EXTRACTED FROM COMMITS] | | | | |

## Auto-Detected Decisions
[SCANNING for "switch to", "migrate", "refactor", "rewrite" in commit messages]
"""
        self._write('06-DECISION_LOG.md', content)
    
    def _build_risk_heatmap(self):
        risks = self.analysis.get('risk_scores', {})
        sorted_risks = sorted(risks.items(), key=lambda x: -x[1].get('score', 0))
        content = ["# Risk Heatmap", ""]
        content.append("## 🔴 CRITICAL (Score > 80)")
        for path, risk in sorted_risks:
            if risk.get('score', 0) > 80:
                content.append(f"- `{path}`: {risk['score']}/100 (complexity: {risk['complexity']}, churn: {risk['churn']}, tested: {risk['has_tests']})")
        content.append("\n## 🟡 HIGH (Score 50-80)")
        for path, risk in sorted_risks:
            if 50 <= risk.get('score', 0) <= 80:
                content.append(f"- `{path}`: {risk['score']}/100")
        content.append("\n## 🟢 STABLE (Score < 50)")
        content.append(f"- {len([r for r in risks.values() if r.get('score', 0) < 50])} files in stable condition")
        self._write('07-RISK_HEATMAP.md', '\n'.join(content))
    
    def _build_test_coverage(self):
        content = """# Test Coverage Gap Analysis

## Untested Critical Paths
[FILES WITH high_risk AND NOT has_tests]

## Test Quality Assessment
[SCAN for: mock abuse, missing assertions, test files that don't test logic]

## Recommended Test Priorities
1. [HIGHEST RISK + NO TESTS]
2. [ENTRY POINTS]
3. [BUSINESS LOGIC]
"""
        self._write('08-TEST_COVERAGE_GAP.md', content)
    
    def _build_api_contract(self):
        content = """# API Contract

## Internal Interfaces
[EXTRACTED FROM function signatures]

## External Endpoints
[DETECTED FROM route definitions, API clients]

## Data Schemas
[INFERRED FROM models, types, interfaces]

## Error Contracts
[DETECTED FROM error handling patterns]
"""
        self._write('09-API_CONTRACT.md', content)
    
    def _build_onboarding(self):
        content = f"""# Onboarding Checklist

## 15-Minute Setup

### Prerequisites
[DETECTED FROM package files, README]
- Node.js version: [check package.json engines]
- Python version: [check requirements.txt, pyproject.toml]
- Database: [detected from config files]

### Quick Start
```bash
# Clone
git clone [repo]

# Install
[DETECTED COMMAND]

# Run
[DETECTED COMMAND]

# Test
[DETECTED COMMAND]
```

## Troubleshooting
[DETECTED COMMON ISSUES]
"""
        self._write('10-ONBOARDING_CHECKLIST.md', content)

        self._write('10-ONBOARDING_CHECKLIST.md', content)
    
    def _build_conversation_log(self):
        if not self.chat_data:
            return
        content = self.chat_data.get('verbatim_doc', '# No chat data')
        self._write('11-CONVERSATION_LOG.md', content)

    def _build_discussion_synthesis(self):
        if not self.chat_data:
            return
        content = self.chat_data.get('synthesis', '# No chat data')
        self._write('12-DISCUSSION_SYNTHESIS.md', content)

    def _build_implementation_state(self):
        if not self.chat_data:
            return
        content = self.chat_data.get('state_matrix', '# No chat data')
        self._write('13-IMPLEMENTATION_STATE.md', content)

    def _build_project_narrative(self):
        if not self.chat_data:
            return
        content = self.chat_data.get('narrative', '# No chat data')
        self._write('14-PROJECT_NARRATIVE.md', content)

    def _save_diagrams(self):
        diagrams_dir = self.docs_dir / 'diagrams'
        arch = self.analysis.get('diagrams', {}).get('architecture', 'graph TD\n    A[No architecture data]')
        with open(diagrams_dir / 'architecture.mmd', 'w') as f:
            f.write(arch)
        func = self.analysis.get('diagrams', {}).get('function_map', 'graph LR\n    A[No function data]')
        with open(diagrams_dir / 'function_map.mmd', 'w') as f:
            f.write(func)
        for name in ['git_timeline', 'dependencies', 'cognitive_load', 'risk_heatmap', 'chat_timeline']:
            path = diagrams_dir / f'{name}.mmd'
            if not path.exists():
                with open(path, 'w') as f:
                    f.write(f'%% {name} - run specific generator\n')

    def _save_manifest(self):
        manifest = {
            'project_name': self.root.name,
            'analyzed_at': datetime.now().isoformat(),
            'files_analyzed': len(self.analysis.get('files', [])),
            'functions_mapped': sum(len(v) for v in self.analysis.get('functions', {}).values()),
            'confidence_score': sum(self.analysis.get('confidence', {}).values()) / max(len(self.analysis.get('confidence', {})), 1),
            'critical_risks': len([r for r in self.analysis.get('risk_scores', {}).values() if r.get('score', 0) > 80]),
            'documentation_tiers': 14 if self.chat_data else 10,
            'diagrams_generated': 7 if self.chat_data else 6,
            'chatlogs_processed': len(self.chat_data.get('sessions', [])) if self.chat_data else 0,
            'estimated_read_time': '60 minutes' if self.chat_data else '45 minutes'
        }
        with open(self.docs_dir / '.deepdive_manifest.json', 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"Manifest: {manifest['critical_risks']} critical risks detected")

    def _write(self, filename, content):
        with open(self.docs_dir / filename, 'w') as f:
            f.write(content)
        print(f"  ✓ {filename}")

    def _calculate_overall_risk(self):
        risks = self.analysis.get('risk_scores', {})
        if not risks:
            return "Unknown"
        avg = sum(r.get('score', 0) for r in risks.values()) / len(risks)
        if avg > 70: return "🔴 High"
        if avg > 40: return "🟡 Medium"
        return "🟢 Low"

    def _has_tests(self):
        files = self.analysis.get('files', [])
        return any('test' in f['path'].lower() or 'spec' in f['path'].lower() for f in files)

    def _generate_tree(self):
        dirs = set()
        for f in self.analysis.get('files', [])[:30]:
            parts = f['path'].split('/')
            for i in range(len(parts)):
                dirs.add('/'.join(parts[:i]))
        return '\n'.join(sorted(dirs))[:500] + "\n..."

    def _generate_insight(self):
        if self.analysis.get('risk_scores'):
            worst = max(self.analysis['risk_scores'].items(), key=lambda x: x[1].get('score', 0))
            return f"Highest risk file: `{worst[0]}` (score: {worst[1]['score']}/100). Review immediately."
        return "No critical insights generated."

if __name__ == '__main__':
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    builder = DocumentationBuilder(root)
    builder.build_all()
