-- 002: add an optional description to assignments.
-- The table already holds data on Azure. NOT NULL with a DEFAULT makes SQL Server fill
-- every existing row with '' in the same statement, so no row is lost or left NULL.
-- The constraint is named so a later migration can find and drop it if needed.
ALTER TABLE assignments
    ADD description NVARCHAR(500) NOT NULL
    CONSTRAINT DF_assignments_description DEFAULT '';
