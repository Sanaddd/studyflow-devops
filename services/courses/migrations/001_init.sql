-- 001: initial schema of the courses service (ported from the Assignment 1 SQLite table)
CREATE TABLE courses (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(200) NOT NULL,
    code NVARCHAR(50) NOT NULL
);

-- Written and rolled back by GET /health to prove the service can write
CREATE TABLE health_check (
    id INT IDENTITY(1,1) PRIMARY KEY,
    checked_at DATETIME2 NOT NULL
);
