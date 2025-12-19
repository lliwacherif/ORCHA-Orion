-- Migration: Create Admin Table for Dashboard
-- Run this script against your PostgreSQL database

-- Create admins table
CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on username for faster lookups
CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username);

-- Insert default admin user (password: admin)
-- The hash below is bcrypt hash of 'admin'
INSERT INTO admins (username, hashed_password, is_active)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.yMFEZXpGBK6BNW', TRUE)
ON CONFLICT (username) DO NOTHING;

-- Create a view for admin user stats (optimized query for dashboard)
CREATE OR REPLACE VIEW admin_user_stats AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.full_name,
    u.job_title,
    u.is_active,
    u.plan_type,
    u.created_at,
    COUNT(DISTINCT c.id) AS conversation_count,
    COUNT(DISTINCT cm.id) AS message_count,
    MAX(cm.created_at) AS last_activity
FROM users u
LEFT JOIN conversations c ON c.user_id = u.id AND c.is_active = TRUE
LEFT JOIN chat_messages cm ON cm.conversation_id = c.id
GROUP BY u.id, u.username, u.email, u.full_name, u.job_title, u.is_active, u.plan_type, u.created_at
ORDER BY u.created_at DESC;

-- Add trigger to update updated_at on admins table
CREATE OR REPLACE FUNCTION update_admin_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_admin_updated_at ON admins;
CREATE TRIGGER trigger_update_admin_updated_at
    BEFORE UPDATE ON admins
    FOR EACH ROW
    EXECUTE FUNCTION update_admin_updated_at();

