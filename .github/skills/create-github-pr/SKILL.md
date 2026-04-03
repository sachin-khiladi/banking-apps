---
name: create-github-pr
description: >
  Create GitHub pull requests safely with an upstream-first sync workflow,
  branch naming standards (`feat/` or `fix/`), clean local commits, and
  conflict-minimized PR creation. Use this skill whenever the task is to
  prepare a branch and open a PR on GitHub.
---

# GitHub PR Creation Skill

This skill standardizes PR creation for this repository to minimize branch drift,
conflicts, and low-signal pull requests.

## Scope

- Create/update branch for PR work
- Sync from upstream before local branch updates
- Create local commits with clear messages
- Push branch and open PR with meaningful metadata

## Mandatory Workflow (upstream first)

### 1) Discover current state

```bash
git branch --show-current
git remote -v
```

Expected remotes:
- `upstream` = canonical repository
- `origin` = user fork/working remote

If `upstream` is missing, add it before continuing.

### 2) Update upstream branch first

```bash
git fetch upstream --prune
git checkout main
git pull --ff-only upstream main
```

### 3) Update current working branch from updated upstream

- If original branch was `main`:
  - Create a new branch with prefix `feat/` or `fix/`
- If original branch was not `main`:
  - Rebase it on updated `main`

```bash
# case A: original branch == main
# choose one prefix based on intent
# feat/<short-kebab-scope> or fix/<short-kebab-scope>
git checkout -b feat/<scope>
# or
git checkout -b fix/<scope>

# case B: original branch != main
git checkout <current-branch>
git rebase main
```

Branch naming rules:
- Use only `feat/` or `fix/` prefixes
- Kebab-case remainder
- Keep short and descriptive

Examples:
- `feat/infra-first-cd-dependency`
- `fix/cd-yaml-indentation`

### 4) Apply changes and create local commit

```bash
git add -A
git commit -m "feat: <summary>"
# or
git commit -m "fix: <summary>"
```

Commit best practices:
- Use imperative mood
- Keep first line concise (< 72 chars when practical)
- Include body for context/risk where needed

### 5) Push branch

```bash
git push -u origin <branch-name>
```

### 6) Create PR

Preferred via GitHub CLI:

```bash
gh pr create \
  --base main \
  --head <branch-name> \
  --title "feat: <clear title>" \
  --body-file <pr-body-file.md>
```

## PR Body Minimum Quality

Include sections:
- Summary
- Why/Context
- Changes
- Validation (commands run + outcomes)
- Risks and rollback notes

## Conflict Handling

If rebase conflicts occur:
1. Stop and list conflicted files.
2. Resolve conflicts deliberately.
3. Continue rebase.

```bash
git status
git add <resolved-files>
git rebase --continue
```

Do not force-push unless explicitly requested.

## Safety Constraints

- Never open PR directly from `main`
- Never skip upstream-first sync
- Never fabricate validation results
- Never bypass branch naming policy (`feat/` / `fix/`)
