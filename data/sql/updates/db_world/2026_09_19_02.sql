-- Replace rate-scaled gathering yield (2026_09_19_00.sql, 2026_09_19_01.sql) with a
-- flat MinCount=1, MaxCount=4 for skinning, mining/herbalism gameobject nodes,
-- prospecting (Jewelcrafting), milling (Inscription), disenchanting.
-- One-shot migration (not idempotent) -- do not re-run manually after it applies.

UPDATE `skinning_loot_template`
SET `MinCount` = 1,
    `MaxCount` = 4;

UPDATE `gameobject_loot_template` `glt`
JOIN `gameobject_template` `gt` ON `gt`.`type` = 3 AND `gt`.`Data1` = `glt`.`Entry`
SET `glt`.`MinCount` = 1,
    `glt`.`MaxCount` = 4
WHERE `gt`.`name` IN (
    -- Mining nodes
    'Adamantite Deposit', 'Ancient Gem Vein', 'Cobalt Deposit', 'Copper Vein',
    'Dark Iron Deposit', 'Fel Iron Deposit', 'Gold Vein', 'Hakkari Thorium Vein',
    'Incendicite Mineral Vein', 'Indurium Mineral Vein', 'Iron Deposit', 'Khorium Vein',
    'Lesser Bloodstone Deposit', 'Mithril Deposit', 'Nethercite Deposit',
    'Ooze Covered Gold Vein', 'Ooze Covered Iron Deposit', 'Ooze Covered Mithril Deposit',
    'Ooze Covered Rich Thorium Vein', 'Ooze Covered Silver Vein', 'Ooze Covered Thorium Vein',
    'Ooze Covered Truesilver Deposit', 'Pure Saronite Deposit', 'Rich Adamantite Deposit',
    'Rich Cobalt Deposit', 'Rich Saronite Deposit', 'Rich Thorium Vein', 'Saronite Deposit',
    'Silver Vein', 'Small Thorium Vein', 'Tin Vein', 'Titanium Vein', 'Truesilver Deposit',
    -- Herbalism nodes
    'Adder''s Tongue', 'Ancient Lichen', 'Arthas'' Tears', 'Black Lotus', 'Blindweed',
    'Bloodthistle', 'Briarthorn', 'Bruiseweed', 'Dreamfoil', 'Dreaming Glory', 'Earthroot',
    'Fadeleaf', 'Felweed', 'Firebloom', 'Flame Cap', 'Frost Lotus', 'Ghost Mushroom',
    'Goldclover', 'Golden Sansam', 'Goldthorn', 'Grave Moss', 'Gromsblood', 'Icecap',
    'Icethorn', 'Khadgar''s Whisker', 'Kingsblood', 'Lichbloom', 'Liferoot', 'Mageroyal',
    'Mana Thistle', 'Mountain Silversage', 'Netherbloom', 'Nightmare Vine', 'Peacebloom',
    'Plaguebloom', 'Purple Lotus', 'Ragveil', 'Silverleaf', 'Stranglekelp', 'Sungrass',
    'Talandra''s Rose', 'Terocone', 'Tiger Lily', 'Wild Steelbloom'
);

UPDATE `prospecting_loot_template`
SET `MinCount` = 1,
    `MaxCount` = 4;

UPDATE `milling_loot_template`
SET `MinCount` = 1,
    `MaxCount` = 4;

UPDATE `disenchant_loot_template`
SET `MinCount` = 1,
    `MaxCount` = 4;
