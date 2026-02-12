-- ============================================================
-- CV GENERATOR SAAS - DATABASE SCHEMA
-- PostgreSQL 16+ with JSONB support
-- ============================================================

-- ============================================================
-- EXTENSION SETUP
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Recherche fuzzy

-- ============================================================
-- ENUMS
-- ============================================================
CREATE TYPE proficiency_level AS ENUM (
    'beginner', 'intermediate', 'advanced', 'expert', 'native'
);

CREATE TYPE section_type AS ENUM (
    'experience', 'education', 'skills', 'languages',
    'certifications', 'projects', 'volunteering',
    'publications', 'awards', 'custom'
);

CREATE TYPE resume_status AS ENUM (
    'draft', 'published', 'archived'
);

CREATE TYPE subscription_tier AS ENUM (
    'free', 'pro', 'enterprise'
);

-- ============================================================
-- TABLE: users
-- ============================================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_auth_id VARCHAR(255) UNIQUE NOT NULL,  -- Clerk/Auth0 ID
    email           VARCHAR(320) NOT NULL,           -- RFC 5321 max
    email_verified  BOOLEAN DEFAULT FALSE,
    display_name    VARCHAR(200),
    avatar_url      TEXT,
    locale          VARCHAR(10) DEFAULT 'en-US',     -- BCP 47
    timezone        VARCHAR(50) DEFAULT 'UTC',
    subscription    subscription_tier DEFAULT 'free',
    
    -- Audit
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ,
    deleted_at      TIMESTAMPTZ,                     -- Soft delete
    
    -- Constraints
    CONSTRAINT chk_email_format 
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_external_auth ON users(external_auth_id);
CREATE INDEX idx_users_deleted ON users(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================
-- TABLE: resumes (document principal)
-- ============================================================
CREATE TABLE resumes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Metadata
    title           VARCHAR(200) NOT NULL DEFAULT 'Untitled Resume',
    slug            VARCHAR(250) UNIQUE,
    status          resume_status DEFAULT 'draft',
    template_id     VARCHAR(100) NOT NULL DEFAULT 'modern',
    locale          VARCHAR(10) DEFAULT 'en-US',
    
    -- Theme Configuration (flexible JSON)
    theme_config    JSONB DEFAULT '{
        "primaryColor": "#2563EB",
        "fontFamily": "Inter",
        "fontSize": "medium",
        "spacing": "comfortable",
        "showPhoto": false
    }'::jsonb,
    
    -- Section Ordering (array of section IDs pour réorganisation)
    section_order   UUID[] DEFAULT '{}',
    
    -- Versioning
    version         INTEGER DEFAULT 1,
    
    -- Audit
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    published_at    TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT chk_version_positive CHECK (version > 0)
);

CREATE INDEX idx_resumes_user ON resumes(user_id);
CREATE INDEX idx_resumes_status ON resumes(status);
CREATE INDEX idx_resumes_template ON resumes(template_id);
CREATE INDEX idx_resumes_updated ON resumes(updated_at DESC);

-- ============================================================
-- TABLE: contact_info
-- ============================================================
CREATE TABLE contact_info (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resume_id       UUID UNIQUE NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    
    -- Identity
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    professional_title VARCHAR(200),
    
    -- Contact
    email           VARCHAR(320),
    phone_raw       VARCHAR(50),        -- Saisie brute utilisateur
    phone_e164      VARCHAR(20),        -- Format E.164 normalisé : +33612345678
    phone_country   CHAR(2),            -- ISO 3166-1 alpha-2 : FR, US, JP...
    
    -- Location (pas d'adresse complète pour RGPD)
    city            VARCHAR(100),
    region          VARCHAR(100),       -- État/Province
    country_code    CHAR(2),            -- ISO 3166-1
    postal_code     VARCHAR(20),
    
    -- Online Presence
    linkedin_url    TEXT,
    website_url     TEXT,
    github_url      TEXT,
    portfolio_url   TEXT,
    
    -- Extended (flexible)
    custom_links    JSONB DEFAULT '[]'::jsonb,
    -- Format: [{"label": "Twitter", "url": "...", "icon": "twitter"}]
    
    -- Photo
    photo_url       TEXT,
    
    -- Summary / Objective
    summary         TEXT,
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_contact_resume ON contact_info(resume_id);

-- ============================================================
-- TABLE: resume_sections (polymorphique via JSONB)
-- ============================================================
CREATE TABLE resume_sections (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resume_id       UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    
    -- Section Metadata
    type            section_type NOT NULL,
    title           VARCHAR(200),           -- Titre personnalisé (ex: "Expérience" → "Parcours")
    visible         BOOLEAN DEFAULT TRUE,
    sort_order      INTEGER DEFAULT 0,
    
    -- Content (polymorphique, structure varie selon `type`)
    content         JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- Audit
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT chk_content_array CHECK (jsonb_typeof(content) = 'array')
);

CREATE INDEX idx_sections_resume ON resume_sections(resume_id);
CREATE INDEX idx_sections_type ON resume_sections(type);
CREATE INDEX idx_sections_order ON resume_sections(resume_id, sort_order);

-- Index GIN pour recherche dans le contenu JSONB
CREATE INDEX idx_sections_content ON resume_sections USING GIN (content);

-- ============================================================
-- TABLE: templates (registre de templates)
-- ============================================================
CREATE TABLE templates (
    id              VARCHAR(100) PRIMARY KEY,   -- 'modern', 'classic', 'minimal'
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    thumbnail_url   TEXT,
    
    -- Config
    category        VARCHAR(50) DEFAULT 'general', -- 'general', 'creative', 'academic'
    is_premium      BOOLEAN DEFAULT FALSE,
    supported_locales VARCHAR(10)[] DEFAULT '{en-US}',
    
    -- Layout Definition
    layout_config   JSONB NOT NULL,
    -- Defines: column count, section placement rules, page break logic
    
    -- Constraints
    max_pages       INTEGER DEFAULT 2,
    supports_photo  BOOLEAN DEFAULT TRUE,
    
    -- Audit
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT TRUE,
    version         INTEGER DEFAULT 1
);

CREATE INDEX idx_templates_category ON templates(category);
CREATE INDEX idx_templates_active ON templates(is_active) WHERE is_active = TRUE;

-- ============================================================
-- TABLE: pdf_generations (audit trail)
-- ============================================================
CREATE TABLE pdf_generations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resume_id       UUID NOT NULL REFERENCES resumes(id),
    user_id         UUID NOT NULL REFERENCES users(id),
    
    -- Result
    file_url        TEXT,
    file_size_bytes BIGINT,
    page_count      INTEGER,
    generation_time_ms INTEGER,
    
    -- Metadata
    template_id     VARCHAR(100),
    locale          VARCHAR(10),
    ip_address      INET,
    user_agent      TEXT,
    
    -- Status
    status          VARCHAR(20) DEFAULT 'pending',  -- pending, success, failed
    error_message   TEXT,
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pdf_gen_user ON pdf_generations(user_id, created_at DESC);
CREATE INDEX idx_pdf_gen_resume ON pdf_generations(resume_id);
CREATE INDEX idx_pdf_gen_status ON pdf_generations(status);

-- ============================================================
-- TABLE: resume_versions (historique complet)
-- ============================================================
CREATE TABLE resume_versions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resume_id       UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    version         INTEGER NOT NULL,
    
    -- Snapshot complet
    snapshot        JSONB NOT NULL,
    
    -- Audit
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    created_by      UUID REFERENCES users(id),
    
    UNIQUE(resume_id, version)
);

CREATE INDEX idx_versions_resume ON resume_versions(resume_id, version DESC);

-- ============================================================
-- TRIGGERS - Auto update timestamps
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resumes_updated_at BEFORE UPDATE ON resumes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contact_info_updated_at BEFORE UPDATE ON contact_info
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resume_sections_updated_at BEFORE UPDATE ON resume_sections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- FUNCTIONS - Helper functions
-- ============================================================

-- Generate slug from title
CREATE OR REPLACE FUNCTION generate_resume_slug(p_title TEXT, p_user_id UUID)
RETURNS TEXT AS $$
DECLARE
    v_slug TEXT;
    v_counter INTEGER := 0;
    v_unique_slug TEXT;
BEGIN
    -- Convert to lowercase, replace spaces with hyphens
    v_slug := lower(regexp_replace(p_title, '[^a-zA-Z0-9]+', '-', 'g'));
    v_slug := trim(both '-' from v_slug);
    v_unique_slug := v_slug;
    
    -- Ensure uniqueness
    WHILE EXISTS (SELECT 1 FROM resumes WHERE slug = v_unique_slug) LOOP
        v_counter := v_counter + 1;
        v_unique_slug := v_slug || '-' || v_counter;
    END LOOP;
    
    RETURN v_unique_slug;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SEED DATA - Default templates
-- ============================================================
INSERT INTO templates (id, name, description, category, is_premium, supported_locales, layout_config, max_pages, supports_photo) VALUES
('modern', 'Modern', 'Clean and contemporary design with accent colors', 'general', FALSE, 
 ARRAY['en-US', 'fr-FR', 'de-DE', 'es-ES', 'ja-JP', 'ar-SA'],
 '{"columns": 1, "headerStyle": "gradient", "sectionSpacing": "comfortable", "features": ["timeline-dots", "skill-badges", "gradient-header"]}'::jsonb,
 2, TRUE),

('classic', 'Classic', 'Traditional professional layout', 'general', FALSE,
 ARRAY['en-US', 'fr-FR', 'de-DE', 'es-ES'],
 '{"columns": 1, "headerStyle": "simple", "sectionSpacing": "compact", "features": ["traditional-bullets", "serif-font"]}'::jsonb,
 2, TRUE),

('minimal', 'Minimal', 'Simple and elegant typography-focused design', 'general', FALSE,
 ARRAY['en-US', 'fr-FR', 'de-DE', 'es-ES', 'ja-JP'],
 '{"columns": 1, "headerStyle": "clean", "sectionSpacing": "spacious", "features": ["minimal-design", "typography-focus"]}'::jsonb,
 2, FALSE),

('creative', 'Creative', 'Bold and colorful design for creative professionals', 'creative', TRUE,
 ARRAY['en-US', 'fr-FR'],
 '{"columns": 2, "headerStyle": "creative", "sectionSpacing": "comfortable", "features": ["two-column", "color-blocks", "icons"]}'::jsonb,
 2, TRUE),

('academic', 'Academic', 'Formal layout for academic positions', 'academic', FALSE,
 ARRAY['en-US', 'fr-FR', 'de-DE'],
 '{"columns": 1, "headerStyle": "formal", "sectionSpacing": "compact", "features": ["publications-section", "detailed-format"]}'::jsonb,
 4, FALSE);

-- ============================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================
COMMENT ON TABLE users IS 'User accounts with authentication from Clerk/Auth0';
COMMENT ON TABLE resumes IS 'Main resume documents with metadata and configuration';
COMMENT ON TABLE contact_info IS 'Personal contact information for each resume';
COMMENT ON TABLE resume_sections IS 'Polymorphic sections with JSONB content for flexibility';
COMMENT ON TABLE templates IS 'Available CV templates with configuration';
COMMENT ON TABLE pdf_generations IS 'Audit trail for all PDF generations';
COMMENT ON TABLE resume_versions IS 'Version history for resume changes';

COMMENT ON COLUMN contact_info.phone_e164 IS 'Normalized phone number in E.164 format (+33612345678)';
COMMENT ON COLUMN contact_info.custom_links IS 'Additional social/professional links as JSON array';
COMMENT ON COLUMN resume_sections.content IS 'Polymorphic content structure varies by section type';
COMMENT ON COLUMN resumes.theme_config IS 'Theme customization: colors, fonts, spacing';
