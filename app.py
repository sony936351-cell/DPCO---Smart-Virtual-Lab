import os
import sqlite3
from functools import wraps

from flask import Flask, jsonify, render_template, request, session
from werkzeug.security import generate_password_hash, check_password_hash

from logic_engine import (
    logic_gate,
    truth_table,
    binary_convert,
    adder,
    alu_operation,
    Memory,
    CacheSimulator,
    CPU
)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "students.db")
)

# Create the database directory if it does not exist.
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key-before-deployment"
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)


# ==========================================
# DATABASE
# ==========================================
def db():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def init_db():
    with db() as con:

        con.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                student_id INTEGER NOT NULL,
                module TEXT NOT NULL,
                visited_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(student_id, module),
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
        """)


# ==========================================
# LOGIN PROTECTION
# ==========================================

def login_required(fn):

    @wraps(fn)
    def wrapper(*args, **kwargs):

        if not session.get("student_id"):
            return jsonify({
                "error": "Please sign in to use this feature."
            }), 401

        return fn(*args, **kwargs)

    return wrapper


# ==========================================
# HOME PAGE
# ==========================================

@app.get("/")
def index():

    return render_template(
        "index.html",
        student=session.get("student_name")
    )


# ==========================================
# CURRENT STUDENT
# ==========================================

@app.get("/api/me")
def me():

    if session.get("student_id"):

        return jsonify({
            "logged_in": True,
            "name": session.get("student_name")
        })

    return jsonify({
        "logged_in": False
    })


# ==========================================
# STUDENT REGISTRATION
# ========================================
@app.post("/api/register")
def register():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            error="Invalid registration request."
        ), 400

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    # Validate student information
    if len(name) < 2:
        return jsonify(
            error="Enter your name (at least 2 characters)."
        ), 400

    if "@" not in email or len(email) > 180:
        return jsonify(
            error="Enter a valid email address."
        ), 400

    if len(password) < 8:
        return jsonify(
            error="Password must contain at least 8 characters."
        ), 400

    try:
        with db() as con:

            # Check whether the email already exists
            existing_student = con.execute(
                "SELECT id FROM students WHERE email = ?",
                (email,)
            ).fetchone()

            if existing_student:
                return jsonify(
                    error="This email is already registered. Please sign in."
                ), 409

            # Create student account
            cursor = con.execute(
                """
                INSERT INTO students
                (name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (
                    name,
                    email,
                    generate_password_hash(password)
                )
            )

            student_id = cursor.lastrowid

        # Log student in after successful registration
        session.clear()
        session["student_id"] = student_id
        session["student_name"] = name

        app.logger.info(
            "Student registration successful."
        )

        return jsonify({
            "success": True,
            "message": "Registration successful!",
            "name": name
        }), 201

    except sqlite3.IntegrityError:
        app.logger.exception("Registration database integrity error")

        return jsonify({
            "success": False,
            "error": "This email is already registered. Please sign in."
        }), 409

    except Exception:
        app.logger.exception("Unexpected student registration error")

        return jsonify({
            "success": False,
            "error": "Registration failed because of a server error. Please try again."
        }), 500          


# ==========================================
# STUDENT LOGIN
# ==========================================

@app.post("/api/login")
def login():

    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    with db() as con:

        student = con.execute(
            "SELECT * FROM students WHERE email = ?",
            (email,)
        ).fetchone()

    if not student or not check_password_hash(
        student["password_hash"],
        password
    ):

        return jsonify(
            error="Incorrect email or password."
        ), 401

    session["student_id"] = student["id"]
    session["student_name"] = student["name"]

    return jsonify({
        "message": "Signed in successfully.",
        "name": student["name"]
    })


# ==========================================
# STUDENT LOGOUT
# ==========================================

@app.post("/api/logout")
def logout():

    session.clear()

    return jsonify({
        "message": "Signed out."
    })


# ==========================================
# DIGITAL LOGIC GATES
# ==========================================

@app.post("/api/logic")
def logic_api():

    data = request.get_json(silent=True) or {}

    try:

        gate = str(data.get("gate", "AND")).upper()

        a = int(data.get("a", 0))

        b = None if gate == "NOT" else int(
            data.get("b", 0)
        )

        return jsonify(
            gate=gate,
            a=a,
            b=b,
            output=logic_gate(gate, a, b),
            truth_table=truth_table(gate)
        )

    except (ValueError, TypeError) as error:

        return jsonify(
            error=str(error)
        ), 400


# ==========================================
# ADDER CIRCUITS
# ==========================================

@app.post("/api/adder")
def adder_api():

    data = request.get_json(silent=True) or {}

    try:

        result = adder(
            int(data.get("a", 0)),
            int(data.get("b", 0)),
            str(data.get("type", "half")).lower()
        )

        return jsonify(result)

    except (ValueError, TypeError) as error:

        return jsonify(
            error=str(error)
        ), 400


# ==========================================
# BINARY CONVERTER
# ==========================================

@app.post("/api/binary")
def binary_api():

    data = request.get_json(silent=True) or {}

    try:

        result = binary_convert(
            int(data.get("number", 0)),
            int(data.get("bits", 8))
        )

        return jsonify(result)

    except (ValueError, TypeError) as error:

        return jsonify(
            error=str(error)
        ), 400


# ==========================================
# ALU SIMULATOR
# ==========================================

@app.post("/api/alu")
def alu_api():

    data = request.get_json(silent=True) or {}

    try:

        result = alu_operation(
            str(data.get("operation", "ADD")),
            int(data.get("a", 0)),
            int(data.get("b", 0)),
            int(data.get("bits", 8))
        )

        return jsonify(result)

    except (ValueError, TypeError) as error:

        return jsonify(
            error=str(error)
        ), 400


# ==========================================
# MEMORY LAB
# ==========================================

MEMORY = Memory(16)


@app.get("/api/memory")
def memory_get():

    return jsonify(
        cells=MEMORY.dump()
    )


@app.post("/api/memory")
def memory_api():

    data = request.get_json(silent=True) or {}

    try:

        address = int(data.get("address", 0))

        action = data.get("action", "read")

        if action == "write":

            value = int(data.get("value", 0))

            MEMORY.write(address, value)

        elif action != "read":

            raise ValueError(
                "Action must be read or write."
            )

        result = MEMORY.read(address)

        return jsonify(
            result=result,
            cells=MEMORY.dump()
        )

    except (ValueError, TypeError) as error:

        return jsonify(
            error=str(error)
        ), 400


# ==========================================
# CACHE SIMULATOR
# ==========================================

CACHE = CacheSimulator(
    lines=4,
    block_size=1
)


@app.post("/api/cache")
def cache_api():

    data = request.get_json(silent=True) or {}

    try:

        address = int(data.get("address", 0))

        operation = str(
            data.get("operation", "READ")
        ).upper()

        value = int(data.get("value", 0))

        result = CACHE.access(
            address,
            operation,
            value
        )

        return jsonify(
            result=result,
            stats=CACHE.stats(),
            lines=CACHE.dump()
        )

    except (ValueError, TypeError) as error:

        return jsonify(
            error=str(error)
        ), 400


# ==========================================
# CPU EXPLORER
# ==========================================

@app.post("/api/cpu")
def cpu_api():

    data = request.get_json(silent=True) or {}

    try:

        program = str(
            data.get("program", "")
        )

        result = CPU().run_text(program)

        return jsonify(result)

    except (ValueError, TypeError) as error:

        return jsonify(
            error=str(error)
        ), 400


# ==========================================
# KNOWLEDGE QUIZ
# ==========================================

QUIZZES = {

    "Digital Logic": [

        (
            "Which gate outputs 1 only when both inputs are 1?",
            ["AND", "OR", "XOR", "NOR"],
            0,
            "AND is 1 only for inputs 1 and 1."
        ),

        (
            "What is the output of NOT 0?",
            ["0", "1", "10", "Undefined"],
            1,
            "NOT reverses its single input."
        ),

        (
            "Which gate is called an inverter?",
            ["OR", "NAND", "NOT", "XOR"],
            2,
            "A NOT gate inverts its input."
        )

    ],

    "Number Systems": [

        (
            "Binary 1010 equals which decimal value?",
            ["8", "9", "10", "12"],
            2,
            "1010₂ = 8 + 2 = 10."
        ),

        (
            "How many bits are in one byte?",
            ["4", "8", "16", "32"],
            1,
            "One byte contains eight bits."
        )

    ],

    "Computer Organization": [

        (
            "Which register stores the next instruction address?",
            ["ACC", "PC", "IR", "MAR"],
            1,
            "The Program Counter stores the next instruction address."
        ),

        (
            "Which unit performs arithmetic and logic?",
            ["ALU", "RAM", "CU", "ROM"],
            0,
            "The Arithmetic Logic Unit performs arithmetic and logic."
        )

    ]

}


@app.get("/api/quiz")
def quiz_get():

    topic = request.args.get(
        "topic",
        "Digital Logic"
    )

    questions = QUIZZES.get(topic)

    if not questions:

        return jsonify(
            error="Unknown quiz topic."
        ), 404

    return jsonify(
        topic=topic,
        questions=[
            {
                "question": question,
                "options": options
            }
            for question, options, _, _ in questions
        ]
    )


@app.post("/api/quiz")
def quiz_post():

    data = request.get_json(silent=True) or {}

    topic = data.get(
        "topic",
        "Digital Logic"
    )

    answers = data.get(
        "answers",
        []
    )

    questions = QUIZZES.get(topic)

    if (
        not questions
        or not isinstance(answers, list)
        or len(answers) != len(questions)
    ):

        return jsonify(
            error="Submit one answer for every question."
        ), 400

    feedback = []

    score = 0

    for index, (
        question,
        options,
        correct,
        explanation
    ) in enumerate(questions):

        is_correct = (
            isinstance(answers[index], int)
            and answers[index] == correct
        )

        score += int(is_correct)

        feedback.append({

            "question": question,

            "correct": is_correct,

            "correct_answer": options[correct],

            "explanation": explanation

        })

    return jsonify(

        score=score,

        total=len(questions),

        percentage=round(
            score / len(questions) * 100
        ),

        feedback=feedback

    )


# ==========================================
# STUDENT LEARNING PROGRESS
# ==========================================

@app.post("/api/progress/<module>")
@login_required
def mark_progress(module):

    allowed = {

        "Digital Logic",
        "Adder Circuits",
        "Binary Playground",
        "ALU Studio",
        "Memory Lab",
        "Cache Simulator",
        "CPU Explorer",
        "Knowledge Quiz"

    }

    if module not in allowed:

        return jsonify(
            error="Unknown module."
        ), 404

    with db() as con:

        con.execute(

            """
            INSERT OR REPLACE INTO progress
            (student_id, module, visited_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,

            (
                session["student_id"],
                module
            )

        )

    return jsonify(
        message="Progress saved."
    )


@app.get("/api/progress")
@login_required
def get_progress():

    with db() as con:

        rows = con.execute(

            """
            SELECT module, visited_at
            FROM progress
            WHERE student_id = ?
            ORDER BY visited_at DESC
            """,

            (session["student_id"],)

        ).fetchall()

    return jsonify(

        visited=[
            dict(row)
            for row in rows
        ],

        total=8

    )


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

init_db()


# ==========================================
# START APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )