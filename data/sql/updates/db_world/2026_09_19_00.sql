-- Gathering yield x3: multiply MinCount/MaxCount by 3 for skinning and for
-- mining/herbalism gameobject nodes, capped at the tinyint unsigned max (255).
-- One-shot migration (not idempotent) -- do not re-run manually after it applies.

UPDATE `skinning_loot_template`
SET `MinCount` = LEAST(`MinCount` * 3, 255),
    `MaxCount` = LEAST(`MaxCount` * 3, 255);

UPDATE `gameobject_loot_template` `glt`
JOIN `gameobject_template` `gt` ON `gt`.`type` = 3 AND `gt`.`Data1` = `glt`.`Entry`
SET `glt`.`MinCount` = LEAST(`glt`.`MinCount` * 3, 255),
    `glt`.`MaxCount` = LEAST(`glt`.`MaxCount` * 3, 255)
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
