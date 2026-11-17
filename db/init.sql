-- Local setup only: creates one database and one login per service.
-- Idempotent: safe to run on every `docker compose up`.
-- The passwords are sqlcmd variables passed with -v from .env, never stored here.
IF DB_ID('courses') IS NULL CREATE DATABASE courses;
IF DB_ID('assignments') IS NULL CREATE DATABASE assignments;
GO

IF SUSER_ID('courses_user') IS NULL
    CREATE LOGIN courses_user WITH PASSWORD = '$(COURSES_DB_PASSWORD)', CHECK_POLICY = OFF;
IF SUSER_ID('assignments_user') IS NULL
    CREATE LOGIN assignments_user WITH PASSWORD = '$(ASSIGNMENTS_DB_PASSWORD)', CHECK_POLICY = OFF;
GO

-- Each login is a user only in its own database, so it cannot open the other one.
-- db_ddladmin lets the service run its own migrations (CREATE/ALTER TABLE).
USE courses;
GO
IF USER_ID('courses_user') IS NULL CREATE USER courses_user FOR LOGIN courses_user;
ALTER ROLE db_ddladmin ADD MEMBER courses_user;
ALTER ROLE db_datareader ADD MEMBER courses_user;
ALTER ROLE db_datawriter ADD MEMBER courses_user;
GO

USE assignments;
GO
IF USER_ID('assignments_user') IS NULL CREATE USER assignments_user FOR LOGIN assignments_user;
ALTER ROLE db_ddladmin ADD MEMBER assignments_user;
ALTER ROLE db_datareader ADD MEMBER assignments_user;
ALTER ROLE db_datawriter ADD MEMBER assignments_user;
GO
