-- Gem Preview Schema Migration
-- Run this in Supabase SQL Editor

-- Gems: replaces 'products' table
CREATE TABLE IF NOT EXISTS gems (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  product_image_url TEXT NOT NULL,
  context_image_url TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Setting categories (ring, earring, pendant)
CREATE TABLE IF NOT EXISTS setting_categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  body_part TEXT NOT NULL,
  sort_order INT DEFAULT 0
);

-- Metals
CREATE TABLE IF NOT EXISTS metals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  sort_order INT DEFAULT 0
);

-- Styles (linked to category)
CREATE TABLE IF NOT EXISTS setting_styles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category_id UUID REFERENCES setting_categories(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  sort_order INT DEFAULT 0
);

-- Prompt templates: one per category x metal x style combination
CREATE TABLE IF NOT EXISTS prompt_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category_id UUID REFERENCES setting_categories(id),
  metal_id UUID REFERENCES metals(id),
  style_id UUID REFERENCES setting_styles(id),
  prompt_body TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(category_id, metal_id, style_id)
);

-- Preset model photos (organized by body part)
CREATE TABLE IF NOT EXISTS model_photos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  body_part TEXT NOT NULL,
  image_url TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Results cache
CREATE TABLE IF NOT EXISTS generation_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gem_id UUID REFERENCES gems(id),
  prompt_template_id UUID REFERENCES prompt_templates(id),
  model_photo_url TEXT NOT NULL,
  result_image_url TEXT NOT NULL,
  processing_time_ms FLOAT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Seed setting_categories
INSERT INTO setting_categories (name, body_part, sort_order) VALUES
  ('Ring', 'hand', 1),
  ('Earring', 'ear', 2),
  ('Pendant', 'neck', 3);

-- Seed metals
INSERT INTO metals (name, sort_order) VALUES
  ('Gold', 1),
  ('White Gold', 2),
  ('Rose Gold', 3),
  ('Silver', 4);

-- Seed setting_styles (rings)
INSERT INTO setting_styles (category_id, name, sort_order)
SELECT c.id, s.name, s.sort_order
FROM setting_categories c
CROSS JOIN (VALUES ('Solitaire', 1), ('Halo', 2), ('Three-Stone', 3), ('Pave', 4)) AS s(name, sort_order)
WHERE c.name = 'Ring';

-- Seed setting_styles (earrings)
INSERT INTO setting_styles (category_id, name, sort_order)
SELECT c.id, s.name, s.sort_order
FROM setting_categories c
CROSS JOIN (VALUES ('Stud', 1), ('Drop', 2), ('Hoop', 3), ('Chandelier', 4)) AS s(name, sort_order)
WHERE c.name = 'Earring';

-- Seed setting_styles (pendants)
INSERT INTO setting_styles (category_id, name, sort_order)
SELECT c.id, s.name, s.sort_order
FROM setting_categories c
CROSS JOIN (VALUES ('Solitaire', 1), ('Halo', 2), ('Bezel', 3), ('Cluster', 4)) AS s(name, sort_order)
WHERE c.name = 'Pendant';
