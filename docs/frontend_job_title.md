# Frontend guide: user job title field

## Options (must match backend)
- Doctor
- Lawyer
- Engineer
- Accountant

## Sign-up form
- Add a required select/dropdown for `job_title` with the four exact options above.
- Keep the existing fields (`username`, `email`, `password`, `full_name` optional).
- Prevent submission until a job title is chosen.

### Request payload (POST `/api/v1/auth/register`)
```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "secret123",
  "full_name": "Alice Smith",
  "job_title": "Doctor"
}
```

### Success response shape
`/register`, `/login`, and `/me` now include `job_title`:
```json
{
  "access_token": "...",        // register/login only
  "token_type": "bearer",       // register/login only
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "full_name": "Alice Smith",
    "is_active": true,
    "plan_type": "free",
    "job_title": "Doctor",
    "created_at": "2025-12-18T09:00:00Z"
  }
}
```

## State handling
- Update your frontend user/session store type to include `job_title: string`.
- After register/login, persist `user.job_title` alongside the token.
- On app start, when calling `/api/v1/auth/me`, store the returned `job_title`.
- Existing users created before this change will come back as `"Engineer"` (backfill).

## Validation UX
- Only allow the four options; do not send free text.
- Show a clear error if the register API returns 400 (e.g., username/email already taken).
- Disable submit while the request is in flight; show a spinner/toast on success/fail.

## Display ideas
- Show the job title in the profile header/account menu.
- If you expose an edit profile UI later, keep the same four-option dropdown and reuse the value from `/me`.

## Notes
- No migration needs to be run from frontend; backend already expects `job_title`.
- If you add client-side form schemas (e.g., zod/yup), mirror the exact literals: `"Doctor" | "Lawyer" | "Engineer" | "Accountant"`.

