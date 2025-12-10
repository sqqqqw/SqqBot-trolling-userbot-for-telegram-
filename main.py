## WARNING! ALL YOU DO WITH THIS USERBOT ITS ON YOU OWN RISK! IF YOUR ACCOUNT GETS FREEZED/BANNED, I AM NOT RESPONSIBLE FOR IT!

## предупрждение! все что вы делаете с этим юзерботом, это на ваш страх и риск! если ваш аккаунт будет заблокирован/заморожен, я не несу ответственности за это!


import os
import time
import random
import asyncio
import io
import json
from telethon import TelegramClient, events
from telethon.network import connection
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

## get your own api, how to get it? https://my.telegram.org/auth?to=apps

API_ID = ""
API_HASH = ""

client = TelegramClient("userbot_session", int(API_ID), API_HASH)

start_time = None
template = []
sessions = {}
pending_session = {}
proxies = {}
active_proxy = None
session_clients = {}

trl_running = False
trl_task = None
trl2_running = False
trl2_task = None
trl3_state = {"enabled": True, "targets": {}}
trl3_last_reply = {}
spam_running = False
spam_task = None
trl4_running = False
trl4_task = None

SESSIONS_FILE = "sessions.json"
PROXIES_FILE = "proxies.json"
TRL3_FILE = "trl3_state.json"

def load_trl3_state():
    global trl3_state
    if os.path.exists(TRL3_FILE):
        try:
            with open(TRL3_FILE, "r") as f:
                trl3_state = json.load(f)
        except:
            trl3_state = {"enabled": True, "targets": {}}

def save_trl3_state():
    with open(TRL3_FILE, "w") as f:
        json.dump(trl3_state, f)


def load_sessions():
    global sessions
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r") as f:
                sessions = json.load(f)
        except:
            sessions = {}


def save_sessions():
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f)


def load_proxies():
    global proxies, active_proxy
    if os.path.exists(PROXIES_FILE):
        try:
            with open(PROXIES_FILE, "r") as f:
                data = json.load(f)
                proxies = data.get("proxies", {})
                active_proxy = data.get("active", None)
        except:
            proxies = {}
            active_proxy = None


def save_proxies():
    with open(PROXIES_FILE, "w") as f:
        json.dump({"proxies": proxies, "active": active_proxy}, f)


def get_uptime():
    if not start_time:
        return ""
    delta = int(time.time() - start_time)
    days = delta // 86400
    hours = (delta % 86400) // 3600
    minutes = (delta % 3600) // 60

    parts = []
    if days > 0:
        parts.append(f"{days}д")
    if hours > 0:
        parts.append(f"{hours}ч")
    if minutes > 0 or not parts:
        parts.append(f"{minutes}м")

    return "-".join(parts)


def register_handlers(target_client):

    @target_client.on(events.NewMessage(pattern=r"^\.info$", outgoing=True))
    async def info_handler(event):
        uptime = get_uptime()
        commands = [
            ".info - инфо о боте", ".sessions - список сессий",
            ".addsession (номер) - добавить сессию",
            ".removesession (номер) - удалить сессию",
            ".addproxy (ip) (port) (secret) - добавить прокси",
            ".proxylist - список прокси",
            ".useproxy (ip) - использовать прокси",
            ".checkproxy (ip) - проверить прокси",
            ".removeproxy (ip) - удалить прокси",
            ".delmenow - удалить свои сообщения в чате",
            ".spam (задержка) (сообщение) - спам сообщением",
            ".trl4 (задержка) (id) - упоминание юзера + шаблон",
            ".trl3 (id) (задержка) - добавить в автоответчик",
            ".trl3 list - список автоответчика",
            ".trl3 on/off - вкл/выкл автоответчик",
            ".trl3 clear (id) - убрать из списка",
            ".trl3 clearall - очистить список",
            ".trl2 (задержка) (доп текст) (айди группы) - спам в группу",
            ".trl (задержка) (доп текст) - спам в чат",
            ".shablon - сохранить шаблон", ".ping - проверка задержки"
        ]

        info_text = "**SqqBot** - Best bot you can find.\n\n"
        info_text += "**Команды:**\n"
        info_text += "\n".join(commands)
        info_text += f"\n\n**Аптайм:** {uptime}"

        await event.edit(info_text)

    @target_client.on(events.NewMessage(pattern=r"^\.ping$", outgoing=True))
    async def ping_handler(event):
        ping_start = time.time()
        await event.edit("Pinging...")
        ping_end = time.time()
        latency_ms = (ping_end - ping_start) * 1000
        await event.edit(f"Pong! Latency: {latency_ms:.2f}ms")

    @target_client.on(events.NewMessage(pattern=r"^\.sessions$",
                                        outgoing=True))
    async def sessions_handler(event):
        load_sessions()
        if not sessions:
            await event.edit("Нет сохранённых сессий.")
            return

        text = "**Сессии:**\n\n"
        for phone, data in sessions.items():
            is_active = phone in session_clients and session_clients[
                phone].is_connected()
            status = "✅" if is_active else "❌"
            text += f"{status} `{phone}`\n"

        await event.edit(text)

    @target_client.on(
        events.NewMessage(pattern=r"^\.addproxy (.+)", outgoing=True))
    async def addproxy_handler(event):
        global proxies

        args = event.pattern_match.group(1).strip().split()

        if len(args) < 3:
            await event.edit("Формат: .addproxy (ip) (port) (secret)")
            return

        ip = args[0]
        try:
            port = int(args[1])
        except ValueError:
            await event.edit("Порт должен быть числом!")
            return

        secret = args[2]

        load_proxies()
        proxies[ip] = {"ip": ip, "port": port, "secret": secret}
        save_proxies()

        await event.edit(f"✅ Прокси добавлен: `{ip}:{port}`")

    @target_client.on(
        events.NewMessage(pattern=r"^\.proxylist$", outgoing=True))
    async def proxylist_handler(event):
        load_proxies()

        if not proxies:
            await event.edit("Нет сохранённых прокси.")
            return

        text = "**Прокси:**\n\n"
        for ip, data in proxies.items():
            status = "🟢" if active_proxy == ip else "⚪"
            text += f"{status} `{ip}:{data['port']}`\n"

        if active_proxy:
            text += f"\n**Активный:** `{active_proxy}`"
        else:
            text += "\n**Активный:** нет"

        await event.edit(text)

    @target_client.on(
        events.NewMessage(pattern=r"^\.useproxy (.+)", outgoing=True))
    async def useproxy_handler(event):
        global active_proxy

        ip = event.pattern_match.group(1).strip()

        load_proxies()

        if ip == "off" or ip == "none":
            active_proxy = None
            save_proxies()
            await event.edit("✅ Прокси отключен")
            return

        if ip not in proxies:
            await event.edit(f"Прокси `{ip}` не найден.")
            return

        active_proxy = ip
        save_proxies()

        await event.edit(f"✅ Активный прокси: `{ip}:{proxies[ip]['port']}`")

    @target_client.on(
        events.NewMessage(pattern=r"^\.removeproxy (.+)", outgoing=True))
    async def removeproxy_handler(event):
        global proxies, active_proxy

        ip = event.pattern_match.group(1).strip()

        load_proxies()

        if ip not in proxies:
            await event.edit(f"Прокси `{ip}` не найден.")
            return

        del proxies[ip]

        if active_proxy == ip:
            active_proxy = None

        save_proxies()

        await event.edit(f"✅ Прокси `{ip}` удалён.")

    @target_client.on(
        events.NewMessage(pattern=r"^\.checkproxy($| .+)", outgoing=True))
    async def checkproxy_handler(event):
        args = event.raw_text[12:].strip()

        load_proxies()

        if args:
            ip = args
        elif active_proxy:
            ip = active_proxy
        else:
            await event.edit("Укажи IP или выбери прокси через .useproxy")
            return

        if ip not in proxies:
            await event.edit(f"Прокси `{ip}` не найден.")
            return

        await event.edit(f"Проверяю прокси `{ip}`...")

        proxy_data = proxies[ip]
        proxy = (proxy_data["ip"], proxy_data["port"], proxy_data["secret"])

        test_client = TelegramClient(
            "test_proxy_session",
            int(API_ID),
            API_HASH,
            connection=connection.ConnectionTcpMTProxyRandomizedIntermediate,
            proxy=proxy)

        try:
            await asyncio.wait_for(test_client.connect(), timeout=10)
            await test_client.disconnect()

            if os.path.exists("test_proxy_session.session"):
                os.remove("test_proxy_session.session")

            await event.edit(f"✅ Прокси `{ip}:{proxy_data['port']}` работает!")

        except asyncio.TimeoutError:
            await event.edit(f"❌ Прокси `{ip}` - таймаут (10 сек)")
        except Exception as e:
            await event.edit(f"❌ Прокси `{ip}` не работает: {str(e)[:100]}")

    @target_client.on(
        events.NewMessage(pattern=r"^\.addsession (.+)", outgoing=True))
    async def addsession_handler(event):
        global pending_session

        phone = event.pattern_match.group(1).strip()

        if not phone:
            await event.edit("Укажи номер: .addsession +79001234567")
            return

        chat_id = event.chat_id

        pending_session[chat_id] = {
            "phone": phone,
            "state": "waiting_code",
            "client": None,
            "phone_code_hash": None
        }

        session_name = f"session_{phone.replace('+', '').replace(' ', '')}"

        load_proxies()

        if active_proxy and active_proxy in proxies:
            proxy_data = proxies[active_proxy]
            proxy = (proxy_data["ip"], proxy_data["port"],
                     proxy_data["secret"])
            new_client = TelegramClient(
                session_name,
                int(API_ID),
                API_HASH,
                connection=connection.
                ConnectionTcpMTProxyRandomizedIntermediate,
                proxy=proxy)
            proxy_info = f" через прокси `{active_proxy}`"
        else:
            new_client = TelegramClient(session_name, int(API_ID), API_HASH)
            proxy_info = ""

        try:
            await new_client.connect()

            result = await new_client.send_code_request(phone)
            pending_session[chat_id]["client"] = new_client
            pending_session[chat_id][
                "phone_code_hash"] = result.phone_code_hash

            await event.edit(
                f"Код отправлен на {phone}{proxy_info}\n\n**Код:**")

        except Exception as e:
            await event.edit(f"Ошибка: {str(e)}")
            if new_client:
                try:
                    await new_client.disconnect()
                except:
                    pass
            if chat_id in pending_session:
                del pending_session[chat_id]

    @target_client.on(events.NewMessage(outgoing=True))
    async def code_handler(event):
        global pending_session, session_clients

        chat_id = event.chat_id

        if chat_id not in pending_session:
            return

        session_data = pending_session[chat_id]
        text = event.raw_text.strip()

        if text.startswith("."):
            return

        if session_data["state"] == "waiting_code":
            code = text.replace(" ", "").replace("-", "")

            if not code.isdigit():
                return

            new_client = session_data["client"]
            phone = session_data["phone"]
            phone_code_hash = session_data["phone_code_hash"]

            try:
                result = await new_client.sign_in(
                    phone, code, phone_code_hash=phone_code_hash)

                if result:
                    me = await new_client.get_me()

                    load_sessions()
                    sessions[phone] = {
                        "active": True,
                        "session_name":
                        f"session_{phone.replace('+', '').replace(' ', '')}",
                        "user_id": me.id,
                        "username": me.username,
                        "first_name": me.first_name
                    }
                    save_sessions()

                    register_handlers(new_client)
                    session_clients[phone] = new_client

                    await event.edit(
                        f"✅ Сессия добавлена и запущена!\n\nАккаунт: {me.first_name} (@{me.username})"
                    )

                    del pending_session[chat_id]

            except SessionPasswordNeededError:
                pending_session[chat_id]["state"] = "waiting_2fa"
                await event.edit("Требуется 2FA\n\n**Пароль:**")

            except PhoneCodeInvalidError:
                await event.edit("Неверный код! Попробуй ещё раз.\n\n**Код:**")

            except Exception as e:
                error_msg = str(e)
                if "password" in error_msg.lower() or "2fa" in error_msg.lower(
                ):
                    pending_session[chat_id]["state"] = "waiting_2fa"
                    await event.edit("Требуется 2FA\n\n**Пароль:**")
                else:
                    await event.edit(f"Ошибка: {error_msg}")
                    if new_client:
                        await new_client.disconnect()
                    if chat_id in pending_session:
                        del pending_session[chat_id]

        elif session_data["state"] == "waiting_2fa":
            password = text
            new_client = session_data["client"]
            phone = session_data["phone"]

            try:
                await new_client.sign_in(password=password)

                me = await new_client.get_me()

                load_sessions()
                sessions[phone] = {
                    "active": True,
                    "session_name":
                    f"session_{phone.replace('+', '').replace(' ', '')}",
                    "user_id": me.id,
                    "username": me.username,
                    "first_name": me.first_name
                }
                save_sessions()

                register_handlers(new_client)
                session_clients[phone] = new_client

                await event.edit(
                    f"✅ Сессия добавлена и запущена!\n\nАккаунт: {me.first_name} (@{me.username})"
                )

                del pending_session[chat_id]

            except Exception as e:
                await event.edit(
                    f"Неверный пароль. Попробуй ещё.\n\n**Пароль:**")

    @target_client.on(
        events.NewMessage(pattern=r"^\.removesession (.+)", outgoing=True))
    async def removesession_handler(event):
        global session_clients

        phone = event.pattern_match.group(1).strip()

        load_sessions()

        if phone not in sessions:
            await event.edit(f"Сессия `{phone}` не найдена.")
            return

        session_name = sessions[phone].get("session_name", "")

        if phone in session_clients:
            try:
                await session_clients[phone].disconnect()
            except:
                pass
            del session_clients[phone]

        del sessions[phone]
        save_sessions()

        session_file = f"{session_name}.session"
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
            except:
                pass

        await event.edit(f"✅ Сессия `{phone}` удалена и остановлена.")

    @target_client.on(events.NewMessage(pattern=r"^\.shablon$", outgoing=True))
    async def shablon_handler(event):
        global template
        reply = await event.get_reply_message()

        if not reply or not reply.document:
            await event.edit("Реплай на .txt файл!")
            return

        if reply.document.mime_type != "text/plain":
            await event.edit("Только .txt файлы!")
            return

        file = io.BytesIO()
        await reply.download_media(file=file)
        text = file.getvalue().decode("utf-8")
        template = [line.strip() for line in text.splitlines() if line.strip()]

        if template:
            await event.edit(f"Шаблон сохранён! ({len(template)} строк)")
        else:
            await event.edit("Пустой шаблон!")

    async def trl_loop(chat_id, delay, prefix=""):
        global trl_running
        while trl_running:
            if not template:
                break
            line = random.choice(template)
            text = f"{prefix} {line}".strip() if prefix else line
            try:
                await target_client.send_message(chat_id, text)
            except Exception:
                pass
            await asyncio.sleep(delay)

    @target_client.on(
        events.NewMessage(pattern=r"^\.trl($| .+)", outgoing=True))
    async def trl_handler(event):
        global trl_running, trl_task

        if trl_running:
            trl_running = False
            if trl_task:
                trl_task.cancel()
            await event.edit("Остановлено.")
            return

        args = event.raw_text[4:].strip().split()

        if not args:
            await event.edit("Укажи задержку: .trl <задержка> [доп текст]")
            return

        try:
            delay = int(args[0])
        except ValueError:
            await event.edit("Задержка должна быть числом!")
            return

        prefix = " ".join(args[1:]) if len(args) > 1 else ""

        if not template:
            await event.edit("Сначала сохрани шаблон через .shablon")
            return

        trl_running = True
        await event.edit("Запущено!")
        trl_task = asyncio.create_task(trl_loop(event.chat_id, delay, prefix))

    async def trl2_loop(chat_id, delay, prefix=""):
        global trl2_running
        while trl2_running:
            if not template:
                break
            line = random.choice(template)
            text = f"{prefix} {line}".strip() if prefix else line
            try:
                await target_client.send_message(chat_id, text)
            except Exception:
                pass
            await asyncio.sleep(delay)

    @target_client.on(
        events.NewMessage(pattern=r"^\.trl2($| .+)", outgoing=True))
    async def trl2_handler(event):
        global trl2_running, trl2_task

        if trl2_running:
            trl2_running = False
            if trl2_task:
                trl2_task.cancel()
            await event.edit("Остановлено.")
            return

        args = event.raw_text[5:].strip()

        if not args:
            await event.edit("Формат: .trl2 <задержка> [доп текст] <group_id>")
            return

        parts = args.rsplit(" ", 1)
        if len(parts) < 2:
            await event.edit("Формат: .trl2 <задержка> [доп текст] <group_id>")
            return

        try:
            group_id = int(parts[1])
        except ValueError:
            await event.edit("Неверный ID группы!")
            return

        rest = parts[0].split(" ", 1)
        try:
            delay = int(rest[0])
        except ValueError:
            await event.edit("Задержка должна быть числом!")
            return

        prefix = rest[1] if len(rest) > 1 else ""

        if not template:
            await event.edit("Сначала сохрани шаблон через .shablon")
            return

        trl2_running = True
        await event.edit("Запущено!")
        trl2_task = asyncio.create_task(trl2_loop(group_id, delay, prefix))

    @target_client.on(
        events.NewMessage(pattern=r"^\.trl3($| .+)", outgoing=True))
    async def trl3_handler(event):
        global trl3_state, trl3_last_reply

        args = event.raw_text[5:].strip().split()
        load_trl3_state()

        if not args:
            await event.edit("Формат:\n.trl3 (id) [задержка] - добавить\n.trl3 list - список\n.trl3 on/off - вкл/выкл\n.trl3 clear (id) - убрать\n.trl3 clearall - очистить")
            return

        cmd = args[0].lower()

        if cmd == "list":
            if not trl3_state["targets"]:
                await event.edit("Список автоответчика пуст.")
                return
            status = "✅ ВКЛ" if trl3_state["enabled"] else "❌ ВЫКЛ"
            text = f"**Автоответчик:** {status}\n\n"
            for uid, data in trl3_state["targets"].items():
                delay = data.get("delay", 0)
                text += f"• ID: `{uid}` (задержка: {delay}с)\n"
            await event.edit(text)
            return

        if cmd == "on":
            trl3_state["enabled"] = True
            save_trl3_state()
            await event.edit("✅ Автоответчик включен")
            return

        if cmd == "off":
            trl3_state["enabled"] = False
            save_trl3_state()
            await event.edit("❌ Автоответчик выключен")
            return

        if cmd == "clear":
            if len(args) < 2:
                await event.edit("Укажи ID: .trl3 clear (id)")
                return
            uid = args[1]
            if uid in trl3_state["targets"]:
                del trl3_state["targets"][uid]
                if uid in trl3_last_reply:
                    del trl3_last_reply[uid]
                save_trl3_state()
                await event.edit(f"✅ ID `{uid}` убран из списка")
            else:
                await event.edit(f"ID `{uid}` не найден в списке")
            return

        if cmd == "clearall":
            trl3_state["targets"] = {}
            trl3_last_reply = {}
            save_trl3_state()
            await event.edit("✅ Список автоответчика очищен")
            return

        try:
            user_id = int(args[0])
        except ValueError:
            await event.edit("ID должен быть числом!")
            return

        delay = 0
        if len(args) > 1:
            try:
                delay = int(args[1])
            except ValueError:
                await event.edit("Задержка должна быть числом!")
                return

        if not template:
            await event.edit("Сначала сохрани шаблон через .shablon")
            return

        trl3_state["targets"][str(user_id)] = {"delay": delay}
        save_trl3_state()
        await event.edit(f"✅ Добавлен в автоответчик: `{user_id}` (задержка: {delay}с)")

    @target_client.on(events.NewMessage(incoming=True))
    async def trl3_watcher(event):
        global trl3_last_reply

        load_trl3_state()

        if not trl3_state["enabled"] or not trl3_state["targets"] or not template:
            return

        sender_id = str(event.sender_id)
        if sender_id not in trl3_state["targets"]:
            return

        target_data = trl3_state["targets"][sender_id]
        delay = target_data.get("delay", 0)

        current_time = time.time()
        last_time = trl3_last_reply.get(sender_id, 0)
        if current_time - last_time < delay:
            return

        line = random.choice(template)
        try:
            await event.reply(line)
            trl3_last_reply[sender_id] = current_time
        except Exception:
            pass

    @target_client.on(events.NewMessage(pattern=r"^\.delmenow$",
                                        outgoing=True))
    async def delmenow_handler(event):
        me = await target_client.get_me()
        async for msg in target_client.iter_messages(event.chat_id,
                                                     from_user=me.id):
            try:
                await msg.delete()
            except Exception:
                pass

    async def spam_loop(chat_id, delay, message):
        global spam_running
        while spam_running:
            try:
                await target_client.send_message(chat_id, message)
            except Exception:
                pass
            await asyncio.sleep(delay)

    @target_client.on(
        events.NewMessage(pattern=r"^\.spam($| .+)", outgoing=True))
    async def spam_handler(event):
        global spam_running, spam_task

        if spam_running:
            spam_running = False
            if spam_task:
                spam_task.cancel()
            await event.edit("Остановлено.")
            return

        args = event.raw_text[5:].strip().split(" ", 1)

        if len(args) < 2:
            await event.edit("Формат: .spam <задержка> <сообщение>")
            return

        try:
            delay = int(args[0])
        except ValueError:
            await event.edit("Задержка должна быть числом!")
            return

        message = args[1]

        spam_running = True
        await event.edit("Спам запущен!")
        spam_task = asyncio.create_task(
            spam_loop(event.chat_id, delay, message))

    async def trl4_loop(chat_id, delay, user_id, user_entity):
        global trl4_running
        while trl4_running:
            if not template:
                break
            line = random.choice(template)
            try:
                if user_entity.username:
                    mention = f"@{user_entity.username}"
                    text = f"{mention} {line}"
                    await target_client.send_message(chat_id, text)
                else:
                    first_name = user_entity.first_name or "User"
                    mention = f"[{first_name}](tg://user?id={user_id})"
                    text = f"{mention} {line}"
                    await target_client.send_message(chat_id, text, parse_mode='md')
            except Exception as e:
                print(f"trl4 error: {e}")
            await asyncio.sleep(delay)

    @target_client.on(
        events.NewMessage(pattern=r"^\.trl4($| .+)", outgoing=True))
    async def trl4_handler(event):
        global trl4_running, trl4_task

        if trl4_running:
            trl4_running = False
            if trl4_task:
                trl4_task.cancel()
            await event.edit("Остановлено.")
            return

        args = event.raw_text[5:].strip().split()

        if len(args) < 2:
            await event.edit("Формат: .trl4 <задержка> <id юзера>")
            return

        try:
            delay = int(args[0])
        except ValueError:
            await event.edit("Задержка должна быть числом!")
            return

        try:
            user_id = int(args[1])
        except ValueError:
            await event.edit("ID должен быть числом!")
            return

        if not template:
            await event.edit("Сначала сохрани шаблон через .shablon")
            return

        try:
            user_entity = await target_client.get_entity(user_id)
        except Exception as e:
            await event.edit(f"Не удалось найти юзера: {e}")
            return

        trl4_running = True
        await event.edit("Запущено!")
        trl4_task = asyncio.create_task(
            trl4_loop(event.chat_id, delay, user_id, user_entity))


register_handlers(client)


async def start_saved_sessions():
    global session_clients
    load_sessions()
    load_proxies()

    for phone, data in sessions.items():
        if not data.get("active"):
            continue

        session_name = data.get("session_name")
        if not session_name:
            continue

        session_file = f"{session_name}.session"
        if not os.path.exists(session_file):
            continue

        try:
            if active_proxy and active_proxy in proxies:
                proxy_data = proxies[active_proxy]
                proxy = (proxy_data["ip"], proxy_data["port"],
                         proxy_data["secret"])
                session_client = TelegramClient(
                    session_name,
                    int(API_ID),
                    API_HASH,
                    connection=connection.
                    ConnectionTcpMTProxyRandomizedIntermediate,
                    proxy=proxy)
            else:
                session_client = TelegramClient(session_name, int(API_ID),
                                                API_HASH)

            await session_client.connect()

            if await session_client.is_user_authorized():
                register_handlers(session_client)
                session_clients[phone] = session_client
                me = await session_client.get_me()
                print(
                    f"Session started: {me.first_name} (@{me.username}) - {phone}"
                )
            else:
                await session_client.disconnect()
                print(f"Session {phone} is not authorized, skipping")

        except Exception as e:
            print(f"Failed to start session {phone}: {e}")


async def main():
    global start_time
    print("Starting Telegram Userbot...")
    load_sessions()
    load_proxies()
    load_trl3_state()
    await client.start()
    start_time = time.time()
    me = await client.get_me()
    print(f"Logged in as: {me.first_name} (@{me.username})")

    await start_saved_sessions()

    print("Userbot is running!")
    print(
        "type .info for commands"
    )
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
