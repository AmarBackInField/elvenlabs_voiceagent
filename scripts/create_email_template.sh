#!/usr/bin/env bash
# Create an email template via the API (server must be running on port 8000)

curl -s -X POST "http://localhost:8000/api/v1/email-templates" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "booking_confirmation",
    "description": "Send a confirmation email when the customer confirms an appointment or booking.",
    "subject_template": "Appointment Confirmed – {{name}}",
    "body_template": "Dear {{name}},\n\nYour appointment has been confirmed.\n\nDate: {{date}}\nTime: {{time}}\n\nWe look forward to seeing you.\n\nBest regards",
    "parameters": [
      {"name": "date", "description": "Appointment date", "required": true},
      {"name": "time", "description": "Appointment time", "required": true}
    ],
    "webhook_base_url": "http://localhost:8000/api/v1"
  }' | python3 -m json.tool
