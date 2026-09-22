# Plan: plan-server-activities-mount-roulette-system.md

**PRD:** @docs/prd-server-activities-mount-roulette-system.md
**Date:** 2026-09-22

## Scope

Три новых модуля: `mod-server-activities` (ежедневные активности, лимиты, выдача круток), `mod-mount-roulette` (баланс круток, RNG, pity, маунты, shards, коллекция, AIO-интерфейс), `mod-world-events` (случайные мировые события). Все активности и интерфейс доступны только при `Level >= RequiredLevel` (по умолчанию 80). Все значения в конфиге. GM-команды `.mroulette`, `.mactivity`, `.mevent`. Отдельный лог `MountRoulette.log`.

Вне объёма (PRD §20 и Phase 5 roadmap): сезонный контент, питомцы/игрушки/трансмог/титулы/баннеры, интеграция playerbots.

## Existing architecture

- Модули подключаются как статические скрипты (`modules/*/src`, loader `Add<Name>Scripts()`); SQL модуля — `data/sql/db-characters|db-world|db-auth` (пример: `modules/mod-mythic-plus/data/sql/db-characters/`). Команды модуля — `CommandScript` (пример: `modules/mod-dungeon-clear/src/DungeonClearCommand.cpp`). Свой лог-файл через `Appender.*`/`Logger.*` в `.conf.dist` модуля (пример: `Appender.DungeonClear` в `mod-dungeon-clear`).
- Хуки для активностей (проверено по объявлениям):
  - BG victory: `AllBattlegroundScript::OnBattlegroundEndReward(bg, player, winnerTeamId)`.
  - Dungeon / Heroic completion: `GlobalScript::OnAfterUpdateEncounterState(map, …, difficulty, encounters, dungeonCompleted, updated)`; используется в `mod-autobalance/src/ABGlobalScript.cpp`.
  - Raid boss / World boss участие: `PlayerScript::OnPlayerRewardKillRewarder(player, rewarder, isDungeon, …)` — вызывается для каждого игрока, получающего kill credit (группа + дистанция решаются ядром).
  - Achievement: `PlayerScript::OnPlayerAchievementComplete`.
  - Lifetime: `OnPlayerLogin`, `OnPlayerLogout`, `OnPlayerDeleteFromDB`.
  - Кандидаты без подтверждённой семантики: `OnPlayerGiveXP(xpSource)` / `OnPlayerCanAreaExploreAndOutdoor` (exploration), `OnPlayerUpdateGatheringSkill` / `OnPlayerUpdateCraftingSkill` / `OnPlayerUpdateFishingSkill` (срабатывают на skill-up, на капе — не проверено), `OnPlayerLootItem` (сбор/рыбалка по списку item ID).
- Lua: `mod-ale` включён (`ALE.ScriptPath = "lua_scripts"`, runtime `C:\azerothcore\server\bin\lua_scripts`). Есть `ADDON_EVENT_ON_MESSAGE` и `PLAYER_EVENT_ON_COMMAND`. **AIO не установлен** (в `lua_scripts` только `extensions`).
- `mod-npc-all-mounts` содержит SQL со списком маунтов — возможный источник spell ID для конфигов наград (только данные, не зависимость).
- Модульных автотестов нет; верификация — targeted build + runtime-сценарии + read-only проверка БД/логов.

## Design decisions

- Хранилище — БД `characters` (схема модуля, стандартный updater модуля):
  - `mod_mount_roulette_account` (account_id PK, spins, shards, epic_pity, legendary_pity) — account-scoped данные PRD §19.
  - `mod_mount_roulette_collection` (account_id, spell_id) — коллекция.
  - `mod_server_activities_daily` (guid, activity_id, day_key, count) — дневные лимиты по персонажу.
- Ежедневный сброс — ленивый: `day_key` вычисляется из серверного времени и `ServerActivities.ResetHour`; нет периодической работы и массовых UPDATE.
- Кэш аккаунта загружается на логине (async), сохраняется транзакцией при изменении; ключ — account id / `ObjectGuid`, без хранения `Player*`.
- Playerbots (`IsBot`-предикат модуля playerbots) в v1.0 не получают крутки и не пишут в БД — интеграция ботов вне объёма. BOT_BOT правила не затрагиваются.
- Крутка выполняется только на сервере: списание, RNG, pity, выдача награды — в world thread одним путём; клиент получает только результат для анимации.

## Implementation phases

### Phase 1: Tracer bullet — BG victory даёт крутки

**Goal:** Игрок 80+ выигрывает BG, получает N круток один раз в день; GM видит и меняет баланс.

**Touches:**
- module/core: новые `modules/mod-server-activities`, `modules/mod-mount-roulette` (skeleton + loader)
- database: characters — `mod_mount_roulette_account`, `mod_server_activities_daily` (schema)
- config: `mod_server_activities.conf.dist` (`Enable`, `RequiredLevel`, `ResetHour`, `BG.Spins`, `BG.DailyLimit`), `mod_mount_roulette.conf.dist` (`RequiredLevel`, `SpinCost`, Appender/Logger `MountRoulette.log`)
- runtime: новый лог-файл

**Tasks:**
- [ ] Создать оба модуля, конфиги, SQL схемы; публичный API баланса в `mod-mount-roulette` (AddSpins/GetState по account id), используемый `mod-server-activities`.
- [ ] Activity Manager: реестр активностей, проверка уровня/бота, ленивый daily-limit по `day_key`, начисление через API.
- [ ] Активность Battleground Victory через `OnBattlegroundEndReward` (только игроки winnerTeam).
- [ ] Команды `.mroulette addspins <player> <n>`, `.mroulette info <player>` (spins, pity, дневные активности), `.mactivity reset <player>`; online + offline игрок.
- [ ] Логирование начисления (игрок, активность, крутки) в `MountRoulette.log`.

**Verification:**
- build: инкрементальная сборка `worldserver`.
- runtime/gameplay: модули грузятся без ошибок; BG win игроком 80 уровня → +N круток; вторая победа в тот же день → 0; игрок <80 → 0; `.mactivity reset` снимает лимит.
- DB/log verification: read-only select по `mod_mount_roulette_account`, `mod_server_activities_daily`; строки в `MountRoulette.log`.

**Done when:** `.mroulette info` показывает крутки, начисленные реальной BG победой, и лимит 1/1 соблюдается.

### Phase 2: PvE и Achievement активности

**Goal:** Dungeon, Heroic, Raid Boss, Achievement выдают крутки по своим лимитам.

**Touches:**
- module/core: `mod-server-activities`
- config: `Dungeon.*`, `Heroic.*`, `Raid.*`, `Achievement.*` (Spins, DailyLimit, Enable)

**Tasks:**
- [ ] Dungeon/Heroic через `OnAfterUpdateEncounterState` при `dungeonCompleted != 0`; тип по `map->IsNonRaidDungeon()` + difficulty; кредит игрокам карты с уровнем 80+.
- [ ] Raid Boss через `OnPlayerRewardKillRewarder` для boss-существ на raid-карте (участие и «рядом» — из KillRewarder, «в рейде» — raid group).
- [ ] Achievement через `OnPlayerAchievementComplete` (опционально фильтр по списку ID из конфига — только если нужен для антиспама, иначе любое).
- [ ] Отображение новых активностей в `.mroulette info`.

**Verification:**
- build: `worldserver`.
- runtime/gameplay: пройти normal и heroic подземелье (или `.instance` + убийство последнего босса GM) → раздельные начисления; убить рейд-босса в рейде вне дистанции → нет кредита, рядом → кредит; получить достижение `.achievement add` → кредит 1 раз/день.
- DB/log verification: строки активностей в `mod_server_activities_daily` и лог.

**Done when:** Каждая из 4 активностей начисляет крутки ровно один раз в день и только участникам 80+.

### Phase 3: Mount Roulette backend

**Goal:** Серверная крутка: RNG по редкостям, pity, маунт или shards за дубликат, коллекция.

**Touches:**
- module/core: `mod-mount-roulette`
- database: characters — `mod_mount_roulette_collection` (schema)
- config: `Chance.Common|Rare|Epic|Legendary|Mythic`, `Rewards.<Rarity>` (списки spell ID), `EpicPity`, `LegendaryPity`, `DuplicateShards.<Rarity>`, `ShardCost`

**Tasks:**
- [ ] Загрузка и валидация конфига (сумма шансов, существование spell ID через `sSpellMgr`), ошибки в лог при старте/reload.
- [ ] Spin: проверка уровня и `SpinCost`, RNG (`urand`/`rand_chance`), pity-счётчики (Legendary ≥ Epic приоритет, сброс при выпадении редкости ≥ порога).
- [ ] Выдача: `learnSpell` маунта + запись в коллекцию; если уже изучен → shards; сохранение транзакцией.
- [ ] Команды `.mroulette spin <player>`, `.mroulette reward <player> <spellId>`.
- [ ] Лог: потраченные крутки, редкость, маунт/shards.

**Verification:**
- build: `worldserver`.
- runtime/gameplay: с тестовым конфигом `EpicPity=3` серия `.mroulette spin` гарантирует Epic на 3-й без Epic; дубликат даёт shards; без круток — отказ; <80 — отказ.
- DB/log verification: pity/shards/collection в БД совпадают с логом.

**Done when:** `.mroulette spin` детерминированно соблюдает pity и корректно обрабатывает дубликаты.

### Phase 4: AIO интерфейс

**Goal:** Игрок 80+ открывает окно Mount Roulette, жмёт SPIN, видит анимацию и серверный результат, spins и pity; окно коллекции.

**Touches:**
- runtime: установка AIO (server Lua в `lua_scripts`, client addon) — **требует разрешения на загрузку внешнего кода**
- module/core: `mod-mount-roulette` (bridge), Lua-скрипты модуля

**Tasks:**
- [ ] Spike: выбрать и проверить мост Lua(AIO) ↔ C++ (см. Open questions), зафиксировать решение.
- [ ] Серверный AIO handler: Spin Request → C++ spin → ответ (результат, spins, pity); никаких наград, выбранных клиентом.
- [ ] Клиентское окно: SPIN, spins, Epic/Legendary pity, анимация по результату сервера.
- [ ] Окно коллекции (список из `mod_mount_roulette_collection`).
- [ ] Отказ доступа для игроков <80 на сервере (не только скрытие UI).

**Verification:**
- runtime/gameplay: реальный клиент 3.3.5a: окно открывается, spin меняет состояние, повторный запрос с 0 круток отклоняется; игрок 79 — нет доступа; подменённый клиентский запрос не влияет на награду.
- DB/log verification: каждая UI-крутка есть в логе и БД.

**Done when:** Реальный клиент крутит рулетку через UI с результатом, совпадающим с БД и логом.

### Phase 5: World events framework + Invasion + World Boss активность

**Goal:** `.mevent start|stop invasion` запускает/останавливает вторжение; участники убийства финального босса получают кредит World Event/World Boss.

**Touches:**
- module/core: новый `modules/mod-world-events`
- config: `WorldEvents.Enable`, интервал/шанс случайного старта, Invasion: зона, entries волн/элит/босса, координаты; `WorldEvent.*`, `WorldBoss.*` в `mod-server-activities`

**Tasks:**
- [ ] Менеджер событий: состояние по id, запуск по таймеру через `WorldScript::OnUpdate` с накопителем (без сканов каждый тик), announce.
- [ ] Invasion: волны → элиты → финальный босс через TempSummon на карте зоны; хранение `ObjectGuid`, despawn при stop/завершении/выгрузке карты.
- [ ] Кредит World Event/World Boss через `OnPlayerRewardKillRewarder` по entry финального/мирового босса.
- [ ] Команды `.mevent start <id>`, `.mevent stop <id>`.

**Verification:**
- build: `worldserver`.
- runtime/gameplay: `.mevent start invasion` в Western Plaguelands → волны и босс; убийство группой 80 → кредит 1/1; `.mevent stop` удаляет все спавны; перезапуск события не оставляет «сирот».
- DB/log verification: кредиты в daily-таблице; логи старта/стопа без спама.

**Done when:** Invasion полностью проходит цикл start → волны → босс → кредит → cleanup.

### Phase 6: Exploration, Profession, Fishing активности

**Goal:** Оставшиеся активности PRD §7 начисляют крутки 1 раз в день.

**Touches:**
- module/core: `mod-server-activities`
- config: списки item/area ID для редкого крафта, сбора, рыбалки, зон ловли

**Tasks:**
- [ ] Проверить, срабатывают ли кандидаты-хуки на 80 уровне и max skill; выбрать хуки (см. Open questions).
- [ ] Exploration: открытие новой зоны/области.
- [ ] Profession: редкий крафт / сбор / создание предмета по спискам из конфига.
- [ ] Fishing: улов предмета из списка редкой рыбы или в спец-зоне.

**Verification:**
- runtime/gameplay: для каждой активности один положительный и один отрицательный сценарий (не тот предмет/зона, повтор в тот же день).

**Done when:** Все активности §7 дают кредит по конфигу и соблюдают лимит.

### Phase 7: Остальные World Random Events

**Goal:** City Defense, Caravan Escort, Random World Boss, Treasure Hunt, Rare Hunt, Resource Rush, Fishing Frenzy, Bounty Hunt, Portal Event, Corrupted Zone, Dungeon Event, World PvP Event, Server Wide Event работают на фреймворке Phase 5.

**Tasks:**
- [ ] Разбить на под-фазы по общим механикам: spawn-and-kill (Random World Boss, Rare Hunt, Bounty Hunt, Portal), defend/escort (City Defense, Caravan), collect (Treasure Hunt, Resource Rush, Server Wide), modifiers (Corrupted Zone, Dungeon Event, Fishing Frenzy), PvP (World PvP).
- [ ] Для каждого события — данные (NPC entries, координаты, пути, награды) и отдельная верификация.

**Verification:** runtime-сценарий start → цель → награда → stop/cleanup для каждого события.

**Done when:** Каждое событие проходит свой runtime-сценарий. Эта фаза требует уточнения дизайна до реализации.

## Open questions

1. **Мост AIO ↔ C++.** ALE не даёт прямого вызова C++ модуля. Варианты: Lua-реализация только UI + C++ приём addon-сообщений (`ADDON_EVENT_ON_MESSAGE` или PlayerScript chat-хук) по своему префиксу; или player-команда уровня SEC_PLAYER. Нужна проверка в Phase 4 spike.
2. **Установка AIO** (внешний код Rochet2/AIO, сервер + клиентский аддон) — нужно разрешение и выбор версии.
3. **Коллекция и дубликаты:** «уже изучен» — на текущем персонаже или в аккаунтной коллекции? Изучать маунта всем персонажам аккаунта?
4. **Shards:** PRD задаёт «стоимость shards», но не механику траты. Тратятся ли shards (обмен на крутку/маунта)? Без ответа — только накопление.
5. **Количество круток** по каждой активности и значения шансов по умолчанию — не заданы.
6. **Exploration/Profession/Fishing:** точные условия («редкий крафт», «спец-зоны») и работоспособность хуков на капе не подтверждены.
7. **Детали World Events** Phase 7 (зоны, NPC, награды «золото/ресурсы/shards») не заданы.
8. **Время ежедневного сброса** — предлагается `ResetHour` по серверному времени; подтвердить.
9. **Account data в `characters` vs `auth`:** план использует `characters` (account-scoped таблицы). Подтвердить, что это приемлемо.
