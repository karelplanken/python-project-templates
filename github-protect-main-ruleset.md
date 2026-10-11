# GitHub `protect-main` ruleset

Branch protection for solo-maintained repos: nothing reaches `main` except
through a squash-merged pull request. Apply it to every repo generated from
these templates.

## Ruleset

**Settings → Rules → Rulesets → New ruleset → New branch ruleset**

| Setting | Value | Why |
|---|---|---|
| Ruleset name | `protect-main` | |
| Enforcement status | Active | |
| Bypass list | *empty* | Adding yourself would re-allow direct pushes to `main`. |
| Target branches | Add target → **Include default branch** | Survives a rename of `main`. |
| Restrict deletions | ✅ | `main` can't be deleted. |
| Block force pushes | ✅ | `main` history can't be rewritten. |
| Require linear history | ✅ | Matches the squash-merge workflow. |
| Require a pull request before merging | ✅ | Blocks direct commits and pushes to `main`. |
| ↳ Required approvals | **0** | GitHub won't let you approve your own PR; 1 would lock you out. |
| ↳ Dismiss stale approvals / code owner review / last-push approval | ☐ | Only relevant with other reviewers. |
| ↳ Require conversation resolution | ✅ (optional) | Useful if you leave yourself review notes. |
| ↳ Allowed merge methods | **Squash** only | Enforces the squash-merge convention. |
| Require status checks | ☐ until the repo has CI | Then add the CI job(s) as required checks. |
| Require signed commits | ☐ | Only once you sign your own commits (e.g. SSH signing). |

## Who can merge

Rulesets don't control who can merge; repo permissions do. Only people with
write access can merge PRs, so with no collaborators under
**Settings → Collaborators**, you're the only one who can. Others can still
open PRs from forks.

## Related repo settings

**Settings → General → Pull Requests**

- ☐ Allow merge commits
- ✅ Allow squash merging (default message: *Pull request title and description*)
- ☐ Allow rebase merging
- ✅ Automatically delete head branches

## Applying it with `gh` instead of the UI

Run from inside the repo's clone. Requires an authenticated `gh` with admin
rights on the repo.

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

# Ruleset
gh api -X POST "repos/$REPO/rulesets" --input - <<'EOF'
{
  "name": "protect-main",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "required_linear_history" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": true,
        "allowed_merge_methods": ["squash"]
      }
    }
  ]
}
EOF

# Repo merge settings
gh repo edit "$REPO" \
  --enable-merge-commit=false \
  --enable-rebase-merge=false \
  --enable-squash-merge \
  --delete-branch-on-merge
gh api -X PATCH "repos/$REPO" \
  -f squash_merge_commit_title=PR_TITLE \
  -f squash_merge_commit_message=PR_BODY
```

Check the result: `gh api "repos/$REPO/rulesets"`, or the Rulesets page.

## Day-to-day effect

- `git push origin main` is rejected — always branch, push, open a PR.
- Merge via the PR's **Squash and merge** button (or `gh pr merge --squash
  --delete-branch`), then locally:
  `git checkout main && git pull && git fetch --prune`.
