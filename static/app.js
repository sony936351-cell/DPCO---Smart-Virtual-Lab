// ========================================
// DPCO SMART VIRTUAL LAB - JAVASCRIPT
// ========================================

const $ = (id) => document.getElementById(id);

const MODULE_NAMES = {
    dashboard: "Dashboard",
    logic: "Digital Logic",
    adder: "Adder Circuits",
    binary: "Binary Playground",
    alu: "ALU Studio",
    memory: "Memory Lab",
    cache: "Cache Simulator",
    cpu: "CPU Explorer",
    quiz: "Knowledge Quiz",
    progress: "My Progress",
    account: "Student Account"
};

let currentStudent = null;
let quizQuestions = [];

// ========================================
// API HELPER
// ========================================

async function api(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            }
        });

        const responseText = await response.text();

        let data = {};

        try {
            data = responseText ? JSON.parse(responseText) : {};
        } catch {
            console.error("Server returned non-JSON response:", responseText);

            throw new Error(
                `Server error (${response.status}). Check your Flask server logs.`
            );
        }

        if (!response.ok) {
            throw new Error(
                data.error || `Request failed (${response.status}).`
            );
        }

        return data;

    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
}
function post(url, data = {}) {
    return api(url, {
        method: "POST",
        body: JSON.stringify(data)
    });
}
window.post = post;
// ========================================
// PAGE NAVIGATION
// ========================================

function openPage(page) {
    if (!MODULE_NAMES[page]) return;

    document.querySelectorAll(".page").forEach(element => {
        element.classList.remove("active");
    });

    document.querySelectorAll(".nav-link").forEach(element => {
        element.classList.remove("active");
    });

    const pageElement = $("page-" + page);

    if (pageElement) {
        pageElement.classList.add("active");
    }

    const navElement = document.querySelector(
        `.nav-link[data-page="${page}"]`
    );

    if (navElement) {
        navElement.classList.add("active");
    }

    $("pageHeading").textContent = MODULE_NAMES[page];
    $("breadcrumbPage").textContent = MODULE_NAMES[page];

    if (page !== "dashboard" && page !== "account") {
        saveProgress(page);
    }

    if (page === "memory") loadMemory();
    if (page === "progress") loadProgress();
    if (page === "cache") loadCacheLines();
}

document.querySelectorAll("[data-page]").forEach(button => {
    button.addEventListener("click", () => {
        openPage(button.dataset.page);
    });
});

document.querySelectorAll("[data-open]").forEach(button => {
    button.addEventListener("click", () => {
        openPage(button.dataset.open);
    });
});

$("accountButton").addEventListener("click", () => {
    openPage("account");
});

$("topAccountButton").addEventListener("click", () => {
    openPage("account");
});


// ========================================
// STUDENT ACCOUNT DISPLAY
// ========================================

function updateStudentUI(name) {
    currentStudent = name || null;

    const initial = name
        ? name.charAt(0).toUpperCase()
        : "S";

    $("sidebarAvatar").textContent = initial;
    $("topAccountButton").textContent = initial;

    $("sidebarName").textContent = name || "Guest Student";

    $("sidebarStatus").textContent = name
        ? "Signed in"
        : "Not signed in";

    $("accountState").textContent = name
        ? "Active"
        : "Guest";

    $("accountHint").textContent = name
        ? "Student account"
        : "Sign in to save progress";

    $("logoutButton").hidden = !name;
    $("loginForm").hidden = !!name;
    $("registerForm").hidden = !!name;

    if (name) {
        $("accountMessage").textContent =
            "Welcome, " + name + "! You are signed in.";
    }
}

async function checkLogin() {
    try {
        const data = await api("/api/me");

        updateStudentUI(
            data.logged_in ? data.name : null
        );

        if (data.logged_in) {
            await loadProgress();
        }
    } catch (error) {
        console.error(error);
    }
}


// ========================================
// ACCOUNT TABS
// ========================================

document.querySelectorAll("[data-account]").forEach(button => {
    button.addEventListener("click", () => {

        document.querySelectorAll(".account-tab").forEach(tab => {
            tab.classList.remove("active");
        });

        button.classList.add("active");

        const mode = button.dataset.account;

        $("loginForm").hidden = mode !== "login";
        $("registerForm").hidden = mode !== "register";

        showMessage("accountMessage", "");
    });
});


// ========================================
// STUDENT REGISTRATION
// ========================================

$("registerForm").addEventListener("submit", async event => {
    event.preventDefault();

    try {
        const data = await post("/api/register", {
            name: $("registerName").value.trim(),
            email: $("registerEmail").value.trim(),
            password: $("registerPassword").value
        });

        updateStudentUI(data.name);

        $("registerForm").reset();

        showMessage(
            "accountMessage",
            "Registration successful. Welcome!"
        );

        await loadProgress();

    } catch (error) {
        showError(error, "accountMessage");
    }
});


// ========================================
// STUDENT LOGIN
// ========================================

$("loginForm").addEventListener("submit", async event => {
    event.preventDefault();

    try {
        const data = await post("/api/login", {
            email: $("loginEmail").value.trim(),
            password: $("loginPassword").value
        });

        updateStudentUI(data.name);

        $("loginForm").reset();

        showMessage(
            "accountMessage",
            "You have signed in successfully."
        );

        await loadProgress();

    } catch (error) {
        showError(error, "accountMessage");
    }
});


// ========================================
// STUDENT LOGOUT
// ========================================

$("logoutButton").addEventListener("click", async () => {
    try {
        await post("/api/logout");

        updateStudentUI(null);

        showMessage(
            "accountMessage",
            "You have signed out."
        );

        $("completedCount").textContent = "0";
        $("progressPercent").textContent = "0%";

    } catch (error) {
        showError(error, "accountMessage");
    }
});


// ========================================
// SAVE LEARNING PROGRESS
// ========================================

async function saveProgress(page) {
    if (!currentStudent) return;

    try {
        await post(
            "/api/progress/" + encodeURIComponent(
                MODULE_NAMES[page]
            )
        );

        await loadProgress();

    } catch (error) {
        console.error("Progress error:", error);
    }
}


async function loadProgress() {
    if (!currentStudent) return;

    try {
        const data = await api("/api/progress");

        const completed = data.visited.length;

        const percentage = Math.round(
            completed / data.total * 100
        );

        $("completedCount").textContent = completed;
        $("progressPercent").textContent = percentage + "%";

        $("progressBar").style.width =
            percentage + "%";

        $("progressLabel").textContent =
            percentage + "% Completed";

        const completedModules = new Set(
            data.visited.map(item => item.module)
        );

        const modules = [
            "Digital Logic",
            "Adder Circuits",
            "Binary Playground",
            "ALU Studio",
            "Memory Lab",
            "Cache Simulator",
            "CPU Explorer",
            "Knowledge Quiz"
        ];

        $("progressList").innerHTML = modules.map(module => {
            const done = completedModules.has(module);

            return `
                <div class="progress-item ${done ? "done" : ""}">
                    ${done ? "✓" : "○"} ${module}
                    <span style="float:right">
                        ${done ? "Visited" : "Not visited"}
                    </span>
                </div>
            `;
        }).join("");

    } catch (error) {
        console.error(error);
    }
}


// ========================================
// DIGITAL LOGIC
// ========================================

$("logicGate").addEventListener("change", () => {
    $("logicBGroup").hidden =
        $("logicGate").value === "NOT";

    $("gateVisual").textContent =
        $("logicGate").value;
});

$("runLogic").addEventListener("click", async () => {
    try {
        const gate = $("logicGate").value;

        const data = await post("/api/logic", {
            gate,
            a: Number($("logicA").value),
            b: Number($("logicB").value)
        });

        $("logicOutput").textContent = data.output;
        $("gateVisual").textContent = gate;

        showMessage(
            "logicMessage",
            data.output === 1
                ? "HIGH signal: output is 1."
                : "LOW signal: output is 0."
        );

        if (data.truth_table.length) {
            const isNot = gate === "NOT";

            $("logicTableHead").innerHTML = `
                <tr>
                    <th>Input A</th>
                    ${isNot ? "" : "<th>Input B</th>"}
                    <th>Output</th>
                </tr>
            `;

            $("logicTableBody").innerHTML =
                data.truth_table.map(row => `
                    <tr>
                        <td>${row.a}</td>
                        ${isNot ? "" : `<td>${row.b}</td>`}
                        <td>${row.output}</td>
                    </tr>
                `).join("");
        }

    } catch (error) {
        showError(error, "logicMessage");
    }
});


// ========================================
// ADDER CIRCUITS
// ========================================

$("runAdder").addEventListener("click", async () => {
    try {
        const data = await post("/api/adder", {
            type: $("adderType").value,
            a: Number($("adderA").value),
            b: Number($("adderB").value)
        });

        $("adderSum").textContent = data.sum;
        $("adderCarry").textContent = data.carry;

    } catch (error) {
        alert(error.message);
    }
});


// ========================================
// BINARY CONVERTER
// ========================================

$("convertBinary").addEventListener("click", async () => {
    try {
        const data = await post("/api/binary", {
            number: Number($("binaryNumber").value),
            bits: Number($("binaryBits").value)
        });

        $("binaryResult").textContent = data.binary;
        $("decimalResult").textContent = data.decimal;
        $("hexResult").textContent = data.hexadecimal;
        $("octalResult").textContent = data.octal;

    } catch (error) {
        alert(error.message);
    }
});


// ========================================
// ALU STUDIO
// ========================================

$("runAlu").addEventListener("click", async () => {
    try {
        const data = await post("/api/alu", {
            operation: $("aluOperation").value,
            a: Number($("aluA").value),
            b: Number($("aluB").value),
            bits: Number($("aluBits").value)
        });

        $("aluResult").textContent =
            data.binary + " (" + data.result + ")";

        $("flagZero").textContent = data.zero;
        $("flagNegative").textContent = data.negative;
        $("flagCarry").textContent = data.carry;

    } catch (error) {
        alert(error.message);
    }
});


// ========================================
// MEMORY LAB
// ========================================

function renderMemory(cells) {
    $("memoryGrid").innerHTML = cells.map(cell => `
        <div class="memory-cell">
            <span>ADDR ${cell.address}</span>
            <strong>${cell.value}</strong>
        </div>
    `).join("");
}

async function loadMemory() {
    try {
        const data = await api("/api/memory");

        renderMemory(data.cells);

    } catch (error) {
        showError(error, "memoryMessage");
    }
}

$("memoryRead").addEventListener("click", async () => {
    try {
        const data = await post("/api/memory", {
            action: "read",
            address: Number($("memoryAddress").value)
        });

        renderMemory(data.cells);

        showMessage(
            "memoryMessage",
            "Read address " + data.result.address +
            ": value = " + data.result.value
        );

    } catch (error) {
        showError(error, "memoryMessage");
    }
});

$("memoryWrite").addEventListener("click", async () => {
    try {
        const data = await post("/api/memory", {
            action: "write",
            address: Number($("memoryAddress").value),
            value: Number($("memoryValue").value)
        });

        renderMemory(data.cells);

        showMessage(
            "memoryMessage",
            "Memory updated successfully."
        );

    } catch (error) {
        showError(error, "memoryMessage");
    }
});


// ========================================
// CACHE SIMULATOR
// ========================================

function renderCache(lines) {
    $("cacheLines").innerHTML = lines.map(line => `
        <div class="cache-cell">
            <span>CACHE LINE ${line.slot}</span>
            <strong>
                ${line.block === null ? "EMPTY" : "BLOCK " + line.block}
            </strong>
            <span>VALUE: ${line.value ?? "—"}</span>
        </div>
    `).join("");
}

async function loadCacheLines() {
    try {
        const data = await post("/api/cache", {
            address: 0,
            operation: "READ"
        });

        updateCacheStats(data);
    } catch (error) {
        console.error(error);
    }
}

function updateCacheStats(data) {
    $("cacheHits").textContent = data.stats.hits;
    $("cacheMisses").textContent = data.stats.misses;
    $("cacheRate").textContent = data.stats.hit_rate + "%";

    renderCache(data.lines);
}

$("runCache").addEventListener("click", async () => {
    try {
        const data = await post("/api/cache", {
            address: Number($("cacheAddress").value),
            operation: $("cacheOperation").value,
            value: Number($("cacheValue").value)
        });

        updateCacheStats(data);

        showMessage(
            "cacheMessage",
            data.result.hit
                ? "CACHE HIT — data found in cache."
                : "CACHE MISS — data loaded into cache."
        );

    } catch (error) {
        showError(error, "cacheMessage");
    }
});


// ========================================
// CPU EXPLORER
// ========================================

$("runCpu").addEventListener("click", async () => {
    try {
        const data = await post("/api/cpu", {
            program: $("cpuProgram").value
        });

        Object.entries(data.registers).forEach(
            ([register, value]) => {
                $("reg" + register).textContent = value;
            }
        );

        $("regACC").textContent = data.acc;
        $("regPC").textContent = data.pc;

        $("cpuLog").innerHTML = data.log.map(entry => `
            <tr>
                <td>${entry.pc}</td>
                <td>${entry.instruction}</td>
                <td>${entry.acc}</td>
            </tr>
        `).join("");

        if (!data.log.length) {
            $("cpuLog").innerHTML =
                "<tr><td colspan='3'>No instructions executed.</td></tr>";
        }

    } catch (error) {
        alert(error.message);
    }
});


// ========================================
// KNOWLEDGE QUIZ
// ========================================

$("loadQuiz").addEventListener("click", loadQuiz);

async function loadQuiz() {
    try {
        const topic = $("quizTopic").value;

        const data = await api(
            "/api/quiz?topic=" + encodeURIComponent(topic)
        );

        quizQuestions = data.questions;

        $("quizResult").hidden = true;

        $("quizQuestions").innerHTML =
            data.questions.map((question, index) => `
                <div class="quiz-question">
                    <h3>${index + 1}. ${question.question}</h3>

                    ${question.options.map((option, optionIndex) => `
                        <label class="quiz-option">
                            <input
                                type="radio"
                                name="question-${index}"
                                value="${optionIndex}"
                            >
                            ${option}
                        </label>
                    `).join("")}
                </div>
            `).join("");

        $("submitQuiz").hidden = false;

    } catch (error) {
        alert(error.message);
    }
}

$("submitQuiz").addEventListener("click", async () => {
    try {
        const answers = quizQuestions.map((question, index) => {
            const selected = document.querySelector(
                `input[name="question-${index}"]:checked`
            );

            return selected
                ? Number(selected.value)
                : -1;
        });

        if (answers.includes(-1)) {
            alert("Please answer every question.");
            return;
        }

        const data = await post("/api/quiz", {
            topic: $("quizTopic").value,
            answers
        });

        $("quizResult").hidden = false;

        $("quizResult").innerHTML = `
            <h3>Quiz Results</h3>
            <div class="result-value">${data.percentage}%</div>
            <p class="muted">
                You scored ${data.score} out of ${data.total}.
            </p>
            <div class="progress-track">
                <div class="progress-fill" style="width:${data.percentage}%"></div>
            </div>
            ${data.feedback.map((item, index) => `
                <div class="progress-item ${item.correct ? "done" : ""}">
                    <strong>${index + 1}. ${item.correct ? "Correct" : "Incorrect"}</strong>
                    <p>${item.explanation}</p>
                    <small>Correct answer: ${item.correct_answer}</small>
                </div>
            `).join("")}
        `;

        if (currentStudent) {
            await saveProgress("quiz");
        }

    } catch (error) {
        alert(error.message);
    }
});


// ========================================
// INITIALIZE APPLICATION
// ========================================

document.addEventListener("DOMContentLoaded", async () => {
    await checkLogin();

    $("logicBGroup").hidden =
        $("logicGate").value === "NOT";

    $("gateVisual").textContent =
        $("logicGate").value;

    await loadMemory();

    await loadQuiz();

    await loadProgressIfLoggedIn();
});

async function loadProgressIfLoggedIn() {
    if (currentStudent) {
        await loadProgress();
    }
}