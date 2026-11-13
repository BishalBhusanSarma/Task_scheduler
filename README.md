# AI Task Scheduling and Reminder API

This project accepts a natural-language event request, uses Groq to extract the event details, sends a task-created notification, and schedules a reminder email or SMS with Redis Queue (RQ).

## How it works

```text
Client
  │ POST /send_prompt/?input_text=...&session_id=...
  ▼
FastAPI (main.py)
  │ calls send_prompt()
  ▼
Groq chat completion (job.py)
  │ returns event, description, timestamp, reminder option
  ├── missing required details → API returns status=incomplete
  └── complete event
        ├── send task-created email/SMS immediately
        └── enqueue_at(timestamp_iso) on Redis queue "task_queue"
                         │
                         ▼
                RQ worker with scheduler
                         │ when due
                         ▼
                 send reminder email/SMS
```

### Request and response flow

1. A client sends text such as “Email me a reminder to call the dentist tomorrow at 10 AM.” The endpoint currently accepts `input_text` and `session_id` as query parameters.
2. `send_prompt()` in `job.py` sends the text, the current Asia/Kolkata time, and any saved incomplete event details to Groq. The model is asked to return JSON containing the event type, short description, readable timestamp, ISO timestamp, and `Email` or `SMS` preference.
3. If the model says required details are missing, the API returns an `incomplete` response and does not enqueue a reminder. The missing details are held in the Python process memory under `session_id`, so the follow-up must reach the same running API process.
4. For a complete event, `main.py` sends a confirmation notification immediately, then schedules a second notification for `timestamp_iso` using RQ's `enqueue_at()`.
5. The RQ worker listens on `task_queue`. With its scheduler enabled, it promotes due scheduled jobs to the queue and executes `send_email()` or `send_message()` from `job.py`.

Email is sent through Resend. SMS is sent through Textbee. The current API sends to the single `email` or `phone_number` configured in `.env`; recipients are not taken from the natural-language request.

## Requirements

- Python 3.10 or newer
- Redis server
- Groq API key
- Resend API key for email reminders
- Textbee API key and configured device for SMS reminders

## Run locally

Run each long-lived service in its own terminal, from the project directory.

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
pip install fastapi uvicorn redis rq resend requests openai python-dotenv
```

### 2. Configure environment variables

Copy the example file and edit `.env` with valid credentials and destination details:

```bash
cp .env.example .env
```

Set these values in `.env`:

```dotenv
groq_api_key=your_groq_api_key
resend_api_key=your_resend_api_key
textbee_api_key=your_textbee_api_key
phone_number=+15551234567
email=you@example.com
```

The email `from` address is currently hard-coded as `onboarding@resend.dev` in `job.py`. Resend may restrict this test sender to verified recipients; use a sender address permitted by your Resend account for production delivery.

### 3. Start Redis

On macOS with Homebrew:

```bash
brew services start redis
```

Alternatively, run `redis-server` in a terminal and leave it running. The application connects to `localhost:6379`, database 0.

### 4. Start an RQ worker

In another terminal, activate the virtual environment and start a worker on the queue used by the API:

```bash
source .venv/bin/activate
rq worker task_queue --with-scheduler
```

Keep this process running. For additional concurrent workers, run the same command in additional terminals. Workers process jobs one at a time each; RQ coordinates the scheduler for this queue.

### 5. Start the API

In another terminal:

```bash
source .venv/bin/activate
uvicorn main:app --reload
```

The API is available at <http://127.0.0.1:8000>. Use <http://127.0.0.1:8000/docs> to submit a request through Swagger UI, or call the endpoint directly:

```bash
curl -X POST --get \
  --data-urlencode 'input_text=Remind me to call the dentist tomorrow at 10 AM by email' \
  --data-urlencode 'session_id=demo' \
  http://127.0.0.1:8000/send_prompt/
```

The response includes the parsed event and, when scheduling succeeds, an RQ `job_id` and `run_at` timestamp. The task-created notification is sent immediately; the reminder notification is sent at the scheduled time.

## Troubleshooting

- **Connection refused at `localhost:6379`:** Start Redis and confirm it is listening on the host and port configured in `main.py`.
- **Worker shows no jobs:** Start it with the exact queue name `task_queue`, and use `--with-scheduler` for `enqueue_at()` jobs. The scheduled notification will not run until its scheduled time.
- **No email arrives:** Check the API and worker terminal output, verify `resend_api_key`, and confirm the configured sender and recipient are allowed by Resend.
- **No SMS arrives:** Check `textbee_api_key`, the Textbee device ID in `job.py`, and the configured `phone_number`.
- **Request returns `incomplete`:** Provide the missing event details in a follow-up using the same `session_id` and the same API process.

## Current implementation notes

- `pending_events` is a regular in-memory Python dictionary. Incomplete conversations are lost when the API restarts and are not shared between multiple API processes.
- Email and SMS delivery functions currently print a success message without checking the provider's response status. An API response that says a notification was sent does not guarantee provider acceptance or final delivery.
- The API parses the model's `timestamp_iso` with `datetime.fromisoformat()`. The model must return a valid ISO 8601 timestamp with a timezone offset for scheduling to work.
- The event field supports `create`, `update`, and `delete` in the prompt, but current endpoint logic schedules a notification for any complete response; it does not implement update/delete behavior.

## Technology

Python · FastAPI · Redis · RQ · Groq · Resend · Textbee
