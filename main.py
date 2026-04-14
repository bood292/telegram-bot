# -*- coding: utf-8 -*-

import json
import random
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatPermissions,
)

# =========================================================
# الإعدادات
# =========================================================
API_ID = 36318598
API_HASH = "a177454f07b10a87ede14c509b9cf2c0"
BOT_TOKEN = "8507741295:AAF_HE8mADXdJvuCBFdiPqQ-OSrPEnqHO98"
OWNER_ID = 838755938

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

SETTINGS_FILE = DATA_DIR / "settings.json"
BANK_FILE = DATA_DIR / "bank.json"
ROLES_FILE = DATA_DIR / "roles.json"
WARNS_FILE = DATA_DIR / "warns.json"
POINTS_FILE = DATA_DIR / "points.json"
REPLIES_FILE = DATA_DIR / "replies.json"

app = Client(
    "super_arabic_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# =========================================================
# التخزين
# =========================================================
def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


chat_settings: Dict[str, Any] = load_json(SETTINGS_FILE, {})
bank_data: Dict[str, Any] = load_json(BANK_FILE, {})
roles_data: Dict[str, Any] = load_json(ROLES_FILE, {})
warns_data: Dict[str, Any] = load_json(WARNS_FILE, {})
points_data: Dict[str, Any] = load_json(POINTS_FILE, {})
replies_data: Dict[str, Any] = load_json(REPLIES_FILE, {})

# =========================================================
# بيانات ثابتة
# =========================================================
BAD_WORDS = [
    "sex", "porn", "xxx", "nude", "naked",
    "اباحية", "إباحية", "اباحي", "جنس", "سكس", "عاري", "عارية",
    "نيك", "مفاخذة", "مقاطع ساخنة", "فيديو اباحي"
]

QUIZ_QUESTIONS = [
    {"q": "ما هي عاصمة فرنسا؟", "a": "باريس"},
    {"q": "كم يساوي 2 + 2 ؟", "a": "4"},
    {"q": "ما أكبر كوكب في المجموعة الشمسية؟", "a": "المشتري"},
    {"q": "كم عدد أيام الأسبوع؟", "a": "7"},
    {"q": "ما عاصمة مصر؟", "a": "القاهرة"},
    {"q": "ما لون السماء في اليوم الصافي؟", "a": "ازرق"},
]

RIDDLES = [
    {"q": "شيء له مفاتيح لكن لا يفتح أبواب، ما هو؟", "a": "لوحة المفاتيح"},
    {"q": "له عقارب لكنه لا يلدغ، ما هو؟", "a": "الساعة"},
    {"q": "شيء يجب كسره قبل استخدامه، ما هو؟", "a": "البيض"},
    {"q": "شيء يصعد ولا ينزل، ما هو؟", "a": "العمر"},
    {"q": "له عين واحدة ولا يرى، ما هو؟", "a": "الابرة"},
]

LOVE_REPLIES = ["حب نار 🔥", "حب متوسط 🙂", "حب ضعيف 😅", "حب أسطوري 😍"]
OPINION_REPLIES = ["حلو 😎", "مو طبيعي 😂", "عادي 🙂", "أسطوري 🔥", "يبيله شغل 😅"]

# =========================================================
# الحالة المؤقتة
# =========================================================
guess_state: Dict[str, int] = {}
quiz_state: Dict[str, Dict[str, Any]] = {}
riddle_state: Dict[str, Dict[str, Any]] = {}
spam_tracker: Dict[str, Dict[str, List[float]]] = {}

# =========================================================
# أدوات عامة
# =========================================================
def cid(chat_id: int) -> str:
    return str(chat_id)


def uid(user_id: int) -> str:
    return str(user_id)


def args_from_text(text: str) -> List[str]:
    parts = (text or "").strip().split()
    return parts[1:] if len(parts) > 1 else []


async def send_bold(message, text: str, reply_markup=None):
    await message.reply_text(f"<b>{text}</b>", parse_mode=ParseMode.HTML, reply_markup=reply_markup)


async def edit_bold(message, text: str, reply_markup=None):
    await message.edit_text(f"<b>{text}</b>", parse_mode=ParseMode.HTML, reply_markup=reply_markup)


async def answer_bold(query, text: str):
    await query.answer(text, show_alert=False)


def get_chat_settings(chat_id: int) -> Dict[str, Any]:
    key = cid(chat_id)
    if key not in chat_settings:
        chat_settings[key] = {
            "links_lock": False,
            "anti_bad_words": True,
            "welcome_enabled": True,
            "bank_enabled": True,
            "games_enabled": True,
            "fun_enabled": True,
            "id_enabled": True,
            "clean_enabled": True,
            "replies_enabled": True,
            "warn_limit": 3,
            "anti_spam": True,
        }
        save_json(SETTINGS_FILE, chat_settings)
    return chat_settings[key]


def set_chat_setting(chat_id: int, key: str, value: Any):
    s = get_chat_settings(chat_id)
    s[key] = value
    save_json(SETTINGS_FILE, chat_settings)


def get_user_bank(user_id: int) -> Dict[str, Any]:
    key = uid(user_id)
    if key not in bank_data:
        bank_data[key] = {
            "balance": 0,
            "last_daily": 0,
            "last_work": 0,
        }
        save_json(BANK_FILE, bank_data)
    return bank_data[key]


def get_chat_warns(chat_id: int) -> Dict[str, int]:
    key = cid(chat_id)
    if key not in warns_data:
        warns_data[key] = {}
        save_json(WARNS_FILE, warns_data)
    return warns_data[key]


def get_chat_points(chat_id: int) -> Dict[str, int]:
    key = cid(chat_id)
    if key not in points_data:
        points_data[key] = {}
        save_json(POINTS_FILE, points_data)
    return points_data[key]


def add_points(chat_id: int, user_id: int, amount: int):
    p = get_chat_points(chat_id)
    key = uid(user_id)
    p[key] = p.get(key, 0) + amount
    save_json(POINTS_FILE, points_data)


def get_points(chat_id: int, user_id: int) -> int:
    return get_chat_points(chat_id).get(uid(user_id), 0)


def get_chat_replies(chat_id: int) -> Dict[str, str]:
    key = cid(chat_id)
    if key not in replies_data:
        replies_data[key] = {}
        save_json(REPLIES_FILE, replies_data)
    return replies_data[key]


def get_chat_roles(chat_id: int) -> Dict[str, Dict[str, str]]:
    key = cid(chat_id)
    if key not in roles_data:
        roles_data[key] = {
            "owners": {},
            "founders": {},
            "admins": {},
            "special": {},
        }
        save_json(ROLES_FILE, roles_data)
    return roles_data[key]


def set_role(chat_id: int, user_id: int, section: str, title: str):
    roles = get_chat_roles(chat_id)
    roles[section][uid(user_id)] = title
    save_json(ROLES_FILE, roles_data)


def remove_role(chat_id: int, user_id: int, section: str):
    roles = get_chat_roles(chat_id)
    roles[section].pop(uid(user_id), None)
    save_json(ROLES_FILE, roles_data)


def has_custom_role(chat_id: int, user_id: int, sections: List[str]) -> bool:
    roles = get_chat_roles(chat_id)
    key = uid(user_id)
    for section in sections:
        if key in roles.get(section, {}):
            return True
    return False


async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        status_name = getattr(member.status, "name", str(member.status))
        status_name = str(status_name).upper()
        return status_name in ("ADMINISTRATOR", "OWNER", "CREATOR")
    except Exception:
        return False


async def require_admin(client: Client, message) -> bool:
    if not message.from_user:
        await send_bold(message, "تعذر معرفة المستخدم")
        return False
    if not await is_admin(client, message.chat.id, message.from_user.id):
        await send_bold(message, "هذا الأمر للمشرفين فقط")
        return False
    return True


async def require_owner_or_admin(client: Client, message) -> bool:
    if not message.from_user:
        return False
    if await is_admin(client, message.chat.id, message.from_user.id):
        return True
    if has_custom_role(message.chat.id, message.from_user.id, ["owners", "founders"]):
        return True
    await send_bold(message, "هذا الأمر للمالكين أو المشرفين فقط")
    return False


async def get_target_user(client: Client, message) -> Optional[Any]:
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    args = args_from_text(message.text or "")
    if not args:
        return None

    try:
        return await client.get_users(args[0])
    except Exception:
        return None

# =========================================================
# الأزرار
# =========================================================
def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛡️ الحماية", callback_data="menu_protection"),
            InlineKeyboardButton("👮 الادمنية", callback_data="menu_admins"),
        ],
        [
            InlineKeyboardButton("💰 البنك", callback_data="menu_bank"),
            InlineKeyboardButton("🎮 الألعاب", callback_data="menu_games"),
        ],
        [
            InlineKeyboardButton("😂 التحشيش", callback_data="menu_fun"),
            InlineKeyboardButton("🧹 التنظيف", callback_data="menu_clean"),
        ],
        [
            InlineKeyboardButton("🔒 القفل / الفتح", callback_data="menu_lock"),
            InlineKeyboardButton("⚡ التفعيل / التعطيل", callback_data="menu_enable"),
        ],
        [
            InlineKeyboardButton("🧠 الردود", callback_data="menu_replies"),
            InlineKeyboardButton("📊 النقاط", callback_data="menu_points"),
        ],
        [
            InlineKeyboardButton("👑 الرتب", callback_data="menu_roles"),
        ],
    ])


def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="back_main")]])


def lock_menu(chat_id: int):
    s = get_chat_settings(chat_id)
    links_icon = "❌" if s["links_lock"] else "✔️"
    bad_icon = "❌" if s["anti_bad_words"] else "✔️"
    spam_icon = "✔️" if s["anti_spam"] else "❌"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{links_icon} الروابط", callback_data="toggle_lock_links")],
        [InlineKeyboardButton(f"{bad_icon} الكلمات الممنوعة", callback_data="toggle_bad_words")],
        [InlineKeyboardButton(f"{spam_icon} مضاد السبام", callback_data="toggle_spam")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")],
    ])


def enable_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ تعطيل الترحيب", callback_data="set_off:welcome_enabled"), InlineKeyboardButton("✔️ تفعيل الترحيب", callback_data="set_on:welcome_enabled")],
        [InlineKeyboardButton("❌ تعطيل البنك", callback_data="set_off:bank_enabled"), InlineKeyboardButton("✔️ تفعيل البنك", callback_data="set_on:bank_enabled")],
        [InlineKeyboardButton("❌ تعطيل الألعاب", callback_data="set_off:games_enabled"), InlineKeyboardButton("✔️ تفعيل الألعاب", callback_data="set_on:games_enabled")],
        [InlineKeyboardButton("❌ تعطيل التحشيش", callback_data="set_off:fun_enabled"), InlineKeyboardButton("✔️ تفعيل التحشيش", callback_data="set_on:fun_enabled")],
        [InlineKeyboardButton("❌ تعطيل الايدي", callback_data="set_off:id_enabled"), InlineKeyboardButton("✔️ تفعيل الايدي", callback_data="set_on:id_enabled")],
        [InlineKeyboardButton("❌ تعطيل التنظيف", callback_data="set_off:clean_enabled"), InlineKeyboardButton("✔️ تفعيل التنظيف", callback_data="set_on:clean_enabled")],
        [InlineKeyboardButton("❌ تعطيل الردود", callback_data="set_off:replies_enabled"), InlineKeyboardButton("✔️ تفعيل الردود", callback_data="set_on:replies_enabled")],
        [InlineKeyboardButton("🔙 القائمه الرئيسيه", callback_data="back_main")],
    ])


def pro_games_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 افتح @gamee", url="https://t.me/gamee")],
        [InlineKeyboardButton("🕹️ لعبة 1", url="https://t.me/gamee"), InlineKeyboardButton("🕹️ لعبة 2", url="https://t.me/gamee")],
        [InlineKeyboardButton("🕹️ لعبة 3", url="https://t.me/gamee"), InlineKeyboardButton("🕹️ لعبة 4", url="https://t.me/gamee")],
        [InlineKeyboardButton("🕹️ لعبة 5", url="https://t.me/gamee"), InlineKeyboardButton("🕹️ لعبة 6", url="https://t.me/gamee")],
    ])

# =========================================================
# البداية والقوائم
# =========================================================
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    text = "اوامر البوت الرئيسية\nــــــــــــــــــــــ\nاختر ما تريد عرضه من القائمة:"
    await send_bold(message, text, reply_markup=main_menu())


@app.on_message(filters.regex(r"^(الاوامر|الأوامر|اوامر)$"))
async def commands_cmd(client, message):
    text = "اوامر البوت الرئيسية\nــــــــــــــــــــــ\nاختر ما تريد عرضه من القائمة:"
    await send_bold(message, text, reply_markup=main_menu())


@app.on_callback_query()
async def callback_handler(client, query):
    if not query.message:
        return

    data = query.data
    chat_id = query.message.chat.id

    if data == "back_main":
        await edit_bold(query.message, "اوامر البوت الرئيسية\nــــــــــــــــــــــ\nاختر ما تريد عرضه من القائمة:", reply_markup=main_menu())
        return

    if data == "menu_protection":
        await edit_bold(query.message, "قسم الحماية\nقفل الروابط\nفتح الروابط\nفلترة كلمات\nمضاد سبام", reply_markup=back_button())
        return

    if data == "menu_admins":
        await edit_bold(query.message, "قسم الادمنية\nحظر\nطرد\nكتم\nالغاء_كتم\nتاك للكل\nايدي\nايدي بالرد", reply_markup=back_button())
        return

    if data == "menu_bank":
        await edit_bold(query.message, "قسم البنك\nرصيدي\nراتب\nعمل\nتحويل 100 بالرد", reply_markup=back_button())
        return

    if data == "menu_games":
        await edit_bold(query.message, "قسم الألعاب\nنرد\nخمن\nتخمين_الرقم 5\nسؤال\nلغز\nجواب ...\nxo\nالعاب احترافيه", reply_markup=back_button())
        return

    if data == "menu_fun":
        await edit_bold(query.message, "قسم التحشيش\nنسبه الحب\nنسبه الذكاء\nشنو رايك بهذا\nبوسه", reply_markup=back_button())
        return

    if data == "menu_clean":
        await edit_bold(query.message, "قسم التنظيف\nمسح بالرد\nمسح 10", reply_markup=back_button())
        return

    if data == "menu_replies":
        await edit_bold(query.message, "قسم الردود\nاضف رد\nمسح رد\nقائمة الردود", reply_markup=back_button())
        return

    if data == "menu_points":
        await edit_bold(query.message, "قسم النقاط\nنقاطي\nتوب النقاط\nبيع نقاطي 10", reply_markup=back_button())
        return

    if data == "menu_roles":
        await edit_bold(query.message, "قسم الرتب\nرفع مميز\nتنزيل مميز\nالمميزين\nرفع مالك\nتنزيل مالك\nالمالكين", reply_markup=back_button())
        return

    if data == "menu_lock":
        await edit_bold(query.message, "اعدادات القفل / الفتح", reply_markup=lock_menu(chat_id))
        return

    if data == "toggle_lock_links":
        s = get_chat_settings(chat_id)
        s["links_lock"] = not s["links_lock"]
        save_json(SETTINGS_FILE, chat_settings)
        await answer_bold(query, "تم تحديث قفل الروابط")
        await edit_bold(query.message, "اعدادات القفل / الفتح", reply_markup=lock_menu(chat_id))
        return

    if data == "toggle_bad_words":
        s = get_chat_settings(chat_id)
        s["anti_bad_words"] = not s["anti_bad_words"]
        save_json(SETTINGS_FILE, chat_settings)
        await answer_bold(query, "تم تحديث فلترة الكلمات")
        await edit_bold(query.message, "اعدادات القفل / الفتح", reply_markup=lock_menu(chat_id))
        return

    if data == "toggle_spam":
        s = get_chat_settings(chat_id)
        s["anti_spam"] = not s["anti_spam"]
        save_json(SETTINGS_FILE, chat_settings)
        await answer_bold(query, "تم تحديث مضاد السبام")
        await edit_bold(query.message, "اعدادات القفل / الفتح", reply_markup=lock_menu(chat_id))
        return

    if data == "menu_enable":
        await edit_bold(query.message, "اوامر التفعيل والتعطيل", reply_markup=enable_menu())
        return

    if data.startswith("set_on:"):
        key = data.split(":", 1)[1]
        set_chat_setting(chat_id, key, True)
        await answer_bold(query, "تم التفعيل")
        await edit_bold(query.message, "اوامر التفعيل والتعطيل", reply_markup=enable_menu())
        return

    if data.startswith("set_off:"):
        key = data.split(":", 1)[1]
        set_chat_setting(chat_id, key, False)
        await answer_bold(query, "تم التعطيل")
        await edit_bold(query.message, "اوامر التفعيل والتعطيل", reply_markup=enable_menu())
        return

# =========================================================
# الترحيب
# =========================================================
@app.on_message(filters.new_chat_members)
async def welcome_new_members(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["welcome_enabled"]:
        return
    names = [u.first_name for u in message.new_chat_members]
    await send_bold(message, f"اهلاً وسهلاً {' ، '.join(names)}\nنورتوا المجموعة")

# =========================================================
# الأيدي
# =========================================================
@app.on_message(filters.regex(r"^ايدي$"))
async def my_id_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["id_enabled"]:
        return await send_bold(message, "أمر الايدي معطل")
    add_points(message.chat.id, message.from_user.id, 1)
    await send_bold(message, f"ايديك: {message.from_user.id}\nايدي المجموعة: {message.chat.id}")


@app.on_message(filters.regex(r"^ايدي بالرد$"))
async def reply_id_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["id_enabled"]:
        return await send_bold(message, "أمر الايدي معطل")
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await send_bold(message, "رد على شخص أولاً")
    await send_bold(message, f"ايدي المستخدم: {message.reply_to_message.from_user.id}")

# =========================================================
# رتب بسيطة
# =========================================================
@app.on_message(filters.regex(r"^(رفع مميز|/رفع مميز)(\s+.+)?$") & filters.group)
async def promote_special_cmd(client, message):
    if not await require_owner_or_admin(client, message):
        return
    target = await get_target_user(client, message)
    if not target:
        return await send_bold(message, "استخدم بالرد أو هكذا:\nرفع مميز @username")
    set_role(message.chat.id, target.id, "special", "مميز")
    await send_bold(message, f"تم رفع {target.first_name} مميز")


@app.on_message(filters.regex(r"^(تنزيل مميز|/تنزيل مميز)(\s+.+)?$") & filters.group)
async def demote_special_cmd(client, message):
    if not await require_owner_or_admin(client, message):
        return
    target = await get_target_user(client, message)
    if not target:
        return await send_bold(message, "استخدم بالرد أو هكذا:\nتنزيل مميز @username")
    remove_role(message.chat.id, target.id, "special")
    await send_bold(message, f"تم تنزيل {target.first_name} من رتبة مميز")


@app.on_message(filters.regex(r"^المميزين$"))
async def list_special_cmd(client, message):
    roles = get_chat_roles(message.chat.id)["special"]
    if not roles:
        return await send_bold(message, "لا يوجد مميزين")
    text = "المميزين:\n" + "\n".join(f"- {u}" for u in roles.keys())
    await send_bold(message, text)


@app.on_message(filters.regex(r"^(رفع مالك|/رفع مالك)(\s+.+)?$") & filters.group)
async def promote_owner_cmd(client, message):
    if not await require_admin(client, message):
        return
    target = await get_target_user(client, message)
    if not target:
        return await send_bold(message, "استخدم بالرد أو هكذا:\nرفع مالك @username")
    set_role(message.chat.id, target.id, "owners", "مالك")
    await send_bold(message, f"تم رفع {target.first_name} مالك")


@app.on_message(filters.regex(r"^(تنزيل مالك|/تنزيل مالك)(\s+.+)?$") & filters.group)
async def demote_owner_cmd(client, message):
    if not await require_admin(client, message):
        return
    target = await get_target_user(client, message)
    if not target:
        return await send_bold(message, "استخدم بالرد أو هكذا:\nتنزيل مالك @username")
    remove_role(message.chat.id, target.id, "owners")
    await send_bold(message, f"تم تنزيل {target.first_name} من رتبة مالك")


@app.on_message(filters.regex(r"^المالكين$"))
async def list_owners_cmd(client, message):
    roles = get_chat_roles(message.chat.id)["owners"]
    if not roles:
        return await send_bold(message, "لا يوجد مالكين")
    text = "المالكين:\n" + "\n".join(f"- {u}" for u in roles.keys())
    await send_bold(message, text)

# =========================================================
# الادمنية الفعلية
# =========================================================
@app.on_message(filters.regex(r"^(حظر|/حظر)(\s+.+)?$") & filters.group)
async def ban_cmd(client, message):
    if not await require_admin(client, message):
        return
    target = await get_target_user(client, message)
    if not target:
        return await send_bold(message, "استخدم بالرد أو هكذا:\nحظر @username")
    try:
        await client.ban_chat_member(message.chat.id, target.id)
        await send_bold(message, f"تم حظر {target.first_name}")
    except Exception as e:
        await send_bold(message, f"تعذر الحظر:\n{e}")


@app.on_message(filters.regex(r"^(طرد|/طرد)(\s+.+)?$") & filters.group)
async def kick_cmd(client, message):
    if not await require_admin(client, message):
        return
    target = await get_target_user(client, message)
    if not target:
        return await send_bold(message, "استخدم بالرد أو هكذا:\nطرد @username")
    try:
        await client.ban_chat_member(message.chat.id, target.id)
        await client.unban_chat_member(message.chat.id, target.id)
        await send_bold(message, f"تم طرد {target.first_name}")
    except Exception as e:
        await send_bold(message, f"تعذر الطرد:\n{e}")


@app.on_message(filters.regex(r"^(كتم|/كتم)(\s+.+)?$") & filters.group)
async def mute_cmd(client, message):
    if not await require_admin(client, message):
        return
    target = await get_target_user(client, message)
    if not target:
        return await send_bold(message, "استخدم بالرد أو هكذا:\nكتم @username")
    try:
        await client.restrict_chat_member(message.chat.id, target.id, ChatPermissions())
        await send_bold(message, f"تم كتم {target.first_name}")
    except Exception as e:
        await send_bold(message, f"تعذر الكتم:\n{e}")


@app.on_message(filters.regex(r"^(الغاء_كتم|/الغاء_كتم)(\s+.+)?$") & filters.group)
async def unmute_cmd(client, message):
    if not await require_admin(client, message):
        return
    target = await get_target_user(client, message)
    if not target:
        return await send_bold(message, "استخدم بالرد أو هكذا:\nالغاء_كتم @username")
    try:
        await client.restrict_chat_member(
            message.chat.id,
            target.id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
                can_invite_users=True,
            )
        )
        await send_bold(message, f"تم إلغاء كتم {target.first_name}")
    except Exception as e:
        await send_bold(message, f"تعذر إلغاء الكتم:\n{e}")

# =========================================================
# تاك للكل
# =========================================================
@app.on_message(filters.regex(r"^(تاك للكل|تاك)$") & filters.group)
async def tag_all_cmd(client, message):
    if not await require_admin(client, message):
        return

    mentions = []
    count = 0
    async for msg in client.get_chat_history(message.chat.id, limit=80):
        if msg.from_user and not msg.from_user.is_bot:
            mention = msg.from_user.mention
            if mention not in mentions:
                mentions.append(mention)
                count += 1
            if count >= 30:
                break

    if not mentions:
        return await send_bold(message, "ما لقيت أعضاء كفاية للمنشن")
    await send_bold(message, "نداء للكل:\n\n" + "\n".join(mentions))

# =========================================================
# الحماية
# =========================================================
@app.on_message(filters.group & filters.text)
async def protection_handler(client, message):
    if not message.from_user:
        return

    text = (message.text or "").lower().strip()
    settings = get_chat_settings(message.chat.id)
    chat_key = cid(message.chat.id)
    user_key = uid(message.from_user.id)

    ignored = [
        "/start", "الاوامر", "الأوامر", "اوامر",
        "حظر", "طرد", "كتم", "الغاء_كتم",
        "قفل الروابط", "فتح الروابط",
        "رصيدي", "راتب", "عمل", "تحويل",
        "خمن", "تخمين_الرقم", "نرد", "سؤال", "لغز", "جواب",
        "العاب احترافيه", "الألعاب الاحترافيه",
        "نسبه الحب", "نسبه الذكاء", "شنو رايك بهذا", "بوسه",
        "ايدي", "ايدي بالرد", "تاك", "تاك للكل",
        "مسح", "اضف رد", "مسح رد", "قائمة الردود", "الردود", "نقاطي", "توب النقاط", "بيع نقاطي",
        "رفع مميز", "تنزيل مميز", "المميزين", "رفع مالك", "تنزيل مالك", "المالكين"
    ]
    if any(text.startswith(x) for x in ignored):
        return

    if settings["anti_bad_words"]:
        for bad in BAD_WORDS:
            if bad in text:
                try:
                    await message.delete()
                except Exception:
                    pass
                return await send_bold(message, f"تم حذف رسالة مخالفة من {message.from_user.first_name}")

    if settings["links_lock"] and ("http" in text or "www" in text or "t.me/" in text):
        try:
            await message.delete()
        except Exception:
            pass
        warns = get_chat_warns(message.chat.id)
        warns[user_key] = warns.get(user_key, 0) + 1
        save_json(WARNS_FILE, warns_data)
        limit = settings.get("warn_limit", 3)
        await send_bold(message, f"تم حذف رابط من {message.from_user.first_name}\nالتحذير: {warns[user_key]}/{limit}")
        if warns[user_key] >= limit:
            try:
                await client.restrict_chat_member(message.chat.id, message.from_user.id, ChatPermissions())
                await send_bold(message, f"تم كتم {message.from_user.first_name} بسبب تكرار المخالفة")
            except Exception:
                pass
        return

    if settings["anti_spam"]:
        if chat_key not in spam_tracker:
            spam_tracker[chat_key] = {}
        if user_key not in spam_tracker[chat_key]:
            spam_tracker[chat_key][user_key] = []
        now = time.time()
        spam_tracker[chat_key][user_key].append(now)
        spam_tracker[chat_key][user_key] = [t for t in spam_tracker[chat_key][user_key] if now - t < 5]
        if len(spam_tracker[chat_key][user_key]) > 5:
            try:
                await message.delete()
            except Exception:
                pass
            await send_bold(message, f"تم حذف سبام من {message.from_user.first_name}")
            return

# =========================================================
# أوامر القفل المباشرة
# =========================================================
@app.on_message(filters.regex(r"^قفل الروابط$") & filters.group)
async def lock_links_cmd(client, message):
    if not await require_admin(client, message):
        return
    set_chat_setting(message.chat.id, "links_lock", True)
    await send_bold(message, "تم قفل الروابط")


@app.on_message(filters.regex(r"^فتح الروابط$") & filters.group)
async def unlock_links_cmd(client, message):
    if not await require_admin(client, message):
        return
    set_chat_setting(message.chat.id, "links_lock", False)
    await send_bold(message, "تم فتح الروابط")

# =========================================================
# البنك
# =========================================================
@app.on_message(filters.regex(r"^رصيدي$"))
async def balance_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["bank_enabled"]:
        return await send_bold(message, "البنك معطل")
    add_points(message.chat.id, message.from_user.id, 1)
    user_bank = get_user_bank(message.from_user.id)
    await send_bold(message, f"رصيدك: {user_bank['balance']} عملة")


@app.on_message(filters.regex(r"^راتب$"))
async def daily_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["bank_enabled"]:
        return await send_bold(message, "البنك معطل")
    user_bank = get_user_bank(message.from_user.id)
    now = int(time.time())
    if now - user_bank["last_daily"] < 86400:
        remain = 86400 - (now - user_bank["last_daily"])
        h = remain // 3600
        m = (remain % 3600) // 60
        return await send_bold(message, f"أخذت راتبك اليومي بالفعل\nارجع بعد {h} ساعة و {m} دقيقة")
    user_bank["balance"] += 100
    user_bank["last_daily"] = now
    save_json(BANK_FILE, bank_data)
    await send_bold(message, "أخذت راتبك اليومي: 100 عملة")


@app.on_message(filters.regex(r"^عمل$"))
async def work_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["bank_enabled"]:
        return await send_bold(message, "البنك معطل")
    user_bank = get_user_bank(message.from_user.id)
    now = int(time.time())
    if now - user_bank["last_work"] < 300:
        remain = 300 - (now - user_bank["last_work"])
        return await send_bold(message, f"انتظر {remain} ثانية قبل العمل مرة أخرى")
    reward = random.randint(20, 80)
    user_bank["balance"] += reward
    user_bank["last_work"] = now
    save_json(BANK_FILE, bank_data)
    await send_bold(message, f"اشتغلت وربحت {reward} عملة")


@app.on_message(filters.regex(r"^(تحويل|/تحويل)(\s+.+)?$"))
async def transfer_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["bank_enabled"]:
        return await send_bold(message, "البنك معطل")
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await send_bold(message, "رد على الشخص أولاً ثم اكتب:\nتحويل 100")
    args = args_from_text(message.text or "")
    if not args:
        return await send_bold(message, "اكتب المبلغ هكذا:\nتحويل 100")
    try:
        amount = int(args[0])
    except Exception:
        return await send_bold(message, "اكتب مبلغًا صحيحًا")
    if amount <= 0:
        return await send_bold(message, "المبلغ يجب أن يكون أكبر من صفر")
    target = message.reply_to_message.from_user
    sender_bank = get_user_bank(message.from_user.id)
    target_bank = get_user_bank(target.id)
    if sender_bank["balance"] < amount:
        return await send_bold(message, "رصيدك غير كافٍ")
    sender_bank["balance"] -= amount
    target_bank["balance"] += amount
    save_json(BANK_FILE, bank_data)
    await send_bold(message, f"تم تحويل {amount} عملة إلى {target.first_name}")

# =========================================================
# الألعاب
# =========================================================
@app.on_message(filters.regex(r"^نرد$"))
async def dice_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["games_enabled"]:
        return await send_bold(message, "الألعاب معطلة")
    add_points(message.chat.id, message.from_user.id, 1)
    await send_bold(message, f"🎲 النتيجة: {random.randint(1, 6)}")


@app.on_message(filters.regex(r"^خمن$"))
async def guess_start_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["games_enabled"]:
        return await send_bold(message, "الألعاب معطلة")
    guess_state[cid(message.chat.id)] = random.randint(1, 10)
    await send_bold(message, "خمن رقم من 1 إلى 10\nاكتب:\nتخمين_الرقم 5")


@app.on_message(filters.regex(r"^(تخمين_الرقم|/تخمين_الرقم)(\s+.+)?$"))
async def guess_number_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["games_enabled"]:
        return await send_bold(message, "الألعاب معطلة")
    key = cid(message.chat.id)
    if key not in guess_state:
        return await send_bold(message, "اكتب أولاً: خمن")
    args = args_from_text(message.text or "")
    if not args:
        return await send_bold(message, "اكتب:\nتخمين_الرقم 5")
    try:
        num = int(args[0])
    except Exception:
        return await send_bold(message, "اكتب رقمًا صحيحًا")
    if num == guess_state[key]:
        del guess_state[key]
        add_points(message.chat.id, message.from_user.id, 2)
        return await send_bold(message, "إجابة صحيحة 🎉")
    await send_bold(message, "خطأ، حاول مرة أخرى")


@app.on_message(filters.regex(r"^سؤال$"))
async def quiz_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["games_enabled"]:
        return await send_bold(message, "الألعاب معطلة")
    q = random.choice(QUIZ_QUESTIONS)
    quiz_state[cid(message.chat.id)] = q
    await send_bold(message, f"السؤال:\n{q['q']}\n\nاكتب:\nجواب {q['a']}")


@app.on_message(filters.regex(r"^لغز$"))
async def riddle_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["games_enabled"]:
        return await send_bold(message, "الألعاب معطلة")
    q = random.choice(RIDDLES)
    riddle_state[cid(message.chat.id)] = q
    await send_bold(message, f"اللغز:\n{q['q']}\n\nاكتب:\nجواب {q['a']}")


@app.on_message(filters.regex(r"^(جواب|/جواب)(\s+.+)?$"))
async def answer_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["games_enabled"]:
        return await send_bold(message, "الألعاب معطلة")
    key = cid(message.chat.id)
    args = args_from_text(message.text or "")
    if not args:
        return await send_bold(message, "اكتب:\nجواب الحل")
    ans = " ".join(args).strip().lower()
    if key in quiz_state:
        correct = str(quiz_state[key]["a"]).strip().lower()
        if ans == correct:
            del quiz_state[key]
            add_points(message.chat.id, message.from_user.id, 3)
            return await send_bold(message, "إجابة صحيحة ✅")
        return await send_bold(message, "إجابة خاطئة ❌")
    if key in riddle_state:
        correct = str(riddle_state[key]["a"]).strip().lower()
        if ans == correct:
            del riddle_state[key]
            add_points(message.chat.id, message.from_user.id, 3)
            return await send_bold(message, "إجابة صحيحة ✅")
        return await send_bold(message, "إجابة خاطئة ❌")
    await send_bold(message, "لا يوجد سؤال أو لغز نشط")

# =========================================================
# XO
# =========================================================
def xo_keyboard(cells: List[str]):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(cells[0], callback_data="xo:0"), InlineKeyboardButton(cells[1], callback_data="xo:1"), InlineKeyboardButton(cells[2], callback_data="xo:2")],
        [InlineKeyboardButton(cells[3], callback_data="xo:3"), InlineKeyboardButton(cells[4], callback_data="xo:4"), InlineKeyboardButton(cells[5], callback_data="xo:5")],
        [InlineKeyboardButton(cells[6], callback_data="xo:6"), InlineKeyboardButton(cells[7], callback_data="xo:7"), InlineKeyboardButton(cells[8], callback_data="xo:8")],
    ])


def check_winner(cells: List[str]) -> Optional[str]:
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,b,c in wins:
        if cells[a] == cells[b] == cells[c] and cells[a] in ("X", "O"):
            return cells[a]
    if all(x in ("X", "O") for x in cells):
        return "draw"
    return None


@app.on_message(filters.regex(r"^xo$"))
async def xo_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["games_enabled"]:
        return await send_bold(message, "الألعاب معطلة")
    xo_state[cid(message.chat.id)] = {"cells": ["➖"] * 9, "turn": "X"}
    await message.reply_text("<b>لعبة XO</b>", reply_markup=xo_keyboard(["➖"] * 9), parse_mode="html")


@app.on_callback_query(filters.regex(r"^xo:(\d)$"))
async def xo_play(client, query):
    chat_id = cid(query.message.chat.id)
    if chat_id not in xo_state:
        return await query.answer("لا توجد لعبة نشطة")
    state = xo_state[chat_id]
    idx = int(query.data.split(":")[1])
    if state["cells"][idx] in ("X", "O"):
        return await query.answer("هذا المكان مستخدم")
    state["cells"][idx] = state["turn"]
    result = check_winner(state["cells"])
    display = [c if c in ("X", "O") else "➖" for c in state["cells"]]
    if result in ("X", "O"):
        await query.message.edit_text(f"<b>الفائز: {result}</b>", reply_markup=xo_keyboard(display), parse_mode="html")
        del xo_state[chat_id]
        return
    if result == "draw":
        await query.message.edit_text("<b>تعادل</b>", reply_markup=xo_keyboard(display), parse_mode="html")
        del xo_state[chat_id]
        return
    state["turn"] = "O" if state["turn"] == "X" else "X"
    await query.message.edit_text(f"<b>الدور: {state['turn']}</b>", reply_markup=xo_keyboard(display), parse_mode="html")
    await query.answer("تم")

# =========================================================
# ألعاب احترافية
# =========================================================
@app.on_message(filters.regex(r"^(العاب احترافيه|الألعاب الاحترافيه)$"))
async def pro_games_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["games_enabled"]:
        return await send_bold(message, "الألعاب معطلة")
    await send_bold(message, "قائمة العاب احترافيه من GAMEE\n\nاضغط على أي زر وسيفتح لك بوت الألعاب.", reply_markup=pro_games_keyboard())

# =========================================================
# التحشيش
# =========================================================
@app.on_message(filters.regex(r"^نسبه الحب$"))
async def love_percent_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["fun_enabled"]:
        return await send_bold(message, "التحشيش معطل")
    await send_bold(message, f"نسبة الحب: {random.randint(1, 100)}%\n{random.choice(LOVE_REPLIES)}")


@app.on_message(filters.regex(r"^نسبه الذكاء$"))
async def smart_percent_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["fun_enabled"]:
        return await send_bold(message, "التحشيش معطل")
    await send_bold(message, f"نسبة الذكاء: {random.randint(1, 100)}%")


@app.on_message(filters.regex(r"^شنو رايك بهذا$"))
async def opinion_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["fun_enabled"]:
        return await send_bold(message, "التحشيش معطل")
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await send_bold(message, "رد على شخص أولاً")
    await send_bold(message, random.choice(OPINION_REPLIES))


@app.on_message(filters.regex(r"^بوسه$"))
async def kiss_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["fun_enabled"]:
        return await send_bold(message, "التحشيش معطل")
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await send_bold(message, "رد على شخص أولاً")
    await send_bold(message, f"😘 بوسة إلى {message.reply_to_message.from_user.first_name}")

# =========================================================
# الردود المخصصة
# =========================================================
@app.on_message(filters.regex(r"^(اضف رد|/اضف رد)(\s+.+)?$") & filters.group)
async def add_reply_cmd(client, message):
    if not await require_admin(client, message):
        return
    args = args_from_text(message.text or "")
    if len(args) < 2:
        return await send_bold(message, "استخدم:\nاضف رد مرحبا اهلاً")
    trigger = args[0].strip().lower()
    reply_text = " ".join(args[1:]).strip()
    replies = get_chat_replies(message.chat.id)
    replies[trigger] = reply_text
    save_json(REPLIES_FILE, replies_data)
    await send_bold(message, "تم حفظ الرد")


@app.on_message(filters.regex(r"^(مسح رد|/مسح رد)(\s+.+)?$") & filters.group)
async def del_reply_cmd(client, message):
    if not await require_admin(client, message):
        return
    args = args_from_text(message.text or "")
    if not args:
        return await send_bold(message, "استخدم:\nمسح رد مرحبا")
    trigger = args[0].strip().lower()
    replies = get_chat_replies(message.chat.id)
    if trigger not in replies:
        return await send_bold(message, "هذا الرد غير موجود")
    del replies[trigger]
    save_json(REPLIES_FILE, replies_data)
    await send_bold(message, "تم مسح الرد")


@app.on_message(filters.regex(r"^(قائمة الردود|الردود)$") & filters.group)
async def list_replies_cmd(client, message):
    replies = get_chat_replies(message.chat.id)
    if not replies:
        return await send_bold(message, "لا توجد ردود محفوظة")
    text = "الردود المحفوظة:\n\n" + "\n".join(f"- {k}" for k in replies.keys())
    await send_bold(message, text)


@app.on_message(filters.group & filters.text)
async def custom_replies_handler(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["replies_enabled"]:
        return
    text = (message.text or "").strip().lower()
    replies = get_chat_replies(message.chat.id)
    if text in replies:
        await send_bold(message, replies[text])

# =========================================================
# التنظيف
# =========================================================
@app.on_message(filters.regex(r"^مسح$") & filters.group)
async def delete_reply_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["clean_enabled"]:
        return await send_bold(message, "التنظيف معطل")
    if not await require_admin(client, message):
        return
    if not message.reply_to_message:
        return await send_bold(message, "رد على رسالة أولاً")
    try:
        await message.reply_to_message.delete()
        await message.delete()
    except Exception as e:
        await send_bold(message, f"تعذر الحذف:\n{e}")


@app.on_message(filters.regex(r"^(مسح|/مسح)(\s+\d+)$") & filters.group)
async def purge_cmd(client, message):
    settings = get_chat_settings(message.chat.id)
    if not settings["clean_enabled"]:
        return await send_bold(message, "التنظيف معطل")
    if not await require_admin(client, message):
        return
    args = args_from_text(message.text or "")
    if not args:
        return await send_bold(message, "اكتب:\nمسح 10")
    try:
        count = int(args[0])
    except Exception:
        return await send_bold(message, "اكتب رقمًا صحيحًا")
    if count < 1 or count > 100:
        return await send_bold(message, "العدد يجب أن يكون بين 1 و 100")
    deleted = 0
    async for msg in client.get_chat_history(message.chat.id, limit=count + 1):
        try:
            await msg.delete()
            deleted += 1
        except Exception:
            pass
    if deleted == 0:
        await send_bold(message, "لم أستطع حذف الرسائل")

# =========================================================
# النقاط
# =========================================================
@app.on_message(filters.regex(r"^نقاطي$"))
async def my_points_cmd(client, message):
    await send_bold(message, f"نقاطك: {get_points(message.chat.id, message.from_user.id)}")


@app.on_message(filters.regex(r"^توب النقاط$"))
async def top_points_cmd(client, message):
    p = get_chat_points(message.chat.id)
    if not p:
        return await send_bold(message, "لا توجد نقاط بعد")
    top = sorted(p.items(), key=lambda x: x[1], reverse=True)[:10]
    lines = ["توب النقاط:\n"]
    for i, (user_id, pts) in enumerate(top, start=1):
        lines.append(f"{i}- {user_id} : {pts}")
    await send_bold(message, "\n".join(lines))


@app.on_message(filters.regex(r"^(بيع نقاطي|/بيع نقاطي)(\s+.+)?$"))
async def sell_points_cmd(client, message):
    args = args_from_text(message.text or "")
    if not args:
        return await send_bold(message, "اكتب:\nبيع نقاطي 10")
    try:
        amount = int(args[0])
    except Exception:
        return await send_bold(message, "اكتب عددًا صحيحًا")
    if amount <= 0:
        return await send_bold(message, "العدد يجب أن يكون أكبر من صفر")
    current = get_points(message.chat.id, message.from_user.id)
    if current < amount:
        return await send_bold(message, "نقاطك غير كافية")
    p = get_chat_points(message.chat.id)
    p[uid(message.from_user.id)] = current - amount
    save_json(POINTS_FILE, points_data)
    user_bank = get_user_bank(message.from_user.id)
    reward = amount * 50
    user_bank["balance"] += reward
    save_json(BANK_FILE, bank_data)
    await send_bold(message, f"تم بيع {amount} نقطة مقابل {reward} عملة")

# =========================================================
# التشغيل
# =========================================================
print("RUNNING...")
import os
from threading import Thread
from flask import Flask

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    Thread(target=run_web).start()
    print("RUNNING...")
    app.run()
