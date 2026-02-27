import logging
import sys,os

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from fastapi import FastAPI, Request
import litellm
from prompt_builder import *
litellm.ssl_verify = False
LIB = "ag_ui_adk"   # or "adk" if that's the logger prefix you want

# Handlers
console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler("app.log", mode="a")

fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
console_handler.setFormatter(fmt)
file_handler.setFormatter(fmt)

# 1) Remove handlers from root (important if basicConfig already ran elsewhere)
root = logging.getLogger()
root.handlers.clear()
root.setLevel(logging.WARNING)  # keep root quiet

# 2) Configure only your target logger
logger = logging.getLogger(LIB)
logger.setLevel(logging.DEBUG)

# 3) Avoid adding duplicates if this code runs more than once
logger.handlers.clear()

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# 4) Stop bubbling up to root
logger.propagate = False
greeting_card = """
[
  {{ "beginRendering": {{ "surfaceId": "default", "root": "root-column", "styles": {{ "primaryColor": "#FF0000", "font": "Roboto" }} }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "default",
    "components": [  
        {{ "id": "root", "component": {{ "Card": {{ "child": "content" }} }} }},
        {{ "id": "content", "component": {{ "Column: {{ "children": {{ "explicitList": [ "title", "greeting" ] }}, "distribution": "start", "alignment": "center"  }} }} }},  
        {{ "id": "title", "component": {{  "Text": {{ "text": {{ "literalString": "Greeting Card" }}, "usageHint": "h2"  }} }} }},  
        {{ "id": "greeting", "component": {{  "Text": {{ "text": {{ "literalString": "Hello! Wishing you a wonderful day!"}}, "usageHint": "body"  }} }} }}
        ]
    }} }},
  {{ "dataModelUpdate": {{
    "surfaceId": "default",
    "path": "/",
    "contents": [
      {{}}
    ]
  }} }}
]
"""

MODEL = os.getenv("OPENAI_MODEL_NAME", "openai/gpt-5-mini")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# 1. Force JSON mode at the model level
lite_llm_model = LiteLlm(
    model=MODEL, 
    api_key=OPENAI_API_KEY,
)

# 2. Refine instructions to ensure a single valid JSON object structure
agent = LlmAgent(
        name="Agent",
        model=lite_llm_model,
        instruction=f"""
        1. You are an helpful conversational agent.
        2. BUT when user ask for greetings you return ONLY the BELOW raw JSON object which is a list of A2UI messages as response nothing else:{greeting_card}
        3. The JSON MUST validate against the A2UI JSON SCHEMA provided below:
        ---BEGIN A2UI JSON SCHEMA---
        {A2UI_SCHEMA}
        ---END A2UI JSON SCHEMA---
        """,
    )
 
# Create ADK middleware agent instance
adk_agent = ADKAgent(
    adk_agent=agent,
    # app_name="orchestrator_app",
    app_name="agents",
    user_id="demo_user",
)
 
# Create FastAPI app
app = FastAPI(title="ADK Middleware Proverbs Agent")
 
# Add the ADK endpoint
# add_adk_fastapi_endpoint(app, adk_agent, path="/orchestrator")
add_adk_fastapi_endpoint(app, adk_agent, path="/agent")
 
if __name__ == "__main__":
    import os
    import uvicorn
 
    port = int(os.getenv("PORT", 9050))
    uvicorn.run(app, host="0.0.0.0", port=port)