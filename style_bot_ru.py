"""
Femboy Vibe Bot (Русская версия) для Telegram
---------------------------------------------
Переписывает твой текст в мягком, милом стиле.

Как пользоваться:
  1. Напиши боту в личку любой текст: он пришлёт милую версию.
  2. Inline-режим: в ЛЮБОМ чате набери  @имя_бота привет как дела
     и выбери стиль (soft / cute / max): сообщение отправится от твоего имени.

Настройка:
  1. @BotFather -> /newbot -> скопируй токен.
  2. Там же выполни /setinline и задай подсказку (иначе inline не заработает).
  3. pip install "python-telegram-bot>=21"
  4. export BOT_TOKEN="123456:ABC..."   (Windows: set BOT_TOKEN=...)
  5. python style_bot_ru.py
"""

import os
import random
import re
import uuid

from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

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
    r"\bчто\b": "чтооо",
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
    "soft": dict(elong=0.10, stutter=0.0, lisp=0.0, emote=0.4, action=0.0, filler=0.0),
    "cute": dict(elong=0.25, stutter=0.10, lisp=0.0, emote=0.7, action=0.15, filler=0.10),
    "max": dict(elong=0.50, stutter=0.25, lisp=0.30, emote=1.0, action=0.5, filler=0.25),
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

    # украшения в конце предложений
    def flair(match):
        extras = ""
        if random.random() < p["emote"]:
            extras += " " + random.choice(EMOTICONS)
        if random.random() < p["emote"]:
            extras += " " + random.choice(EMOJIS)
        return match.group(0) + extras

    out = re.sub(r"[.!?]+(?=\s|$)", flair, out)
    if not re.search(r"[.!?]\s*\S*\s*$", out) and random.random() < p["emote"]:
        out += " " + random.choice(EMOTICONS)

    if random.random() < p["action"]:
        out += " " + random.choice(ACTIONS)
    return out


# ---------- обработчики ----------

HELP = (
    "приветик~ я делаю твои сообщения мягкими и милыми 🎀\n\n"
    "• отправь мне любой текст, и я перепишу его\n"
    "• /soft /cute /max: выбрать интенсивность\n"
    "• /fem: включить/выключить женские формы («я рада», «я сделала»)\n"
    "• inline: набери @{bot} твой текст в любом чате и выбери стиль ✨"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP.format(bot=context.bot.username))


def make_level_cmd(level: str):
    async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["level"] = level
        await update.message.reply_text(f"окей, интенсивность: {level} {random.choice(EMOTICONS)}")
    return cmd


async def toggle_fem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new = not context.user_data.get("fem", False)
    context.user_data["fem"] = new
    await update.message.reply_text(
        "женские формы включены 🎀" if new else "женские формы выключены ✨"
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    level = context.user_data.get("level", "cute")
    fem = context.user_data.get("fem", False)
    await update.message.reply_text(femboyify(update.message.text, level, fem))


async def on_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = (update.inline_query.query or "").strip()
    if not q:
        return
    # в inline нельзя хранить user_data, так что показываем оба варианта для /cute
    results = []
    for level in ("soft", "cute", "max"):
        for fem in (False, True):
            styled = femboyify(q, level, fem)
            label = f"{level.capitalize()}" + (" 🎀 (жен.)" if fem else " ✨")
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=label,
                    description=styled[:100],
                    input_message_content=InputTextMessageContent(styled),
                )
            )
    await update.inline_query.answer(results, cache_time=0, is_personal=True)


def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise SystemExit("Сначала задай BOT_TOKEN (получи у @BotFather).")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    for lvl in PRESETS:
        app.add_handler(CommandHandler(lvl, make_level_cmd(lvl)))
    app.add_handler(CommandHandler("fem", toggle_fem))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(InlineQueryHandler(on_inline))
    print("Бот запущен... Ctrl+C чтобы остановить.")
    app.run_polling()


if __name__ == "__main__":
    main()
