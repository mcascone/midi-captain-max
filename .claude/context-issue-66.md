# Issue #66 Context - Deploy Script Fixes

## Status: Resolved (PEBCAK - user error confirmed)

## Summary
User reported deploy scripts failing on v1.5.0 download. After investigation and fixes, user confirmed v1.5.0 works fine as-is — original issue was likely user error.

## Commits on branch `claude/fix-issue-66-JipaU`

1. **6b23069** - Fix deploy scripts misidentifying STD10 as Mini6
   - Root cause: `detect_device()` in both `deploy-unix.sh` and `deploy-windows.ps1` checked for `Mini6` directory before `STD10`, and since STD10 bundles contain a `Mini6/` subdirectory, STD10 devices were misidentified as Mini6.
   - Fix: Reordered detection to check STD10 first (most specific match).
   - **Worth keeping** — this is a real bug regardless of the user's PEBCAK.

2. **4446766** - Fix fallback message: config.json may exist without device field
   - Improved error message in interactive prompt fallback when config.json exists but has no `device` field.
   - **Worth keeping** — better UX for edge cases.

3. **100924f** - Add early filesystem I/O check to deploy scripts
   - Adds a write/read/delete test at script start to catch permission or filesystem issues early.
   - **May not be necessary** — user confirmed things work fine. Kept as a safety net in case the issue resurfaces.

## Files Modified
- `deploy-unix.sh` — all three fixes
- `deploy-windows.ps1` — all three fixes

## Resolution
User confirmed existing v1.5.0 download works. No PR merged yet. Branch kept intact in case the issue resurfaces.
