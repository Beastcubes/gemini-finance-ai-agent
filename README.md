# Gemini Finance AI Agent

Enterprise-grade FP&A variance analysis agent built using:

- Google Agent Development Kit (ADK)
- BigQuery
- Gemini Enterprise
- Python

This project demonstrates a governed enterprise AI architecture where financial calculations remain fully deterministic within BigQuery and controlled Python tool layers, while Gemini is used strictly for orchestration and executive narrative generation.

> **Architecture Principle:** Deterministic Data → Controlled Tool Layer → AI Narrative Only

---

# Why This Project Exists

Most enterprise AI finance demos allow large language models to directly calculate, summarize, or infer financial results.

This project intentionally avoids that pattern.

The architecture separates:
- deterministic financial computation
- governed semantic data access
- AI-generated executive narration

The result is a more auditable, explainable, and enterprise-safe AI workflow for finance operations.

---

# Enterprise Architecture

```text
Enterprise Financial Sources
        ↓
Alteryx Designer Cloud
(Data Preparation + Governance + AI Classification)
        ↓
BigQuery Governed Semantic Layer
        ↓
Deterministic Python Tool Layer
(BigQuery Retrieval + Structured Logic)
        ↓
Google ADK Agent
(Orchestration + Prompt Control)
        ↓
Gemini Enterprise
(Executive Narrative + Conversational Q&A)
```

---

# Core Design Principles

| Principle | Description |
|---|---|
| Deterministic Computation | Financial calculations never occur inside the LLM |
| Governed Semantic Layer | All metrics originate from controlled BigQuery datasets |
| Controlled Tool Access | Agent retrieves only pre-defined structured data |
| Narrative-Only AI | Gemini formats and explains results but does not generate financial logic |
| Explainable Outputs | Every metric traces back to governed data |

---

# Supported Use Cases

- Budget vs Actual (BvA) variance analysis
- Overspend detection
- Variance contributor ranking
- Trend shift analysis
- Executive finance Q&A
- Controlled conversational analytics

---

# Example Questions

### Overspend Analysis

```text
What are the largest overspends for September 2025?
```

### Variance Contributors

```text
Explain the primary contributors to overspend this period.
```

### Trend Analysis

```text
What spending trends shifted significantly this month?
```

### Executive Summary

```text
Summarize the current financial risk posture.
```

---

# Tech Stack

| Component | Technology |
|---|---|
| Data Preparation | Alteryx Designer Cloud |
| Data Warehouse | BigQuery |
| AI Classification | Google Gemini |
| Agent Framework | Google ADK |
| Model | Gemini 2.5 Flash |
| Programming Language | Python |
| Deployment | Vertex AI Agent Engine |
| UI Layer | Gemini Enterprise |

---

# Project Structure

```text
.
├── finance_agent/
│   ├── agent.py
│   ├── prompts.py
│   └── tools/
│       └── bigquery_tools.py
├── .env.template
├── Dockerfile
├── pyproject.toml
├── README.md
└── uv.lock
```

---

# Key Architectural Decision

The LLM does not calculate financial values.

Instead:

1. BigQuery stores governed financial data
2. Python tools retrieve structured results
3. The ADK agent orchestrates workflows
4. Gemini generates executive-ready narrative responses

This prevents:
- hallucinated metrics
- uncontrolled calculations
- inconsistent reporting logic
- non-auditable outputs

---

# Example Output Structure

Every response follows a structured executive finance reporting format:

```text
Executive Summary
Risk Assessment
Largest Variances
Trend Shifts
Summary Table
Recommended Follow-Up
```

---

# Local Setup

## Install Dependencies

```bash
uv sync
```

## Configure Environment

Create a `.env` file from `.env.template`.

Example configuration:

```env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=us-central1

BQ_PROJECT_ID=YOUR_PROJECT_ID
BQ_DATASET_ID=finance_analytics
BQ_TABLE_ID=finance_variance_fact

MODEL_NAME=gemini-2.5-flash
```

---

# Run Locally

```bash
uv run adk run finance_agent
```

Web UI:

```bash
uv run adk web
```

---

# Deployment

The solution is designed for deployment using:

- Vertex AI Agent Engine
- BigQuery
- Gemini Enterprise
- Docker-based runtime environments

---

# Security & Governance

This repository intentionally demonstrates enterprise-safe AI patterns:

- No dynamic SQL generation
- No LLM-based calculations
- No unrestricted data access
- No direct financial inference by AI
- Controlled tool orchestration only

---

# Future Enhancements

- Multi-period comparison analysis
- Department-level drilldowns
- Cost center analytics
- Audit trace visibility
- Dashboard integration
- Agent memory and workflow chaining
- Streamlit-based conversational UI

---

# Architecture Before Intelligence

Enterprise AI systems should prioritize:

- governed data
- deterministic logic
- auditability
- explainability
- controlled orchestration

before introducing generative AI capabilities.

This project is designed around that principle.