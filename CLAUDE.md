# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

An agentic EDA (Exploratory Data Analysis) system built on **Amazon Bedrock AgentCore** and the **Strands Agents SDK**. The agent dynamically generates and executes Python code in an isolated sandbox (via AgentCore's built-in Code Interpreter) to analyze datasets placed in the `data/` directory.

## Setup

```bash
python -m venv venv
source .venv/bin/activate
pip install -r requirements.txt
```

Place datasets in the `data/` directory before running.

## Commands

**Run locally (starts HTTP server on port 8080):**
```bash
python3 src/data_analyzer_agent.py
```

**Test the local server:**
```bash
curl -X POST http://localhost:8080/invocations \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello!"}'
```

**Deploy to AWS Bedrock AgentCore:**
```bash
agentcore configure --entrypoint src/data_analyzer_agent.py
agentcore deploy
```

**Invoke the deployed agent:**
```bash
python3 src/invoke_agent.py
```

**Destroy the deployed agent:**
```bash
agentcore destroy
```

## Architecture

**`src/data_analyzer_agent.py`** — The core agent. Key components:
- `BedrockAgentCoreApp` wraps the app and exposes the `@app.entrypoint` HTTP handler at `/invocations`
- `CodeInterpreter` manages a persistent sandbox session (20-minute timeout); data files must be explicitly synced into it via `writeFiles` before code execution
- `execute_python` is a Strands `@tool` that sends code to the sandbox via `executeCode` and returns stdout/stderr
- `Agent` (Strands) uses `deepseek.v3.2` via `BedrockModel` and the system prompt from `assets/system_prompt.txt`
- On each invocation, `write_data_file_in_sandbox()` syncs `data/train_small.csv` into the sandbox before the agent runs

**`src/invoke_agent.py`** — A standalone script that calls the *deployed* AgentCore runtime via `boto3.client('bedrock-agentcore')`. Contains a hardcoded agent ARN and example EDA prompt — update the ARN after each deploy.

**`assets/system_prompt.txt`** — Instructs the agent to always validate answers through `execute_python` rather than responding without code execution.

## Key Behaviors

- The sandbox maintains state between `execute_python` calls within a single invocation, so the agent can build on prior results across multiple tool calls.
- Data must be written to the sandbox via `writeFiles` before it can be read by executed code — the sandbox filesystem is isolated from the host.
- AWS credentials and `AWS_REGION` env var must be configured for both local runs (Code Interpreter uses Bedrock) and deployments.
