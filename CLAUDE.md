<!-- GSD:project-start source:PROJECT.md -->

## Project

**Biblio — Sistem Manajemen Perpustakaan**

A digital library management system that replaces a manual, error-prone spreadsheet process. Built with FastAPI (backend), React (frontend), and PostgreSQL (database), packaged for `docker-compose`. Two roles: **mahasiswa** (search the catalog, request loans, track due dates and fines) and **pustakawan** (manage the catalog, approve/reject loan requests, hand books over, process returns, track overdue loans and fines, view a dashboard). The UI follows the "Biblio" design system — a navy/cream academic aesthetic (Playfair Display + Inter) with 6 designed screens: login, book catalog, loan request form, librarian dashboard, member management, and loan history.

**Core Value:** The end-to-end loan lifecycle must work correctly: a mahasiswa can find a book and request to borrow it, a pustakawan can approve/reject and hand it over, and the system tracks the due date through to return — automatically calculating fines (Rp 1.000/day) and blocking the mahasiswa's account on late returns.

### Constraints

- **Tech stack**: FastAPI + React + PostgreSQL + Docker — fixed by the course PRD, not open for substitution
- **Timeline**: 4 weeks total, 4-person student team — favors a phased build that gets a working vertical slice early
- **Auth**: bcrypt password hashing, JWT sessions with 1-hour expiry (NF02)
- **Performance**: All API responses under 2 seconds under normal load (NF01)
- **Responsiveness**: React frontend must work at 375px width and up (NF03)
- **Schema language**: DB table/column names use Bahasa Indonesia, as specified in the PRD
- **Design system**: UI must follow the Biblio design system (colors, typography, spacing, component styles) defined in `docs/design/stitch_botanical_scholar_library/biblio_design_system/DESIGN.md`

<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->

## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
