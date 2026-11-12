import json

from fastapi import FastAPI
from pydantic import BaseModel
from redis import Redis
from rq import Queue
from datetime import datetime, timezone, timedelta
from job import send_email, send_message, send_prompt
import resend
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_conn = Redis(host='localhost', port=6379, db=0)
task_queue = Queue("task_queue", connection=redis_conn)


class SendMessageRequest(BaseModel):
    recipients: list[str]
    message: str
    sec: int



@app.get("/")
def read_root():
    return {"Status": "API is running"}

# @app.post("/send_email/")
# def create_job(to_email: str, subject: str, body: str, sec: int):
#     run_at = datetime.now(timezone.utc) + timedelta(seconds=sec)

#     job = task_queue.enqueue_at(run_at, send_email, to_email=to_email, subject=subject, body=body)

#     return {"job_id": job.id,
#             "run_at": run_at.isoformat()}


# @app.post("/send_message/")
# def create_message_job(request: SendMessageRequest):
#     run_at = datetime.now(timezone.utc) + timedelta(seconds=request.sec)

#     job = task_queue.enqueue_at(
#         run_at,
#         send_message,
#         recipients=request.recipients,
#         message=request.message,
#     )

#     return {"job_id": job.id,
#             "run_at": run_at.isoformat()}

@app.post("/send_prompt/")
def create_prompt_job(input_text: str, session_id: str = "b1"):

    res = send_prompt(input_text, session_id)
    run_at = datetime.fromisoformat(res['data'].get('timestamp_iso'))

    if res["status"] == "incomplete":
        return res

    if res["data"].get("reminder_option") == "SMS":
        sm = send_message(["+919999999999"], f"*Task Created*{res['data'].get('description')} is scheduled on {res['data'].get('timestamp')} and will send via {res['data'].get('reminder_option')}.")
        
        
        job_sms = task_queue.enqueue_at(
                    run_at,
                    send_message,
                    recipients=["+919999999999"],
                    message=f"*Reminder*\n{res['data'].get('description')} is scheduled on {res['data'].get('timestamp')} and will send via {res['data'].get('reminder_option')}.",
            )
        return {
            **res,
            "message": "Message sent successfully",
            "response": sm,
            "job_id": job_sms.id,
            "run_at": res['data'].get('timestamp_iso'),
        }
        
        
    else:
        job_email = task_queue.enqueue_at(
                    run_at,
                    send_email,
                    to_email="add_your_email@gmail.com",
                    subject=res["data"].get("description"),
                    body=f"*Reminder*\n{res['data'].get('description')} is scheduled on {res['data'].get('timestamp')} and will send via {res['data'].get('reminder_option')}.",
        sm = send_email("add_your_email@gmail.com", res["data"].get("description"), f"*Task Created* {res['data'].get('description')} is scheduled on {res['data'].get('timestamp')} and will send via {res['data'].get('reminder_option')}.")
            )
        return {
            **res,
            "message": "Email sent successfully",
            "response": sm,
            "job_id": job_email.id,
            "run_at": res['data'].get('timestamp_iso'),
        }

    
   
