from bedrock_agentcore.tools.code_interpreter_client import CodeInterpreter
from bedrock_agentcore import BedrockAgentCoreApp
from strands.models import BedrockModel
import pandas as pd
from strands import Agent, tool
import asyncio
from typing import Dict, Any
import json
import os

app = BedrockAgentCoreApp()

region = os.getenv("AWS_REGION", "us-east-1")
code_client = CodeInterpreter(region)
code_client.start(session_timeout_seconds=1200)

def call_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Helper to invoke sandbox tools with session persistence"""
    # Note: AgentCore invoke returns a stream. We need the full result.
    response = code_client.invoke(tool_name, arguments)
    
    for event in response["stream"]:
        return json.dumps(event["result"])

def read_file(file_path: str) -> str:
    """Helper function to read file content with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return ""
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""


#Define and configure the code interpreter tool
@tool
def execute_python(code: str, session_id: str, description: str = "") -> str:
    """Execute Python code in the secure sandbox."""
    if description:
        code = f"# {description}\n{code}"

    print(f"\n--- Executing Code ---\n{code}\n----------------------")

    response = code_client.invoke("executeCode", {
            "code": code,
            "language": "python",
            "clearContext": False
        }
    )
    
    output = ""
    for event in response.get("stream", []):
        if "result" in event:
            output += event["result"].get("stdout", "")
    return output

# Load system prompt
SYSTEM_PROMPT = read_file("assets/system_prompt.txt")

model_id="deepseek.v3.2"
model= BedrockModel(model_id=model_id)

# Instantiate the Strands Agent
agent=Agent(
    model=model,
        tools=[execute_python],
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None)


def write_data_file_in_sandbox():
    data_file_content = read_file("data/train.csv")
    files_to_create = [
                    {
                        "path": "train.csv",
                        "text": data_file_content
                }]

    # Write files to sandbox
    writing_files = call_tool("writeFiles", {"content": files_to_create})
    print("Writing files result:")
    print(writing_files)

    # Verify files were created
    listing_files = call_tool("listFiles", {"path": ""})
    print("\nFiles in sandbox:")
    print(listing_files)

@app.entrypoint
async def invoke(payload: Dict[str, Any]):
    """The main entry point called by AWS AgentCore"""
    
    write_data_file_in_sandbox()
    
    # Extract prompt and session info from payload
    query = "Load the file 'train.csv' and perform exploratory data analysis(EDA) on it. Tell me about distributions and outlier values."
    
    # Execute Agent Logic
    response_text = ""
    try:
        # Strands stream_async returns chunks of the response
        async for event in agent.stream_async(query):
            if "data" in event:
                chunk = event["data"]
                response_text += chunk
                print(chunk, end="", flush=True)
    except Exception as e:
        response_text = f"Error: {str(e)}"

    return {"result": response_text}

if __name__ == "__main__":
    # app.run() starts the HTTP server on port 8080
    app.run()