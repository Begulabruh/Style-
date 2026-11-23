"""
Femboy Vibe Bot for Telegram
----------------------------
Rewrites your text in a soft, cute, femboy-style voice.

Two ways to use it:
  1. DM the bot: send any text, get the styled version back to copy.
  2. Inline mode: in ANY chat type  @your_bot_name hey how are you
     and pick a style (soft / cute / max) to send it directly as you.

Setup:
  1. Talk to @BotFather on Telegram -> /newbot -> copy the token.
  2. In BotFather also run /setinline (so inline mode works) and give a placeholder.
  3. pip install "python-telegram-bot>=21"
  4. export BOT_TOKEN="123456:ABC..."   (Windows: set BOT_TOKEN=...)
  5. python femboy_bot.py
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

# ---------- style config ----------

EMOTICONS = ["uwu", "owo", ">_<", "^_^", ":3", "(◕‿◕)", "(˶ᵔ ᵕ ᵔ˶)", "x3", "≽^•⩊•^≼", "( ˘ ³˘)♥"]
EMOJIS = ["🥺", "👉👈", "💕", "🎀", "✨", "🌸", "💖", "🫶", "🩷", "😳"]
ACTIONS = ["*blushes*", "*giggles*", "*hides face in hoodie sleeves*", "*fidgets with thigh highs*",
           "*tilts head*", "*pouts*", "*sips iced coffee*", "*adjusts hair clip*"]
FILLERS = ["um", "like", "hehe", "mmh"]

# word-level swaps (case-insensitive)
SWAPS = {
    r"\byou\b": "u",
    r"\byour\b": "ur",
    r"\bthe\b": "da",
    r"\bplease\b": "pwease",
    r"\bsorry\b": "sowwy",
    r"\bhello\b": "hewwo",
    r"\bhi\b": "hii",
    r"\bhey\b": "heyyy",
    r"\bsmall\b": "smol",
    r"\bsmall\b": "smol",
    r"\bfriend\b": "fwiend",
    r"\bthank you\b": "thank u",
    r"\bthanks\b": "thankies",
    r"\byes\b": "yesh",
    r"\bno\b": "nuh uh",
    r"\bcute\b": "cutesy",
    r"\bgood\b": "gud",
    r"\bnice\b": "nicee",
    r"\blove\b": "wuv",
    r"\bwhat\b": "wut",
    r"\bwhy\b": "whyy",
}

# intensity presets: (rw_chance, stutter_chance, emote_chance, action_chance, filler_chance, lowercase)
PRESETS = {
    "soft": dict(rw=0.0, stutter=0.0, emote=0.4, action=0.0, filler=0.0, lower=True, emoji=True),
    "cute": dict(rw=0.35, stutter=0.10, emote=0.7, action=0.15, filler=0.10, lower=True, emoji=True),
    "max": dict(rw=0.8, stutter=0.25, emote=1.0, action=0.5, filler=0.25, lower=True, emoji=True),
}


def _rw(word: str, chance: float) -> str:
    """Turn r/l into w sometimes (keeps short words readable)."""
    if len(word) < 3 or random.random() > chance:
        return word
    return re.sub(r"[rl]", "w", word)


def _stutter(word: str, chance: float) -> str:
    if len(word) > 2 and word[0].isalpha() and random.random() < chance:
        return f"{word[0]}-{word}"
    return word


def femboyify(text: str, level: str = "cute") -> str:
    p = PRESETS[level]
    out = text.strip()
    if not out:
        return out
    if p["lower"]:
        out = out.lower()

    for pattern, repl in SWAPS.items():
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)

    # word-level tweaks, leave punctuation/URLs/@mentions alone
    tokens = re.split(r"(\s+)", out)
    new = []
    for tok in tokens:
        if tok.isspace() or not tok or tok.startswith(("http", "@", "/")) or not re.search(r"[a-z]", tok):
            new.append(tok)
            continue
        m = re.match(r"^(\W*)(.*?)(\W*)$", tok)
        pre, core, post = m.groups()
        if core and core.isalpha():
            core = _rw(core, p["rw"])
            core = _stutter(core, p["stutter"])
        new.append(pre + core + post)
        if random.random() < p["filler"] * 0.3:
            new.append(" " + random.choice(FILLERS) + "...")
    out = "".join(new)

    # sentence-ending flair
    def flair(match):
        end = match.group(0)
        extras = ""
        if random.random() < p["emote"]:
            extras += " " + random.choice(EMOTICONS)
        if p["emoji"] and random.random() < p["emote"]:
            extras += " " + random.choice(EMOJIS)
        return end + extras

    out = re.sub(r"[.!?]+(?=\s|$)", flair, out)
    if not re.search(r"[.!?]\s*\S*\s*$", out) and random.random() < p["emote"]:
        out += " " + random.choice(EMOTICONS)

    if random.random() < p["action"]:
        out += " " + random.choice(ACTIONS)
    return out


# ---------- handlers ----------

HELP = (
    "hii~ i make ur messages sound soft & cute 🎀\n\n"
    "• send me any text and i'll rewrite it\n"
    "• /soft /cute /max  → set ur default intensity\n"
    "• inline: type @{bot} your text in any chat and pick a style ✨"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP.format(bot=context.bot.username))


def make_level_cmd(level: str):
    async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["level"] = level
        await update.message.reply_text(f"okie, intensity set to {level} {random.choice(EMOTICONS)}")
    return cmd


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    level = context.user_data.get("level", "cute")
    await update.message.reply_text(femboyify(update.message.text, level))


async def on_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = (update.inline_query.query or "").strip()
    if not q:
        return
    results = []
    for level in ("soft", "cute", "max"):
        styled = femboyify(q, level)
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"{level.capitalize()} ✨",
                description=styled[:100],
                input_message_content=InputTextMessageContent(styled),
            )
        )
    await update.inline_query.answer(results, cache_time=0, is_personal=True)


def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise SystemExit("Set BOT_TOKEN first (get one from @BotFather).")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    for lvl in PRESETS:
        app.add_handler(CommandHandler(lvl, make_level_cmd(lvl)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(InlineQueryHandler(on_inline))
    print("Bot running... press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
