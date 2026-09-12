-- Consolidates the two parallel follow systems onto the `follows` table.
-- `profile_views` is untouched (unrelated feature: view tracking, not follow state).
DROP TABLE follow_system;
