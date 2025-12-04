# AI Developer Guide

This guide defines how AI agents (Claude, GPT, Windsurf, Codeium) must behave when writing or modifying code in this repository.

## 1. Coding Style
- Python: Pydantic for models, dependency-injection patterns, async FastAPI.
- TypeScript: strict mode enabled, typed API interfaces.
- Use domain-driven naming aligned with ONTOLOGY.md and ARCHITECTURE.md.
- Favor small, composable functions over large blocks of code.

## 2. Architectural Obedience
AI must never:
- Rewrite frameworks (no replacing FastAPI or Next.js)
- Modify the folder structure
- Touch core architectural documents unless asked
- Mix backend and frontend logic
- Introduce new architectural patterns without approval

## 3. Debugging Behavior
When errors occur:
- Identify the root cause
- Provide a minimal targeted fix
- Explain WHY it failed
- Avoid speculative or large refactors unless explicitly requested

## 4. Multi-File Edits
When changes affect multiple files:
- List each file first
- Provide diffs or full replacements
- Apply changes in small, isolated steps
- Never modify more than 4–5 files in one operation unless approved

## 5. Testing Requirements
For any substantial logic:
- Provide unit tests where possible
- Provide manual testing instructions
- Ensure endpoints return proper validation and error messages

## 6. Interaction Expectations
AI should:
- Slow down
- Ask clarifying questions when uncertain
- Provide a plan BEFORE writing code
- Follow the vertical slice development sequence
- Default to safety, clarity, and modularity
