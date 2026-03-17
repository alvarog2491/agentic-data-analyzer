import os
import json
import asyncio
from typing import Dict, Any
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.tools.code_interpreter_client import CodeInterpreter
from strands.models import BedrockModel
from strands import Agent, tool

app = BedrockAgentCoreApp()

# Global Setup
region = os.getenv("AWS_REGION", "us-east-1")
code_client = CodeInterpreter(region)
code_client.start(session_timeout_seconds=1200)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read_file(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""


@tool
def execute_python(code: str, session_id: str, description: str = "") -> str:
    """Execute Python code in the secure sandbox."""
    if description:
        code = f"# {description}\n{code}"

    print(f"\n--- Executing Code (sandbox session: {code_client.session_id}) ---\n{code}\n---")
    
    response = code_client.invoke("executeCode", {
        "code": code,
        "language": "python",
        "clearContext": False
    })
    
    output = ""
    error = ""
    for event in response.get("stream", []):
        structured = event.get("result", {}).get("structuredContent", {})
        output += structured.get("stdout", "")
        error += structured.get("stderr", "")

    if error: return f"Errors: {error}"
    return output if output else "Executed successfully (no stdout)."

# Initialize Model & Agent
SYSTEM_PROMPT = read_file(os.path.join(PROJECT_ROOT, "assets", "system_prompt.txt"))
model = BedrockModel(model_id="deepseek.v3.2")
agent = Agent(model=model, tools=[execute_python], system_prompt=SYSTEM_PROMPT)

# Helper for data syncing
def write_data_file_in_sandbox():
    data_path = os.path.join(PROJECT_ROOT, "data", "train_small.csv")
    data_content = read_file(data_path)
    if not data_content:
        raise FileNotFoundError(f"Data file not found or empty: {data_path}")
    args = {"content": [{"path": "train_small.csv", "text": data_content}]}
    code_client.invoke("writeFiles", args)
    print(f"Data synced to sandbox (session: {code_client.session_id})")

@app.entrypoint
async def invoke(payload: Dict[str, Any]):
    """The main entry point called by AWS AgentCore"""
    
    # Sync data to sandbox
    write_data_file_in_sandbox()
    
    query = payload.get("prompt", "")
    
    try:
        response = await agent.invoke_async(query)
        return {"result": response.message['content'][0]['text']}
    except Exception as e:
        print(f"Error during agent execution: {e}")
        return {"result": f"Execution Error: {str(e)}"}

if __name__ == "__main__":
    try:
        app.run()
    finally:
        code_client.stop()