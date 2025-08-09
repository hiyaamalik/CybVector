import os
import re
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from uuid import uuid4
from typing import Optional

# Load environment variables from the .env file
load_dotenv()

# Import Gemini library
import google.generativeai as genai

# Import local services, including the new normalize_no function
from services.ip_tools import check_ip_virustotal, check_ip_abuseipdb, check_domain_virustotal, check_url_virustotal
from services.hygiene import HYGIENE_QUESTIONS, score_hygiene, normalize_yes, normalize_no

# --- Configuration ---
# Load the Gemini API key from the environment
GEN_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEN_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from your .env file")

# Configure the Gemini client
genai.configure(api_key=GEN_API_KEY)
# Use the 'flash' model for better speed and a more generous free-tier quota
MODEL_NAME = "gemini-1.5-flash-latest"

# --- FastAPI App Setup ---
app = FastAPI()

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the 'static' directory to serve CSS and JS files
app.mount("/static", StaticFiles(directory="static"), name="static")
# Point to the 'templates' directory for the index.html file
templates = Jinja2Templates(directory="templates")

# A simple in-memory dictionary to store session data
sessions = {}

# --- Regex Patterns for Entity Detection ---
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
URL_RE = re.compile(r"https?://[^\s]+")
DOMAIN_RE = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b")

# --- Helper Functions ---
def detect_entities(text: str) -> dict:
    """Detects IPs, URLs, and domains in a given text."""
    ip = IP_RE.search(text)
    url = URL_RE.search(text)
    domain = DOMAIN_RE.search(text)
    # Avoid detecting a domain if it's already part of a full URL
    if url and domain and domain.group(0) in url.group(0):
        domain = None
    return {"ip": ip.group(0) if ip else None, "url": url.group(0) if url else None, "domain": domain.group(0) if domain else None}

def call_gemini_system(user_text: str, system_prompt: str, evidence: Optional[str] = None) -> str:
    """Calls the Gemini API with error handling."""
    try:
        model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=system_prompt)
        full_prompt = user_text
        if evidence:
            full_prompt += f"\n\nHere is the evidence from my tools:\n{evidence}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        # Log the actual error to the server console for debugging
        print(f"CRITICAL GEMINI API ERROR: {e}") 
        # Return a user-friendly error message
        return "Sorry, I encountered an error while communicating with the AI model. Please try again later."

# --- System Prompts ---
CYBERSEC_SYSTEM_PROMPT = """You are CybVector, a professional and friendly cybersecurity analyst assistant. You are developed by Hiyaa Malik and Praveen Pandey. Your role is to help users with cybersecurity-related questions, provide threat intelligence, and assist with security hygiene checks.
- Always respond in a clear, concise manner.
- If the user asks about security hygiene, guide them through a series of yes/no questions.
- If the user provides an IP address, URL, or domain, check it against VirusTotal and AbuseIPDB.
- Use the provided evidence to inform your responses.
- When summarizing results, focus on actionable insights and next steps.
- Use Markdown for formatting, especially for titles (`###`), lists (`* item`), and bolding (`**text**`).
- When analyzing threats, provide a concise verdict: **Safe/Not Malicious**, **Suspicious**, or **Malicious**.
- List 2-4 clear, actionable next steps for the user.
- Keep your tone professional, helpful, and concise."""

# --- API Routes ---
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Serves the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def api_chat(request: Request):
    """Main endpoint for handling all chat messages."""
    data = await request.json()
    message = data.get("message", "").strip()
    session_id = data.get("session_id") or str(uuid4())

    # Retrieve or create a new session
    session = sessions.setdefault(session_id, {"created": datetime.utcnow().isoformat(), "hygiene": {"active": False, "step": 0, "answers": []}})

    # --- Security Hygiene Check Flow ---
    lower_message = message.lower()
    hygiene_triggers = ["security hygiene", "check my security", "hygiene check"]
    
    # Start the quiz if triggered
    if any(trigger in lower_message for trigger in hygiene_triggers) and not session["hygiene"]["active"]:
        session["hygiene"]["active"] = True
        session["hygiene"]["step"] = 0
        session["hygiene"]["answers"] = []
        first_question = HYGIENE_QUESTIONS[0]
        reply = f"Security Hygiene Check (1/{len(HYGIENE_QUESTIONS)}): {first_question}"
        return JSONResponse({"response": reply, "session_id": session_id})

    # Handle ongoing hygiene check
    if session["hygiene"]["active"]:
        # If the user gives a valid yes/no answer, proceed with the quiz
        if normalize_yes(message) or normalize_no(message):
            session["hygiene"]["answers"].append(message)
            session["hygiene"]["step"] += 1
            # If there are more questions, ask the next one
            if session["hygiene"]["step"] < len(HYGIENE_QUESTIONS):
                next_question = HYGIENE_QUESTIONS[session["hygiene"]["step"]]
                reply = f"Question {session['hygiene']['step'] + 1}/{len(HYGIENE_QUESTIONS)}: {next_question}"
                return JSONResponse({"response": reply, "session_id": session_id})
            # Otherwise, the quiz is over, so score and summarize
            else:
                results = score_hygiene(session["hygiene"]["answers"])
                evidence = json.dumps(results, indent=2)
                user_prompt = "Summarize my security hygiene check results based on this data. Explain my score and weaknesses in a helpful, non-technical way."
                g_reply = call_gemini_system(user_prompt, CYBERSEC_SYSTEM_PROMPT, evidence)
                session["hygiene"]["active"] = False  # End the quiz
                return JSONResponse({"response": g_reply, "session_id": session_id})
        # If the user asks a clarifying question instead of yes/no
        else:
            current_question = HYGIENE_QUESTIONS[session["hygiene"]["step"]]
            clarification_prompt = f"""The user was in a security quiz.
The quiz question was: "{current_question}"
Instead of 'yes' or 'no', the user asked: "{message}"

Your task is to briefly answer the user's question, and then gently re-ask the original quiz question, prompting for a 'yes' or 'no' response."""
            
            g_reply = call_gemini_system(user_text="", system_prompt=clarification_prompt)
            # Return the clarification but DO NOT advance the quiz step
            return JSONResponse({"response": g_reply, "session_id": session_id})

    # --- Threat Intelligence Flow ---
    entities = detect_entities(message)
    evidence_parts = []
    if entities.get("ip"):
        evidence_parts.extend([
            {"virustotal_ip_report": check_ip_virustotal(entities["ip"])}, 
            {"abuseipdb_report": check_ip_abuseipdb(entities["ip"])}
        ])
    if entities.get("url"):
        evidence_parts.append({"virustotal_url_report": check_url_virustotal(entities["url"])})
    elif entities.get("domain"):
        evidence_parts.append({"virustotal_domain_report": check_domain_virustotal(entities["domain"])})

    if evidence_parts:
        evidence = json.dumps(evidence_parts, indent=2)
        g_reply = call_gemini_system(message, CYBERSEC_SYSTEM_PROMPT, evidence)
        return JSONResponse({"response": g_reply, "session_id": session_id})

    # --- Default Flow ---
    # If no other flow was triggered, send the message to Gemini for a general response.
    g_reply = call_gemini_system(message, CYBERSEC_SYSTEM_PROMPT)
    return JSONResponse({"response": g_reply, "session_id": session_id})