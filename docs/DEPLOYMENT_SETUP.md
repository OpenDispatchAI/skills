# Skill Deployment Setup Guide

This guide walks through connecting the **skills** repository to the **web** project so that merged skills are automatically deployed.

## How It Works

```
Contributor opens PR ──> validate.yml runs ──> validates skill YAML
PR merged to main   ──> sync.yml runs    ──> calls webhook on web
Web receives webhook ──> clones skills repo ──> validates + upserts to DB ──> compiles static API files
```

Two GitHub Actions workflows handle this:

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| `validate.yml` | PR to `main` | Validates skill YAML against schema |
| `sync.yml` | Push to `main` | Validates, then calls the web webhook |

## Setup Steps

### 1. Generate a webhook secret

Pick a strong random string. Both repos must share the same value.

```bash
openssl rand -hex 32
```

Save the output — you'll use it in steps 2 and 3.

### 2. Configure the web project

In your deployed web environment (e.g. `.env.local`, Docker env, or hosting platform):

```env
WEBHOOK_SECRET=<the-secret-from-step-1>
SKILLS_REPO_URL=https://github.com/OpenDispatchAI/skills.git
```

- `WEBHOOK_SECRET` — must match the secret configured in the skills repo (step 3)
- `SKILLS_REPO_URL` — the HTTPS clone URL of this skills repository

The web server must have `git` installed (used by `GitClient` to shallow-clone the repo during sync).

### 3. Add secrets to the skills repository

Go to **GitHub > skills repo > Settings > Secrets and variables > Actions** and add:

| Secret | Value |
|--------|-------|
| `WEBHOOK_URL` | Full URL to the web webhook, e.g. `https://yourdomain.com/api/webhook/sync` |
| `WEBHOOK_SECRET` | The same secret from step 1 |

### 4. Verify the connection

You can test the webhook manually with curl:

```bash
curl -f -X POST https://yourdomain.com/api/webhook/sync \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: <your-secret>" \
  -d '{"commit_sha": "test", "commit_url": "", "action_run_url": null}'
```

Expected response on success:

```json
{"status": "success", "skill_count": 0, "error": null}
```

If there are no skills in the repo yet, `skill_count` will be `0`. Once skills are added and merged, the count reflects the total synced skills.

### 5. Test the full pipeline

1. Create a test skill branch in the skills repo
2. Add a valid `skills/test-skill/skill.yaml`
3. Open a PR — `validate.yml` should run and pass
4. Merge the PR — `sync.yml` should run, call the webhook, and the skill should appear in the web admin dashboard at `/admin/skills`

## Troubleshooting

### Webhook returns 401 Unauthorized

The `X-Webhook-Secret` header doesn't match the `WEBHOOK_SECRET` env var on the web side. Verify both values are identical.

### Webhook returns 422

Skill validation failed on the web side. Check the admin sync log at `/admin/sync-log` for the error message. This usually means the skills repo YAML passed the Python validation but failed the PHP validator — unlikely but possible if validators drift.

### Git clone fails during sync

The web server needs `git` installed and network access to clone from GitHub. For private repos, configure a deploy key or use an access token in the URL:

```env
SKILLS_REPO_URL=https://x-access-token:<GITHUB_TOKEN>@github.com/OpenDispatchAI/skills.git
```

### Sync works but API files are stale

Run `make compile` (or `bin/console app:compile`) to regenerate the static files in `public/api/v1/`.

## Manual Sync

You can trigger a sync without the webhook:

```bash
# Via CLI
docker compose exec php bin/console app:sync

# Via admin dashboard
# POST /admin/resync (requires admin login)
```
