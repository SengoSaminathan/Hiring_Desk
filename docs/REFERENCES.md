# Engineering References

Use official/current documentation for version-specific behavior. These references are starting points, not substitutes for checking the versions actually selected by the repository.

## Harness Engineering and Coding-Agent Workflow
- OpenAI, *Harness engineering: leveraging Codex in an agent-first world* (2026-02-11): https://openai.com/index/harness-engineering/
- OpenAI Cookbook, *Iterating Development Workflows with Codex*: https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex
- OpenAI, *Custom instructions with AGENTS.md*: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Visual Studio Code, *Custom instructions for coding agents*: https://code.visualstudio.com/docs/agent-customization/custom-instructions
- OpenAI, *Best practices*: https://learn.chatgpt.com/docs/learn/best-practices

## Project Technology References
- Python: https://docs.python.org/3/
- FastAPI: https://fastapi.tiangolo.com/
- Playwright Python: https://playwright.dev/python/
- SQLite: https://www.sqlite.org/docs.html
- Ollama: https://docs.ollama.com/
- React: https://react.dev/
- PyInstaller: https://pyinstaller.org/en/stable/

## Usage Rule
Before changing a library, model, provider, or platform version, read the current official version-specific docs, confirm compatibility, and record consequential choices in `docs/DECISIONS.md`. Do not copy deprecated commands simply because they appear in an old setup guide.
