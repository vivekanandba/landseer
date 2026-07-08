# PR review loop

The standard way changes land in Landseer: open a PR and keep it raised, then run a genuine
**reviewer ↔ dev** cycle until it is clean, and only then approve and merge. Never merge unreviewed
code and never commit product changes straight to `main`.

This procedure is designed to run end-to-end autonomously by an agent (Claude Code) or by hand.

> `gh` is installed at `~/.local/bin/gh`. If it is not on your PATH, prefix commands with
> `export PATH="$HOME/.local/bin:$PATH"`. Default merge method is **squash**.

## 0. Ensure a PR exists

- The change must be on a feature branch, not `main`.
- Commit outstanding work (include the repo's co-author/session trailers) and push the branch.
- If no PR is open, create one:

  ```bash
  gh pr create --base main --head <branch> \
    --title "<concise title>" \
    --body "<what changed + how it was verified (pytest/behave results)>"
  ```

## 1. Loop until a review pass is clean

Repeat the two hats below. Stop when a **reviewer** pass produces no actionable findings.

### Reviewer hat (be adversarial, not a rubber stamp)

- Read the diff: `gh pr diff <n>`.
- Look for correctness bugs, edge cases, security issues, missing tests, and simplifications.
  For a non-trivial diff, use the `/code-review` skill for rigor.
- Post findings on the PR, each with `file:line` and a concrete failure scenario:
  - Inline (preferred):
    ```bash
    gh api repos/{owner}/{repo}/pulls/<n>/comments \
      -f body="<finding>" -f commit_id="<sha>" -f path="<file>" -F line=<n> -f side=RIGHT
    ```
  - Or a single summary review: `gh pr review <n> --comment --body "<numbered findings>"`.

### Dev hat (resolve every finding)

- Fix each finding in code.
- Keep the suite green: from `backend/`, run `venv/bin/python -m pytest -q` and
  `venv/bin/python -m behave`.
- Commit per logical fix (reference the finding), then push.
- Reply on each thread noting what changed, and resolve it.

## 2. Approve and merge

```bash
gh pr review <n> --approve         # GitHub blocks approving your OWN PR; see below
gh pr merge <n> --squash --delete-branch
```

**Self-approval caveat:** when the reviewer is the PR author (same `gh` account), `--approve`
fails with "Can not approve your own pull request." In that case post a
`gh pr review <n> --comment --body "Review passed: <summary>"` instead and proceed to merge (the
repo owner may merge their own PR). Note this substitution to the user.

Do not merge while the suite is red or any raised finding is unresolved. After merging, confirm the
PR state is `MERGED` and report the URL, number of rounds, and findings resolved.
