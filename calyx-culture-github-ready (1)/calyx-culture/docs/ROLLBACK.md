# Rollback plan

1. Original project is preserved: keep the uploaded `Clayxculture_Ptt1.zip` untouched; all changes are in Git-trackable files.
2. Before running ANY migration on a real Supabase project: Dashboard > Database > Backups (or `pg_dump`) and keep that dump.
3. The migration `20261116_01_security_hardening.sql` runs in one transaction; if any statement fails nothing is applied.
4. To undo after a successful run: restore the pre-migration dump into the project, or restore `supabase/schema.sql` policies/functions on a staging copy first and compare.
5. Edge functions: redeploy the previous versions of `sign-upload` and `sign-review-upload` from the original zip. NOTE: the new site files send the new signed fields, so roll back `site/` and the functions together.
6. The migration is only compatible with the NEW functions + site (review photos need `issue_review_upload`; old `sign-review-upload` will fail). Deploy order: migration, functions, then site.

Restoring a backup has NOT been tested by this work (see docs/AUDIT-REPORT.md).
