-- Seed prompt templates for all category x metal x style combinations
-- Run this in Supabase SQL Editor AFTER 001_gem_preview_schema.sql

INSERT INTO prompt_templates (category_id, metal_id, style_id, prompt_body)
SELECT c.id, m.id, s.id,
  'You are a professional jewelry retouching artist and photorealistic rendering specialist.' || E'\n\n' ||
  'Image 1: A loose gemstone (clean product photograph).' || E'\n' ||
  'Image 2: A photograph of a person''s ' || c.body_part || '.' || E'\n\n' ||
  'Task: Create a photorealistic image showing this exact gemstone set in a ' || s.name || ' ' || LOWER(c.name) || ' made of ' || LOWER(m.name) || '. Place the ' || LOWER(c.name) || ' naturally on the ' ||
  CASE
    WHEN c.name = 'Ring' THEN 'ring finger'
    WHEN c.name = 'Earring' THEN 'ear'
    WHEN c.name = 'Pendant' THEN 'neck'
  END || ' shown in Image 2.' || E'\n\n' ||
  'Requirements:' || E'\n' ||
  '- Preserve the gemstone''s exact color, cut, clarity, and brilliance from Image 1' || E'\n' ||
  '- Render the ' || LOWER(m.name) || ' setting with realistic reflections, ' ||
  CASE
    WHEN m.name = 'Gold' THEN 'warm yellow luster, and rich metallic sheen'
    WHEN m.name = 'White Gold' THEN 'cool silvery brilliance, subtle warmth, and polished finish'
    WHEN m.name = 'Rose Gold' THEN 'warm pinkish copper tones, romantic glow, and soft reflections'
    WHEN m.name = 'Silver' THEN 'bright cool luster, clean reflections, and crisp highlights'
  END || E'\n' ||
  '- The ' || s.name || ' style should feature ' ||
  CASE
    WHEN s.name = 'Solitaire' THEN 'a single prominent center stone with clean, elegant prong setting'
    WHEN s.name = 'Halo' THEN 'a ring of smaller accent stones surrounding the center gemstone'
    WHEN s.name = 'Three-Stone' THEN 'the center gemstone flanked by two complementary side stones'
    WHEN s.name = 'Pave' THEN 'tiny diamonds set closely along the band, creating a continuous sparkle'
    WHEN s.name = 'Stud' THEN 'the gemstone mounted directly on the earlobe with a secure post backing'
    WHEN s.name = 'Drop' THEN 'the gemstone hanging elegantly below the earlobe'
    WHEN s.name = 'Hoop' THEN 'the gemstone integrated into a circular hoop design'
    WHEN s.name = 'Chandelier' THEN 'an ornate tiered design with the gemstone as the centerpiece'
    WHEN s.name = 'Bezel' THEN 'the gemstone fully encircled by a thin metal rim for a sleek modern look'
    WHEN s.name = 'Cluster' THEN 'multiple smaller stones arranged closely around the center gem'
    ELSE 'classic proportions and refined craftsmanship'
  END || E'\n' ||
  '- Match the lighting, shadows, and skin tones from Image 2' || E'\n' ||
  '- The jewelry must look naturally worn, not digitally pasted' || E'\n' ||
  '- Do not alter the person''s body, skin texture, or background' || E'\n' ||
  '- Output only the final composite image'
FROM setting_categories c
CROSS JOIN metals m
CROSS JOIN setting_styles s
WHERE s.category_id = c.id
ON CONFLICT (category_id, metal_id, style_id) DO UPDATE SET prompt_body = EXCLUDED.prompt_body;
