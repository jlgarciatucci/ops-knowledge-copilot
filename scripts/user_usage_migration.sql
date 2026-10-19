-- Run ONCE in the database before deploying the new backend.
ALTER TABLE query_logs ADD COLUMN IF NOT EXISTS user_email TEXT;
CREATE INDEX IF NOT EXISTS idx_query_logs_user_email_date
ON query_logs (user_email, created_at DESC);
-- Earlier anonymous records remain NULL; they are deliberately not attributed.
