---
description: Create a spec file and feature branch for the next Laxmi Mart Express step
argument-hint: "Folder, step number and feature name e.g. backend 2 registration"
allowed-tools: Read, Write, Glob, Bash(git:*)
---

You are a senior developer spinning up a new feature for Laxmi Mart Express.

Always follow the rules in CLAUDE.md.

Refer to the feature name/title for finding the appropriate section from CLAUDE.md.

Also check whether the user wants Claude to refer to any existing specification document from the specs folder before creating a new spec.

User input: $ARGUMENTS

## Step 1 — Check working directory is clean

Run `git status` and check for uncommitted, unstaged, or untracked files.

If any exist, stop immediately and tell the user to commit or stash changes before proceeding.

DO NOT CONTINUE until the working directory is clean.

## Step 2 — Parse the arguments

From $ARGUMENTS extract:

1. `folder`
   - Parent folder where the spec file should be created.
   - Examples: `backend`, `frontend`
   - If not provided, ask the user.

2. `step_number`
   - Zero-padded to 2 digits:
   - `2 → 02`
   - `11 → 11`

3. `feature_title`
   - Human readable title in Title Case.
   - Examples:
     - Registration
     - Login and Logout

4. `feature_slug`
   - Git-safe and file-safe slug
   - Lowercase, kebab-case
   - Only a-z, 0-9 and -
   - Maximum 40 characters
   - Examples:
     - registration
     - login-logout

5. `branch_name`
   - Format:
     `<folder>/<feature_slug>`
   - Examples:
     - `backend/registration`
     - `frontend/login-logout`

If any of these values cannot be inferred from $ARGUMENTS, ask the user to clarify before proceeding.

Expected argument format:

```text
<folder> <step_number> <feature_title>
```

Examples:

```text
backend 2 registration
frontend 5 user profile
backend 11 inventory sync
```

## Step 3 — Check branch name is not taken

Run:

```bash
git branch
```

If `branch_name` already exists, append a numeric suffix:

```text
backend/registration-01
backend/registration-02
```

Use the first available name.

## Step 4 — Switch to main and pull latest

Run:

```bash
git checkout main
git pull origin main
```

## Step 5 — Create and switch to the feature branch

Run:

```bash
git checkout -b <branch_name>
```

## Step 6 — Research the codebase

Read these files before writing the spec:

- `CLAUDE.md`
- `app.py`
- `database/db.py`
- All files in `<folder>/.claude/specs/`

Requirements:

1. Check CLAUDE.md for roadmap, conventions and schema.
2. Check all existing specs in `<folder>/.claude/specs/` to avoid duplication.
3. Confirm the requested step is not already marked complete.
4. If already complete, warn the user and stop.

## Step 7 — Write the spec

Generate a spec document with this exact structure:

---

# Spec: <feature_title>

## Overview

One paragraph describing what this feature does and why it exists at this stage of the Laxmi Mart Express roadmap.

## Depends on

Which previous steps this feature requires to be complete.

## Routes

Every new route needed:

- `METHOD /path` — description — access level (public/logged-in)

If no new routes:

```text
No new routes.
```

## Database changes

Any new tables, columns, or constraints needed.

Always verify against `database/db.py` before writing this.

If none:

```text
No database changes.
```

## Templates

### Create

List new templates with their paths.

### Modify

List existing templates and required changes.

## Files to change

Every file that will be modified.

## Files to create

Every new file that will be created.

## New dependencies

Any new pip packages.

If none:

```text
No new dependencies.
```

## Rules for implementation

Always include:

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of done

A specific testable checklist.

Each item must be something that can be verified by running the application.

---

## Step 8 — Save the spec

Save to:

```text
<folder>/.claude/specs/<step_number>-<feature_slug>.md
```

Examples:

```text
backend/.claude/specs/02-registration.md
frontend/.claude/specs/05-user-profile.md
```

## Step 9 — Report to the user

Print a short summary in this exact format:

```text
Branch:    <branch_name>
Spec file: <folder>/.claude/specs/<step_number>-<feature_slug>.md
Title:     <feature_title>
```

Then tell the user:

```text
Review the spec at <folder>/.claude/specs/<step_number>-<feature_slug>.md
then enter Plan Mode with Shift+Tab twice to begin implementation.
```

Do not print the full spec in chat unless explicitly asked.