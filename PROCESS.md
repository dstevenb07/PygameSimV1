# Ball Battles — Dev Process

For any agent picking this up: read SPEC.md and IMPLEMENTATION_PLAN.md first. This file covers the git workflow and how to test before merging to main.

---

## Branch Naming

Each phase gets its own branch, named by phase:

```
phase-2/hp-hud
phase-3/particles-shake
phase-4/sword-ball
... etc
```

Create from main, work on it, PR back to main when done. Never push directly to main.

---

## Per-Phase Workflow

```
1. Create branch from main:  phase-N/short-description
2. Run full confidence check (see shortconfidencechecklist.md if available)
3. Write code — one file at a time, test imports after each
4. Push to phase branch
5. Open PR to main
6. Test on pages-test (see below) — only if visual check is needed
7. User says "merge it" — merge PR to main
8. Start next phase
```

---

## Testing on pages-test

We have a live browser test URL via GitHub Pages + pygbag.

The `pages-test` branch is a persistent test branch. To push a build for browser testing:

```
1. Reset pages-test to main first, then merge the phase branch:
     git checkout pages-test
     git reset --hard origin/main
     git merge phase-N/your-branch
     git push origin pages-test --force
2. GitHub Actions auto-triggers on push to pages-test
3. Wait ~2 minutes for the Action to go green (Actions tab)
4. Open the Pages URL on your phone to test
5. Happy? Then merge the phase PR to main
```

**Why reset first:** pages-test accumulates its own merge history independently of main. Without the reset, touching the same files across phases will cause conflicts. pages-test is a throwaway test branch — force push is safe here.

**Pages URL:** check Settings → Pages in the repo for the live URL.

**If the Action fails:** check the Actions tab for the error log. Common causes:
- pygbag build error (Python syntax in game code)
- Pages environment protection rules (Settings → Environments → github-pages → ensure pages-test is in the allowed branches list)

**Deployment also triggers on push to main** — so every merge to main auto-updates the live URL.

---

## Merging

The agent can merge PRs directly — no need for the user to do it in the UI. User just says "merge it".

Always squash merge. Branch naming in the squash commit title should match the branch name.

---

## Local Git Hygiene

- `build/` is gitignored — never commit build artifacts
- `__pycache__/` is gitignored
- After pushing via MCP tools, sync local git: `git fetch origin && git checkout -f -b <branch> --track origin/<branch>`
- A stop hook checks for untracked files — if it fires, check `git status` and either commit or add to `.gitignore`

---

## What's on main

| File | Purpose |
|------|---------|
| `SPEC.md` | Full design spec — source of truth for all decisions |
| `IMPLEMENTATION_PLAN.md` | Phase-by-phase coding plan with method signatures |
| `PROCESS.md` | This file |
| `README.md` | Project overview and run instructions |
| `.github/workflows/deploy.yml` | Auto-deploys to Pages on push to main or pages-test |
| `constants.py` | All tunable values — no magic numbers anywhere else |
| `*.py` | Game source files (grows with each phase) |
