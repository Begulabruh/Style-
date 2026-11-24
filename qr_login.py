"""
Вход по QR-коду (если код из Telegram не приходит).

Как пользоваться:
  1. Положи этот файл в папку femboy, рядом с style_userbot.py.
     В style_userbot.py уже должны быть вписаны API_ID и API_HASH.
  2. Удали файл style.session, если он есть (там мог остаться вход под ботом).
  3. pip install qrcode[pil]
  4. python qr_login.py
     Откроется картинка с QR-кодом.
  5. На телефоне: Telegram -> Настройки -> Устройства -> Подключить устройство
     и наведи камеру на QR-код на экране компьютера.
  6. Когда в терминале появится твоё имя, закрой скрипт и запускай
     python style_userbot.py как обычно.

QR-код никому не показывай и не отправляй: с ним можно войти в твой аккаунт.
"""

import asyncio
import os

import qrcode
from telethon.errors import SessionPasswordNeededError

# берём настройки (API_ID, API_HASH, прокси) из основного скрипта
from style_userbot import client


async def main():
    await client.connect()

    me = await client.get_me() if await client.is_user_authorized() else None
    if me and not me.bot:
        print(f"Ты уже вошёл как {me.first_name}. Можно запускать style_userbot.py")
        return
    if me and me.bot:
        print("В session сохранён вход под БОТОМ. Закрой скрипт, удали style.session и запусти снова.")
        return

    qr = await client.qr_login()
    while True:
        qrcode.make(qr.url).save("qr.png")
        if hasattr(os, "startfile"):
            os.startfile("qr.png")
        else:
            print("Открой файл qr.png в этой папке.")
        print("Отсканируй QR в Telegram: Настройки -> Устройства -> Подключить устройство")
        try:
            await qr.wait(60)
            break
        except asyncio.TimeoutError:
            print("QR устарел, делаю новый...")
            await qr.recreate()
        except SessionPasswordNeededError:
            pw = input("Пароль двухэтапной защиты: ")
            await client.sign_in(password=pw)
            break

    me = await client.get_me()
    print(f"Готово! Вход выполнен как {me.first_name} (@{me.username}).")
    print("Теперь запускай: python style_userbot.py")
    try:
        os.remove("qr.png")
    except OSError:
        pass
    await client.disconnect()


if __name__ == "__main__":
    client.loop.run_until_complete(main())
