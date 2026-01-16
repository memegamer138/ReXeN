# ReXeN ReconSentry: AI-Powered Bug Bounty Recon Assistant

ReXeN is an intelligent, compliance-first reconnaissance assistant for bug bounty hunters and security researchers. It automates deep web application reconnaissance while strictly adhering to program rules and legal boundaries.

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
### AI-Powered Intelligence
* Local LLM Integration (Ollama) for privacy-preserving analysis

* Smart workflow generation based on target technology stack

* Finding correlation to identify attack chains

* Risk prioritization using ML models

* Natural language report generation

### Compliance-First Design
* Automatic scope validation before any testing

* Program rule enforcement (rate limits, restrictions)

* Legal jurisdiction checking

* Immutable audit trail of all actions

* Emergency stop on violation detection

### Deep URL Reconnaissance
* Comprehensive endpoint discovery (not just subdomains)

* JavaScript analysis for hidden API endpoints

* Parameter extraction and categorization

* Authentication flow mapping

* Business logic understanding

### Professional Reporting
* Multiple formats: PDF, HTML, Markdown, JSON

* Executive summaries for different audiences

* Technical evidence with screenshots

* Prioritized remediation steps

* Actionable next steps for further testing

### Architecture

```text
┌─────────────────────────────────────────────────┐
│                   User Interface                 │
│  • CLI Application                              │
│  • Web Dashboard (Future)                       │
│  • REST API                                     │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│              Orchestration Engine                │
│  • Workflow Scheduler                           │
│  • Compliance Validator                         │
│  • Rate Limiter                                 │
│  • Progress Tracker                             │
└─────────────────────┬───────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  URL Discovery  │ │  AI Analysis    │ │  Tool Execution │
│  • Crawling     │ │  • LLM Processing│ │  • 30+ Security │
│  • JS Analysis  │ │  • Correlation  │ │    Tools        │
│  • Param Extract│ │  • Risk Scoring │ │  • Parallel     │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                      │           │           │
                      └───────────┼───────────┘
                                  ▼
┌─────────────────────────────────────────────────┐
│              Data & Storage Layer                │
│  • PostgreSQL (Structured Data)                 │
│  • Elasticsearch (Logs & Search)                │
│  • MinIO (Evidence Storage)                     │
│  • Redis (Cache & Queues)                       │
└─────────────────────────────────────────────────┘
```


## Prerequisites
* Python 3.11+
* Docker & Docker Compose
* Git
* 8GB+ RAM (for AI models)

## How to Use

1. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

2. **Install Go-based tools (optional, for full functionality):**
    ```sh
    go install github.com/tomnomnom/waybackurls@latest
    # ...install other tools as needed
    ```

3. **Run discovery:**
    ```sh
    rexen discover https://target.com
    ```
    Results will be saved in the `src/data/results/` directory.

4. **Analyze results:**
    ```sh
    rexen analyze target.com
    ```
    This will categorize and summarize discovered URLs.

5. **See all commands:**
    ```sh
    rexen --help
    ```

For advanced usage, see the [docs/](docs/) folder.

## How to use

## Tool Integration
ReXeN integrates with 30+ security tools:

### URL Discovery
* **Gospider** - Fast web spider

* **Katana** - Modern crawling

* **Waybackurls** - Historical URL discovery

* **Gau** - Fetch known URLs

* **FFuF** - Directory/parameter fuzzing

### JavaScript Analysis
* **LinkFinder** - Endpoint extraction from JS

* **JSFinder** - JavaScript file analysis

* **Subjs** - JS file discovery

### Infrastructure
* **Subfinder** - Subdomain enumeration

* **Amass** - In-depth DNS enumeration

* **Naabu** - Port scanning

* **Httpx** - HTTP probe

### Vulnerability Detection
* **Nuclei** - Template-based scanning

* **Nikto** - Web server scanner

## Smart Workflow Generation
Based on target technology, ReXeN creates optimized workflows:

* **React/Node.js apps** → Focus on JavaScript analysis, API discovery

* **WordPress sites** → Run wpscan, check plugins/themes

* **APIs only** → Concentrate on endpoint discovery, parameter fuzzing

* **Java applications** → Look for deserialization, XXE

## Security & Compliance
### Safety Features
* Pre-flight Checklist

* Validate target is in bug bounty program

* Parse and understand program rules

* Check legal jurisdiction

* Set appropriate rate limits

* Real-time Monitoring

* Continuous compliance checking

* Rate limit enforcement

* Automatic violation detection

* Emergency stop capability

* Audit Trail

* Immutable logs of all actions

* Cryptographic verification

## Compliance reporting

* Evidence chain of custody

## Data Handling
* All findings encrypted at rest

* Automatic data deletion after 90 days

* No PII storage unless required

* Local processing only (optional)

## Output & Reporting
Report Structure

```text
├── 1. Executive Summary
├── 2. Methodology
├── 3. Attack Surface Overview
├── 4. Critical Findings
│   ├── Vulnerability Details
│   ├── Evidence (Screenshots)
│   ├── Reproduction Steps
│   └── CVSS Scoring
├── 5. Technical Details
├── 6. Remediation Recommendations
└── 7. Appendix: Full Results
```

## Roadmap
### Phase 1: MVP (Current)
* URL discovery engine

* Basic compliance checking

* Local LLM integration

* PDF report generation

### Phase 2: Enhanced Intelligence
* Attack chain detection

* Learning from past results

* Workflow optimization

* Team collaboration features

## Phase 3: Enterprise
* Web dashboard

* REST API

* Scheduled scanning

* Advanced analytics