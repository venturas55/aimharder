-- Run manually ONLY if configs.tipo_app does not exist. Does not remove legacy columns.
ALTER TABLE configs ADD COLUMN tipo_app VARCHAR(100) NOT NULL DEFAULT 'aimharder';
-- If a legacy `tipo` column exists, run separately after inspecting its values:
-- UPDATE configs SET tipo_app = tipo WHERE tipo IN ('aimharder', 'trainingmyapp', 'resamania');
