# Coding-Agent Tool Compatibility

## Why This Exists
Different IDE agents and coding tools do not all load the same instruction filenames or configuration. A correct `AGENTS.md` can be silently ignored by a tool that expects another entry point. Verify instruction discovery for the actual tool used by the project owner.

## Shared Source of Truth
Keep project-wide rules in `AGENTS.md` and the detailed requirements in the linked Markdown files. Tool-specific files should be short adapters that point back to these sources, not copied manuals that drift.

## Setup Procedure for the Selected Tool
1. Identify the coding environment (for example, Codex, Claude Code, GitHub Copilot, Cursor, or another editor/agent).
2. Check the current official documentation for its instruction-file discovery, precedence, nesting, and size limits.
3. Create only the tool-specific entry point that is actually needed, preserving `AGENTS.md` as the shared source when the tool supports it.
4. Keep tool-specific guidance minimal: read the common contract, load the current phase, use the repo's test commands, do not bypass source policies, and report evidence.
5. Run a read-only verification prompt asking the tool which instruction files it loaded and to summarize the important constraints.
6. If it fails to load guidance, fix discovery/configuration and repeat the verification before allowing broad implementation work.

## Avoid Conflicting Rules
- Do not maintain different copies of the same product requirement in multiple agent-specific files.
- If the selected tool requires a separate file, give it routing instructions and tool-specific mechanics only.
- Resolve contradictions in the source-of-truth files first.
- Store tool settings or hooks only when their behavior is understood and tested.
- Do not assume that MCP tools, skills, hooks, subagents, or autonomous terminal access are available; inspect the installed tool and configure only what the user has approved.

## Required Onboarding Check
Before the first implementation phase, ask the selected agent to report:
- instruction files discovered and precedence;
- active phase and acceptance criteria;
- available test/build commands;
- permitted tools/actions and approval gates;
- current repository status and unresolved unknowns.

Compare its response to this harness. Do not proceed if important rules were missed.

## Official Starting Points
See `docs/REFERENCES.md` for current agent-instruction documentation. Tool behavior may change; re-check official docs when upgrading the coding environment.
