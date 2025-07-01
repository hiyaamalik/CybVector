# 🤖 AI Agent Matchmaking - Winniio

AI Agent Matchmaking is a lightweight backend service (FastAPI/Flask) that collects user data and facilitates intelligent matchmaking between users and internal agents or systems. This project is part of the **Winniio** initiative.

---

## 🚀 Features

- Collects user intent and personal info (domain, name, email, phone, etc.)
- Facilitates healthcare service bookings with a conversational AI chatbot
- Sends collected data to a centralized Google Sheet (optional)
- Automatically sends:
  - Confirmation email to the user
  - Notification email to the internal team or provider
- Easily configurable via `.env` for SMTP and other settings
- Modern, interactive frontend with booking forms and chat UI

---

## 🏗️ Architecture Overview

```
User (Web UI/Chatbot)
        │
        ▼
  FastAPI/Flask Backend
        │
 ┌──────┴─────────────┐
 │                    │
▼▼                  ▼▼
Email Utils      Google Sheets API (optional)
(SMTP)           (for logging)
```

- **Frontend:** Interactive chatbot UI (HTML/JS/CSS) for user onboarding, service search, and booking.
- **Backend:** FastAPI (or Flask) handles chat, booking, and email logic.
- **Email:** Uses SMTP to send confirmation and notification emails.
- **(Optional) Google Sheets:** Logs user data for analytics or CRM.

---

## 📂 Folder Structure

```
ai-agent-matchmaking/
│
├── app.py              # Main FastAPI/Flask application
├── email_utils.py      # Utility for sending emails
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (not included in repo)
├── static/             # Frontend static files (JS, CSS)
├── templates/          # HTML templates
├── test.py             # Testing and debugging script
└── README.md           # Project documentation
```

---

## 🛠️ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ai-agent-matchmaking.git
cd ai-agent-matchmaking
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables
Create a `.env` file in the root directory and add:
```env
EMAIL_SENDER=your_email@example.com
EMAIL_PASSWORD=your_email_password_or_app_token
PROVIDER_EMAIL=provider@example.com
GOOGLE_SHEET_API=https://your-google-sheet-endpoint.com  # (optional)
```
> ⚠️ Use application-specific passwords or tokens for Gmail or any secure provider.

### 4. Run the Server
For FastAPI:
```bash
uvicorn app:app --host 0.0.0.0 --port 7860
```
For Flask:
```bash
python app.py
```
Server will run on [http://127.0.0.1:7860/](http://127.0.0.1:7860/) (FastAPI) or [http://127.0.0.1:5000/](http://127.0.0.1:5000/) (Flask) by default.

---

## 📩 API Endpoint

### POST `/api/book`
Send a POST request with JSON payload:
```json
{
  "booking": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890",
    "service": "Lab Test",
    "date": "2025-08-07",
    "time": "10:00",
    "notes": "Any additional info"
  }
}
```
**Response:**
```json
{
  "provider_result": "✅ Email sent to provider: ...",
  "user_result": "✅ Confirmation email sent to user."
}
```

---

## 💬 Chatbot Booking Flow

- User searches for a service (e.g., "allergy test in Delhi").
- Providers are listed with a "Book Appointment" button.
- Clicking the button opens a booking form (name, email, phone, service, date, time, notes).
- On submission, emails are sent and confirmation is shown in the UI.

---

## 📧 Email Notifications

- **To User:** Confirmation of their booking.
- **To Provider:** Notification with all booking details.

> Make sure your email service allows SMTP access.

---

## 📦 Dependencies

- fastapi / flask
- python-dotenv
- smtplib
- email
- requests (if using Google Sheets API)

Install them using:
```bash
pip install -r requirements.txt
```

---

## 🧪 Testing

You can use `test.py` or Postman to test the `/api/book` endpoint.

---

## 🔒 Security Note

- Do **not** commit `.env` or any credentials.
- Always use encrypted environment variables in production.

---

## 🙌 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 📜 License

MIT

---

## 👨‍💻 Author

Developed by Praveen Pandey  
Feel free to reach out for collaborations or feedback!

--- 