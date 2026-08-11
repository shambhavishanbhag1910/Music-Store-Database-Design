# Migration from the Existing Music-Store-Database-Design Repository

This package is intended to replace/extend the current database-only repository without losing its original intent.

## Keep from the current repository

- Business Requirements Document
- Existing logical and physical ERD assets if you want to preserve design history
- Existing data dictionary as a historical/source-design reference
- MIT license attribution

## Replace or upgrade

- replace the one-line README with this project's README
- replace the original schema with `sql/oltp/01_schema.sql`
- replace timestamp trigger logic with `sql/oltp/02_triggers.sql`
- use `03_reference_seed.sql` plus the synthetic generator instead of tiny manual seed data
- replace ad-hoc constraint inserts with automated unit/integration + DQ checks
- expand reporting from one query to the marts and analytics pack
- remove empty `main.ipynb` and empty `requirements.txt`

## Recommended Git history

Use a feature branch such as `production-data-platform`, commit the migration in logical stages, and merge through a pull request so an interviewer can see the evolution of the project.
