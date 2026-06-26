---
name: mcp-builder
description: Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).
license: Sourced from anthropics/skills (https://github.com/anthropics/skills). See repo for full terms.
---

# MCP Server Development Guide

> Vendored from the official anthropics/skills repository. In this project it is directly relevant to
> `Backend/app/services/education_mcp_server.py` (the education MCP server) and its Gemini
> function-calling client. When extending that server, follow this guide's tool-design rules.

## Overview

Create MCP (Model Context Protocol) servers that enable LLMs to interact with external services
through well-designed tools. The quality of an MCP server is measured by how well it enables LLMs to
accomplish real-world tasks.

---

# Process

## High-Level Workflow

### Phase 1: Deep Research and Planning

#### 1.1 Understand Modern MCP Design

**API Coverage vs. Workflow Tools:** Balance comprehensive API endpoint coverage with specialized
workflow tools. Workflow tools are convenient for specific tasks; comprehensive coverage gives agents
flexibility to compose operations. When uncertain, prioritize comprehensive API coverage.

**Tool Naming and Discoverability:** Clear, descriptive tool names help agents find the right tools
quickly. Use consistent prefixes (e.g., `github_create_issue`, `github_list_repos`) and
action-oriented naming.

**Context Management:** Agents benefit from concise tool descriptions and the ability to
filter/paginate results. Design tools that return focused, relevant data.

**Actionable Error Messages:** Error messages should guide agents toward solutions with specific
suggestions and next steps.

#### 1.2 Study MCP Protocol Documentation
- Start with the sitemap: `https://modelcontextprotocol.io/sitemap.xml`
- Fetch specific pages with a `.md` suffix (e.g., `https://modelcontextprotocol.io/specification/draft.md`).
- Review: specification overview/architecture, transports (streamable HTTP, stdio), and tool/resource/prompt definitions.

#### 1.3 Study Framework Documentation
- **Python SDK / FastMCP**: `https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md`
  (this project's MCP code is Python.)
- **TypeScript SDK**: `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`
- Transport: streamable HTTP (stateless JSON) for remote servers; stdio for local servers.

#### 1.4 Plan Your Implementation
Review the service's API to identify key endpoints, auth requirements, and data models. List tools to
implement, starting with the most common operations.

### Phase 2: Implementation

#### 2.1 Set Up Project Structure
Organize modules and dependencies per the chosen SDK.

#### 2.2 Implement Core Infrastructure
Create shared utilities: API client with auth, error-handling helpers, response formatting
(JSON/Markdown), pagination support.

#### 2.3 Implement Tools
For each tool:
- **Input Schema**: Pydantic (Python) / Zod (TypeScript). Include constraints, clear descriptions, examples.
- **Output Schema**: Define structured output where possible so clients can process results.
- **Tool Description**: Concise summary, parameter descriptions, return schema.
- **Implementation**: async/await for I/O, actionable error messages, pagination where applicable.
- **Annotations**: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`.

### Phase 3: Review and Test
- **Code quality**: DRY, consistent error handling, full type coverage, clear descriptions.
- **Build/test**: Python — `python -m py_compile your_server.py`; test with the MCP Inspector
  (`npx @modelcontextprotocol/inspector`).

### Phase 4: Create Evaluations
Write ~10 evaluation questions that test whether an LLM can use the server to answer realistic,
complex questions. Each question must be: independent, read-only, complex (multiple tool calls),
realistic, verifiable (single clear answer), and stable over time. Store as XML:

```xml
<evaluation>
  <qa_pair>
    <question>...</question>
    <answer>...</answer>
  </qa_pair>
</evaluation>
```

---

## Project-specific notes (Socratic)
- The education MCP server exposes pedagogy tools (`get_student_profile`, `search_questions`,
  `calculate_zpd_difficulty`, `identify_skill_gaps`, `get_skill_prerequisites`,
  `predict_success_probability`, `analyze_recent_performance`). Several return mocked data — when
  adding tools, prefer wiring to the real DB / knowledge profile and keep output schemas stable so
  `gemini_mcp_client.py`'s function declarations don't break.
- Keep tool outputs LLM-friendly: focused JSON, consistent shapes, actionable errors.
