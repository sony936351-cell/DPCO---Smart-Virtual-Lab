# DPCO Smart Virtual Lab

An interactive Digital Principles and Computer Organization learning platform.

## Features

- Student registration and login
- Password hashing
- Digital logic gate simulator
- Half and full adder demonstrations
- Binary number converter
- ALU simulator
- Memory address visualization
- Cache simulator
- CPU instruction execution
- Knowledge quizzes
- Student learning progress
- Responsive dark dashboard

## Technology

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript

## Installation

Create a virtual environment:

    py -m venv .venv

Activate it on Windows:

    .\.venv\Scripts\Activate.ps1

Install dependencies:

    pip install -r requirements.txt

Run the application:

    python app.py

Open:

    http://127.0.0.1:5000

## Important

Before deploying publicly:

- Set a strong SECRET_KEY environment variable.
- Disable Flask debug mode.
- Use HTTPS.
- Use a production WSGI server.
- Add CSRF protection and login rate limiting.
- Configure database backups.
- Add password reset and email verification if required.

The memory and cache simulations currently run in server memory and reset when the server restarts.