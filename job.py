from zoneinfo import ZoneInfo
from datetime import datetime, timezone, timedelta
import json
from dotenv import load_dotenv
import resend
import requests
import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("resend_api_key")
groq_api_key = os.getenv("groq_api_key")
textbee_api_key = os.getenv("textbee_api_key")

def send_email(to_email, subject, body):
    r = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": to_email,
            "subject": subject,
            "html": f"<p>{body}</p>"}
            )
    print(f"Email sent to {to_email} with subject '{subject}' and body '{body}'")
    return {"message": "Email sent successfully"}


def send_message(recipients, message):

    res = requests.post(
    'https://api.textbee.dev/api/v1/gateway/send-sms',
    headers={'x-api-key': textbee_api_key},
    json={
        'deviceId': '6ac882b62597187c9ca7285e',
        'recipients': recipients,
        'message': message,},
        )
    print(f"Message sent to {recipients} with message '{message}'")
    return {"message": "Message sent successfully"}




pending_events = {}

client = OpenAI(
    api_key=groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)


def send_prompt(input_text, session_id):

    previous_data = pending_events.get(session_id)

    today = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S %Z")

    prmpt = f"""
    You are an event scheduling assistant.

    Previous event data:
    {json.dumps(previous_data) if previous_data else "None"}

    User's latest message:
    {input_text}

    Today's date and time: {today}

    Rules:
    1. Handle only ONE event per request.
    2. "event" must be "create", "update", or "delete".
    3. "description" must be brief and based only on user-provided details. But dont Add time or date in description. It should be a short description of the event.
    4. "timestamp" must be readable, in Asia/Kolkata timezone.
    5. "reminder_option" must be "SMS" or "Email". Default to "Email".
    6. If previous event data exists, preserve its correct fields and
       merge the user's latest reply with it.
    7. Never invent missing information.
    8. Required fields are "event", "description", and "timestamp".
    9. If information is missing, include "required" as an array of
       missing field names and preserve all available fields.
    10. Return ONLY a valid JSON object, without markdown or explanations.
    11. timestamp_iso will be the ISO format of timestamp. It will be used to schedule the event in the future. If the "timestamp" is missing, do not add anything in "timestamp_iso" as the two are dependent to each other and return incomplete response.

    Complete example:
    {{
        "event": "create",
        "description": "Team meeting",
        "timestamp_iso": "2026-10-11T10:00:00+05:30",
        "timestamp": "October 11, 2026 at 10:00 AM",
        "reminder_option": "Email"
    }}

    Incomplete example:
    {{
        "event": "create",
        "description": "Team meeting",
        "timestamp_iso": "2026-10-11T10:00:00+05:30",
        "reminder_option": "Email",
        "required": ["timestamp"]
    }}
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "user", "content": prmpt}
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    output_text = response.choices[0].message.content

    if not output_text:
        raise ValueError("Empty response from AI")

    data = json.loads(output_text)

    # Save incomplete event details
    if data.get("required"):
        pending_events[session_id] = data

        return {
            "status": "incomplete",
            "data": data,
        }

    # Clear pending event details if complete
    pending_events.pop(session_id, None)

    return {
        "status": "complete",
        "data": data,
    }