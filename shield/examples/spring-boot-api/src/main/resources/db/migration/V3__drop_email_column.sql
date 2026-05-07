-- VIOLATION: Destructive migration without expand/contract pattern.
-- During rolling deploy: old code reads users.email, new code does not. The DROP
-- happens before old code is fully drained, causing runtime errors.
-- Should be split: V3 stop reading email, V4 drop column once all instances upgraded.
ALTER TABLE users DROP COLUMN email;
