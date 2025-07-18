from fastapi import FastAPI, BackgroundTasks, HTTPException
import json
import asyncio
from test import main  

app = FastAPI()

async def run_facebook_tool(user_id_chat):
    await main(user_id_chat)

@app.post("/login")
async def login(data: dict, background_tasks: BackgroundTasks):
    user_id_chat = data.get("user_id_chat")
    with open("user_accounts.json", "r", encoding="utf-8") as f:
        accounts = json.load(f)
    account = next((acc for acc in accounts if acc["user_id_chat"] == user_id_chat), None)
    if not account:
        raise HTTPException(status_code=404, detail="User not found")
    background_tasks.add_task(run_facebook_tool, user_id_chat)
    return {"status": "tool_started", "user_id_chat": user_id_chat, "id_fb": account.get("facebook_username")}