from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
import boto3
import json
import os
import asyncio

app = FastAPI()
load_dotenv()

knowledge_base_id = "JGMPKF6VEI"

class PromptRequest(BaseModel):
    prompt: str

def get_bedrock_client():
    return boto3.client("bedrock-runtime", region_name="us-east-1")

def invoke_llm(prompt: str):
    client = get_bedrock_client()

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "temperature": 0.7,
        "system": "You are a helpful assistant.",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    model='us.anthropic.claude-3-7-sonnet-20250219-v1:0'
    response = client.invoke_model(
        modelId=model,
        body=json.dumps(payload),
        contentType="application/json",
        accept="application/json"
    )

    result_bytes = response["body"].read()
    result_str = result_bytes.decode("utf-8")
    result_json = json.loads(result_str)

    content = result_json.get("content", [])
    if content and len(content) > 0:
        return content[0].get("text", "")

async def stream_generator(prompt: str):
    response = invoke_llm(prompt)
    for word in response.split():
        yield word + " "
        await asyncio.sleep(0.1)

@app.post("/llm/query")
def query_llm(request: PromptRequest):
    try:
        response = invoke_llm(request.prompt)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/llm/stream")
def stream_llm(prompt: str):
    return StreamingResponse(stream_generator(prompt), media_type="text/plain")


@app.post("/kb/query")
def kb_query(request: PromptRequest):
    client = get_bedrock_client()

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "temperature": 0.7,
        "system": f"You are a helpful assistant. Use the knowledge base {knowledge_base_id} to answer the user's question.",
        "messages": [
            {"role": "user", "content": request.prompt}
        ]
    }

    model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(payload),
        contentType="application/json",
        accept="application/json"
    )

    result_bytes = response["body"].read()
    result_json = json.loads(result_bytes.decode("utf-8"))
    content = result_json.get("content", [])
    if content and len(content) > 0:
        return {"answer": content[0].get("text", "")}
    return {"answer": "No response generated"}

