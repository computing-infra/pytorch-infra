---
name: gitcode-issue-create
description: Guide creation of high-quality GitCode issues with duplicate search, templates, labels, dry-run preview, and GitCode CLI submission. Trigger when users want to file a bug, feature request, task, or issue on GitCode.
---

# gitcode-issue-create

Create a clear GitCode issue.

## Command Entry

Use `gitcode` for cross-platform instructions. Linux/macOS may use `gc`; Windows PowerShell should use `gitcode`.

## Workflow

1. Identify repository, issue type, title, and expected outcome.
2. Search existing issues before creating a duplicate.
3. Draft the issue body.
4. Check repository labels.
5. Preview with `--dry-run --json` when possible.
6. Create only after the user confirms the final content, unless the user explicitly asked to create directly.

## Duplicate Search

```bash
gitcode issue list -R owner/repo --state all --search "keyword" --json
gitcode issue list -R owner/repo --state open --search "keyword" --json
```

## Draft Templates

Bug:

```markdown
## Problem

## Reproduction
1.
2.

## Expected

## Actual

## Environment
- GitCode CLI:
- OS:
- Shell:

## Impact
```

Feature:

```markdown
## Background

## Proposal

## Acceptance Criteria
- [ ] ...

## Alternatives
```

## Create

```bash
gitcode label list -R owner/repo --json
gitcode issue create -R owner/repo --title "type(scope): summary" --body-file issue.md --dry-run --json
gitcode issue create -R owner/repo --title "type(scope): summary" --body-file issue.md --label bug,priority-medium --json
```

Advanced fields:

```bash
gitcode issue create -R owner/repo --title "Security report" --body-file issue.md --security-hole --json
gitcode issue create -R owner/repo --title "Feature" --body-file issue.md --issue-type "需求" --issue-severity "高" --json
```

## Rules

- Ask for the repository if it is missing.
- Search both open and closed issues.
- Use `--body-file` for multi-line bodies.
- Redact secrets from logs and issue bodies.
- Align labels with the repository's existing label set.
