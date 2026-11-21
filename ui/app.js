// StudyFlow UI: a static page that calls the two services over HTTP.
// The service addresses come from config.js (window.CONFIG).

const COURSES_URL = window.CONFIG.COURSES_URL;
const ASSIGNMENTS_URL = window.CONFIG.ASSIGNMENTS_URL;

// Give up on a request after this long, so a stopped service never leaves the page hanging
const REQUEST_TIMEOUT_MS = 5000;

const state = {
    courses: [],
    assignments: [],
    coursesError: null,
    assignmentsError: null
};

let calendarDate = new Date();

// ---------- HTTP ----------

async function api(url, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
        const response = await fetch(url, {
            ...options,
            headers: { "Content-Type": "application/json" },
            signal: controller.signal
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return response.status === 204 ? null : await response.json();
    } finally {
        clearTimeout(timer);
    }
}

// Load both lists independently: if one service is down, the other still shows
async function loadData() {
    const [courses, assignments] = await Promise.allSettled([
        api(`${COURSES_URL}/courses`),
        api(`${ASSIGNMENTS_URL}/assignments`)
    ]);

    state.coursesError = courses.status === "rejected" ? courses.reason : null;
    state.courses = courses.status === "fulfilled" ? courses.value : [];

    state.assignmentsError = assignments.status === "rejected" ? assignments.reason : null;
    state.assignments = assignments.status === "fulfilled" ? assignments.value : [];

    render();
}

// Run a change, then reload; a failure is shown instead of being lost
async function change(request) {
    try {
        await request();
    } catch (error) {
        alert(`The change could not be saved: ${error.message}`);
    }
    await loadData();
}

// ---------- Rendering helpers ----------

// Build an element without innerHTML, so text from the API is never parsed as HTML
function el(tag, props = {}, children = []) {
    const element = document.createElement(tag);
    Object.assign(element, props);
    for (const child of children) {
        element.append(child);
    }
    return element;
}

// The assignments service adds course_name by asking the courses service.
// It sends null when the courses service could not be reached.
function courseName(assignment) {
    return assignment.course_name ?? "Course unavailable";
}

function showNotice(id, message) {
    const notice = document.getElementById(id);
    notice.textContent = message || "";
    notice.hidden = !message;
}

// ---------- Rendering ----------

function render() {
    showNotice(
        "coursesNotice",
        state.coursesError && "Courses are unavailable right now. Assignments still work, but course names cannot be shown."
    );
    showNotice(
        "assignmentsNotice",
        state.assignmentsError && "Assignments are unavailable right now. Courses still work."
    );

    document.getElementById("courseCount").textContent =
        state.coursesError ? "–" : state.courses.length;
    document.getElementById("assignmentCount").textContent =
        state.assignmentsError ? "–" : state.assignments.length;

    renderAssignmentForm();
    renderCourseList();
    renderAssignmentList();
    renderCalendar();
}

function renderAssignmentForm() {
    const hasCourses = state.courses.length > 0;

    document.getElementById("assignmentForm").hidden = !hasCourses;
    document.getElementById("assignmentFormEmpty").hidden = hasCourses;

    const select = document.getElementById("course_id");
    select.replaceChildren(
        ...state.courses.map(course => el("option", { value: course.id, textContent: course.name }))
    );
}

function renderCourseList() {
    const list = document.getElementById("courseList");
    // While the service is down the notice explains it; "No courses yet" would be wrong
    document.getElementById("courseListEmpty").hidden =
        state.courses.length > 0 || Boolean(state.coursesError);

    list.replaceChildren(...state.courses.map(course => {
        const nameInput = el("input", { type: "text", value: course.name, required: true });
        const codeInput = el("input", { type: "text", value: course.code, required: true });

        const editForm = el("form", { className: "course-edit" }, [
            nameInput,
            codeInput,
            el("button", { type: "submit", className: "btn-secondary", textContent: "Save" })
        ]);

        editForm.addEventListener("submit", event => {
            event.preventDefault();
            change(() => api(`${COURSES_URL}/courses/${course.id}`, {
                method: "PUT",
                body: JSON.stringify({ name: nameInput.value, code: codeInput.value })
            }));
        });

        const deleteButton = el("button", { type: "button", className: "btn-danger", textContent: "Delete course" });
        deleteButton.addEventListener("click", () =>
            change(() => api(`${COURSES_URL}/courses/${course.id}`, { method: "DELETE" }))
        );

        return el("li", { className: "course-item" }, [
            editForm,
            el("div", { className: "course-actions" }, [deleteButton])
        ]);
    }));
}

function renderAssignmentList() {
    const list = document.getElementById("assignmentList");
    document.getElementById("assignmentListEmpty").hidden =
        state.assignments.length > 0 || Boolean(state.assignmentsError);

    list.replaceChildren(...state.assignments.map(assignment => {
        const priority = assignment.priority.toLowerCase();

        const badges = [
            el("span", { className: "badge", textContent: `Due ${assignment.due_date}` }),
            el("span", { className: `badge priority-${priority}`, textContent: `${assignment.priority} priority` })
        ];
        if (assignment.overdue) {
            badges.push(el("span", { className: "badge overdue", textContent: "Overdue" }));
        }
        if (assignment.completed) {
            badges.push(el("span", { className: "badge completed", textContent: "Completed" }));
        }

        const toggleButton = el("button", {
            type: "button",
            className: "btn-secondary",
            textContent: assignment.completed ? "Mark incomplete" : "Mark complete"
        });
        toggleButton.addEventListener("click", () =>
            change(() => api(`${ASSIGNMENTS_URL}/assignments/${assignment.id}/toggle`, { method: "POST" }))
        );

        const deleteButton = el("button", { type: "button", className: "btn-danger", textContent: "Delete" });
        deleteButton.addEventListener("click", () =>
            change(() => api(`${ASSIGNMENTS_URL}/assignments/${assignment.id}`, { method: "DELETE" }))
        );

        return el("li", {
            className: assignment.completed ? "assignment-item assignment-complete" : "assignment-item"
        }, [
            el("p", { className: "assignment-title", textContent: assignment.title }),
            el("p", { className: "assignment-course", textContent: courseName(assignment) }),
            el("div", { className: "assignment-meta" }, badges),
            el("div", { className: "assignment-actions" }, [toggleButton, deleteButton])
        ]);
    }));
}

function renderCalendar() {
    const calendarGrid = document.getElementById("calendarGrid");
    const year = calendarDate.getFullYear();
    const month = calendarDate.getMonth();

    document.getElementById("calendarTitle").textContent =
        calendarDate.toLocaleDateString("en-US", { month: "long", year: "numeric" });

    // Weeks start on Monday: getDay() is 0 for Sunday, so treat it as 7
    const startingDay = new Date(year, month, 1).getDay() || 7;
    const gridStart = new Date(year, month, 1 - (startingDay - 1));
    const today = new Date();

    const days = [];

    for (let i = 0; i < 42; i++) {
        const dayDate = new Date(gridStart);
        dayDate.setDate(gridStart.getDate() + i);

        const dateString = [
            dayDate.getFullYear(),
            String(dayDate.getMonth() + 1).padStart(2, "0"),
            String(dayDate.getDate()).padStart(2, "0")
        ].join("-");

        const day = el("div", { className: "calendar-day" });
        if (dayDate.getMonth() !== month) {
            day.classList.add("outside");
        }
        if (dayDate.toDateString() === today.toDateString()) {
            day.classList.add("today");
        }

        const events = el("div", { className: "calendar-events" },
            state.assignments
                .filter(assignment => assignment.due_date === dateString)
                .map(assignment => {
                    const event = el("div", {
                        className: "calendar-event",
                        textContent: `${assignment.title} · ${courseName(assignment)}`
                    });
                    if (assignment.completed) {
                        event.classList.add("event-complete");
                    } else if (assignment.overdue) {
                        event.classList.add("event-overdue");
                    }
                    return event;
                })
        );

        day.append(el("span", { className: "day-number", textContent: dayDate.getDate() }), events);
        days.push(day);
    }

    calendarGrid.replaceChildren(...days);
}

// ---------- Forms and controls ----------

// Fields are read by id: form.name and form.title would return the form's own properties
const field = id => document.getElementById(id).value;

document.getElementById("courseForm").addEventListener("submit", event => {
    event.preventDefault();
    change(() => api(`${COURSES_URL}/courses`, {
        method: "POST",
        body: JSON.stringify({ name: field("name"), code: field("code") })
    })).then(() => event.target.reset());
});

document.getElementById("assignmentForm").addEventListener("submit", event => {
    event.preventDefault();
    change(() => api(`${ASSIGNMENTS_URL}/assignments`, {
        method: "POST",
        body: JSON.stringify({
            title: field("title"),
            due_date: field("due_date"),
            priority: field("priority"),
            course_id: Number(field("course_id"))
        })
    })).then(() => event.target.reset());
});

document.getElementById("previousMonth").addEventListener("click", () => {
    calendarDate.setMonth(calendarDate.getMonth() - 1);
    renderCalendar();
});

document.getElementById("nextMonth").addEventListener("click", () => {
    calendarDate.setMonth(calendarDate.getMonth() + 1);
    renderCalendar();
});

loadData();
