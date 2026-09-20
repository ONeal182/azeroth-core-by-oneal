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

#ifndef ACORE_ABSTRACTFOLLOWER_H
#define ACORE_ABSTRACTFOLLOWER_H

class Unit;

#include "UnitUtils.h"

class AbstractFollower
{
public:
    explicit AbstractFollower(Unit* target = nullptr) { SetTarget(target); }
    virtual ~AbstractFollower() { SetTarget(nullptr); }

    void SetTarget(Unit* unit);
    [[nodiscard]] Unit* GetTarget() const { return _target; }

private:
    // SafeUnitPointer (not a raw Unit*): auto-nulled by Unit::HandleSafeUnitPointersOnDelete()
    // when the target is destroyed, even if Unit::RemoveAllFollowers()/FollowerRemoved() never
    // ran for this follower (e.g. target freed outside the normal RemoveFromWorld() path).
    // Without this, ~AbstractFollower() can dereference a dangling _target -> ACCESS_VIOLATION.
    SafeUnitPointer _target{nullptr};
};

#endif
