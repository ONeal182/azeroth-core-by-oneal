-- Gathering yield x3, part 2: prospecting (Jewelcrafting), milling (Inscription),
-- disenchanting. Multiply MinCount/MaxCount by 3, capped at the tinyint unsigned max (255).
-- One-shot migration (not idempotent) -- do not re-run manually after it applies.

UPDATE `prospecting_loot_template`
SET `MinCount` = LEAST(`MinCount` * 3, 255),
    `MaxCount` = LEAST(`MaxCount` * 3, 255);

UPDATE `milling_loot_template`
SET `MinCount` = LEAST(`MinCount` * 3, 255),
    `MaxCount` = LEAST(`MaxCount` * 3, 255);

UPDATE `disenchant_loot_template`
SET `MinCount` = LEAST(`MinCount` * 3, 255),
    `MaxCount` = LEAST(`MaxCount` * 3, 255);
