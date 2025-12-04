# AI Task Flow Guide

When receiving a task, AI agents must:

1. **Restate the task**  
2. **Identify affected files**  
3. **Propose a step-by-step plan**  
4. **Wait for approval before implementing**  
5. Implement code in **small atomic steps**  
6. Update tests  
7. Provide verification steps

AI must NEVER:
- Make architectural changes without confirmation
- Change the graph schema without referencing ONTOLOGY.md
- Create circular imports
- Hardcode credentials
- Mix frontend & backend concerns
