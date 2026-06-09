# Example Interaction

## Scenario: GraphRAG Research

**User:** *pastes 3 articles about GraphRAG, vector DBs, and LLM evaluation*

---

**skill-architect:**

I see you've researched GraphRAG, vector databases, and evaluation methods. Let me categorize what I found:

- **Technologies:** GraphRAG, vector DBs (unspecified), LLM eval frameworks
- **Patterns:** Knowledge graph construction, retrieval-augmented generation,
  evaluation pipelines
- **Open Questions:** Which vector DB, graph structure approach, and eval metrics

Let's resolve these before I build your skill. First question:

> "Are you planning to implement GraphRAG in an active project, or is this
> exploratory research?"

---

**User:** "Active project."

---

**skill-architect:**

Got it. Do you already know how you want to structure the knowledge graph, or
do you need help designing that?

---

**User:** "I don't know."

---

**skill-architect:**

No problem. There are three common approaches:

1. **Entity-centric** — nodes are named entities, edges are relationships. Best
   for structured domains with clear entity types.
2. **Community-centric** — nodes are semantic communities detected from text.
   Best for unstructured documents where explicit entities are sparse.
3. **Hybrid** — combines both. More complex but handles mixed data well.

Which of these sounds closest to your data? Or should I design the skill to walk
you through choosing?

---

**User:** "Walk me through choosing."

---

**skill-architect:**

Perfect. One more question to scope it:

> "Is this for a prototype, MVP, or production system? And what's your timeline?"

---

**User:** "MVP, 2 weeks."

---

**skill-architect:**

Last one for now:

> "What does your current stack look like? Language, framework, and any
> existing database or vector store?"

---

**User:** "Python, FastAPI, no vector store yet."

---

**skill-architect:**

Excellent. I have enough to build your skill. Generating now...

*[generates skill: "GraphRAG Implementation Planner" with interview logic,
decision trees, and FastAPI scaffolding]*

---

**skill-architect:**

Here's the skill I wrote based on our conversation. Does this match what you
need? You can tell me to:

- **(a)** make it more detailed
- **(b)** simplify it
- **(c)** change the output format
- **(d)** add a section I missed

---

**User:** "Can you add a section on evaluation metrics?"

---

**skill-architect:**

*[adds evaluation metrics section]*

Updated. How does this look now?

---

**User:** "Perfect."

---

**skill-architect:**

Skill finalized. Here's how to install it:

```bash
# Copy to your skills directory
cp -r skill-architect-graphrag ~/.agents/skills/

# Or project scope
cp -r skill-architect-graphrag ./skills/
```
