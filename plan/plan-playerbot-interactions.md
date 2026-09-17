# Plan: playerbot-interactions

**Source:** Original `mod-playerbot-interactions` requirements and observer invariant
**Date:** 2026-09-18
**Status:** Active

## Scope

Implement a modular AzerothCore WotLK 3.3.5a system that allows PlayerBots to perform real, observable interactions with real players and with other PlayerBots through existing game mechanics.

The interaction layer must reuse existing AzerothCore/PlayerBots systems where practical and must not replace normal PlayerbotAI, TravelMgr, BackgroundProgression, CityLife, Auction AI, combat AI, or other existing world systems.

Primary BOT_BOT behaviors covered by the overall plan:

- post-combat healing;
- useful buffs;
- resurrection;
- silent social gestures/rest;
- direct real trade based on actual economic needs;
- small temporary groups for compatible open-world goals;
- optional combat assistance after separate safety validation.

BOT_BOT speech, textual emotes, and LLM dialogue are forbidden.

## Cross-Cutting Invariant: Real Player Observer for BOT_BOT

All interactions initiated by the new BOT_BOT interaction layer require at least one eligible real human observer who can observe all direct participants.

A human merely being online on the server is insufficient.

An eligible observer must:

- be a real human player, not a playerbot;
- be online and present in the world;
- be on a compatible map, instance, and phase;
- be sufficiently close;
- satisfy server-side visibility/observability requirements for all participants.

For pair interactions, at least one common observer must be eligible for both bots.

Observer presence permits an otherwise valid interaction; it does not trigger one.

The rule applies to healing, buffs, resurrection, direct trade, gestures, shared rest, temporary groups, future combat assistance, and any other BOT_BOT scene initiated by this module.

Observer eligibility must be checked:

1. at event detection;
2. during participant selection;
3. before task assignment;
4. during approach/waiting;
5. before each new gameplay action;
6. before each scene phase transition.

Cached proximity may be used for cheap prefiltering, but actual actions require a fresh check.

If no common observer remains:

- no new gameplay action may start;
- optional approach/waiting must stop;
- module-owned reservations/tasks must be released;
- control returns to normal AI;
- cancellation reason is `NO_REAL_PLAYER_OBSERVER`.

Already-started indivisible core operations, such as final trade persistence, may finish safely before the scene stops.

Module-owned temporary groups must not be destructively disbanded at an unsafe gameplay boundary such as active combat, but no new module-owned cooperative task may begin without an eligible observer.

One eligible common observer is sufficient. A scene must not be permanently bound to one observer GUID. Multiple observers must not duplicate scenes or increase interaction frequency.

Normal PlayerbotAI, BackgroundProgression, crafting, gathering, leveling, and other existing systems remain unaffected when no observer is present. Only the additional BOT_BOT interaction layer is gated.

BOT_BOT speech remains forbidden regardless of observer presence:

- no bot-to-bot chat;
- no textual emotes;
- no LLM dialogue requests.

## Existing Architecture / Required Investigation

Before changing a subsystem, verify the current checkout rather than assuming names or APIs from the requirements are already implemented.

Use:

- AzerothMCP for DB/game data/runtime/SOAP;
- Graphify for architecture and cross-module relationships;
- clangd for exact C++ definitions/references/callers;
- Atlas only for unfamiliar subsystem orientation;
- ast-grep for structural patterns;
- `rg` for exact strings/config/log text.

Prefer module-level changes over AzerothCore core changes. If a core hook is required, keep it minimal and document why the module layer is insufficient.

---

## Implementation Phases

### Phase 1: Foundation, Interaction Context, Silence Policy, Dry-Run

**Goal:** Establish the shared interaction engine and prove that BOT_BOT interactions can be identified, inspected, and prevented from producing speech or LLM requests before real gameplay scenarios are enabled.

**Touches:**
- module: `mod-playerbot-interactions`
- PlayerBots/chat integration
- config/debug/commands
- metrics

**Tasks:**
- [ ] Verify existing PlayerBots/Core hooks for real-player vs playerbot detection, chat/LLM initiation, task ownership, movement, and action execution.
- [ ] Implement the shared interaction context/lifecycle with interaction ID, mode (`BOT_PLAYER` / `BOT_BOT`), participants, phase, timestamps, and speech policy.
- [ ] Enforce BOT_BOT silence at both interaction origin and final speech/LLM dispatch boundaries without globally muting the bot.
- [ ] Implement dry-run/status/debug inspection that explains candidate selection, rejection reasons, task ownership, limits, and expected action without mutating the world.
- [ ] Add baseline counters/metrics for scenes, outcomes, cancellations, BOT_BOT dialogue attempts/messages, LLM requests, and gameplay actions.

**Verification:**
- BOT_BOT mode is derived from actual participants, not prompt text or LLM output.
- BOT_BOT chat/text emote/LLM requests are blocked.
- Direct BOT_PLAYER communication still works.
- Dry-run does not move, cast, trade, reserve resources, change groups, or mutate strategies.
- Debug/status output is bounded and does not spam every bot every tick.

**Done when:** The interaction engine can classify and inspect candidate scenes, BOT_BOT speech/LLM output remains zero, and no real gameplay mutation is required to verify the base flow.

---

### Phase 2: Ownership, Reservations, Cancellation, System Integration

**Goal:** Make interaction tasks safe to start, cancel, timeout, and release without leaving bots stuck or double-counting background work.

**Touches:**
- task ownership/reservations
- BackgroundProgression
- CityLife
- runtime cancellation/cleanup

**Tasks:**
- [ ] Reuse the existing task registry and add only the minimum InteractionTask metadata required for participants, owner token, phase, timeout, and cancellation reason.
- [ ] Implement ordered participant reservation, timeout, cancellation, and safe cleanup without holding locks during movement/casts/trade waits/external calls.
- [ ] Integrate BackgroundProgression eligibility so active incompatible interaction time is not rewarded in parallel or retroactively.
- [ ] Integrate CityLife ownership so module-owned tasks temporarily protect participants without blindly restoring stale strategy snapshots.
- [ ] Handle logout, teleport/map transfer, death, group changes, and human commands by releasing only module-owned state.

**Verification:**
- One bot cannot participate in two active scenes.
- Failed/expired scenes release tasks and reservations.
- BackgroundProgression does not double-reward active interaction time.
- CityLife does not steal participants mid-scene and resumes correctly afterward.
- Logout/teleport/death does not leave stale pointers, reservations, or waiting tasks.

**Done when:** A scene can safely acquire participants, wait, cancel, timeout, and restore normal behavior without leaks or ownership conflicts.

---

### Phase 3: Healing, Buffs, Silent Gestures

**Goal:** Deliver the first real BOT_BOT gameplay interactions using existing mechanics, without speech or feedback loops.

**Touches:**
- PlayerBots spell/action systems
- post-combat events
- gesture/emote animation
- cooldowns/anti-repeat

**Tasks:**
- [ ] Implement post-combat healing candidate detection, healer/target eligibility, reservation, approach, fresh validation, real cast, and result verification.
- [ ] Implement useful buff interactions with duplicate/stronger-aura protection, resource checks, and pair/action cooldowns.
- [ ] Implement silent gestures/rest using animation/state only, never textual emotes.
- [ ] Add anti-feedback/cooldown logic so successful help does not recursively generate endless reciprocal scenes.
- [ ] Verify indirect chat/event hooks cannot turn heal/buff/gesture results into BOT_BOT dialogue or LLM calls.

**Verification:**
- Injured eligible bot receives a real heal effect.
- Healthy bot does not cause continuous healing attempts.
- Missing mana/spell prevents action.
- Buff is not endlessly refreshed or reciprocated.
- Gestures produce animation without text.
- BOT_BOT dialogue messages and LLM requests remain zero.

**Done when:** Healing, buffs, and silent gestures work end-to-end through real game mechanics and recover cleanly on changing target state.

---

### Phase 4: Resurrection, Relationship Memory, Stable Traits

**Goal:** Add a real resurrection flow and small persistent relationship memory that influences initiative without overriding safety/economy/game rules.

**Touches:**
- resurrection pipeline
- persistent relationship memory
- bot traits
- storage/migrations if required

**Tasks:**
- [ ] Implement resurrection through the normal spell -> offer -> valid acceptance path and verify actual resurrection, not cast intent.
- [ ] Handle already-resurrected, logged-out, interrupted, expired-offer, and changed-state cases safely.
- [ ] Persist only significant relationship events with bounded per-bot memory and expiration/eviction.
- [ ] Add relatively stable traits influencing initiative/helpfulness/patience/caution/trade interest/familiarity preference.
- [ ] Ensure affinity/traits never bypass faction, budget, cooldown, observer, task-priority, or safety rules.

**Verification:**
- Resurrection follows normal death/corpse rules.
- Success is recorded only after actual resurrection.
- Memory does not grow as all-to-all pairs across ~3000 bots.
- Only real significant outcomes affect memory.
- Traits remain stable enough to represent character tendencies and never enable speech in BOT_BOT mode.

**Done when:** Resurrection is real and safe, and bounded persistent relationships can influence candidate preference without violating higher-priority constraints.

---

### Phase 5: Economic Matching and Real Direct Trade

**Goal:** Allow two bots with real complementary economic needs to complete a real direct trade without duplicating Auction AI activity or corrupting inventory/money state.

**Touches:**
- economic need/surplus discovery
- MarketPriceService
- PlayerBots trade pipeline
- Auction AI / NeedList
- inventory/money reservations

**Tasks:**
- [ ] Match real buyer need to real seller surplus while considering inventory, mail/pending purchases, crafting reservations, upgrades, AH state, and budgets.
- [ ] Reserve quantities/money so the same stock cannot participate simultaneously in trade, AH, crafting consumption, or NPC sale.
- [ ] Execute the normal trade pipeline with approach, offer validation, acceptance, confirmation, timeout/cancel, and final state verification.
- [ ] Price actual quantity through the active market-price service and preserve spending/seller/resale/circular-trade protections.
- [ ] Recalculate/update Auction AI and NeedList after confirmed trade so the fulfilled quantity is not bought again.

**Verification:**
- Real items and money move through the normal trade system.
- No bag space -> trade safely fails.
- Reserved crafting stock is not sold.
- One item quantity cannot be sold simultaneously through trade and AH.
- NeedList reflects fulfilled need after confirmed trade.
- Observer loss during indivisible trade confirmation reaches a safe boundary and then the scene stops.
- BOT_BOT chat/LLM remains zero.

**Done when:** A real economic need can be satisfied by a real direct transaction with consistent inventory/money/reservation state and no duplicate Auction AI purchase.

---

### Phase 6: Real Player Observer Gate and Existing-Feature Retrofit

**Goal:** Make the real-player observer requirement a mandatory lifecycle invariant for every BOT_BOT interaction implemented in Phases 1-5 before adding group or combat-assistance behavior.

**Touches:**
- module: `mod-playerbot-interactions`
- PlayerBots/Core visibility/map/phase APIs
- existing healing/buff/resurrection/gesture/trade flows
- debug/metrics

**Tasks:**
- [ ] Define one authoritative observer/common-observer policy using the verified real-player/playerbot distinction plus compatible map, instance, phase, distance, and server-side visibility.
- [ ] Enforce observer checks at discovery, participant selection, pre-task assignment, approach/waiting, immediately before each new gameplay action, and before phase transitions.
- [ ] Implement `NO_REAL_PLAYER_OBSERVER` cancellation, releasing module-owned tasks/reservations and restoring normal AI while allowing indivisible core operations to finish at a safe boundary.
- [ ] Add observer proximity caching/throttling and anti-duplication without making observer arrival a trigger or multiplying scene rate for multiple observers.
- [ ] Add observer diagnostics and regression verification across all BOT_BOT functionality from Phases 1-5.

**Verification:**
- Real player only in Orgrimmar -> no new BOT_BOT interaction scenes in distant Mulgore.
- Eligible real player arrives near bots -> otherwise-valid scenes become permitted.
- Observer leaves before action -> action does not start.
- Observer leaves during approach/wait -> scene cancels, reservations/tasks release, normal AI resumes.
- Observer leaves during final indivisible trade persistence -> transaction finishes safely, then no further scene action occurs.
- One observer leaves while another eligible common observer remains -> scene may continue.
- Multiple observers -> no duplicate scene and no multiplied frequency.
- Observer arrival alone -> no burst of heals/buffs/trades/gestures.
- Bots are not teleported or redirected to humans solely to create scenes.
- Healing, buff, resurrection, gestures, and trade all obey the same observer invariant.
- Normal PlayerbotAI/BackgroundProgression/crafting/gathering/leveling continue without nearby observers.
- `BOT_BOT dialogue messages sent = 0`.
- `BOT_BOT LLM requests = 0`.

**Debug requirements:**
- `ObserverCount`
- `HasCommonObserver`
- `ObserverCheckAge`
- `ObserverBlockReason`
- `CancellationReason`

**Done when:** Existing BOT_BOT behaviors from Phases 1-5 cannot start or continue new scene actions without an eligible common real-player observer, and observer loss terminates them at the correct safe boundary without breaking unrelated bot systems.

---

### Phase 7: Temporary Small Bot Groups in Open World

**Goal:** Allow compatible bots to form small module-owned temporary groups for real open-world goals while respecting the observer invariant and existing group/LFG/player-controlled activity.

**Touches:**
- PlayerBots group actions/group AI
- InteractionTask ownership
- open-world goal compatibility
- BackgroundProgression
- observer lifecycle

**Tasks:**
- [ ] Define eligible real cooperative goals (e.g. compatible grind or actually-held compatible quests) and exclude fake/background-only QUEST_LIKE state.
- [ ] Select compatible available participants without disturbing existing player groups, LFG/BG/raid state, or direct human control.
- [ ] Create/track only module-owned temporary groups through normal group mechanics with leader, route, timeout, completion condition, and exit reason.
- [ ] Coordinate BackgroundProgression so real cooperative gameplay is not double-rewarded and only real gameplay grants XP/loot/quest progress.
- [ ] Apply observer-gated start/continuation rules and safe-boundary cleanup, especially during combat.

**Verification:**
- No temporary BOT_BOT group is created without an eligible common observer.
- Observer presence alone does not create a group.
- Existing groups are never broken to free participants.
- Group creation uses real group mechanics and real compatible goals.
- Observer loss during safe idle activity cleanly ends module-owned cooperation.
- Observer loss during combat does not destructively disband the group mid-combat.
- After reaching a safe boundary, no new module-owned cooperative task begins without an observer.
- Only groups owned by this mechanism are automatically disbanded.
- No duplicate BackgroundProgression rewards occur during real cooperative gameplay.

**Done when:** Small open-world bot groups can form, play, and end safely through normal group mechanics while fully respecting ownership, progression, and observer rules.

---

### Phase 8: Optional Combat Assistance

**Goal:** Add narrowly-scoped friendly combat assistance only after separate gameplay-safety validation.

**Touches:**
- combat AI
- ownership/loot/XP/PvP rules
- observer lifecycle
- group compatibility

**Tasks:**
- [ ] Define strict eligibility for assistance, initially preferring bots already in compatible cooperative groups rather than arbitrary passersby.
- [ ] Validate loot/ownership/XP/PvP implications and prevent interference with real-player targets or unintended PvP.
- [ ] Evaluate helper safety/risk and compatibility with current combat AI before initiating assistance.
- [ ] Gate each newly initiated assistance action on an eligible common real-player observer without making observer presence the trigger.
- [ ] Add cancellation/stop behavior that prevents new module-owned assistance after observer loss without corrupting normal core combat state.

**Verification:**
- Combat assistance cannot start without an eligible common observer.
- Observer presence does not itself trigger combat assistance.
- Observer eligibility is refreshed before newly initiated assistance actions.
- Observer loss prevents new module-owned assistance while existing core combat state remains valid.
- No mass neighborhood aggro/help response occurs.
- No loot stealing from real players.
- No unintended PvP.
- No obviously suicidal assistance that violates configured safety criteria.

**Done when:** Limited combat assistance is safe, observer-gated, and demonstrably does not break ownership, PvP, loot, or normal combat AI behavior.

---

### Phase 9: Load Testing and Gradual Rollout

**Goal:** Validate the interaction layer under realistic server scale and enable functionality gradually without degrading world performance.

**Touches:**
- metrics
- scene/candidate limits
- cooldown tuning
- rollout configuration
- server performance

**Tasks:**
- [ ] Measure baseline and feature-enabled worldserver metrics on a small selected bot cohort before broad rollout.
- [ ] Validate event/candidate selection avoids all-pairs scans and respects global/local/per-bot/per-pair limits.
- [ ] Tune scene/candidate/cooldown limits from observed load rather than assuming initial values are optimal.
- [ ] Verify graceful degradation: decorative initiatives reduce first when latency/load rises while atomic transactions are not corrupted.
- [ ] Expand rollout gradually only after functional, silence, observer, and performance checks pass.

**Verification:**
- One event does not attract dozens of helpers.
- Two observers do not duplicate a scene.
- No all-pairs bot scan is introduced.
- Local/global scene limits are respected.
- No unexplained meaningful regression in baseline worldserver performance.
- BOT_BOT dialogue messages sent remains zero.
- BOT_BOT LLM requests remains zero.
- New functionality is initially enabled only for a controlled bot cohort.

**Done when:** The module is proven stable under representative load and can be rolled out progressively with measured limits and no unexplained performance regression.

---

## Global Verification Matrix

### Functionality
- [ ] Real healing succeeds through game mechanics.
- [ ] Healthy targets do not trigger repeated healing attempts.
- [ ] Missing mana/spell blocks action.
- [ ] Buffs do not recurse indefinitely.
- [ ] Resurrection follows the normal resurrection flow.
- [ ] Target-state changes safely cancel scenes.
- [ ] Direct trade transfers real items and real money.
- [ ] No bag space safely blocks trade.
- [ ] Crafting-reserved items are not sold.
- [ ] NeedList is refreshed after fulfillment.
- [ ] Stock cannot be consumed by trade and AH simultaneously.
- [ ] Temporary groups do not break existing groups.

### Integration and State Safety
- [ ] CityLife does not steal active interaction participants.
- [ ] BackgroundProgression does not double-reward active interaction time.
- [ ] Normal activity resumes after scene completion/cancellation.
- [ ] Logout/teleport/death safely releases module-owned state.
- [ ] No stale `Player*` / `Item*` or equivalent invalid world-object state is retained.
- [ ] Observer loss does not corrupt an indivisible in-progress transaction.

### Silence
- [ ] BOT_BOT sends no say/yell/whisper/party/raid/guild/channel dialogue.
- [ ] BOT_BOT sends no textual emotes.
- [ ] BOT_BOT triggers no LLM dialogue request.
- [ ] Indirect healing/trade/group hooks do not create speech.
- [ ] Delayed callbacks preserve the BOT_BOT speech policy.
- [ ] A nearby human observer does not enable BOT_BOT dialogue.
- [ ] Direct real-player-to-bot dialogue still works.
- [ ] Required gameplay/system packets are not blocked.

### Observer Invariant
- [ ] A remote human elsewhere on the server does not permit a BOT_BOT scene.
- [ ] At least one common observer can permit an otherwise-valid scene.
- [ ] Observer loss is revalidated throughout the scene lifecycle.
- [ ] Multiple observers do not duplicate scenes.
- [ ] Observer arrival does not itself trigger mass interaction.
- [ ] Unrelated PlayerBot world activity remains active without observers.

### Performance
- [ ] One event does not attract excessive candidates/helpers.
- [ ] Multiple observers do not multiply scene count.
- [ ] No all-pairs bot scan occurs.
- [ ] Local/global limits are respected.
- [ ] Performance changes are measured and explainable.

---

## Release Rules

- Incomplete capabilities remain disabled by default.
- Do not publish an enabled config flag for a stub/non-working feature.
- Start with a small predefined bot cohort, not all ~3000 RandomBots.
- Do not disable SmartScale.
- Do not activate large areas solely to create scenes.
- Do not teleport participants to make interactions visible.
- Destructive changes or production server restarts require explicit approval.
- A successful compile is not sufficient to declare the module complete.
