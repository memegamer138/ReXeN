## Problems to Solve:
* Time-consuming recon - Manual tool chaining takes hours

* Rule violations - Accidentally testing out-of-scope

* Missed opportunities - Not connecting related findings

* Poor documentation - Manual report writing slows submissions

## Core Features (MVP):
* Automated URL discovery - Find all endpoints, not just subdomains

* Compliance checking - Auto-validate scope before testing

* AI analysis - Local LLM to prioritize findings

* One-command reports - Generate submission-ready reports

* Safe defaults - Won't DoS or violate rules

## Components:
* CLI (Click) - User interface

* Orchestrator - Manages tool execution order

* Tool Wrappers - 10+ recon tools (Go/installable)

* Compliance Engine - Checks scope/rules before each action

* AI Analyzer - Local Ollama LLM for analysis

* Report Generator - Creates PDF/HTML reports

* Database - PostgreSQL for findings storage

* Cache - Redis for rate limiting

## Tech Stack
**Primary Language:** Python 3.11

Go for waybackurl
Rust for pydantic

## Project Structure

```text
rexen/
├── .env                    # Environment variables
├── .gitignore
├── pyproject.toml         # Project config
├── requirements.txt       # Python deps
├── docker-compose.yml     # Postgres + Redis
├── Makefile               # Common commands
│
├── src/                   # Main source
│   ├── __init__.py
│   ├── cli.py            # CLI entry point
│   ├── config.py         # Configuration
│   │
│   ├── core/             # Core logic
│   │   ├── orchestrator.py
│   │   ├── compliance.py
│   │   └── validator.py
│   │
│   ├── tools/            # Tool wrappers
│   │   ├── __init__.py
│   │   ├── base.py       # Base tool class
│   │   ├── crawlers/     # gospider, katana
│   │   ├── discovery/    # subfinder, waybackurls
│   │   └── scanners/     # nuclei, httpx
│   │
│   ├── ai/               # AI components
│   │   ├── analyzer.py
│   │   ├── ollama_client.py
│   │   └── prompts/      # LLM prompt templates
│   │
│   ├── reporting/        # Report generation
│   │   ├── generator.py
│   │   ├── templates/
│   │   └── exporters/
│   │
│   ├── database/         # Database layer
│   │   ├── models.py
│   │   ├── crud.py
│   │   └── session.py
│   │
│   └── utils/            # Utilities
│       ├── logger.py
│       ├── helpers.py
│       └── file_utils.py
│
├── tests/                # Tests
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── data/                 # Generated data
│   ├── results/
│   ├── reports/
│   └── logs/
│
├── scripts/              # Helper scripts
│   ├── install_tools.sh
│   ├── setup_db.sh
│   └── backup.sh
│
└── docs/                 # Documentation
    ├── api.md
    ├── tools.md
    └── quickstart.md
```