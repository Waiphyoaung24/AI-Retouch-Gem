-- Add dimension columns to gems table
-- Run this in Supabase SQL Editor

ALTER TABLE gems ADD COLUMN IF NOT EXISTS carat_weight FLOAT;
ALTER TABLE gems ADD COLUMN IF NOT EXISTS length_mm FLOAT;
ALTER TABLE gems ADD COLUMN IF NOT EXISTS width_mm FLOAT;
ALTER TABLE gems ADD COLUMN IF NOT EXISTS depth_mm FLOAT;
