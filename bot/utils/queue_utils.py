from telethon import events

from bot import Button, itertools, pyro, queue_lock, re, tele

from .bot_utils import QUEUE, QUEUE_STATUS
from .log_utils import logger

STATUS_START = 1
PAGES = 1
PAGE_NO = 1
STATUS_LIMIT = 10


async def q_dup_check(event):
    try:
        if QUEUE_STATUS:
            check = True
            for q_id in QUEUE_STATUS:
                _q_id = str(event.chat_id) + " " + str(event.id)
                if q_id == _q_id:
                    check = False
        else:
            check = True
    except Exception:
        check = True
        await logger(Exception)
    return check


async def queue_status(event):
    try:
        if QUEUE_STATUS:
            for q_id in QUEUE_STATUS:
                _chat_id, _msg_id = q_id.split()
                if event.chat_id == int(_chat_id):
                    msg = await pyro.get_messages(int(_chat_id), int(_msg_id))
                    try:
                        await msg.delete()
                    except Exception:
                        pass
                    QUEUE_STATUS.remove(q_id)
            return QUEUE_STATUS.append(str(event.chat_id) + " " + str(event.id))
        else:
            QUEUE_STATUS.append(str(event.chat_id) + " " + str(event.id))
    except Exception:
        await logger(Exception)


async def get_queue_msg():
    msg = str()
    button = None
    try:
        i = len(QUEUE)
        globals()["PAGES"] = (i + STATUS_LIMIT - 2) // STATUS_LIMIT
        if PAGE_NO > PAGES and PAGES != 0:
            globals()["STATUS_START"] = (STATUS_LIMIT * PAGES) - 9
            globals()["PAGE_NO"] = PAGES

        for file, _no in zip(
            list(QUEUE.values())[STATUS_START : STATUS_LIMIT + STATUS_START],
            itertools.count(STATUS_START),
        ):
            file_name, u_msg, ver_fil = file
            chat_id, msg_id = list(QUEUE.keys())[list(QUEUE.values()).index(file)]
            user_id, message = u_msg
            user_id = 777000 if str(user_id).startswith("-100") else user_id
            user = await pyro.get_users(user_id)
            # Backwards compatibility:
            ver, fil = ver_fil if isinstance(ver_fil, tuple) else (ver_fil, None)

            msg += f"{_no}. `{file_name}`\n  **•Filter:** {fil.split("\n")}\n  **•Release version:** {ver}\n  **•Added by:** [{user.first_name}](tg://user?id={user_id})\n\n"

        if not msg:
            return None, None
        if (i - 1) > STATUS_LIMIT:
            # Create the Inline button
            btn_prev = Button.inline("<<", data="status prev")
            btn_info = Button.inline(f"{PAGE_NO}/{PAGES} ({i - 1})", data="status 🙆")
            btn_next = Button.inline(">>", data="status next")
            # Define the button layout
            button = [[btn_prev, btn_info, btn_next]]
        else:
            msg += f"**Pending Tasks:** {i - 1}\n"
        msg += f"\n**📌 Tip: To remove an item from queue use** /clear <queue number>"

    except Exception:
        await logger(Exception)
        msg = "__An error occurred.__"
    return msg, button


async def turn_page(event):
    try:
        data = event.pattern_match.group(1).decode().strip()
        await event.answer(f"{data}…")
        global STATUS_START, PAGE_NO, PAGES
        async with queue_lock:
            if data == "next":
                if PAGE_NO == PAGES:
                    STATUS_START = 1
                    PAGE_NO = 1
                else:
                    STATUS_START += STATUS_LIMIT
                    PAGE_NO += 1
            elif data == "prev":
                if PAGE_NO == 1:
                    STATUS_START = (STATUS_LIMIT * (PAGES - 1)) + 1
                    PAGE_NO = PAGES
                else:
                    STATUS_START -= STATUS_LIMIT
                    PAGE_NO -= 1
    except Exception:
        await logger(Exception)


tele.add_event_handler(
    turn_page, events.callbackquery.CallbackQuery(data=re.compile(b"status(.*)"))
)
