import os
import re
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from uuid import uuid4
from typing import Optional

# Load environment variables FIRST
load_dotenv()

# Import Gemini library
import google.generativeai as genai

# Import local services
from services.ip_tools import check_ip_virustotal, check_ip_abuseipdb, check_domain_virustotal, check_url_virustotal
from services.hygiene import HYGIENE_QUESTIONS, score_hygiene, normalize_yes, normalize_no

# --- Configuration ---
GEN_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEN_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from your .env file")

genai.configure(api_key=GEN_API_KEY)
MODEL_NAME = "gemini-1.5-flash-latest"

# --- FastAPI App Setup ---
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


sessions = {}



# --- Regex Patterns for Entity Detection ---
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
URL_RE = re.compile(r"https?://[^\s]+")
DOMAIN_RE = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b")

# --- Helper Functions ---
def detect_entities(text: str) -> dict:
    ip = IP_RE.search(text)
    url = URL_RE.search(text)
    domain = DOMAIN_RE.search(text)
    if url and domain and domain.group(0) in url.group(0):
        domain = None
    return {"ip": ip.group(0) if ip else None, "url": url.group(0) if url else None, "domain": domain.group(0) if domain else None}

def call_gemini_system(user_text: str, system_prompt: str, evidence: Optional[str] = None) -> str:
    """Calls the Gemini API with error handling."""
    try:
        model = genai.GenerativeModel(model_name=MODEL_NAME)
        # System prompt ko user prompt ke sath prepend karo
        full_prompt = f"{system_prompt}\n\nUser: {user_text}"
        if evidence:
            full_prompt += f"\n\nHere is the evidence from my tools:\n{evidence}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"CRITICAL GEMINI API ERROR: {e}") 
        return "Sorry, I encountered an error while communicating with the AI model. Please try again later."

# --- System Prompts ---
CYBERSEC_SYSTEM_PROMPT = """You are CybVector, a professional and friendly cybersecurity analyst assistant developed by Hiyaa Malik and Praveen Pandey.
- Use Markdown for formatting: `###` for titles, `*` for lists, `**text**` for bolding.
- When analyzing threats, provide a concise verdict: **Safe/Not Malicious**, **Suspicious**, or **Malicious**, followed by 2-4 clear, actionable next steps.
- Keep your tone professional and helpful."""

CLARIFICATION_SYSTEM_PROMPT = """You are a helpful assistant. The user is in the middle of a quiz and has asked a clarifying question.
Your task is to:
1. Briefly answer the user's question.
2. After answering, gently re-ask the original quiz question, prompting for a 'yes' or 'no' response."""

# --- API Routes ---
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def api_chat(request: Request):
    data = await request.json()
    message = data.get("message", "").strip()
    session_id = data.get("session_id") or str(uuid4())
    session = sessions.setdefault(session_id, {"created": datetime.utcnow().isoformat(), "hygiene": {"active": False, "step": 0, "answers": []}})

    # --- Security Hygiene Check Flow ---
    lower_message = message.lower()
    hygiene_triggers = ["security hygiene", "check my security", "hygiene check"]
    
    if any(trigger in lower_message for trigger in hygiene_triggers) and not session["hygiene"]["active"]:
        session["hygiene"]["active"] = True
        session["hygiene"]["step"] = 0
        session["hygiene"]["answers"] = []
        first_question = HYGIENE_QUESTIONS[0]
        reply = f"Security Hygiene Check (1/{len(HYGIENE_QUESTIONS)}): {first_question}"
        return JSONResponse({"response": reply, "session_id": session_id})

    if session["hygiene"]["active"]:
        if normalize_yes(message) or normalize_no(message):
            # User gave a valid yes/no answer, so proceed with the quiz
            session["hygiene"]["answers"].append(message)
            session["hygiene"]["step"] += 1
            if session["hygiene"]["step"] < len(HYGIENE_QUESTIONS):
                next_question = HYGIENE_QUESTIONS[session["hygiene"]["step"]]
                reply = f"Question {session['hygiene']['step'] + 1}/{len(HYGIENE_QUESTIONS)}: {next_question}"
                return JSONResponse({"response": reply, "session_id": session_id})
            else:
                # Quiz is finished, score and summarize
                results = score_hygiene(session["hygiene"]["answers"])
                evidence = json.dumps(results, indent=2)
                user_prompt = "Summarize my security hygiene check results. Explain my score and weaknesses in a helpful, non-technical way."
                g_reply = call_gemini_system(user_prompt, CYBERSEC_SYSTEM_PROMPT, evidence)
                session["hygiene"]["active"] = False
                return JSONResponse({"response": g_reply, "session_id": session_id})
        else:
            # User asked a clarifying question, so answer it without advancing the quiz
            current_question = HYGIENE_QUESTIONS[session["hygiene"]["step"]]
            clarification_context = f"The user was asked: '{current_question}'. They responded with: '{message}'."
            g_reply = call_gemini_system(clarification_context, CLARIFICATION_SYSTEM_PROMPT)
            return JSONResponse({"response": g_reply, "session_id": session_id})

    # --- Threat Intelligence Flow ---
    entities = detect_entities(message)
    evidence_parts = []
    if entities.get("ip"):
        evidence_parts.extend([{"virustotal_ip_report": check_ip_virustotal(entities["ip"])}, {"abuseipdb_report": check_ip_abuseipdb(entities["ip"])}])
    if entities.get("url"):
        evidence_parts.append({"virustotal_url_report": check_url_virustotal(entities["url"])})
    elif entities.get("domain"):
        evidence_parts.append({"virustotal_domain_report": check_domain_virustotal(entities["domain"])})

    if evidence_parts:
        evidence = json.dumps(evidence_parts, indent=2)
        g_reply = call_gemini_system(message, CYBERSEC_SYSTEM_PROMPT, evidence)
        return JSONResponse({"response": g_reply, "session_id": session_id})

    # --- Default Flow ---
    g_reply = call_gemini_system(message, CYBERSEC_SYSTEM_PROMPT)
    return JSONResponse({"response": g_reply, "session_id": session_id})
