-- Quest 12955 "Eliminate the Competition": Sigrid Iceborn (30086) and Efrem the Faithful (30081)
-- set/restore their faction with target_type 0 (SMART_TARGET_NONE). SET_FACTION iterates its
-- targets and NONE yields none, so they never turned hostile and could not be duelled.
-- Use SMART_TARGET_SELF (1), like Tinky Wickwhistle (30162) and Onu'zun (30180) already do.
UPDATE `smart_scripts` SET `target_type` = 1 WHERE `source_type` = 0 AND `entryorguid` = 30086 AND `id` IN (14, 19) AND `action_type` = 2;
UPDATE `smart_scripts` SET `target_type` = 1 WHERE `source_type` = 0 AND `entryorguid` = 30081 AND `id` IN (7, 11) AND `action_type` = 2;
