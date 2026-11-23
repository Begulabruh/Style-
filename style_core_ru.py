"""Ядро: функция femboyify() без зависимостей от Telegram."""

import random
import re

# ---------- настройки стиля ----------

EMOTICONS = ["уву", "овo", "^_^", ":3", "(◕‿◕)", "(˶ᵔ ᵕ ᵔ˶)", ">_<", "ня~", "мяу~", "(≧◡≦)", "( ˘ ³˘)♥", "кавай~"]
EMOJIS = ["🥺", "👉👈", "💕", "🎀", "✨", "🌸", "💖", "🫶", "🩷", "😳"]
ACTIONS = [
    "*краснеет*", "*хихикает*", "*прячет лицо в рукавах худи*", "*поправляет заколку*",
    "*наклоняет голову*", "*надувает щёчки*", "*поправляет гольфы*", "*пьёт айс-латте*",
]
FILLERS = ["эм", "ну", "хихи", "ммм"]

# замены целых слов (без учёта регистра)
SWAPS = {
    r"\bпривет\b": "приветик",
    r"\bздравствуй(те)?\b": "здарова~ ой, то есть приветик",
    r"\bпока\b": "покашки",
    r"\bспасибо\b": "спасибки",
    r"\bпожалуйста\b": "пожаааалуйста",
    r"\bизвини(те)?\b": "извиниии",
    r"\bпрости(те)?\b": "простиии",
    r"\bхорошо\b": "хорошоо",
    r"\bда\b": "дааа",
    r"\bнет\b": "неть",
    r"\bочень\b": "ооочень",
    r"\bлюблю\b": "люблюю",
    r"\bмилый\b": "мимими",
    r"\bмилая\b": "мимими",
    r"\bкрасивый\b": "красивенький",
    r"\bкрасивая\b": "красивенькая",
    r"\bсегодня\b": "сегодняшки",
    r"\bдруг\b": "дружочек",
    r"\bподруга\b": "подружка",
    r"\bпочему\b": "почемууу",
    r"\bкот\b": "котик",
    r"\bкошка\b": "кошечка",
    r"\bсладкий\b": "сладенький",
    r"\bмаленький\b": "малюсенький",
    r"\bнапиши\b": "напиши-напиши",
    r"\bпожалуйста\b": "пжлст",
}

# женские формы (опционально, команда /fem), чтобы писать "я рада", "я сделала"
FEM_IRREGULAR = {
    r"\bя пошёл\b": "я пошла", r"\bя пошел\b": "я пошла",
    r"\bя ушёл\b": "я ушла", r"\bя ушел\b": "я ушла",
    r"\bя пришёл\b": "я пришла", r"\bя пришел\b": "я пришла",
}


NOT_VERBS = {"стол", "пол", "угол", "ствол", "сокол", "орёл", "орел", "осёл", "осел", "козёл", "козел", "вол"}


def feminize(text: str) -> str:
    for pat, rep in FEM_IRREGULAR.items():
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    # одиночные формы в предложении с "я"
    parts = re.split(r"([.!?\n]+)", text)
    for i in range(0, len(parts), 2):
        sent = parts[i]
        if not re.search(r"\bя\b", sent, flags=re.IGNORECASE):
            continue
        sent = re.sub(r"\b(рад|готов|уверен|должен|согласен|один|сам)\b",
                      lambda m: {"один": "одна", "сам": "сама"}.get(m.group(1), m.group(1) + "а"), sent)
        sent = re.sub(r"\b(\w{2,}л)\b",
                      lambda m: m.group(1) if m.group(1) in NOT_VERBS else m.group(1) + "а", sent)
        parts[i] = sent
    return "".join(parts)


# пресеты: вероятности эффектов
PRESETS = {
    "soft": dict(elong=0.05, stutter=0.0, lisp=0.0, emote=0.25, action=0.0, filler=0.0),
    "cute": dict(elong=0.12, stutter=0.05, lisp=0.0, emote=0.5, action=0.0, filler=0.04),
    "max": dict(elong=0.30, stutter=0.12, lisp=0.15, emote=0.85, action=0.12, filler=0.10),
}

VOWELS = "аеёиоуыэюя"


def _elongate(word: str, chance: float) -> str:
    if len(word) >= 3 and word[-1] in VOWELS and random.random() < chance:
        return word + word[-1] * random.choice([1, 2])
    return word


def _stutter(word: str, chance: float) -> str:
    if len(word) > 2 and word[0].isalpha() and random.random() < chance:
        return f"{word[0]}-{word}"
    return word


def _lisp(word: str, chance: float) -> str:
    """Милое сюсюканье: с -> ш, з -> ж (иногда)."""
    if len(word) < 4 or random.random() > chance:
        return word
    return word.replace("с", "ш").replace("з", "ж")


def femboyify(text: str, level: str = "cute", fem: bool = False) -> str:
    p = PRESETS[level]
    out = text.strip().lower()
    if not out:
        return out

    if fem:
        out = feminize(out)

    for pattern, repl in SWAPS.items():
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)

    tokens = re.split(r"(\s+)", out)
    new = []
    for tok in tokens:
        if tok.isspace() or not tok or tok.startswith(("http", "@", "/")) or not re.search(r"[а-яёa-z]", tok):
            new.append(tok)
            continue
        m = re.match(r"^(\W*)(.*?)(\W*)$", tok)
        pre, core, post = m.groups()
        if core and core.isalpha() and "-" not in core:
            core = _lisp(core, p["lisp"])
            core = _elongate(core, p["elong"])
            core = _stutter(core, p["stutter"])
        new.append(pre + core + post)
        if random.random() < p["filler"] * 0.3:
            new.append(" " + random.choice(FILLERS) + "...")
    out = "".join(new)

    # одно лёгкое украшение в конце сообщения (не после каждого предложения)
    if random.random() < p["emote"]:
        out = out.rstrip() + " " + random.choice(EMOTICONS + EMOJIS)
    if random.random() < p["action"]:
        out += " " + random.choice(ACTIONS)
    return out


# ---------- режимы: яндере и цундере ----------

YANDERE_SWAPS = {
    r"\bпривет\b": "приветик~ ♡",
    r"\bпока\b": "пока... но ты ведь скоро вернёшься, да? ♡",
    r"\bспасибо\b": "спасибо ♡",
    r"\bлюблю\b": "люблю тебя ♡ только тебя",
    r"\bнет\b": "н-нет... ты же не бросишь меня?",
    r"\bдруг\b": "самый-самый близкий",
    r"\b(?:я )?скучаю\b": "скучаю каждую секундочку ♡",
}
YANDERE_END = [
    "ты ведь будешь только со мной, да? ♡",
    "я всегда рядом~ ♡",
    "не смей пропадать... ♡",
    "я очень скучаю... ♡",
    "ты ведь ответишь мне, да? ♡",
    "никому тебя не отдам ♡",
    "я думаю о тебе каждую секундочку ♡",
    "ты же никуда не денешься, правда? 🖤",
]
YANDERE_MARKS = ["♡", "🖤", "💗", "👁️", "~"]

TSUNDERE_SWAPS = {
    r"\bпривет\b": "п-привет... чего тебе?",
    r"\bспасибо\b": "н-ну... спасибо, наверное",
    r"\bпожалуйста\b": "н-ну... п-пожалуйста",
    r"\bлюблю\b": "м-мне нравится... совсем чуть-чуть!",
    r"\b(?:я )?скучаю\b": "мне тебя немного не хватает... совсем чуть-чуть!",
    r"\bда\b": "ну... да",
    r"\bнет\b": "н-нет, ещё чего!",
    r"\bхорошо\b": "ладно, ладно...",
    r"\bдруг\b": "друг... ну, типа",
}
TSUNDERE_START = ["х-хмф... ", "ха?! ", "б-бака, ", "н-ну... ", "т-ты... "]
TSUNDERE_END = [
    "...и не думай ничего такого!",
    "...но это не потому что ты мне нравишься! >_<",
    "...б-бака!",
    "хмф! 😤",
    "...д-дурак, не смотри так!",
    "...просто так вышло, понял?!",
    "(¬_¬)",
    "/// не смотри на меня!",
]


def _apply_swaps(text, swaps):
    for pattern, repl in swaps.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return re.sub(r"([?!.]),", r"\1", text)


def _tokens(text, fn):
    """Применить fn к «чистым» словам, не трогая ссылки, @упоминания и знаки."""
    out = []
    for tok in re.split(r"(\s+)", text):
        if tok.isspace() or not tok or tok.startswith(("http", "@", "/")) or not re.search(r"[а-яёa-z]", tok):
            out.append(tok)
            continue
        m = re.match(r"^(\W*)(.*?)(\W*)$", tok)
        pre, core, post = m.groups()
        if core and core.isalpha():
            core = fn(core)
        out.append(pre + core + post)
    return "".join(out)


def yandere(text: str, fem: bool = False) -> str:
    out = text.strip().lower()
    if not out:
        return out
    if fem:
        out = feminize(out)
    out = _apply_swaps(out, YANDERE_SWAPS)
    out = _tokens(out, lambda w: _elongate(w, 0.15))
    if random.random() < 0.2:
        out = out.replace(", ", "... ", 1)
    r = random.random()
    if r < 0.3:
        out += " " + random.choice(YANDERE_END)
    elif r < 0.7:
        out += " " + random.choice(YANDERE_MARKS)
    return out


def tsundere(text: str, fem: bool = False) -> str:
    out = text.strip().lower()
    if not out:
        return out
    if fem:
        out = feminize(out)
    out = _apply_swaps(out, TSUNDERE_SWAPS)
    out = _tokens(out, lambda w: _stutter(w, 0.12))
    if random.random() < 0.2:
        out = random.choice(TSUNDERE_START) + out
    if random.random() < 0.35:
        out += " " + random.choice(TSUNDERE_END)
    return out


# ---------- режимы: гопник, депрессивный, деловой ----------

GOPNIK_SWAPS = {
    r"\b(?:кока-кол\w+|кока кол\w+|кол[аыуе]|колой|пепси|фант\w+|спрайт\w*|газировк\w+)\b": "газява",
    r"\b(?:лейс|lays|чипсы|чипсов|чипсики)\b": "хрумки",
    r"\bэнергетик(?:и)?\b": "энергос",
    r"\bпиво\b": "пивас",
    r"\bсигареты\b": "курево",
    r"\bденьги\b": "бабки",
    r"\bдеревня\b": "деревня",
    r"\bмагазин\b": "магаз",
    r"\bтелефон\b": "труба",
    r"\bмашина\b": "тачка",
    r"\bдом\b": "хата",
    r"\bдрузья\b": "пацаны",
    r"\bдруг\b": "братан",
    r"\bребята\b": "пацаны",
    r"\bпривет\b": "здарова",
    r"\bздравствуй(?:те)?\b": "здарова",
    r"\bпока\b": "бывай",
    r"\bспасибо\b": "благодарю, братан",
    r"\bда\b": "ага",
    r"\bнет\b": "не",
    r"\bхорошо\b": "чётко",
    r"\bкруто\b": "красава",
    r"\bочень\b": "реально",
    r"\bпонятно\b": "ясно-понятно",
}
GOPNIK_START = ["короче, ", "слышь, ", "ну чё, ", "в натуре, "]
GOPNIK_END = ["в натуре", "братан", "понял?", "ну чё", "по красоте"]

DEPRESSIVE_SWAPS = {
    r"\bпривет\b": "привет...",
    r"\bхорошо\b": "ну... нормально, наверное",
    r"\bотлично\b": "ну... нормально",
    r"\bкруто\b": "ну, неплохо, наверное",
    r"\bура\b": "ну... ура, наверное",
    r"\bкак дела\b": "как дела... у меня как обычно",
    r"\bспасибо\b": "спасибо... правда",
    r"\bладно\b": "ладно... пусть",
}
DEPRESSIVE_END = ["...", "*вздох*", "ладно, неважно...", "как-то так...", "всё равно...", "ну, такое..."]

BUSINESS_SWAPS = {
    r"\b(?:привет|здорово|хай)\b": "добрый день",
    r"\bздравствуй(?:те)?\b": "добрый день",
    r"\bпока\b": "с уважением",
    r"\bспасибо\b": "благодарю",
    r"\b(?:ок|окей|окей-окей)\b": "принято",
    r"\bда\b": "подтверждаю",
    r"\bнет\b": "не могу подтвердить",
    r"\bхорошо\b": "договорились",
    r"\bдавай\b": "предлагаю",
    r"\bсейчас\b": "в ближайшее время",
    r"\bскоро\b": "в кратчайшие сроки",
    r"\bпозже\b": "в более поздние сроки",
    r"\bзавтра\b": "завтра в рабочем порядке",
    r"\bпомоги\b": "прошу оказать содействие",
    r"\bнадо\b": "необходимо",
    r"\bсрочно\b": "в приоритетном порядке",
}
BUSINESS_END = ["Прошу подтвердить.", "Жду обратной связи.", "Буду признателен за ответ.", "Прошу учесть."]


def _end_with(text, extra):
    """Вставить extra перед завершающей пунктуацией (или в самый конец)."""
    m = re.search(r"([.!?]+)\s*$", text)
    if m:
        return text[:m.start()] + ", " + extra + text[m.start():]
    return text + ", " + extra


def gopnik(text: str, fem: bool = False) -> str:
    out = text.strip().lower()
    if not out:
        return out
    if fem:
        out = feminize(out)
    out = _apply_swaps(out, GOPNIK_SWAPS)
    if random.random() < 0.2:
        out = random.choice(GOPNIK_START) + out
    if random.random() < 0.3:
        out = _end_with(out, random.choice(GOPNIK_END))
    return out


def depressive(text: str, fem: bool = False) -> str:
    out = text.strip().lower()
    if not out:
        return out
    if fem:
        out = feminize(out)
    out = _apply_swaps(out, DEPRESSIVE_SWAPS)
    out = re.sub(r"!+", "...", out)
    out = re.sub(r"(?<![.])\.(?=\s|$)", "...", out)
    out = re.sub(r"\.{4,}", "...", out)
    if random.random() < 0.4:
        out = out.rstrip(".") + " " + random.choice(DEPRESSIVE_END)
    return out


def _capitalize_sentences(text):
    return re.sub(r"(^|[.!?]\s+)([а-яёa-z])",
                  lambda m: m.group(1) + m.group(2).upper(), text)


def business(text: str, fem: bool = False) -> str:
    out = text.strip()
    if not out:
        return out
    if fem:
        out = feminize(out.lower())
    out = _apply_swaps(out, BUSINESS_SWAPS)
    out = re.sub(r"!+", ".", out)
    out = _capitalize_sentences(out)
    if not re.search(r"[.?]\s*$", out):
        out += "."
    if random.random() < 0.3:
        out += " " + random.choice(BUSINESS_END)
    return out


def stylize(text: str, mode: str = "femboy", level: str = "cute", fem: bool = False) -> str:
    """Единая точка входа: femboy | yandere | tsundere | gopnik | depressive | business."""
    if mode == "yandere":
        return yandere(text, fem)
    if mode == "tsundere":
        return tsundere(text, fem)
    if mode == "gopnik":
        return gopnik(text, fem)
    if mode == "depressive":
        return depressive(text, fem)
    if mode == "business":
        return business(text, fem)
    return femboyify(text, level, fem)
