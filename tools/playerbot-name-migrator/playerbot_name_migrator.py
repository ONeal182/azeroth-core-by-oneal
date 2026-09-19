#!/usr/bin/env python3
"""
Playerbot name migrator for AzerothCore WotLK 3.3.5a + mod-playerbots.

Renames ONLY confirmed random-bot characters. A character guid is treated as a
bot if and only if BOTH are true (mirrors RandomPlayerbotMgr::IsRandomBot):
  1. its owning account name matches the configured random-bot account prefix
     (acore_auth.account.username LIKE '<prefix>%', default 'rndbot')
  2. it has an active row in acore_playerbots.playerbots_random_bots
     (owner = 0, event = 'add', value = 1)

Any mismatch between these two sources aborts the whole run with no DB writes.

Stages: analyze -> dry-run -> apply (explicit) -> rollback (explicit).
Nothing is written to the database unless --apply is passed together with
--confirm.
"""

import argparse
import csv
import random
import re
import sys
import time
from dataclasses import dataclass, field

import pymysql
import pymysql.cursors

# ---------------------------------------------------------------------------
# DB connection defaults (from server/configs/{worldserver,modules/playerbots}.conf)
# ---------------------------------------------------------------------------

DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "acore"
DB_PASS = "acore"
DB_AUTH = "acore_auth"
DB_CHAR = "acore_characters"
DB_BOTS = "acore_playerbots"
RANDOM_BOT_PREFIX = "rndbot"

MAX_PLAYER_NAME = 12
MIN_PLAYER_NAME = 2

CYRILLIC_RE = re.compile(r"^[А-Яа-яЁё]+$")


def connect(database: str):
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
        database=database, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


# ---------------------------------------------------------------------------
# Name validity (mirrors ObjectMgr::CheckPlayerName rules the client enforces)
# ---------------------------------------------------------------------------

def has_three_consecutive(s: str) -> bool:
    low = s.lower()
    return any(low[i] == low[i - 1] == low[i - 2] for i in range(2, len(low)))


def is_valid_name(s: str) -> bool:
    if not (MIN_PLAYER_NAME <= len(s) <= MAX_PLAYER_NAME):
        return False
    if not CYRILLIC_RE.match(s):
        return False
    if s[0] != s[0].upper() or s[1:] != s[1:].lower():
        return False
    if has_three_consecutive(s):
        return False
    return True


def cap_case(s: str) -> str:
    return s[0].upper() + s[1:].lower()


# ---------------------------------------------------------------------------
# Word banks. Every entry is a short, single-alphabet (Cyrillic) token.
# Combinators join two tokens with NO separator (spaces/underscores/digits
# are forbidden by the client), so bank words are kept short on purpose.
# ---------------------------------------------------------------------------

SOLO_NICK = [
    "Север", "Шрам", "Лютый", "Тихий", "Мороз", "Карась", "Седой", "Гром",
    "Вжик", "Феникс", "Барс", "Ветер", "Штиль", "Уголь", "Кремень", "Хмурый",
    "Ярость", "Азарт", "Скиталец", "Отшельник", "Странник", "Изгой",
    "Кочевник", "Бродяга", "Гроза", "Вьюга", "Полынь", "Осока", "Рябина",
    "Ольха", "Клык", "Коготь", "Оскал", "Хищник", "Волчок", "Барсук", "Рысь",
    "Сокол", "Ястреб", "Ворон", "Грач", "Филин", "Ёрш", "Судак", "Окунь",
    "Плотва", "Хариус", "Таймень", "Ленок", "Чибис", "Кулик", "Зяблик",
    "Дятел", "Кедр", "Пихта", "Ясень", "Тополь", "Иволга", "Береза",
    "Осина", "Крапива", "Репей", "Лопух", "Валун",
    "Утёс", "Обрыв", "Пустошь", "Топь", "Трясина", "Бурелом", "Чаща",
    "Опушка", "Проседь", "Изморозь", "Наледь", "Гололёд", "Оттепель",
    "Слякоть", "Дымка", "Хмарь", "Морок", "Полумрак", "Сумрак", "Закат",
    "Рассвет", "Полдень", "Полночь", "Зарница", "Всполох", "Отблеск",
    "Стужа", "Заноза", "Огрызок", "Осколок", "Обломок", "Черепок",
    "Ошмёток", "Пельмень", "Огурец", "Чеснок", "Хрен", "Перец", "Изюм",
    "Урюк", "Курага", "Ирис", "Кисель", "Морс", "Компот", "Квас", "Сбитень",
    "Медовуха", "Брага", "Самогон", "Ерофеич", "Пузырь", "Бочка", "Бидон",
    "Канистра", "Лейка", "Грабли", "Лопата", "Тяпка", "Метла", "Веник",
    "Совок", "Молоток", "Гвоздь", "Шуруп", "Дюбель", "Рубанок", "Стамеска",
    "Напильник", "Разводной", "Домкрат", "Насос", "Ниппель", "Тормоз",
    "Глушак", "Карбюратор", "Стартер", "Генератор", "Движок",
    "Пыжик", "Малыш", "Здоровяк", "Крепыш", "Толстяк", "Худышка",
    "Коротышка", "Верзила", "Силач", "Ловкач", "Хитрец", "Простак",
    "Растяпа", "Разгильдяй", "Растрёпа", "Задира", "Балагур", "Молчун",
    "Ворчун", "Хохотун", "Непоседа", "Домосед", "Полуночник",
    "Забияка", "Проныра", "Ротозей", "Шалопай", "Сорвиголова",
    "Оболтус", "Лежебока", "Ротатор", "Живчик", "Крикун", "Ябеда",
    "Задавака", "Воображала", "Свистун", "Скоморох", "Бирюк", "Увалень",
    "Соня", "Ленивец", "Проказник", "Затейник", "Выдумщик", "Умелец",
    "Кулибин", "Самородок", "Талисман", "Оберег", "Амулет", "Символ",
    "Сюрприз", "Загадка", "Сплетник", "Балабол", "Тамада", "Заводила",
    "Затейница", "Певунья", "Плясунья", "Хохотушка",
    "Ромашка", "Незабудка", "Одуванчик", "Подснежник", "Ландыш",
    "Колокольчик", "Василёк", "Клевер", "Мятлик", "Подорожник",
    "Пастушок", "Пастушка", "Мельник", "Косарь", "Пахарь", "Бортник",
    "Птицелов", "Зверолов", "Следопыт", "Проводник", "Дозорный",
    "Сторож", "Караульный", "Гонец", "Вестник", "Посланник", "Лазутчик",
    "Разведчик", "Проходимец", "Пройдоха", "Плут", "Шельма", "Пройда",
    "Бузотёр", "Скандалист", "Правдоруб", "Миротворец", "Заступник",
    "Спаситель", "Освободитель", "Победитель", "Чемпион", "Рекордсмен",
    "Ветеран", "Новичок", "Ученик", "Подмастерье", "Знаток", "Эксперт",
    "Мудрец", "Философ", "Летописец", "Хранитель", "Собиратель",
    "Коллекционер", "Изобретатель", "Механик", "Испытатель",
    "Затворник", "Ротозей", "Полуношник", "Скороход", "Тугодум",
    "Балагур", "Егоза", "Непруха", "Везунчик", "Счастливчик", "Тугодум",
    "Пустомеля", "Говорун", "Молчальник", "Крикунья", "Хвастун",
    "Ленивчик", "Проныра", "Затейщик", "Мастак", "Умелец", "Ловчила",
    "Хитрован", "Хват", "Шустряк", "Юркий", "Прыткий", "Бойкий",
    "Смышлёный", "Смекалистый", "Дошлый", "Тёртыш", "Стойкий", "Крепкий",
    "Ражий", "Дюжий", "Матёрый", "Пузатый", "Долговязый", "Курносый",
    "Рыжий", "Кудрявый", "Лохматый", "Патлатый", "Лысый", "Бородатый",
    "Усатый", "Косматый", "Бровастый", "Зубастый", "Языкастый",
    "Пузырёк", "Стручок", "Колосок", "Початок", "Корешок", "Веточка",
    "Листочек", "Цветочек", "Зёрнышко", "Камешек", "Ракушка", "Жемчуг",
    "Янтарь", "Малахит", "Гранит", "Мрамор", "Кварц", "Самоцвет",
    "Родничок", "Ручеёк", "Озерцо", "Затон", "Плёс", "Перекат",
    "Ивняк", "Ельник", "Сосняк", "Дубняк", "Березняк", "Осинник",
    "Пасечник", "Рыбак", "Лесник", "Егерёк", "Смотритель", "Часовой",
    "Пограничник", "Наблюдатель", "Искатель", "Странствующий",
    "Кряж", "Взгорок", "Ложбина", "Балка", "Овраг", "Курган", "Холм",
    "Взлобок", "Косогор", "Распадок", "Ельцо", "Согра", "Марь",
    "Зимовье", "Заимка", "Хутор", "Заведёнка", "Выселки", "Починок",
    "Пустырь", "Целина", "Залежь", "Пажить", "Выгон", "Пастбище",
    "Загон", "Стойло", "Хлев", "Сарай", "Амбар", "Овин", "Гумно",
    "Погреб", "Ледник", "Сеновал", "Кузня", "Мельница", "Пасека",
    "Колодец", "Криница", "Студенец", "Ключ", "Исток", "Устье",
    "Стрежень", "Мель", "Коса", "Отмель", "Стремнина", "Заводь",
    "Бухта", "Гавань", "Пристань", "Причал", "Маяк", "Бакен",
    "Компас", "Штурвал", "Якорь", "Парус", "Мачта", "Трюм", "Палуба",
    "Борт", "Корма", "Нос", "Штиль", "Шторм", "Прибой", "Волнорез",
    "Пирс", "Мол", "Рейд", "Фарватер", "Буй", "Причал",
    "Чабан", "Табунщик", "Конюх", "Наездник", "Возница", "Кучер",
    "Ямщик", "Извозчик", "Бондарь", "Гончар", "Ткач", "Прядильщик",
    "Вышивальщик", "Резчик", "Чеканщик", "Литейщик", "Клепальщик",
]

DIMINUTIVE_NAMES = [
    "Толян", "Серёга", "Витёк", "Санёк", "Вован", "Колян", "Стёпа", "Гриша",
    "Дениска", "Ромыч", "Тёма", "Слава", "Юрок", "Костян", "Пашка",
    "Мишаня", "Игорёк", "Максон", "Тимоха", "Ленчик", "Валера", "Жека",
    "Артём", "Богдан", "Данила", "Егорка", "Захар", "Илюха", "Кирюха",
    "Лёха", "Матвей", "Наиль", "Олежа", "Петруха", "Роберт", "Семён",
    "Тарас", "Федот", "Харитон", "Эдик", "Юран", "Яшка", "Макарыч",
    "Петрович", "Кузьмич", "Ильич", "Фомич", "Саныч", "Толяныч", "Витальич",
    "Андрюха", "Димон", "Ромас", "Славик", "Тимон", "Гоша", "Лёва", "Миха",
    "Ринат", "Тимка", "Юрец", "Яков", "Вадос", "Гарик", "Дениско",
    "Толик", "Вадик", "Костик", "Ромик", "Стасик", "Витя", "Женёк",
    "Колюня", "Мишутка", "Петюня", "Санчо", "Тёмыч", "Федюня", "Шурик",
    "Эдюня", "Юрик", "Яныч", "Богдос", "Данчик", "Захарыч", "Кирилыч",
    "Лёнчик", "Наилыч", "Олежик", "Робик", "Семёныч", "Тарасыч",
    "Харитоныч", "Игнатыч", "Прохор", "Аркаша", "Валик", "Гриня",
    "Антоха", "Борян", "Вадос", "Гарёк", "Денчик", "Ерёма", "Жорик",
    "Зинчик", "Ильюша", "Костик", "Лёва", "Марат", "Назар", "Осип",
    "Прошка", "Родик", "Савва", "Тихон", "Устин", "Фёдор", "Христя",
    "Эрик", "Юлик", "Ярик", "Афоня", "Бажен", "Вавила", "Гаврюша",
    "Дорофей", "Елисей", "Ждан", "Зот", "Иннокент", "Клим", "Лукьян",
    "Матюша", "Никодим", "Ося", "Пров", "Радим", "Спиря", "Тимофей",
    "Устинка", "Феоктист", "Харлам", "Цезарь", "Черныш", "Шурыга",
    "Щукарь", "Юхим", "Яромир", "Богуслав", "Всеслав", "Годимир",
    "Добран", "Ждислав", "Зорян", "Изяслав", "Казимир", "Лада",
]

NAME_PLUS_ITEM = [
    "Кабан", "Батон", "Пельмень", "Огурец", "Пряник", "Сухарь", "Валенок",
    "Бидон", "Обмылок", "Утюг", "Пиджак", "Веник", "Совок", "Тапок",
    "Бублик", "Кирпич", "Табурет", "Пылесос", "Бочонок", "Огрызок",
    "Кулёк", "Свёрток", "Клубок", "Мешок", "Чемодан", "Рюкзак", "Зонтик",
    "Половник", "Черпак", "Половик", "Коврик", "Матрас", "Подушка",
    "Носок", "Ремень", "Шнурок", "Клин", "Обод", "Каблук", "Сурок",
    "Огарок", "Черенок", "Ободок", "Патрон", "Штопор", "Половица",
    "Чайник", "Кастрюля", "Сковородка", "Ложка", "Вилка", "Кружка",
    "Стакан", "Графин", "Кувшин", "Ковшик", "Сито", "Дуршлаг", "Ступка",
    "Скалка", "Терка", "Кочерга", "Ухват", "Заслонка",
    "Секатор", "Топорик", "Пилка", "Стамеска", "Клещи", "Плоскогуб",
    "Отвёртка", "Молоточек", "Гаечка", "Шайбочка", "Болтик", "Винтик",
    "Гвоздик", "Проволока", "Изолента", "Скотч", "Клей", "Гайка",
    "Шпилька", "Заклёпка", "Прищепка", "Верёвка", "Бельё", "Тазик",
    "Ведёрко", "Корзинка", "Лукошко", "Кадка", "Кадушка", "Бадья",
]

DOMESTIC_ROLE = [
    "Сосед", "Царь", "Барон", "Маг", "Дух", "Страж", "Хозяин", "Гений",
    "Мастер", "Владыка", "Король", "Жилец", "Дворник", "Призрак", "Демон",
    "Шериф", "Смотритель", "Старшой", "Батя", "Атаман", "Князь", "Граф",
    "Бес", "Леший", "Домовой", "Тень", "Гуру", "Кудесник", "Знахарь",
    "Виртуоз", "Ветеран", "Патриарх",
]

DOMESTIC_PLACE = [
    "Двора", "Гаража", "Лавки", "Грядки", "Забора", "Чердака", "Подвала",
    "Балкона", "Розетки", "Подъезда", "Курилки", "Качелей", "Беседки",
    "Помойки", "Аллеи", "Ларька", "Стоянки", "Скамейки", "Детской",
    "Прачечной", "Котельной", "Проходной", "Бытовки", "Веранды",
    "Пристройки", "Голубятни", "Теплицы", "Оградки", "Тропинки",
    "Ограды", "Изгороди",
]

WOW_SUBJ = [
    "Танк", "Хил", "Маг", "Вор", "Друид", "Пал", "Жрец", "Шаман",
    "Охотник", "Локер", "Воин", "Рыцарь", "Бард", "Некро", "Инженер",
    "Рыбак", "Кузнец", "Травник", "Кожевник", "Ювелир", "Алхимик",
]

WOW_PROBLEM = [
    "БезМаны", "Заспал", "Сагрил", "Мисснул", "Убегает", "Молчит", "Кидал",
    "Спит", "Рвётся", "Лагает", "Дисконнект", "НеЛечит", "НеТанчит",
    "Забыл", "Вайпнул", "Слился", "Афк", "Задержался", "Опоздал",
    "Затупил", "Промазал", "Скипнул", "Зазевался", "Отвлёкся",
    "Заигрался",
]

PHRASE_NICKS = [
    "ЯСРаботы", "ПятьМинут", "ПоследнДанж", "ЖенаЗлится", "НеБейКвест",
    "СамоАгрилось", "ДумалТанк", "ПервТанкую", "СпатьПора", "ХватитПить",
    "ЕщёОдинРейд", "ПоследнРаз", "ВсёНормально", "НеЖдитеМеня", "ЯУжеИду",
    "ПодождитеМиг", "СейчасВорнусь", "ДайтеШанс", "НеБросайте",
    "ПочтиГотов", "ЕщёНемного", "СейчасВыйду", "ТерпениеЕсть", "ПрощеПаре",
]

OFFICE_A = [
    "Зам", "Нач", "Отв", "Глав", "Стар", "Млад", "Врио", "Шеф", "Куратор",
    "Дежурный", "Смотрящий", "Комендант", "Инспектор", "Ответств",
    "Заведующий", "Управляющий", "Ревизор", "Контролёр", "Диспетчер",
    "Модератор", "Координатор", "Регулировщик",
    "Зав", "Пом", "Тех", "Мод", "Рев", "Упр", "Дир", "Гос",
]

OFFICE_B = [
    "ПоАгро", "ПоЛуту", "ПоВайпу", "ПоФлагу", "ПоБаффам", "ПоМанне",
    "ПоЗелью", "ПоКвестам", "ПоРейдам", "ПоАрене", "ПоГильдии",
    "ПоКрафту", "ПоТорговле", "ПоФарму", "ПоБанку", "ПоЧату",
    "ПоЛагам", "ПоДампу", "ПоТаргету", "ПоТряпке", "ПоМетле",
    "ПоШвабре",
]

PROF_ROOT = [
    "Сварщик", "Токарь", "Плотник", "Маляр", "Слесарь", "Таксист",
    "Грузчик", "Охранник", "Диспетчер", "Кассир", "Электрик", "Сантехник",
    "Столяр", "Курьер", "Кровельщик", "Тракторист", "Комбайнёр",
    "Экскаваторщик", "Крановщик", "Стропальщик", "Монтажник", "Бетонщик",
]

PROF_PLACE = [
    "Орды", "Тьмы", "Света", "Льда", "Огня", "Бездны", "Степей", "Гор",
    "Дюн", "Топей", "Круга", "Клана", "Стужи", "Праха", "Дыма", "Пепла",
    "Ветра", "Дождя", "Тумана", "Заката",
]

FOOD_ROOT = [
    "Пиво", "Сало", "Блин", "Квас", "Мёд", "Уха", "Борщ", "Компот",
    "Морс", "Кисель", "Брага", "Кулич", "Пряник", "Хрен", "Изюм",
    "Сбитень", "Студень", "Холодец", "Окрошка", "Ботвинья",
    "Расстегай", "Ватрушка",
]

FOOD_SUFFIX = [
    "Вар", "Вор", "Царь", "Босс", "Лорд", "Маг", "Дух", "Жнец", "Кузнец",
    "Мастер", "Барон", "Хан", "Гуру", "Тролль", "Витязь", "Батыр",
]

STREET_SLANG = [
    "Бывалый", "Матёрый", "Отвязный", "Хваткий", "Пробивной", "Проверенный",
    "Битый", "Тёртый", "Дворовый", "Уличный", "Заводной", "Резкий",
    "Ушлый", "Прожжённый", "Стреляный", "Хватский", "Оторва", "Отчаянный",
    "Бесшабашный", "Разбитной",
]

SYS_A = [
    "Игрок", "Польз", "Сессия", "Статус", "Ошибка", "Сервер", "Кэш",
    "Пинг", "Связь", "Аккаунт", "Пакет", "Клиент", "Протокол", "Буфер",
    "Модуль", "Процесс", "Поток", "Драйвер", "Патч", "Билд",
]

SYS_B = [
    "Вышел", "Пропал", "Истекла", "Сброшен", "Высокий", "Потерян",
    "Лагнул", "Стёрта", "Занят", "Отвалился", "Завис", "Перезапущен",
    "Обновлён", "Заблокирован", "Отключён", "Просрочен", "Недоступен",
    "Занижен",
]

REGIONAL = [
    "Уральский", "Омский", "Сибирский", "Кубанский", "Донской", "Волжский",
    "Поморский", "Уссурийский", "Алтайский", "Ямальский", "Тульский",
    "Рязанский", "Брянский", "Пермский", "Тверской", "Курский",
    "Липецкий", "Орловский", "Псковский", "Вятский",
]

REGIONAL_ROLE = [
    "Воин", "Жрец", "Танк", "Хил", "Маг", "Друид", "Бард", "Странник",
    "Рыцарь", "Егерь", "Лучник", "Шаман",
]

MAX_ABSURD = [
    "КирпичОнович", "КартошкаАпок", "ТабуреткаЗла", "Холодильник",
    "ПельменьЦарь", "СковородаЗла", "КастрюляБунт", "МясорубкаЗла",
    "ПылесосБунт", "УтюгБунтарь", "ЧайникЗлится", "ТерморегДух",
    "МикроволновДух", "ХолодецБунт", "ВареникБунт",
]

MILD_18PLUS = [
    "ПьяныйГоблин", "Похмельный", "ТуалетныйДух", "ХмельнойВор",
    "ПивнойБарон", "СамогонБосс", "ОпохмелМаг", "БуйныйДед",
    "ВеселыйПьян", "БраговарДед", "ГрогоЛюб", "ХмельноеЭхо",
    "ПивнойДух", "БуянПьяный",
]

CLASS_FLAVOR = {
    1: ["Танк", "Латник"], 2: ["Паладин", "Светоносец"], 3: ["Лучник", "Егерь"],
    4: ["Тень", "Ассасин"], 5: ["Жрец", "Молитвенник"], 6: ["Плеть", "Мортис"],
    7: ["Шаман", "Тотемщик"], 8: ["Пиро", "Крио"], 9: ["Демон", "Чернокнижник"],
    11: ["Друид", "Коготь"],
}

BLOCKLIST_SUBSTR = ["админ", "admin", "модер", "moder", "support", "гм", "blizz", "close"]


def clean_bank(words):
    out = []
    for w in words:
        w = cap_case(w)
        if is_valid_name(w) and not any(b in w.lower() for b in BLOCKLIST_SUBSTR):
            out.append(w)
    seen = set()
    uniq = []
    for w in out:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return uniq


SOLO_NICK = clean_bank(SOLO_NICK)
DIMINUTIVE_NAMES = clean_bank(DIMINUTIVE_NAMES)
NAME_PLUS_ITEM = clean_bank(NAME_PLUS_ITEM)
DOMESTIC_ROLE = clean_bank(DOMESTIC_ROLE)
DOMESTIC_PLACE = clean_bank(DOMESTIC_PLACE)
WOW_SUBJ = clean_bank(WOW_SUBJ)
WOW_PROBLEM = clean_bank(WOW_PROBLEM)
PHRASE_NICKS = clean_bank(PHRASE_NICKS)
OFFICE_A = clean_bank(OFFICE_A)
OFFICE_B = clean_bank(OFFICE_B)
PROF_ROOT = clean_bank(PROF_ROOT)
PROF_PLACE = clean_bank(PROF_PLACE)
FOOD_ROOT = clean_bank(FOOD_ROOT)
FOOD_SUFFIX = clean_bank(FOOD_SUFFIX)
STREET_SLANG = clean_bank(STREET_SLANG)
SYS_A = clean_bank(SYS_A)
SYS_B = clean_bank(SYS_B)
REGIONAL = clean_bank(REGIONAL)
REGIONAL_ROLE = clean_bank(REGIONAL_ROLE)
MAX_ABSURD = clean_bank(MAX_ABSURD)
MILD_18PLUS = clean_bank(MILD_18PLUS)


@dataclass
class Category:
    key: str
    weight: float
    bank: list = field(default_factory=list)
    combinator: bool = False
    parts: tuple = ()


CATEGORIES = [
    Category("solo_nick", 0.16, bank=SOLO_NICK),
    Category("diminutive", 0.10, bank=DIMINUTIVE_NAMES),
    Category("name_item", 0.10, combinator=True, parts=(DIMINUTIVE_NAMES, NAME_PLUS_ITEM)),
    Category("domestic_absurd", 0.10, combinator=True, parts=(DOMESTIC_ROLE, DOMESTIC_PLACE)),
    Category("wow_jokes", 0.10, combinator=True, parts=(WOW_SUBJ, WOW_PROBLEM)),
    Category("phrase_nicks", 0.05, bank=PHRASE_NICKS),
    Category("office_titles", 0.08, combinator=True, parts=(OFFICE_A, OFFICE_B)),
    Category("profession", 0.08, combinator=True, parts=(PROF_ROOT, PROF_PLACE)),
    Category("food_culture", 0.07, combinator=True, parts=(FOOD_ROOT, FOOD_SUFFIX)),
    Category("street_slang", 0.04, bank=STREET_SLANG),
    Category("system_fake", 0.06, combinator=True, parts=(SYS_A, SYS_B)),
    Category("regional", 0.03, combinator=True, parts=(REGIONAL, REGIONAL_ROLE)),
    Category("max_absurd", 0.02, bank=MAX_ABSURD),
    Category("mild_18plus", 0.01, bank=MILD_18PLUS),  # mild-only, per explicit user choice
]

CLASS_FLAVOR_SHARE = 0.10  # of names, only this share may reference class/role, rest stay independent


def build_class_pool():
    pool = []
    for cls, words in CLASS_FLAVOR.items():
        for w in words:
            w = cap_case(w)
            if is_valid_name(w):
                pool.append((cls, w))
    return pool


CLASS_POOL = build_class_pool()


# ---------------------------------------------------------------------------
# Generation
#
# Each category's full candidate pool (solo words, or every valid a+b pair
# for combinators) is precomputed and shuffled ONCE. Consumption walks each
# pool forward with a single index pointer per category, so every candidate
# is examined at most once for the whole run - no rescanning, no O(n^2)
# blowup even when a category is nearly exhausted.
# ---------------------------------------------------------------------------

def build_pool(cat: "Category", rng: random.Random):
    pool = []
    if cat.combinator:
        a_list, b_list = cat.parts
        for a in a_list:
            for b in b_list:
                cand = cap_case(a + b.lower())
                if is_valid_name(cand):
                    pool.append((cand, (a, b)))
    else:
        for w in cat.bank:
            pool.append((w, (w,)))
    rng.shuffle(pool)
    return pool


def generate_names(bot_rows, existing_names, seed: int, word_use_cap: int = 16):
    rng = random.Random(seed)
    used_names = set(existing_names)
    word_usage = {}

    cat_state = {cat.key: {"cat": cat, "pool": build_pool(cat, rng), "idx": 0} for cat in CATEGORIES}
    active = set(cat_state.keys())

    def bump_all(words) -> bool:
        if any(word_usage.get(w, 0) >= word_use_cap for w in words):
            return False
        for w in words:
            word_usage[w] = word_usage.get(w, 0) + 1
        return True

    def next_from(key):
        state = cat_state[key]
        pool = state["pool"]
        while state["idx"] < len(pool):
            cand, comps = pool[state["idx"]]
            state["idx"] += 1
            if cand in used_names:
                continue
            if not bump_all(comps):
                continue
            return cand
        active.discard(key)
        return None

    ordered_guids = sorted(r["guid"] for r in bot_rows)
    rows_by_guid = {r["guid"]: r for r in bot_rows}

    rotation = []
    for cat in CATEGORIES:
        rotation.extend([cat.key] * max(1, round(cat.weight * 200)))
    rng.shuffle(rotation)

    mapping = {}
    stats = {"per_category": {}, "class_flavored": 0, "failed": []}

    rot_i = 0
    for guid in ordered_guids:
        row = rows_by_guid[guid]
        new_name = None

        if rng.random() < CLASS_FLAVOR_SHARE:
            candidates = [w for cls, w in CLASS_POOL if cls == row["class"] and w not in used_names]
            rng.shuffle(candidates)
            for w in candidates:
                if bump_all((w,)):
                    new_name = w
                    stats["class_flavored"] += 1
                    break

        spins = 0
        max_spins = len(rotation) + len(CATEGORIES)
        while new_name is None and active and spins < max_spins:
            key = rotation[rot_i % len(rotation)]
            rot_i += 1
            spins += 1
            if key not in active:
                continue
            new_name = next_from(key)
            if new_name is not None:
                stats["per_category"][key] = stats["per_category"].get(key, 0) + 1

        if new_name is None:
            stats["failed"].append(guid)
            continue

        used_names.add(new_name)
        mapping[guid] = new_name

    return mapping, stats


# ---------------------------------------------------------------------------
# DB access
# ---------------------------------------------------------------------------

def fetch_bot_rows():
    with connect(DB_BOTS) as cb:
        with cb.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT bot FROM playerbots_random_bots "
                "WHERE owner = 0 AND event = 'add' AND value = 1"
            )
            bot_guids = {r["bot"] for r in cur.fetchall()}

    with connect(DB_CHAR) as cc:
        with cc.cursor() as cur:
            cur.execute(
                "SELECT guid, account, name, race, class, gender, level FROM characters"
            )
            all_chars = cur.fetchall()

    with connect(DB_AUTH) as ca:
        with ca.cursor() as cur:
            cur.execute(
                "SELECT id FROM account WHERE username LIKE %s",
                (f"{RANDOM_BOT_PREFIX}%",),
            )
            rndbot_accounts = {r["id"] for r in cur.fetchall()}

    all_by_guid = {r["guid"]: r for r in all_chars}
    existing_names = {r["name"] for r in all_chars}

    bot_rows = []
    mismatched = []
    for guid in bot_guids:
        row = all_by_guid.get(guid)
        if row is None:
            mismatched.append((guid, "missing_in_characters"))
            continue
        if row["account"] not in rndbot_accounts:
            mismatched.append((guid, f"account_{row['account']}_not_rndbot"))
            continue
        bot_rows.append(row)

    return bot_rows, bot_guids, existing_names, mismatched


# ---------------------------------------------------------------------------
# CLI actions
# ---------------------------------------------------------------------------

def action_dry_run(args):
    bot_rows, bot_guids, existing_names, mismatched = fetch_bot_rows()

    if mismatched:
        print(f"ABORT: {len(mismatched)} guid(s) failed cross-validation, "
              f"identification is NOT 100% safe. No names generated.")
        for guid, reason in mismatched[:20]:
            print(f"  guid={guid} reason={reason}")
        sys.exit(1)

    if len(bot_rows) != len(bot_guids):
        print("ABORT: bot row count mismatch after validation.")
        sys.exit(1)

    mapping, stats = generate_names(bot_rows, existing_names, seed=args.seed,
                                     word_use_cap=args.word_use_cap)

    generated_names = list(mapping.values())
    duplicates = len(generated_names) - len(set(generated_names))
    invalid = sum(1 for n in generated_names if not is_valid_name(n))
    collide_existing = sum(1 for n in generated_names if n in existing_names)

    print("=== DRY RUN REPORT ===")
    print(f"Bots found: {len(bot_rows)}")
    print(f"Names generated: {len(mapping)}")
    print(f"Unique names: {len(set(generated_names))}")
    print(f"Duplicates: {duplicates}")
    print(f"Invalid names: {invalid}")
    print(f"Collide with existing DB names: {collide_existing}")
    print("Real players affected: 0 (mapping is built only from cross-validated bot guids)")
    print(f"Class-flavored names: {stats['class_flavored']} "
          f"({stats['class_flavored'] / max(1, len(mapping)):.1%})")
    print(f"Failed to generate (no free candidate): {len(stats['failed'])}")
    print("Per-category counts:")
    for k, v in sorted(stats["per_category"].items(), key=lambda x: -x[1]):
        print(f"  {k:20s} {v:5d} ({v / len(mapping):.1%})")

    rows_by_guid = {r["guid"]: r for r in bot_rows}
    sample_guids = sorted(mapping.keys())
    rng = random.Random(args.seed)
    rng.shuffle(sample_guids)
    print("\nSample (guid | old_name | new_name):")
    for guid in sample_guids[:50]:
        print(f"  {guid} | {rows_by_guid[guid]['name']} | {mapping[guid]}")

    if args.backup_out:
        write_backup_csv(args.backup_out, bot_rows, mapping)
        print(f"\nFull mapping written to {args.backup_out} (dry-run, not applied).")


def write_backup_csv(path, bot_rows, mapping):
    rows_by_guid = {r["guid"]: r for r in bot_rows}
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["guid", "account", "old_name", "new_name", "race", "class", "gender", "level"])
        for guid in sorted(mapping.keys()):
            r = rows_by_guid[guid]
            w.writerow([guid, r["account"], r["name"], mapping[guid], r["race"], r["class"], r["gender"], r["level"]])


def action_apply(args):
    if not args.confirm:
        print("Refusing to apply: pass --confirm to actually write to the database.")
        sys.exit(1)

    bot_rows, bot_guids, existing_names, mismatched = fetch_bot_rows()
    if mismatched:
        print(f"ABORT: {len(mismatched)} mismatch(es), refusing to apply.")
        sys.exit(1)

    mapping, stats = generate_names(bot_rows, existing_names, seed=args.seed,
                                     word_use_cap=args.word_use_cap)

    if len(stats["failed"]) or len(mapping) != len(bot_rows):
        print("ABORT: could not generate a name for every bot, refusing to apply.")
        sys.exit(1)

    generated_names = list(mapping.values())
    if len(set(generated_names)) != len(generated_names):
        print("ABORT: duplicate generated names, refusing to apply.")
        sys.exit(1)
    if any(n in existing_names for n in generated_names):
        print("ABORT: a generated name collides with an existing character name, refusing to apply.")
        sys.exit(1)

    backup_path = args.backup_out or f"bot_name_migration_backup_{int(time.time())}.csv"
    write_backup_csv(backup_path, bot_rows, mapping)
    print(f"Backup written to {backup_path} before applying.")

    bot_guid_set = set(mapping.keys())
    guid_tuple = tuple(bot_guid_set)

    with connect(DB_CHAR) as conn:
        with conn.cursor() as cur:
            # pre-check: every guid we are about to touch must already be a
            # validated bot guid, and nothing else
            cur.execute("SELECT COUNT(*) AS c FROM characters WHERE guid IN %s", (guid_tuple,))
            if cur.fetchone()["c"] != len(bot_guid_set):
                print("ABORT: pre-check row count mismatch, refusing to apply.")
                sys.exit(1)

            updated = 0
            for guid, new_name in mapping.items():
                cur.execute("UPDATE characters SET name = %s WHERE guid = %s", (new_name, guid))
                updated += cur.rowcount

            if updated != len(bot_guid_set):
                conn.rollback()
                print(f"ABORT: UPDATE_COUNT ({updated}) != BOT_GUIDS_COUNT ({len(bot_guid_set)}), rolled back.")
                sys.exit(1)

            # post-check: exactly BOT_GUIDS_COUNT rows now carry their new name,
            # nothing outside guid_tuple was touched (guaranteed by WHERE guid=%s above)
            cur.execute(
                "SELECT COUNT(*) AS c FROM characters WHERE guid IN %s AND name IN %s",
                (guid_tuple, tuple(mapping.values())),
            )
            if cur.fetchone()["c"] != len(bot_guid_set):
                conn.rollback()
                print("ABORT: post-check failed, rolled back.")
                sys.exit(1)

            conn.commit()

    print(f"Applied: {updated} bot characters renamed. Backup: {backup_path}")
    print("Reminder: worldserver CharacterCache is only refreshed for renamed guids "
          "after a restart (or per-guid '.cache' command). No restart was performed "
          "by this tool.")


def action_rollback(args):
    if not args.confirm:
        print("Refusing to rollback: pass --confirm to actually write to the database.")
        sys.exit(1)

    with open(args.rollback, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    bot_guids = {int(r["guid"]) for r in rows}

    with connect(DB_CHAR) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT guid, name FROM characters WHERE guid IN %s",
                (tuple(bot_guids),),
            )
            current = {r["guid"]: r["name"] for r in cur.fetchall()}

            mismatched = [r for r in rows if current.get(int(r["guid"])) != r["new_name"]]
            if mismatched:
                print(f"ABORT: {len(mismatched)} row(s) no longer match the expected "
                      f"post-migration name (someone/something changed them since). "
                      f"Refusing to blindly rollback.")
                for r in mismatched[:20]:
                    print(f"  guid={r['guid']} expected={r['new_name']!r} actual={current.get(int(r['guid']))!r}")
                sys.exit(1)

            updated = 0
            for r in rows:
                cur.execute(
                    "UPDATE characters SET name = %s WHERE guid = %s",
                    (r["old_name"], int(r["guid"])),
                )
                updated += cur.rowcount
            if updated != len(rows):
                conn.rollback()
                print(f"ABORT: rollback UPDATE_COUNT ({updated}) != expected ({len(rows)}), rolled back.")
                sys.exit(1)
            conn.commit()

    print(f"Rollback applied: {updated} characters restored to their original names.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    dr = sub.add_parser("dry-run")
    dr.add_argument("--seed", type=int, required=True)
    dr.add_argument("--word-use-cap", type=int, default=16)
    dr.add_argument("--backup-out", type=str, default=None)
    dr.set_defaults(func=action_dry_run)

    ap = sub.add_parser("apply")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--word-use-cap", type=int, default=16)
    ap.add_argument("--backup-out", type=str, default=None)
    ap.add_argument("--confirm", action="store_true")
    ap.set_defaults(func=action_apply)

    rb = sub.add_parser("rollback")
    rb.add_argument("rollback", type=str)
    rb.add_argument("--confirm", action="store_true")
    rb.set_defaults(func=action_rollback)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
