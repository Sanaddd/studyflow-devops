# Architecture Decision Records

## 1. Use Python with Flask for the backend
Date: 2026-10-05
Status: Decided

Context: I needed a simple backend that I could build and understand properly. Since the app is quite small, I did not want to use something too complicated.

Decision: I decided to use Python with Flask for the backend.

Alternatives considered: I thought about Django, but it has a lot of built-in features that I do not really need for this project. I also looked at FastAPI, but Flask seemed simpler for the type of app I am making.

Consequences: Flask keeps the project simple and lightweight. The downside is that I have to organise things like the database and project structure myself.

## 3. Store courses in a simple SQLite table
Date: 2026-10-06
Status: Decided

Context: I needed a simple way to store course data that would work locally and also fit the assignment requirement to use SQLite.

Decision: I created one `courses` table with an id, course name, and course code. Each course gets its own automatically generated id.

Alternatives considered: I considered storing more fields such as lecturer name or classroom, but I left them out because they are not needed for the main purpose of the app.

Consequences: The table stays simple and easy to understand. It also gives each course a unique id that can be used when editing or deleting it.