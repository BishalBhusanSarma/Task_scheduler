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

## Workflow

```text
User request → FastAPI → Groq natural-language parsing → Structured task
             → Redis/RQ scheduled job → Worker → Email or SMS notification
```

## Next Steps

- Improve input validation and clarification handling.
- Strengthen reliability of scheduled job execution.
- Refine the end-to-end task creation and reminder workflow.
