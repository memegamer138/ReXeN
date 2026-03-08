# ReXeN ReconSentry: AI-Powered Bug Bounty Recon Assistant

ReXeN is an adaptive, compliance-first reconnaissance assistant for bug bounty hunters and security researchers. It automates deep web application recon using a local LLM (Ollama) to intelligently select and sequence tools, while enforcing program rules and legal boundaries.

**Disclaimer:** ReXeN is a tool for authorized security testing only. 
Users are solely responsible for:

1. Ensuring they have explicit permission to test any target
2. Complying with all applicable laws and regulations
3. Respecting program rules and rate limits
4. Using findings responsibly and ethically

The developer assumes no liability for misuse of this tool.

## What Makes ReXeN Different?
|Traditional Recon Tools|	ReXeN |
|----------|-------------------|
|❌ Just run tools in sequence|	✅ AI-driven workflow optimization|
|❌ Output dumps without context|	✅ Intelligent analysis & correlation|
|❌ Risk of rule violations|	✅ Compliance-first architecture|
|❌ Manual report writing|	✅ Automated professional reports|
|❌ One-size-fits-all approach|	✅ Adaptive to target technology|


## Key Features
### AI-Powered Adaptive Recon
* Local LLM (Ollama) for privacy and speed
* Dynamic tool selection and workflow adaptation
* Context-aware, iterative scanning (RAG-powered)
* Minimal human intervention

### Compliance-First Design
* Scope validation before any scan
* Program rule enforcement (rate limits, restrictions)
* Emergency stop on violation detection

### Modular Tool Integration
* Wrappers for top recon tools (gospider, katana, httpx, subfinder, etc.)
* Easy to add more tools (nuclei, amass, waybackurls, etc.)

### Automated Reporting
* Generates text reports (HTML, PDF, etc. planned)
* Aggregates all tool outputs and findings
### Architecture

```text
┌───────────────┐
│   User/CLI    │
└──────┬────────┘
       │
┌──────▼────────┐
│   Pipeline    │  ← Adaptive loop: LLM ↔ Orchestrator ↔ Tools
│ (LLM, RAG)    │
└──────┬────────┘
       │
┌──────▼────────┐
│ Orchestrator  │  ← Rate limiting, error handling, parallelism
└──────┬────────┘
       │
┌──────▼────────┐
│ Tool Wrappers │  ← Modular, extensible
└───────────────┘
       │
┌──────▼────────┐
│  Reporting    │  ← Aggregates results, generates report
└───────────────┘
```

## Quickstart

1. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

2. Currently, rexen is a pip installable, install through:

```sh
 pip install -e .
```

3. **Install Go-based tools (optional, for full functionality):**
    ```sh
    go install github.com/tomnomnom/waybackurls@latest
    # ...install other tools as needed
    ```

4. **Run adaptive discovery (pipeline):**
    ```sh
    rexen discover https://target.com
    ```

5. **Analyze results:**
    ```sh
    rexen analyze target.com
    ```
    This will categorize and summarize discovered URLs.

6. **See all commands:**
    ```sh
    rexen --help
    ```
---


For advanced usage, see the [docs/](docs/) folder.

## Current MVP Capabilities
* Adaptive, LLM-driven tool selection and orchestration
* Modular wrappers for core recon tools
* RAG context for iterative, context-aware scanning
* Automated text report generation
* Compliance checks (scope, rate limits, etc.)

## Roadmap
### Phase 1: MVP (Current)
- Adaptive pipeline with LLM and orchestrator
- Core tool wrappers
- Basic compliance and reporting

### Phase 2: Enhanced Intelligence
- Add more tools (nuclei, amass, waybackurls, etc.)
- Advanced reporting (HTML, PDF, executive summaries)
- Attack chain detection, risk scoring

### Phase 3: Enterprise
- Web dashboard & REST API
- Team collaboration, scheduling, analytics
- Evidence storage, audit trail, advanced compliance

## Security & Compliance
- Pre-flight scope and rule validation
- Rate limiting and emergency stop
- Immutable logs (planned)
- No unauthorized testing—always follow program rules!

## Ideas Dump

## Ideas Dump

- **LLM-Guided Report Templates:** Allow users to select or customize report templates/styles for different audiences (executive, technical, compliance).
- **Historical Recon Memory:** Let the LLM review or retrieve summaries of previous discoveries for the same target or similar technologies to improve tool selection and reporting.
- **Semantic Search for RAG:** Use embeddings/vector search to retrieve the most relevant past findings or context for the current scan.
- **Auto-Tuning Orchestrator:** Dynamically adjust rate limits, parallelism, or tool order based on target response and previous scan performance.
- **Plugin System:** Allow users to add custom tool wrappers, post-processing, or reporting modules via a plugin interface.
- **Web UI/Visualization:** Build a web dashboard for visualizing recon results, timelines, and findings.
- **API Integration:** Integrate with bug bounty platforms, ticketing systems, or notification services for automated reporting and workflow.
- **Evidence Archiving:** Store screenshots, HTTP responses, and other artifacts for each finding.
- **Advanced Compliance:** Add features for GDPR, SOC2, or other regulatory requirements (e.g., data redaction, audit trails).
- **Multi-Target/Scope Support:** Run recon on multiple targets in parallel, with per-scope rules and reporting.
- **Automated Exploitation/Validation:** Integrate with tools like nuclei or custom scripts to validate discovered issues automatically.
- **Interactive CLI/Chat:** Add a conversational CLI or chat interface for interactive recon guidance and Q&A.
- **Cloud/Distributed Execution:** Support running tools across multiple machines or in the cloud for large-scale recon.
- **User Feedback Loop:** Let users rate findings or report accuracy to improve LLM prompts and tool selection over time.
