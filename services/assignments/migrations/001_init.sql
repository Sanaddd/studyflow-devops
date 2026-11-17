-- 001: initial schema of the assignments service (ported from the Assignment 1 SQLite table)
-- course_id refers to a course owned by the courses service. There is no FOREIGN KEY
-- because that table lives in another database, so the database does not enforce the link.
CREATE TABLE assignments (
    id INT IDENTITY(1,1) PRIMARY KEY,
    title NVARCHAR(200) NOT NULL,
    due_date DATE NOT NULL,
    priority NVARCHAR(20) NOT NULL,
    completed BIT NOT NULL DEFAULT 0,
    course_id INT NOT NULL
);

-- Written and rolled back by GET /health to prove the service can write
CREATE TABLE health_check (
    id INT IDENTITY(1,1) PRIMARY KEY,
    checked_at DATETIME2 NOT NULL
);
