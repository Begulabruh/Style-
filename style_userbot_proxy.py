"""
Femboy Userbot (Русская версия) + MTProto прокси
------------------------------------------------
Ты пишешь "Привет", отправляешь, и сообщение сразу редактируется в
"приветик ^_^". Работает от твоего аккаунта.

Что сделать перед запуском:
  1. Впиши свои API_ID и API_HASH ниже (берутся на https://my.telegram.org).
  2. pip install telethon
  3. Файл femboy_core_ru.py должен лежать в той же папке.
  4. Программа, которая создаёт прокси 127.0.0.1:1080, должна быть запущена.
  5. python femboy_userbot_proxy.py

Команды (пиши в любом чате, сообщение-команда сразу удалится):
  .on / .off          включить / выключить стиль
  .soft .cute .max    фембой-стиль (интенсивность)
  .yandere            режим яндере
  .tsundere           режим цундере
  .depressive         депрессивный режим
  .gopnik             режим гопника
  .business           деловой режим
  .fem                женские формы вкл/выкл
  .status             показать настройки

Чтобы отправить сообщение БЕЗ обработки, начни его с "!"  (например: !привет)

Файл femboy.session, который появится после входа, это ключ к твоему аккаунту.
Никому его не отправляй.
"""

import asyncio
import re

from telethon import TelegramClient, connection, events

from femboy_core_ru import stylize

# ====== ВПИШИ СВОИ ДАННЫЕ ======
API_ID = 12345678                                   # число, без кавычек
API_HASH = "abcdef0123456789abcdef0123456789"       # строка, в кавычках
# ================================

# ====== ПРОКСИ ======
PROXY_HOST = ""
PROXY_PORT = 1080
PROXY_SECRET = ""
# ====================

if API_ID == 12345678 or API_HASH.startswith("abcdef"):
    raise SystemExit("Впиши свои API_ID и API_HASH в начале файла.")

client = TelegramClient(
    "femboy",
    API_ID,
    API_HASH,
    connection=connection.ConnectionTcpMTProxyRandomizedIntermediate,
    proxy=(PROXY_HOST, PROXY_PORT, PROXY_SECRET),
)

# Если MTProto не заработает и у тебя SOCKS5-прокси, удали блок выше
# и используй этот (нужно: pip install python-socks[asyncio]):
#
# client = TelegramClient(
#     "femboy", API_ID, API_HASH,
#     proxy=("socks5", PROXY_HOST, PROXY_PORT),
# )

state = {"on": True, "mode": "femboy", "level": "cute", "fem": False}

COMMANDS = {".on", ".off", ".soft", ".cute", ".max", ".yandere", ".tsundere",
            ".depressive", ".gopnik", ".business", ".fem", ".status"}


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
        elif text in (".yandere", ".tsundere", ".depressive", ".gopnik", ".business"):
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
    print("Пиши сообщения в любом чате. Команды: .on .off .soft .cute .max .yandere .tsundere .depressive .gopnik .business .fem .status")
    await client.run_until_disconnected()


if __name__ == "__main__":
    client.loop.run_until_complete(main())
