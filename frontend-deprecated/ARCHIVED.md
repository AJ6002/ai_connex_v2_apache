# [ARCHIVED] Legacy Frontend (Deprecated)

> **Status:** RETIRED / ARCHIVED  
> **Archived Date:** 2026-08-23  
> **Replacement:** `web/` (Vite + React + TS clean-room UI)  
> **Authorized by:** User Directive  

---

## Notice to Developers & Automation

1. **DO NOT import from this directory** or reference `frontend-deprecated/` in any new package.
2. **DO NOT add this directory as a workspace dependency**.
3. All UI feature development, design token work, and route implementations must take place strictly within `web/`.
4. The CI build job for `frontend-deprecated/` has been neutered to a 5-second sentinel no-op to prevent resource waste and accidental build dependencies.
