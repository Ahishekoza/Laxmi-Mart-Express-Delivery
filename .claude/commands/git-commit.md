---
description: Analyzes git changes, generates a commit message following Spendly commit conventions, commits after approval, and pushes only after explicit user approval.
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*)
---

Run the git commit workflow using the current repository changes.

If no changes are detected, stop immediately and say:

"No changes detected. Nothing to commit."

---

## Pre-flight Check

Before generating a commit message:

- Run `git status`
- Run `git diff` for unstaged changes
- Run `git diff --staged` for staged changes
- Combine all changes into a single review context

If both unstaged and staged diffs are empty, stop immediately and say:

"No changes detected. Nothing to commit."

---

## Step 1: Analyze Changes

Review all modified files and determine the commit scope.

### Backend Only

If only backend files or folders are modified, the commit message must start with:

```text
backend: <actual change>
```

### Frontend Only

If only frontend files or folders are modified, the commit message must start with:

```text
frontend: <actual change>
```

### Frontend and Backend

If both frontend and backend files are modified, the commit message must start with:

```text
frontend&backend: <actual change>
```

### Docs only

If only docs are changed or .md file is created or changed, then commit message must start with:

```text
docs: <actual change>
```

---

## Step 2: Generate Commit Message

Generate a concise commit message that:

- Clearly explains the actual change made
- Describes the functionality or behavior change
- Uses a single-line commit message
- Does not exceed 72 characters
- Avoids vague messages such as:
  - update code
  - bug fixes
  - misc changes
  - WIP
  - temporary changes

Examples:

```text
backend: add validation for duplicate invoices

frontend: improve dashboard loading experience

frontend&backend: add bulk customer import support

backend: prevent duplicate payment processing

frontend: simplify customer search filters
```

If unrelated changes are detected, recommend splitting them into multiple commits.

---

## Step 3: Show Commit Message

Display the generated commit message:

```text
Proposed Commit Message:
<generated commit message>
```

Then ask:

```text
Do you want me to create this commit? (yes/no)
```

Wait for explicit user approval.

Do not create the commit until approval is received.

---

## Step 4: Create Commit

After approval:

- Stage any required files
- Create the commit using the approved commit message

Report:

```text
Commit created successfully.
```

---

## Step 5: Ask for Push Approval

After the commit is successfully created, ask:

```text
Do you want me to push the commit to the remote repository? (yes/no)
```

Wait for explicit user approval.

Do not push until approval is received.

If approved:

- Run `git push`

Report:

```text
Changes pushed successfully.
```

If declined:

```text
Push skipped.
```

---

## Rules

- Always review `git diff` and `git diff --staged`
- Always generate the commit message from the actual changes
- ! important Always show the commit message before committing 
- Never commit without explicit user approval
- Never push without explicit user approval
- Commit messages must not exceed 72 characters
- Commit messages must explain the actual change
- Use `backend:` for backend-only changes
- Use `frontend:` for frontend-only changes
- Use `frontend&backend:` when both areas are modified
- Use `docs:` when only documentation or `.md` files are changed
- Suggest multiple commits when unrelated changes are detected
- Do not automatically commit or push changes