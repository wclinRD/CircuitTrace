# CircuitTrace AI Agent Map (AGENTS.md)

Welcome to the CircuitTrace repository. This document serves as the entry point for all AI agents working on this project, following the **Harness Engineering** paradigm.

## 🧭 Repository Structure

*   `backend/` - Python FastAPI backend handling AST parsing and EDA logic.
    *   **Rule**: Use `pyslang` for all SystemVerilog/Verilog parsing. Do not use regex for logic extraction.
    *   **Entry**: `backend/src/desktop_app.py` or `backend/src/api.py`.
    *   **Types**: Strict type hints (`typing`) and `Pydantic` models are mandatory.
*   `frontend/` - React 19 + Vite frontend.
    *   **Style**: Vanilla CSS (`App.css`). No Tailwind unless explicitly requested.
    *   **Component Logic**: Keep components small and focused.
*   `artifacts/` - Design and execution plans for the AI agent (stored locally by the IDE).

## 🛠️ Mechanical Rules

1.  **Run Tests After Changes**: Always run `pytest tests/` in the `backend` directory after modifying logic.
2.  **Linting & Types**: Use `uv` to manage dependencies. Code must pass basic typing rules.
3.  **No Unverified Assumptions**: If a parsing API is unknown, write a small probe script (like `probe_slang.py`) to verify it first.
4.  **Agent Readability**: Favor explicit, straightforward code over complex, "clever" abstractions.

## 🎯 Current Task

Upgrading the core trace engine to use `pyslang` (AST-based) instead of regex.
See the `task.md` and `plan_ast_upgrade.md` artifacts for the checklist.
