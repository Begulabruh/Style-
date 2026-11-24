"""
Femboy Userbot (Русская версия), прокси необязателен
------------------------------------------------
Ты пишешь "Привет", отправляешь, и сообщение сразу редактируется в
"приветик ^_^". Работает от твоего аккаунта.

Что сделать перед запуском:
  1. Впиши свои API_ID и API_HASH ниже (берутся на https://my.telegram.org).
  2. pip install telethon
  3. Файл style_core.py должен лежать в той же папке.
  4. Прокси необязателен: если он нужен, впиши PROXY_HOST, PROXY_PORT и PROXY_SECRET
     (и держи запущенной программу, которая его создаёт). Если не нужен, оставь пустым.
  5. python style_userbot.py

Команды (пиши в любом чате, сообщение-команда сразу удалится):
  .on / .off          включить / выключить стиль
  .soft .cute .max    фембой-стиль (интенсивность)
  .yandere            режим яндере
  .tsundere           режим цундере
  .depressive         депрессивный режим
  .gopnik             режим гопника
  .business           деловой режим
  .gremlin            хаотичный (мемный) режим
  .formal             сверхофициальный режим
  .uwu                анимешный режим
  .fem                женские формы вкл/выкл
  .status             показать настройки

Чтобы отправить сообщение БЕЗ обработки, начни его с "!"  (например: !привет)

Файл style.session, который появится после входа, это ключ к твоему аккаунту.
Никому его не отправляй.
"""

import asyncio
import os
import re

from telethon import TelegramClient, connection, events

from style_core import stylize

# ====== ВПИШИ СВОИ ДАННЫЕ ======
# Можно вписать прямо сюда или задать переменные окружения API_ID и API_HASH.
API_ID = int(os.environ.get("API_ID", "12345678"))                         # число, без кавычек
API_HASH = os.environ.get("API_HASH", "abcdef0123456789abcdef0123456789")  # строка, в кавычках
# ================================

# ====== ПРОКСИ (необязательно) ======
# Если Telegram у тебя работает без прокси, оставь PROXY_HOST пустым.
# Для MTProto-прокси впиши адрес, порт и секрет (32 символа).
PROXY_HOST = os.environ.get("PROXY_HOST", "")      # например "127.0.0.1"; пусто = без прокси
PROXY_PORT = int(os.environ.get("PROXY_PORT", "1080"))
PROXY_SECRET = os.environ.get("PROXY_SECRET", "")  # секрет MTProto-прокси
# ====================================

if API_ID == 12345678 or API_HASH.startswith("abcdef"):
    raise SystemExit("Впиши свои API_ID и API_HASH в начале файла.")

if PROXY_HOST:
    client = TelegramClient(
        "style",
        API_ID,
        API_HASH,
        connection=connection.ConnectionTcpMTProxyRandomizedIntermediate,
        proxy=(PROXY_HOST, PROXY_PORT, PROXY_SECRET),
    )
    # Если у тебя SOCKS5-прокси, замени блок выше на (pip install python-socks[asyncio]):
    # client = TelegramClient("style", API_ID, API_HASH,
    #                         proxy=("socks5", PROXY_HOST, PROXY_PORT))
else:
    client = TelegramClient("style", API_ID, API_HASH)

state = {"on": True, "mode": "femboy", "level": "cute", "fem": False}

COMMANDS = {".on", ".off", ".soft", ".cute", ".max", ".yandere", ".tsundere",
            ".depressive", ".gopnik", ".business", ".gremlin", ".formal", ".uwu",
            ".fem", ".status"}


async def flash(event, text, seconds=2):
    """Показать короткое сообщение вместо команды и удалить его."""
    await event.edit(text)
    await asyncio.sleep(seconds)
    await event.delete()


@client.on(events.NewMessage(outgoing=True))
async def on_outgoing(event):
    msg = event.message
    text = (msg.raw_text or "").strip()
    if not text:
        return

    # --- команды ---
    if text in COMMANDS:
        if text == ".on":
            state["on"] = True
        elif text == ".off":
            state["on"] = False
        elif text == ".fem":
            state["fem"] = not state["fem"]
        elif text in (".soft", ".cute", ".max"):
            state["mode"] = "femboy"
            state["level"] = text[1:]
        elif text in (".yandere", ".tsundere", ".depressive", ".gopnik", ".business",
                      ".gremlin", ".formal", ".uwu"):
            state["mode"] = text[1:]
        status = (
            f"{'вкл' if state['on'] else 'выкл'} | "
            f"{state['level'] if state['mode'] == 'femboy' else state['mode']} | "
            f"жен. формы: {'да' if state['fem'] else 'нет'}"
        )
        await flash(event, f"🎀 {status}")
        return

    if not state["on"]:
        return

    # --- пропускаем то, что лучше не трогать ---
    if msg.media and not msg.web_preview:       # фото, файлы, стикеры и т.д.
        return
    if msg.entities:                            # форматирование, ссылки, упоминания
        return
    if text.startswith("/"):                    # команды ботов
        return
    if re.fullmatch(r"\S*https?://\S+", text):  # просто ссылка
        return

    # --- "!" в начале = отправить как есть ---
    if text.startswith("!"):
        await event.edit(text[1:].lstrip())
        return

    styled = stylize(text, state["mode"], state["level"], state["fem"])
    if styled and styled != text:
        await event.edit(styled)


async def main():
    await client.start()
    me = await client.get_me()
    print(f"Запущено от аккаунта: {me.first_name} (@{me.username})")
    print("Пиши сообщения в любом чате. Команды: .on .off .soft .cute .max .yandere .tsundere .depressive .gopnik .business .gremlin .formal .uwu .fem .status")
    await client.run_until_disconnected()


if __name__ == "__main__":
    client.loop.run_until_complete(main())
