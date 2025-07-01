# Copied from app.py for Vercel deployment
import os
from dotenv import load_dotenv
load_dotenv()
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.runnables.config import RunnableConfig
from email_utils import send_booking_email
import smtplib
from email.message import EmailMessage

# ... rest of your app.py code here ... 