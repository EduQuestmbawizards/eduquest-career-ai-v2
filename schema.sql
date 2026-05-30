-- Create the single consolidated table for all student and report data
CREATE TABLE IF NOT EXISTS career_students_data (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    full_name TEXT,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    city TEXT,
    country TEXT,
    nationality TEXT,
    education_level TEXT,
    field_of_study TEXT,
    target_university TEXT,
    target_country TEXT,
    target_field TEXT,
    raw_form_data JSONB,
    career_interest TEXT,
    generated_response TEXT,
    generated_html TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
