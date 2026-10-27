# Local Development Setup

## Scope

This is a baseline guide. Verify versions against the actual repository
before executing commands. Install optional components only when needed.

## Prerequisites

-   Supported 64-bit Windows for the first target build.
-   Git.
-   Python version pinned by project metadata.
-   Node.js LTS for frontend development.
-   Ollama only for the local-model path.
-   Sufficient disk space for dependencies, browser binaries, and
    optional model weights.

## Backend Setup (example)

From the repository root, adapt paths to the actual layout:

``` powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If the project uses `pyproject.toml` or a lockfile-based tool, follow
that workflow instead of maintaining duplicate dependency sources.

## Browser Runtime

Install Playwright through the project's locked dependencies, then
install the required browser runtime. Example:

``` powershell
python -m playwright install chromium
```

Do not automate a source until its permitted access method is
established.

## Frontend Setup (example)

Run from the frontend directory:

``` powershell
npm ci
npm run dev
```

Use `npm ci` when a valid lockfile exists. Do not replace the lockfile
casually.

## Local Model

-   Ollama is optional for core functionality.
-   Check that Ollama is installed and responding before enabling the
    local-model path.
-   Download a model only after checking disk space and informing the
    user of approximate size.
-   Benchmark load and inference latency on the device.
-   Keep deterministic fallback available.

## Configuration

-   Copy `.env.example` only if the app uses environment configuration.
-   Never commit `.env`.
-   Validate configuration at startup.
-   Do not put API keys in frontend variables bundled into client code.

## Verification

Run the repository's actual documented commands for backend tests,
frontend tests, lint/format checks, API health, and database integrity.
Record exact commands and outcomes. If a command was not run, say so.
