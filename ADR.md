# Architecture Decision Records

## 1. Use Python with Flask for the backend
Date: 2026-10-05
Status: Decided

Context: I needed a simple backend that I could build and understand properly. Since the app is quite small, I did not want to use something too complicated.

Decision: I decided to use Python with Flask for the backend.

Alternatives considered: I thought about Django, but it has a lot of built-in features that I do not really need for this project. I also looked at FastAPI, but Flask seemed simpler for the type of app I am making.

Consequences: Flask keeps the project simple and lightweight. The downside is that I have to organise things like the database and project structure myself.

## 2. Keep courses and assignments as separate feature areas
Date: 2026-10-07
Status: Decided

Context: The assignment requires two backend feature domains that are separate enough to potentially become different services later.

Decision: I kept course management and assignment management in separate service files. Courses handle course data, while assignments handle assignment data and only use a course id to connect the two.

Alternatives considered: I considered putting all of the course and assignment logic in one file, but I rejected that because it would make the two parts of the app more dependent on each other and harder to separate later.

Consequences: The app is still one monolithic application, but the two areas are easier to understand and could be split into separate services later with less restructuring.

## 3. Store courses in a simple SQLite table
Date: 2026-10-06
Status: Decided

Context: I needed a simple way to store course data that would work locally and also fit the assignment requirement to use SQLite.

Decision: I created one `courses` table with an id, course name, and course code. Each course gets its own automatically generated id.

Alternatives considered: I considered storing more fields such as lecturer name or classroom, but I left them out because they are not needed for the main purpose of the app.

Consequences: The table stays simple and easy to understand. It also gives each course a unique id that can be used when editing or deleting it.