-- Mount Vendor: sells all mounts, faction-restricted + neutral mounts, min price 3000g.
-- Item clones use entry+200000 offset so BuyPrice change does not affect any other vendor/source
-- that already sells the original mount items (compatibility: original item_template rows untouched).

-- 1) Clone all mount items (class 15 / subclass 5) with a floor price of 3000g (30000000 copper).
DELETE FROM `item_template` WHERE `entry` BETWEEN 200000 AND 200999;
INSERT INTO `item_template` (`entry`,`class`,`subclass`,`SoundOverrideSubclass`,`name`,`displayid`,`Quality`,`Flags`,`FlagsExtra`,`BuyCount`,`BuyPrice`,`SellPrice`,`InventoryType`,`AllowableClass`,`AllowableRace`,`ItemLevel`,`RequiredLevel`,`RequiredSkill`,`RequiredSkillRank`,`requiredspell`,`requiredhonorrank`,`RequiredCityRank`,`RequiredReputationFaction`,`RequiredReputationRank`,`maxcount`,`stackable`,`ContainerSlots`,`stat_type1`,`stat_value1`,`stat_type2`,`stat_value2`,`stat_type3`,`stat_value3`,`stat_type4`,`stat_value4`,`stat_type5`,`stat_value5`,`stat_type6`,`stat_value6`,`stat_type7`,`stat_value7`,`stat_type8`,`stat_value8`,`stat_type9`,`stat_value9`,`stat_type10`,`stat_value10`,`ScalingStatDistribution`,`ScalingStatValue`,`dmg_min1`,`dmg_max1`,`dmg_type1`,`dmg_min2`,`dmg_max2`,`dmg_type2`,`armor`,`holy_res`,`fire_res`,`nature_res`,`frost_res`,`shadow_res`,`arcane_res`,`delay`,`ammo_type`,`RangedModRange`,`spellid_1`,`spelltrigger_1`,`spellcharges_1`,`spellppmRate_1`,`spellcooldown_1`,`spellcategory_1`,`spellcategorycooldown_1`,`spellid_2`,`spelltrigger_2`,`spellcharges_2`,`spellppmRate_2`,`spellcooldown_2`,`spellcategory_2`,`spellcategorycooldown_2`,`spellid_3`,`spelltrigger_3`,`spellcharges_3`,`spellppmRate_3`,`spellcooldown_3`,`spellcategory_3`,`spellcategorycooldown_3`,`spellid_4`,`spelltrigger_4`,`spellcharges_4`,`spellppmRate_4`,`spellcooldown_4`,`spellcategory_4`,`spellcategorycooldown_4`,`spellid_5`,`spelltrigger_5`,`spellcharges_5`,`spellppmRate_5`,`spellcooldown_5`,`spellcategory_5`,`spellcategorycooldown_5`,`bonding`,`description`,`PageText`,`LanguageID`,`PageMaterial`,`startquest`,`lockid`,`Material`,`sheath`,`RandomProperty`,`RandomSuffix`,`block`,`itemset`,`MaxDurability`,`area`,`Map`,`BagFamily`,`TotemCategory`,`socketColor_1`,`socketContent_1`,`socketColor_2`,`socketContent_2`,`socketColor_3`,`socketContent_3`,`socketBonus`,`GemProperties`,`RequiredDisenchantSkill`,`ArmorDamageModifier`,`duration`,`ItemLimitCategory`,`HolidayId`,`ScriptName`,`DisenchantID`,`FoodType`,`minMoneyLoot`,`maxMoneyLoot`,`flagsCustom`,`VerifiedBuild`)
SELECT `entry`+200000,`class`,`subclass`,`SoundOverrideSubclass`,`name`,`displayid`,`Quality`,`Flags`,`FlagsExtra`,`BuyCount`,GREATEST(`BuyPrice`,30000000),`SellPrice`,`InventoryType`,`AllowableClass`,`AllowableRace`,`ItemLevel`,`RequiredLevel`,`RequiredSkill`,`RequiredSkillRank`,`requiredspell`,`requiredhonorrank`,`RequiredCityRank`,`RequiredReputationFaction`,`RequiredReputationRank`,`maxcount`,`stackable`,`ContainerSlots`,`stat_type1`,`stat_value1`,`stat_type2`,`stat_value2`,`stat_type3`,`stat_value3`,`stat_type4`,`stat_value4`,`stat_type5`,`stat_value5`,`stat_type6`,`stat_value6`,`stat_type7`,`stat_value7`,`stat_type8`,`stat_value8`,`stat_type9`,`stat_value9`,`stat_type10`,`stat_value10`,`ScalingStatDistribution`,`ScalingStatValue`,`dmg_min1`,`dmg_max1`,`dmg_type1`,`dmg_min2`,`dmg_max2`,`dmg_type2`,`armor`,`holy_res`,`fire_res`,`nature_res`,`frost_res`,`shadow_res`,`arcane_res`,`delay`,`ammo_type`,`RangedModRange`,`spellid_1`,`spelltrigger_1`,`spellcharges_1`,`spellppmRate_1`,`spellcooldown_1`,`spellcategory_1`,`spellcategorycooldown_1`,`spellid_2`,`spelltrigger_2`,`spellcharges_2`,`spellppmRate_2`,`spellcooldown_2`,`spellcategory_2`,`spellcategorycooldown_2`,`spellid_3`,`spelltrigger_3`,`spellcharges_3`,`spellppmRate_3`,`spellcooldown_3`,`spellcategory_3`,`spellcategorycooldown_3`,`spellid_4`,`spelltrigger_4`,`spellcharges_4`,`spellppmRate_4`,`spellcooldown_4`,`spellcategory_4`,`spellcategorycooldown_4`,`spellid_5`,`spelltrigger_5`,`spellcharges_5`,`spellppmRate_5`,`spellcooldown_5`,`spellcategory_5`,`spellcategorycooldown_5`,`bonding`,`description`,`PageText`,`LanguageID`,`PageMaterial`,`startquest`,`lockid`,`Material`,`sheath`,`RandomProperty`,`RandomSuffix`,`block`,`itemset`,`MaxDurability`,`area`,`Map`,`BagFamily`,`TotemCategory`,`socketColor_1`,`socketContent_1`,`socketColor_2`,`socketContent_2`,`socketColor_3`,`socketContent_3`,`socketBonus`,`GemProperties`,`RequiredDisenchantSkill`,`ArmorDamageModifier`,`duration`,`ItemLimitCategory`,`HolidayId`,`ScriptName`,`DisenchantID`,`FoodType`,`minMoneyLoot`,`maxMoneyLoot`,`flagsCustom`,`VerifiedBuild`
FROM `item_template` WHERE `class`=15 AND `subclass`=5;

-- 2) Vendor creature templates (Alliance / Horde), pure vendor (npcflag VENDOR only).
DELETE FROM `creature_template` WHERE `entry` IN (190000,190001);
INSERT INTO `creature_template` (`entry`,`difficulty_entry_1`,`difficulty_entry_2`,`difficulty_entry_3`,`KillCredit1`,`KillCredit2`,`name`,`subname`,`IconName`,`gossip_menu_id`,`minlevel`,`maxlevel`,`exp`,`faction`,`npcflag`,`speed_walk`,`speed_run`,`speed_swim`,`speed_flight`,`detection_range`,`rank`,`dmgschool`,`DamageModifier`,`BaseAttackTime`,`RangeAttackTime`,`BaseVariance`,`RangeVariance`,`unit_class`,`unit_flags`,`unit_flags2`,`dynamicflags`,`family`,`type`,`type_flags`,`lootid`,`pickpocketloot`,`skinloot`,`PetSpellDataId`,`VehicleId`,`mingold`,`maxgold`,`AIName`,`MovementType`,`HoverHeight`,`HealthModifier`,`ManaModifier`,`ArmorModifier`,`ExperienceModifier`,`RacialLeader`,`movementId`,`RegenHealth`,`CreatureImmunitiesId`,`flags_extra`,`ScriptName`) VALUES
(190000,0,0,0,0,0,'Mount Vendor','Alliance Mounts',NULL,0,80,80,0,35,128,1,1.14286,1,1,20,0,0,1,2000,2000,1,1,1,0,0,0,0,7,0,0,0,0,0,0,0,0,'',0,1,1,1,1,1,0,0,1,0,0,''),
(190001,0,0,0,0,0,'Mount Vendor','Horde Mounts',NULL,0,80,80,0,35,128,1,1.14286,1,1,20,0,0,1,2000,2000,1,1,1,0,0,0,0,7,0,0,0,0,0,0,0,0,'',0,1,1,1,1,1,0,0,1,0,0,'');

DELETE FROM `creature_template_model` WHERE `CreatureID` IN (190000,190001);
INSERT INTO `creature_template_model` (`CreatureID`,`Idx`,`CreatureDisplayID`,`DisplayScale`,`Probability`) VALUES
(190000,0,16923,1,1),
(190001,0,13385,1,1);

-- 3) Spawns in every capital city (map/coords taken from game_tele reference points).
DELETE FROM `creature` WHERE `id` IN (190000,190001);
INSERT INTO `creature` (`id`,`map`,`zoneId`,`areaId`,`spawnMask`,`phaseMask`,`equipment_id`,`position_x`,`position_y`,`position_z`,`orientation`,`spawntimesecs`,`wander_distance`,`currentwaypoint`,`curhealth`,`curmana`,`MovementType`,`npcflag`,`unit_flags`,`dynamicflags`,`ScriptName`,`CreateObject`,`Comment`) VALUES
-- Alliance
(190000,0,0,0,1,1,0,-8833.38,628.628,94.0066,1.06535,300,0,0,1,0,0,0,0,0,'',1,'Mount Vendor - Stormwind'),
(190000,0,0,0,1,1,0,-4918.88,-940.406,501.564,5.42347,300,0,0,1,0,0,0,0,0,'',1,'Mount Vendor - Ironforge'),
(190000,1,0,0,1,1,0,9949.56,2284.21,1341.4,1.59587,300,0,0,1,0,0,0,0,0,'',1,'Mount Vendor - Darnassus'),
(190000,530,0,0,1,1,0,-3965.7,-11653.6,-138.844,0.852154,300,0,0,1,0,0,0,0,0,'',1,'Mount Vendor - The Exodar'),
-- Horde
(190001,1,0,0,1,1,0,1629.85,-4373.64,31.5573,3.69762,300,0,0,1,0,0,0,0,0,'',1,'Mount Vendor - Orgrimmar'),
(190001,1,0,0,1,1,0,-1277.37,124.804,131.287,5.22274,300,0,0,1,0,0,0,0,0,'',1,'Mount Vendor - Thunder Bluff'),
(190001,0,0,0,1,1,0,1584.14,240.308,-52.1534,0.041793,300,0,0,1,0,0,0,0,0,'',1,'Mount Vendor - Undercity'),
(190001,530,0,0,1,1,0,9487.69,-7279.2,14.2866,6.16478,300,0,0,1,0,0,0,0,0,'',1,'Mount Vendor - Silvermoon City');

-- 4) Vendor lists: same-faction mounts + all neutral ("all others") mounts, min 3000g via cloned items.
DELETE FROM `npc_vendor` WHERE `entry` IN (190000,190001);

-- entry < 200000 excludes our own item clones (they share class/subclass with the originals).
INSERT INTO `npc_vendor` (`entry`,`slot`,`item`,`maxcount`,`incrtime`,`ExtendedCost`)
SELECT 190000, ROW_NUMBER() OVER (ORDER BY `name`), `entry`+200000, 0, 0, 0
FROM `item_template`
WHERE `entry` < 200000 AND `class`=15 AND `subclass`=5 AND (`AllowableRace` & 1101) <> 0;

INSERT INTO `npc_vendor` (`entry`,`slot`,`item`,`maxcount`,`incrtime`,`ExtendedCost`)
SELECT 190001, ROW_NUMBER() OVER (ORDER BY `name`), `entry`+200000, 0, 0, 0
FROM `item_template`
WHERE `entry` < 200000 AND `class`=15 AND `subclass`=5 AND (`AllowableRace` & 690) <> 0;
