# Исправление mod-random-enchants - Ошибка SQL запроса

## Проблема
Модуль `mod-random-enchants` дает **слишком высокие характеристики** низкоуровневым предметам:
- Предметы уровня 1-14 получают tier 5 энчанты
- Пример: "Простые льняные штаны" (уровень 5) получают +26/+44/+56 к статам вместо +3-5

## Причина
SQL запрос в файле `modules/mod-random-enchants/src/random_enchants.cpp` (строка 170) имеет **ошибку логики операторов**:

```cpp
// НЕПРАВИЛЬНО - OR class='ANY' игнорирует ограничение tier
QueryResult result = WorldDatabase.Query("SELECT `enchantID` FROM `item_enchantment_random_tiers` WHERE `tier`={} AND `exclusiveSubClass`=NULL AND exclusiveSubClass='{}' OR `class`='{}' OR `class`='ANY'{} ORDER BY RAND() LIMIT 1",
    tier, item->GetTemplate()->SubClass, classQueryString, classQueryString, statFilter);
```

Из-за приоритета операторов SQL, условие `OR class='ANY'` применяется ко **всем tier'ам**, игнорируя ограничение `tier=1`.

## Решение
Добавить **скобки** для правильной группировки условий:

```cpp
// ПРАВИЛЬНО - tier проверяется обязательно
QueryResult result = WorldDatabase.Query("SELECT `enchantID` FROM `item_enchantment_random_tiers` WHERE `tier`={} AND (`exclusiveSubClass` IS NULL OR `exclusiveSubClass`='{}') AND (`class`='{}' OR `class`='ANY'){} ORDER BY RAND() LIMIT 1",
    tier, item->GetTemplate()->SubClass, classQueryString, statFilter);
```

## Как применить исправление

### Шаг 1: Остановить сервер
```bash
# Остановить worldserver
```

### Шаг 2: Применить исправление
Открыть файл: `C:/azerothcore/azerothcore-wotlk/modules/mod-random-enchants/src/random_enchants.cpp`

Найти строку 170 и заменить на:
```cpp
QueryResult result = WorldDatabase.Query("SELECT `enchantID` FROM `item_enchantment_random_tiers` WHERE `tier`={} AND (`exclusiveSubClass` IS NULL OR `exclusiveSubClass`='{}') AND (`class`='{}' OR `class`='ANY'){} ORDER BY RAND() LIMIT 1",
    tier, item->GetTemplate()->SubClass, classQueryString, statFilter);
```

**Изменения:**
1. Добавлены скобки: `(`exclusiveSubClass` IS NULL OR `exclusiveSubClass`='{}')`
2. Добавлены скобки: `(`class`='{}' OR `class`='ANY')`  
3. Заменено `exclusiveSubClass=NULL` на `exclusiveSubClass` IS NULL`
4. Удален дублирующий параметр `classQueryString`

### Шаг 3: Пересобрать модуль
```bash
cd C:/azerothcore/azerothcore-wotlk/build
cmake --build . --config RelWithDebInfo --target modules
cmake --install . --config RelWithDebInfo
```

### Шаг 4: Перезапустить сервер

### Шаг 5: Проверить
Создать предмет через портняжку (например, "Простые льняные штаны"):
- **До исправления:** +26/+44/+56 к статам
- **После исправления:** +3-5 к статам (tier 1 энчанты)

## Проверка работы
После применения исправления предметы будут получать энчанты по уровням:
- **Уровень 1-14:** только tier 1 (+3-5 к статам)
- **Уровень 15-29:** максимум tier 2 (+6-10 к статам)
- **Уровень 30-44:** максимум tier 3 (+11-15 к статам)
- **Уровень 45-59:** максимум tier 4 (+16-20 к статам)
- **Уровень 60+:** все tier'ы доступны (+20-30 к статам)

## Статус исправления
✅ Код исправлен в: `C:/azerothcore/azerothcore-wotlk/modules/mod-random-enchants/src/random_enchants.cpp`  
❌ Модуль не пересобран (проблема с зависимостями Boost/ZLIB)  
⏳ Требуется пересборка после решения проблем с vcpkg

---
**Дата:** 16 сентября 2024  
**Исправлено:** SQL запрос в GetEnchantment() - строка 170-171
