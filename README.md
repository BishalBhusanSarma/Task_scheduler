# AI-Powered Task Scheduling and Reminder System

## Project Summary

Built a task scheduling API that turns natural-language requests into structured reminders and schedules email or SMS notifications for future delivery. The project began with an end-to-end email reminder delivered five seconds after scheduling, then grew to include AI-assisted request parsing and SMS support.

## Highlights

- Developed API endpoints with **FastAPI** to accept and process scheduling requests.
- Integrated **Groq AI** to extract event details, date and time, and notification preference from natural-language input.
- Added handling for incomplete requests that retains supplied event details while requesting missing information.
- Queued delayed notification jobs with **Redis** and **RQ**.
- Integrated **Resend** for email and **Textbee** for SMS delivery; email is the default notification method.
- Returned task status and scheduled job details from the API.

## Technology Stack

**Python · FastAPI · Redis · RQ · Groq · Resend · Textbee**

## Run Locally

### 1. Create the environment and install dependencies

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn redis rq resend requests openai python-dotenv
```

### 2. Configure API keys

Copy `.env.example` to `.env` and replace the placeholders with your real keys:

```bash
cp .env.example .env
```

The app needs `groq_api_key`, `resend_api_key`, and `textbee_api_key`. Email delivery also requires a sender address allowed by your Resend account. The current code uses `onboarding@resend.dev` as the sender.

### 3. Start Redis

On macOS with Homebrew:

```bash
brew services start redis
```

Or run `redis-server` in its own terminal and leave it running. The app connects to Redis at `localhost:6379`.

### 4. Start the RQ worker with scheduling enabled

In a second terminal, activate the same virtual environment and run:

```bash
source .venv/bin/activate
rq worker task_queue --with-scheduler
```

The API enqueues jobs on `task_queue`; the scheduler option is needed to promote `enqueue_at()` reminders when their scheduled time arrives. Keep this process running.

### 5. Start the API

In another terminal, from the project directory:

```bash
source .venv/bin/activate
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/docs` to try the `POST /send_prompt/` endpoint. It accepts `input_text` as a query parameter and an optional `session_id`.

The endpoint sends the task-created notification immediately and schedules the reminder for the parsed timestamp. Check the worker terminal at that time for delivery errors.

## Workflow

```text
User request → FastAPI → Groq natural-language parsing → Structured task
             → Redis/RQ scheduled job → Worker → Email or SMS notification
```

## Next Steps

- Improve input validation and clarification handling.
- Strengthen reliability of scheduled job execution.
- Refine the end-to-end task creation and reminder workflow.
