# JobPilot Database Schema

SQLite database used by the JobPilot API. All user-owned data is scoped by `user_id`; there is no shared profile or project table row between accounts.

**Database file:** `data/jobpilot.db` (configurable via `Settings.db_path`)

---

## Entity-relationship diagram

```mermaid
erDiagram
    users ||--|| profiles : "has one"
    users ||--o{ oauth_tokens : "has many"
    users ||--o{ search_runs : "owns"
    users ||--o{ job_packages : "owns"
    users ||--o{ job_applications : "owns"
    search_runs ||--o{ job_packages : "produces"
    job_packages ||--o{ job_applications : "tracks"

    users {
        INTEGER id PK
        TEXT email UK "NOT NULL UNIQUE"
        TEXT password_hash "NOT NULL"
        TIMESTAMP created_at
    }

    profiles {
        INTEGER user_id PK,FK "REFERENCES users(id) ON DELETE CASCADE"
        TEXT cv_filename
        TEXT cv_path
        TEXT cv_text "encrypted Fernet blob"
        TEXT skills "JSON array"
        TEXT skills_extraction_status "idle|pending|ready|failed"
        TEXT target_roles "JSON array"
        TEXT projects "JSON array of StoredProject"
        TIMESTAMP updated_at
    }

    oauth_tokens {
        INTEGER user_id PK,FK
        TEXT provider PK "google|github"
        TEXT email
        TEXT access_token "encrypted"
        TEXT refresh_token "encrypted, nullable"
        TIMESTAMP expires_at
    }

    search_runs {
        INTEGER id PK
        INTEGER user_id FK "NOT NULL"
        TEXT role
        TEXT platform
        TEXT status "default pending"
        TIMESTAMP created_at
    }

    job_packages {
        INTEGER id PK
        INTEGER user_id FK "NOT NULL"
        INTEGER run_id FK "nullable, SET NULL on delete"
        TIMESTAMP created_at
    }

    job_applications {
        INTEGER id PK
        INTEGER user_id FK "NOT NULL"
        INTEGER job_package_id FK "nullable, SET NULL on delete"
        TIMESTAMP created_at
    }
```

---

## Table summary

| Table | Purpose | User isolation |
|-------|---------|----------------|
| `users` | Account email + password hash | Primary identity |
| `profiles` | CV, skills, target roles, projects JSON | **1:1** with `users.id` via `user_id` PK |
| `oauth_tokens` | Google / GitHub tokens (encrypted) | Composite PK `(user_id, provider)` |
| `search_runs` | Job search batch runs | `user_id` FK on every row |
| `job_packages` | Scored job results per run | `user_id` FK on every row |
| `job_applications` | Sent / tracked applications | `user_id` FK on every row |

---

## `profiles.projects` JSON shape

Each element in the `projects` column is a `StoredProject` object:

```json
{
  "id": "uuid",
  "name": "JobPilot",
  "description": "5+ line technical summary (API + UI)",
  "source": "github",
  "repo_full_name": "user/repo",
  "readme_md": "# Full README at import time (server-only, not returned by API)"
}
```

| Field | In API response | Notes |
|-------|-----------------|-------|
| `id`, `name`, `description`, `source` | Yes | User-visible project card |
| `repo_full_name` | Yes (`repoFullName`) | GitHub repo identifier |
| `readme_md` | **No** | Stored for agents / CV tailoring; stripped in `ProfileResponse` |

`cv_text` in `profiles` is encrypted at rest. `readme_md` is stored in plain text inside the user's JSON blob (same row isolation as CV).

---

## Access pattern

```
JWT cookie → get_current_user() → user_id
    → SELECT ... FROM profiles WHERE user_id = ?
    → SELECT ... FROM oauth_tokens WHERE user_id = ? AND provider = ?
```

No API route queries profile or OAuth data without filtering on the authenticated `user_id`.

---

## Cascade deletes

Deleting a `users` row cascades to:

- `profiles`
- `oauth_tokens`
- `search_runs`
- `job_packages`
- `job_applications`

---

*Last updated: 2026-07-02 — includes GitHub `readme_md` storage per project.*
