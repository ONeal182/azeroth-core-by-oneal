/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include "ItemEnchantmentMgr.h"
#include "DBCStores.h"
#include "DatabaseEnv.h"
#include "Log.h"
#include "ObjectMgr.h"
#include "QueryResult.h"
#include "Timer.h"
#include "Util.h"
#include "Player.h"
#include "SharedDefines.h"
#include "ItemTemplate.h"
#include <cmath>
#include <functional>
#include <vector>
#include <set>

struct EnchStoreItem
{
    uint32  ench;
    float   chance;

    EnchStoreItem()
        : ench(0), chance(0) {}

    EnchStoreItem(uint32 _ench, float _chance)
        : ench(_ench), chance(_chance) {}
};

typedef std::vector<EnchStoreItem> EnchStoreList;
typedef std::unordered_map<uint32, EnchStoreList> EnchantmentStore;

static EnchantmentStore RandomItemEnch;

void LoadRandomEnchantmentsTable()
{
    uint32 oldMSTime = getMSTime();

    RandomItemEnch.clear();                                 // for reload case

    //                                                 0      1      2
    QueryResult result = WorldDatabase.Query("SELECT entry, ench, chance FROM item_enchantment_template");

    if (result)
    {
        uint32 count = 0;

        do
        {
            Field* fields = result->Fetch();

            uint32 entry = fields[0].Get<uint32>();
            uint32 ench = fields[1].Get<uint32>();
            float chance = fields[2].Get<float>();

            if (chance > 0.000001f && chance <= 100.0f)
                RandomItemEnch[entry].push_back(EnchStoreItem(ench, chance));

            ++count;
        } while (result->NextRow());

        LOG_INFO("server.loading", ">> Loaded {} Item Enchantment Definitions in {} ms", count, GetMSTimeDiffToNow(oldMSTime));
        LOG_INFO("server.loading", " ");
    }
    else
    {
        LOG_WARN("server.loading", ">> Loaded 0 Item Enchantment definitions. DB table `item_enchantment_template` is empty.");
        LOG_INFO("server.loading", " ");
    }
}

uint32 GetItemEnchantMod(int32 entry, Player const* player)
{
    if (!entry)
        return 0;

    if (entry == -1)
        return 0;

    EnchantmentStore::const_iterator tab = RandomItemEnch.find(entry);
    if (tab == RandomItemEnch.end())
    {
        LOG_ERROR("sql.sql", "Item RandomProperty / RandomSuffix id #{} used in `item_template` but it does not have records in `item_enchantment_template` table.", entry);
        return 0;
    }

    // Build a filtered list of candidates allowed for this player's class/spec
    std::vector<EnchStoreItem> allowedEnchants;
    float totalChance = 0.0f;

    if (player)
    {
        LOG_DEBUG("entities.item", "GetItemEnchantMod: Filtering enchants for entry {} (player class={}, spec={})",
                  entry, player->getClass(), player->GetMostPointsTalentTree());
    }
    else
    {
        LOG_DEBUG("entities.item", "GetItemEnchantMod: No player context, skipping filter for entry {}", entry);
    }

    for (EnchStoreList::const_iterator ench_iter = tab->second.begin(); ench_iter != tab->second.end(); ++ench_iter)
    {
        bool allowed = IsEnchantmentAllowedForPlayer(ench_iter->ench, player);

        if (player)
        {
            LOG_DEBUG("entities.item", "  Enchant {} - {}", ench_iter->ench, allowed ? "ALLOWED" : "REJECTED");
        }

        if (allowed)
        {
            allowedEnchants.push_back(*ench_iter);
            totalChance += ench_iter->chance;
        }
    }

    // If no enchants are allowed (shouldn't happen with proper data), fall back to unfiltered
    if (allowedEnchants.empty())
    {
        LOG_WARN("entities.item", "No enchants allowed for player class/spec in entry {}. Falling back to unfiltered.", entry);
        allowedEnchants.assign(tab->second.begin(), tab->second.end());
        totalChance = 0.0f;
        for (auto const& item : allowedEnchants)
            totalChance += item.chance;
    }
    else if (player)
    {
        LOG_DEBUG("entities.item", "GetItemEnchantMod: {} enchants allowed out of {} total",
                  allowedEnchants.size(), tab->second.size());
    }

    double dRoll = rand_chance();
    float fCount = 0;

    for (auto const& ench_item : allowedEnchants)
    {
        fCount += ench_item.chance;

        if (fCount > dRoll)
            return ench_item.ench;
    }

    // We could get here only if sum of all enchantment chances is lower than 100%
    dRoll = (irand(0, (int)std::floor(totalChance * 100) + 1)) / 100;
    fCount = 0;

    for (auto const& ench_item : allowedEnchants)
    {
        fCount += ench_item.chance;

        if (fCount > dRoll)
            return ench_item.ench;
    }

    return 0;
}

uint32 GenerateEnchSuffixFactor(uint32 item_id)
{
    ItemTemplate const* itemProto = sObjectMgr->GetItemTemplate(item_id);

    if (!itemProto)
        return 0;
    if (!itemProto->RandomSuffix)
        return 0;

    RandomPropertiesPointsEntry const* randomProperty = sRandomPropertiesPointsStore.LookupEntry(itemProto->ItemLevel);
    if (!randomProperty)
        return 0;

    uint32 suffixFactor;
    switch (itemProto->InventoryType)
    {
        // Items of that type don`t have points
        case INVTYPE_NON_EQUIP:
        case INVTYPE_BAG:
        case INVTYPE_TABARD:
        case INVTYPE_AMMO:
        case INVTYPE_QUIVER:
        case INVTYPE_RELIC:
            return 0;
        // Select point coefficient
        case INVTYPE_HEAD:
        case INVTYPE_BODY:
        case INVTYPE_CHEST:
        case INVTYPE_LEGS:
        case INVTYPE_2HWEAPON:
        case INVTYPE_ROBE:
            suffixFactor = 0;
            break;
        case INVTYPE_SHOULDERS:
        case INVTYPE_WAIST:
        case INVTYPE_FEET:
        case INVTYPE_HANDS:
        case INVTYPE_TRINKET:
            suffixFactor = 1;
            break;
        case INVTYPE_NECK:
        case INVTYPE_WRISTS:
        case INVTYPE_FINGER:
        case INVTYPE_SHIELD:
        case INVTYPE_CLOAK:
        case INVTYPE_HOLDABLE:
            suffixFactor = 2;
            break;
        case INVTYPE_WEAPON:
        case INVTYPE_WEAPONMAINHAND:
        case INVTYPE_WEAPONOFFHAND:
            suffixFactor = 3;
            break;
        case INVTYPE_RANGED:
        case INVTYPE_THROWN:
        case INVTYPE_RANGEDRIGHT:
            suffixFactor = 4;
            break;
        default:
            return 0;
    }
    // Select rare/epic modifier
    switch (itemProto->Quality)
    {
        case ITEM_QUALITY_UNCOMMON:
            return randomProperty->UncommonPropertiesPoints[suffixFactor];
        case ITEM_QUALITY_RARE:
            return randomProperty->RarePropertiesPoints[suffixFactor];
        case ITEM_QUALITY_EPIC:
            return randomProperty->EpicPropertiesPoints[suffixFactor];
        case ITEM_QUALITY_LEGENDARY:
        case ITEM_QUALITY_ARTIFACT:
            return 0;                                       // not have random properties
        default:
            break;
    }
    return 0;
}

// Helper to build a bitmask of allowed ItemModType values for a given class and talent spec
static uint64 BuildAllowedStatMask(uint8 playerClass, uint8 talentTree)
{
    // Stat bit helper
    auto M = [](uint32 modType) -> uint64 { return (1ULL << modType); };

    // Universal stats allowed for all roles
    uint64 universal = M(ITEM_MOD_STAMINA) | M(ITEM_MOD_RESILIENCE_RATING);

    // Define role-specific stat masks
    uint64 physicalTank = M(ITEM_MOD_STRENGTH) | M(ITEM_MOD_DEFENSE_SKILL_RATING) | M(ITEM_MOD_DODGE_RATING) |
                          M(ITEM_MOD_PARRY_RATING) | M(ITEM_MOD_BLOCK_RATING) | M(ITEM_MOD_HIT_RATING) |
                          M(ITEM_MOD_EXPERTISE_RATING) | M(ITEM_MOD_HEALTH) | M(ITEM_MOD_HEALTH_REGEN);

    uint64 physicalDps = M(ITEM_MOD_STRENGTH) | M(ITEM_MOD_AGILITY) | M(ITEM_MOD_ATTACK_POWER) |
                         M(ITEM_MOD_CRIT_RATING) | M(ITEM_MOD_HIT_RATING) | M(ITEM_MOD_HASTE_RATING) |
                         M(ITEM_MOD_EXPERTISE_RATING) | M(ITEM_MOD_ARMOR_PENETRATION_RATING) |
                         M(ITEM_MOD_CRIT_MELEE_RATING) | M(ITEM_MOD_HIT_MELEE_RATING) | M(ITEM_MOD_HASTE_MELEE_RATING);

    uint64 rangedDps = M(ITEM_MOD_AGILITY) | M(ITEM_MOD_ATTACK_POWER) | M(ITEM_MOD_RANGED_ATTACK_POWER) |
                       M(ITEM_MOD_CRIT_RATING) | M(ITEM_MOD_HIT_RATING) | M(ITEM_MOD_HASTE_RATING) |
                       M(ITEM_MOD_ARMOR_PENETRATION_RATING) | M(ITEM_MOD_CRIT_RANGED_RATING) |
                       M(ITEM_MOD_HIT_RANGED_RATING) | M(ITEM_MOD_HASTE_RANGED_RATING);

    uint64 casterDps = M(ITEM_MOD_INTELLECT) | M(ITEM_MOD_SPELL_POWER) | M(ITEM_MOD_CRIT_SPELL_RATING) |
                       M(ITEM_MOD_HIT_SPELL_RATING) | M(ITEM_MOD_HASTE_SPELL_RATING) | M(ITEM_MOD_SPELL_PENETRATION) |
                       M(ITEM_MOD_MANA) | M(ITEM_MOD_MANA_REGENERATION) | M(ITEM_MOD_SPIRIT);

    uint64 healer = M(ITEM_MOD_INTELLECT) | M(ITEM_MOD_SPIRIT) | M(ITEM_MOD_SPELL_POWER) |
                    M(ITEM_MOD_MANA) | M(ITEM_MOD_MANA_REGENERATION) | M(ITEM_MOD_CRIT_SPELL_RATING) |
                    M(ITEM_MOD_HASTE_SPELL_RATING) | M(ITEM_MOD_HEALTH_REGEN);

    // Mana-using tank (Paladin)
    uint64 manaTank = physicalTank | M(ITEM_MOD_MANA) | M(ITEM_MOD_INTELLECT) | M(ITEM_MOD_MANA_REGENERATION);

    // Hybrid melee with mana (Ret Paladin, Enhancement Shaman)
    uint64 hybridMelee = physicalDps | M(ITEM_MOD_MANA) | M(ITEM_MOD_INTELLECT) | M(ITEM_MOD_MANA_REGENERATION) | M(ITEM_MOD_SPELL_POWER);

    // Feral druid (tank/dps hybrid, uses agility primarily)
    uint64 feralDruid = M(ITEM_MOD_AGILITY) | M(ITEM_MOD_STRENGTH) | M(ITEM_MOD_ATTACK_POWER) |
                        M(ITEM_MOD_CRIT_RATING) | M(ITEM_MOD_HIT_RATING) | M(ITEM_MOD_HASTE_RATING) |
                        M(ITEM_MOD_EXPERTISE_RATING) | M(ITEM_MOD_ARMOR_PENETRATION_RATING) |
                        M(ITEM_MOD_DEFENSE_SKILL_RATING) | M(ITEM_MOD_DODGE_RATING) |
                        M(ITEM_MOD_CRIT_MELEE_RATING) | M(ITEM_MOD_HIT_MELEE_RATING) | M(ITEM_MOD_HASTE_MELEE_RATING);

    // Hunter with some mana relevance
    uint64 hunterDps = rangedDps | M(ITEM_MOD_MANA) | M(ITEM_MOD_INTELLECT) | M(ITEM_MOD_MANA_REGENERATION);

    switch (playerClass)
    {
        case CLASS_WARRIOR:
            // Arms (0), Fury (1), Protection (2)
            if (talentTree == 2)
                return universal | physicalTank;
            else
                return universal | physicalDps;

        case CLASS_PALADIN:
            // Holy (0), Protection (1), Retribution (2)
            if (talentTree == 0)
                return universal | healer;
            else if (talentTree == 1)
                return universal | manaTank;
            else
                return universal | hybridMelee;

        case CLASS_HUNTER:
            // All trees are ranged DPS (Beast Mastery 0, Marksmanship 1, Survival 2)
            return universal | hunterDps;

        case CLASS_ROGUE:
            // All trees are melee DPS (Assassination 0, Combat 1, Subtlety 2)
            return universal | physicalDps;

        case CLASS_PRIEST:
            // Discipline (0), Holy (1), Shadow (2)
            if (talentTree == 2)
                return universal | casterDps;
            else
                return universal | healer;

        case CLASS_DEATH_KNIGHT:
            // Blood (0), Frost (1), Unholy (2)
            // All DK trees can tank or DPS; treat as physical hybrid without mana
            // Tanks need tanking stats, DPS need DPS stats - for simplicity allow both
            return universal | physicalTank | physicalDps;

        case CLASS_SHAMAN:
            // Elemental (0), Enhancement (1), Restoration (2)
            if (talentTree == 0)
                return universal | casterDps;
            else if (talentTree == 1)
                return universal | hybridMelee;
            else
                return universal | healer;

        case CLASS_MAGE:
            // All trees are caster DPS (Arcane 0, Fire 1, Frost 2)
            return universal | casterDps;

        case CLASS_WARLOCK:
            // All trees are caster DPS (Affliction 0, Demonology 1, Destruction 2)
            return universal | casterDps;

        case CLASS_DRUID:
            // Balance (0), Feral (1), Restoration (2)
            if (talentTree == 0)
                return universal | casterDps;
            else if (talentTree == 1)
                return universal | feralDruid;
            else
                return universal | healer;

        default:
            // Unknown class - allow everything to be safe
            return 0xFFFFFFFFFFFFFFFFULL;
    }
}

bool IsEnchantmentAllowedForPlayer(uint32 enchantId, Player const* player)
{
    if (!player)
        return true; // No player context - allow

    SpellItemEnchantmentEntry const* enchant = sSpellItemEnchantmentStore.LookupEntry(enchantId);
    if (!enchant)
        return false; // Invalid enchant

    uint8 playerClass = player->getClass();
    uint8 talentTree = player->GetMostPointsTalentTree();
    uint64 allowedStats = BuildAllowedStatMask(playerClass, talentTree);

    LOG_DEBUG("entities.item", "IsEnchantmentAllowedForPlayer: enchantId={} class={} spec={}",
              enchantId, playerClass, talentTree);

    // Check all three enchantment effects
    for (uint8 i = 0; i < MAX_SPELL_ITEM_ENCHANTMENT_EFFECTS; ++i)
    {
        uint32 enchantType = enchant->type[i];

        // Only filter STAT-type effects; allow resistance, procs, etc.
        if (enchantType == ITEM_ENCHANTMENT_TYPE_STAT)
        {
            uint32 statType = enchant->spellid[i]; // For STAT type, spellid field holds the ItemModType

            LOG_DEBUG("entities.item", "  Effect[{}]: type={} (STAT), statType={}, allowed={}",
                      i, enchantType, statType, (statType < 64 && ((allowedStats >> statType) & 1ULL)));

            // If the stat is not in the allowed mask, reject this enchant
            if (statType < 64 && !((allowedStats >> statType) & 1ULL))
            {
                LOG_DEBUG("entities.item", "  -> REJECTED: stat {} not in allowed mask", statType);
                return false;
            }
        }
        else if (enchantType != 0)
        {
            LOG_DEBUG("entities.item", "  Effect[{}]: type={} (non-STAT), ALLOWED", i, enchantType);
        }
    }

    LOG_DEBUG("entities.item", "  -> ALLOWED: all stats match");
    return true; // All stat effects are allowed (or no stat effects present)
}
