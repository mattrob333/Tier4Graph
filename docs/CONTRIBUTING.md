# Contributing Guide

## Branching Strategy
- `main` – stable production-intended branch  
- `dev` – active development  
- Feature branches: `feat/<feature-name>`  
- Fix branches: `fix/<issue>`  

## Workflow
1. Create a feature branch.  
2. Implement changes with tests.  
3. Submit a PR into `dev`.  
4. All PRs require:
   - Passing CI  
   - Code review  
   - Architectural consistency  

## Coding Standards
- TypeScript strict mode  
- Python type hints  
- No secrets in code  
- Unit tests for all services  
