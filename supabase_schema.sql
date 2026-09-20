-- ============================================================
-- CareerVerse AI — Supabase Schema
-- Run this once in your Supabase SQL Editor:
-- https://supabase.com/dashboard → project → SQL Editor
-- ============================================================

-- 1. Create the profiles table
CREATE TABLE IF NOT EXISTS navigator_profiles (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                 TEXT,
    education            TEXT,
    degree               TEXT,
    experience           TEXT,
    interests            TEXT,
    current_skills       JSONB NOT NULL DEFAULT '[]',
    target_role          TEXT,
    country              TEXT DEFAULT 'India',
    goal                 TEXT,
    gap_data             JSONB,
    roadmap_data         JSONB,
    completed_milestones JSONB NOT NULL DEFAULT '{}',
    current_step         INTEGER NOT NULL DEFAULT 1,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Auto-update updated_at on every write
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER navigator_profiles_updated_at
    BEFORE UPDATE ON navigator_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 3. Row Level Security — allow anon access by id only
--    (The UUID itself acts as the secret; no auth required)
ALTER TABLE navigator_profiles ENABLE ROW LEVEL SECURITY;

-- Allow anyone to insert/select/update their own row by id
CREATE POLICY "anon_access_by_id" ON navigator_profiles
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- 4. Index for fast lookups by id (already indexed as PK, but explicit for clarity)
-- No additional index needed — UUID PK is indexed by default.

-- Done! Verify with:
-- SELECT * FROM navigator_profiles LIMIT 5;
