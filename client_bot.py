import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8863152053:AAFsYUTkUP8W20mNquvX8HeP-sro567zrvI"
GROQ_API_KEY = "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"
LYUDA = "LyudmilaVadimovna1"

groq_client = Groq(api_key=GROQ_API_KEY)
lyuda_chat_ids = set()
sessions = {}
processing = set()

# ─── УСЛУГИ ──────────────────────────────────────────────────────────────────
SERVICES = [
    ("🌐 Сайт-визитка",           "site_card"),
    ("🛍 Каталог / Магазин",      "site_shop"),
    ("🏨 База отдыха / Отель",    "site_hotel"),
    ("🍕 Кафе / Ресторан",        "site_cafe"),
    ("📱 Telegram Mini App",      "site_miniapp"),
    ("🤖 Бот с ИИ",               "site_bot"),
    ("🎨 Лендинг",                "site_landing"),
    ("❓ Помогите выбрать",       "site_help"),
]
SERVICE_NAMES = {s[1]: s[0] for s in SERVICES}

# ─── РАЗДЕЛЫ ПО ТИПУ БИЗНЕСА ─────────────────────────────────────────────────
SECTIONS_BY_SERVICE = {
    "site_card":    ["О нас", "Услуги и цены", "Портфолио / Работы", "Отзывы", "Команда", "Контакты", "Онлайн-запись", "FAQ"],
    "site_shop":    ["Главная", "Каталог товаров", "Акции", "О компании", "Доставка и оплата", "Отзывы", "Контакты", "Корзина"],
    "site_hotel":   ["Главная", "Номера и цены", "Территория", "Питание", "Галерея", "Отзывы", "Бронирование", "Контакты", "Как добраться"],
    "site_cafe":    ["Главная", "Меню", "Акции", "О нас", "Галерея", "Доставка", "Бронирование стола", "Контакты"],
    "site_miniapp": ["Главный экран", "Каталог", "Корзина", "Оплата", "История заказов", "Личный кабинет", "Поддержка"],
    "site_bot":     ["Приветствие", "FAQ", "Приём заявок", "Расчёт стоимости", "Портфолио", "Контакты менеджера"],
    "site_landing": ["Оффер", "Преимущества", "Как это работает", "Отзывы", "Цены", "FAQ", "Форма заявки"],
    "site_help":    ["О нас", "Услуги", "Портфолио", "Отзывы", "Контакты"],
}

# ─── ВОПРОСЫ С ДА/НЕТ ────────────────────────────────────────────────────────
YES_NO_QUESTIONS = {
    "Форма связи", "Карта", "Онлайн чат", "SEO", "Аналитика",
    "Техподдержка", "Домен", "Хостинг", "Панель управления",
    "Онлайн-запись", "Онлайн-оплата", "Доставка", "Бронирование",
    "Видео", "Логотип", "Фото", "Тексты", "Многоязычность"
}

# ─── ВОПРОСЫ ─────────────────────────────────────────────────────────────────
COMMON_QUESTIONS = [
    ("Имя",               "text",   "Как Вас зовут?"),
    ("Бизнес",            "text",   "Как называется Ваш бизнес?"),
    ("Город",             "text",   "В каком городе находитесь?"),
    ("О бизнесе",         "text",   "Расскажите о своём бизнесе — чем занимаетесь, чем отличаетесь от конкурентов?"),
    ("Клиенты",           "text",   "Кто Ваши клиенты — кому продаёте или оказываете услуги?"),
    ("Цель сайта",        "text",   "Какая главная цель? Что должен сделать посетитель — позвонить, записаться, купить?"),
    ("Телефон",           "text",   "Контактный телефон для сайта:"),
    ("Соцсети",           "text",   "Соцсети, мессенджеры, email для сайта (все ссылки):"),
    ("Домен",             "yn",     "Есть ли у Вас домен (например mysite.ru)?"),
    ("Хостинг",           "yn",     "Есть ли хостинг (сервер)? Или всё нужно с нуля?"),
    ("Логотип",           "yn_file","Есть ли готовый логотип?"),
    ("Фото",              "yn_file","Есть ли готовые фотографии (интерьер, товары, команда)?"),
    ("Тексты",            "yn_file","Есть ли готовые тексты об услугах или компании?"),
    ("Видео",             "yn",     "Есть ли видео для размещения на сайте?"),
    ("Стиль",             "text",   "Какой стиль предпочитаете — строгий, яркий, минимализм, природный?"),
    ("Примеры",           "text",   "Сайты которые нравятся по дизайну (ссылки если есть):"),
    ("Конкуренты",        "text",   "Сайты конкурентов — что нравится или не нравится?"),
    ("Разделы",           "sections","Какие разделы нужны на сайте? Выберите:"),
    ("Форма связи",       "yn",     "Нужна ли форма обратной связи / заявки?"),
    ("Карта",             "yn",     "Нужна ли карта с адресом?"),
    ("Онлайн чат",        "yn",     "Нужен ли онлайн-чат на сайте?"),
    ("SEO",               "yn",     "Нужно ли SEO-продвижение (поиск в Google/Яндекс)?"),
    ("Аналитика",         "yn",     "Нужна ли статистика посещений?"),
    ("Многоязычность",    "yn",     "Нужен ли сайт на нескольких языках?"),
    ("Панель управления", "yn",     "Нужна ли панель для самостоятельного обновления контента?"),
    ("Техподдержка",      "yn",     "Нужна ли техподдержка после сдачи?"),
    ("Срок",              "text",   "Когда нужно готово — есть дедлайн?"),
    ("Бюджет",            "text",   "Примерный бюджет:"),
    ("Пожелания",         "text",   "Что обязательно должно быть — самое важное для Вас:"),
    ("Не нужно",          "text",   "Что точно НЕ нужно на сайте:"),
    ("Дополнительно",     "text",   "Любые идеи, вопросы, пожелания — напишите всё:"),
]

EXTRA_QUESTIONS = {
    "site_card": [
        ("Услуги и цены",   "text", "Перечислите Ваши услуги и цены:"),
        ("Онлайн-запись",   "yn",   "Нужна ли онлайн-запись на сайте?"),
        ("Портфолио",       "yn_file", "Есть ли портфолио или примеры работ?"),
    ],
    "site_shop": [
        ("Кол-во товаров",  "text", "Сколько примерно товаров в каталоге?"),
        ("Онлайн-оплата",   "yn",   "Нужна ли онлайн-оплата?"),
        ("Доставка",        "yn",   "Есть ли доставка?"),
        ("Фильтры",         "yn",   "Нужны ли фильтры и поиск по каталогу?"),
    ],
    "site_hotel": [
        ("Номера и цены",   "text", "Опишите типы номеров/домиков и цены:"),
        ("Бронирование",    "yn",   "Нужно ли онлайн-бронирование?"),
        ("Питание",         "text", "Есть ли питание — завтраки, столовая, ресторан?"),
        ("Территория",      "text", "Что есть на территории — бассейн, баня, мангал?"),
        ("Сезон",           "text", "Работаете круглый год или сезонно?"),
    ],
    "site_cafe": [
        ("Меню",            "yn_file","Есть ли готовое меню?"),
        ("Доставка",        "yn",   "Есть ли доставка еды?"),
        ("Бронирование",    "yn",   "Нужно ли бронирование столика?"),
        ("Вместимость",     "text", "Сколько мест? Есть ли банкетный зал?"),
    ],
    "site_miniapp": [
        ("Функционал",      "text", "Что должно делать приложение — запись, заказы, каталог, оплата?"),
        ("Онлайн-оплата",   "yn",   "Нужна ли оплата внутри приложения?"),
        ("Уведомления",     "yn",   "Нужны ли push-уведомления?"),
    ],
    "site_bot": [
        ("Назначение",      "text", "Для чего бот — ответы на вопросы, заявки, консультации?"),
        ("Частые вопросы",  "text", "Какие вопросы чаще всего задают клиенты?"),
        ("Уведомления",     "yn",   "Нужны ли уведомления о новых заявках?"),
    ],
    "site_landing": [
        ("Оффер",           "text", "Что продаёт лендинг — услугу, товар, акцию?"),
        ("Целевое действие","text", "Что должен сделать посетитель — заявка, покупка, запись?"),
        ("Акция",           "text", "Есть ли спецпредложение или дедлайн акции?"),
        ("Отзывы",          "yn_file","Есть ли отзывы клиентов?"),
    ],
    "site_help": [
        ("Задача",          "text", "Опишите что хотите получить — какую задачу решить?"),
    ],
}

def get_session(user_id):
    if user_id not in sessions:
        sessions[user_id] = {
            "stage": "start", "service": None,
            "data": {}, "files": [],
            "q_index": 0, "extra_index": 0,
            "phase": "common",
            "selected_sections": [],
            "user_info": {},
        }
    s = sessions[user_id]
    # Если сессия есть но stage сбросился — восстанавливаем
    if s.get("stage") == "start" and s.get("service") and s.get("q_index", 0) > 0:
        s["stage"] = f"q_{s['q_index']}"
    return s

def reset_session(user_id):
    sessions[user_id] = {
        "stage": "start", "service": None,
        "data": {}, "files": [],
        "q_index": 0, "extra_index": 0,
        "phase": "common",
        "selected_sections": [],
        "user_info": {},
    }

# ─── КЛАВИАТУРЫ ──────────────────────────────────────────────────────────────
def kb_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Оставить заявку на разработку", callback_data="start_order")],
        [InlineKeyboardButton("💬 Связаться с менеджером", url=f"https://t.me/{LYUDA}")],
    ])

def kb_services():
    rows = [[InlineKeyboardButton(n, callback_data=f"svc_{d}")] for n,d in SERVICES]
    return InlineKeyboardMarkup(rows)

def kb_yn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да", callback_data="yn_yes"),
         InlineKeyboardButton("❌ Нет", callback_data="yn_no")],
        [InlineKeyboardButton("⏭ Пропустить", callback_data="skip_q")],
        [InlineKeyboardButton("💬 Связаться с менеджером", url=f"https://t.me/{LYUDA}")],
    ])

def kb_yn_file():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да — пришлю файл/фото", callback_data="yn_yes"),
         InlineKeyboardButton("❌ Нет", callback_data="yn_no")],
        [InlineKeyboardButton("⏭ Пропустить", callback_data="skip_q")],
        [InlineKeyboardButton("💬 Связаться с менеджером", url=f"https://t.me/{LYUDA}")],
    ])

def kb_text():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Пропустить", callback_data="skip_q")],
        [InlineKeyboardButton("💬 Связаться с менеджером", url=f"https://t.me/{LYUDA}")],
    ])

def kb_sections(service, selected):
    sections = SECTIONS_BY_SERVICE.get(service, [])
    rows = []
    for s in sections:
        mark = "✅ " if s in selected else ""
        rows.append([InlineKeyboardButton(f"{mark}{s}", callback_data=f"sec_{s}")])
    rows.append([InlineKeyboardButton("➡️ Готово — продолжить", callback_data="sec_done")])
    return InlineKeyboardMarkup(rows)

def kb_done():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Новая заявка", callback_data="start_order")],
        [InlineKeyboardButton("💬 Связаться с менеджером", url=f"https://t.me/{LYUDA}")],
    ])

def kb_skip():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Пропустить", callback_data="skip_q")],
        [InlineKeyboardButton("💬 Связаться с менеджером", url=f"https://t.me/{LYUDA}")],
    ])

# ─── ВОПРОСЫ ─────────────────────────────────────────────────────────────────
def get_all_questions(service):
    return COMMON_QUESTIONS + EXTRA_QUESTIONS.get(service, [])

def get_current_question(session):
    questions = get_all_questions(session["service"])
    idx = session["q_index"]
    if idx < len(questions):
        return idx, questions[idx]
    return idx, None

async def send_question(bot, chat_id, session):
    idx, q = get_current_question(session)
    if q is None:
        await finish_order(bot, chat_id, session)
        return

    label, qtype, text = q
    total = len(get_all_questions(session["service"]))
    header = f"❓ *Вопрос {idx+1} из {total}*\n\n{text}"
    session["stage"] = f"q_{idx}"

    if qtype == "sections":
        await bot.send_message(
            chat_id=chat_id,
            text=header + "\n\n_Нажмите на разделы которые нужны, потом «Готово»_",
            parse_mode="Markdown",
            reply_markup=kb_sections(session["service"], session["selected_sections"])
        )
    elif qtype == "yn":
        await bot.send_message(chat_id=chat_id, text=header,
            parse_mode="Markdown", reply_markup=kb_yn())
    elif qtype == "yn_file":
        await bot.send_message(chat_id=chat_id, text=header,
            parse_mode="Markdown", reply_markup=kb_yn_file())
    else:
        await bot.send_message(chat_id=chat_id, text=header,
            parse_mode="Markdown", reply_markup=kb_text())

async def save_answer(session, label, answer):
    """Сохраняет ответ и переходит к следующему вопросу"""
    session["data"][label] = answer
    session["q_index"] += 1

async def clarify_sections(business, service, selected):
    """Расшифровывает выбранные разделы под конкретный бизнес"""
    if not selected:
        return "не выбраны"
    prompt = (
        f"Бизнес: {business}, тип сайта: {SERVICE_NAMES.get(service,'')}\n"
        f"Клиент выбрал разделы: {', '.join(selected)}\n"
        f"Коротко опиши что должно быть в каждом разделе под этот бизнес. "
        f"Формат: Раздел — краткое описание содержимого. Без лишних слов."
    )
    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            max_tokens=300, temperature=0.3
        )
        return resp.choices[0].message.content.strip()
    except:
        return ", ".join(selected)

async def make_tz(session):
    data = session["data"]
    service = session["service"]
    business = data.get("Бизнес", "не указан")
    sections_raw = data.get("Разделы", "")

    # Расшифровываем разделы
    if session["selected_sections"]:
        sections_detail = await clarify_sections(
            business, service, session["selected_sections"]
        )
        data["Разделы"] = sections_detail

    data_text = "\n".join([f"{k}: {v}" for k,v in data.items()])
    files_note = f"\nПрикреплённых файлов: {len(session['files'])}" if session["files"] else ""

    prompt = (
        f"Составь подробное техническое задание для разработчика.\n\n"
        f"Услуга: {SERVICE_NAMES.get(service, service)}\n"
        f"Данные:\n{data_text}{files_note}\n\n"
        f"Оформи чётко по разделам без предисловий:\n"
        f"КЛИЕНТ: ...\nБИЗНЕС: ...\nУСЛУГА: ...\nЦЕЛЬ: ...\n"
        f"РАЗДЕЛЫ И СОДЕРЖИМОЕ: ...\nФУНКЦИОНАЛ: ...\nДИЗАЙН: ...\n"
        f"КОНТЕНТ: ...\nТЕХТРЕБОВАНИЯ: ...\nКОНТАКТЫ: ...\n"
        f"СРОК: ...\nБЮДЖЕТ: ...\nПОЖЕЛАНИЯ: ...\nПРИМЕЧАНИЯ: ..."
    )
    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role":"system","content":"Ты составляешь техзадание для разработчика. Чётко и конкретно."},
                {"role":"user","content":prompt}
            ],
            max_tokens=1200, temperature=0.3
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return data_text

async def finish_order(bot, chat_id, session):
    await bot.send_message(chat_id=chat_id, text="⏳ Оформляю заявку...")
    tz = await make_tz(session)
    user = session["user_info"]
    username = user.get("username","")
    name = user.get("name","клиент")
    user_link = f"@{username}" if username else name

    # Отправляем Люде
    for lyuda_id in lyuda_chat_ids:
        try:
            msg = (
                f"🆕 *НОВАЯ ЗАЯВКА*\n\n"
                f"От: {user_link}\n"
                f"Услуга: {SERVICE_NAMES.get(session['service'],'')}\n\n"
                f"📄 *ТЗ:*\n\n{tz}"
            )
            await bot.send_message(chat_id=lyuda_id, text=msg, parse_mode="Markdown")

            # Пересылаем файлы
            for file_id, file_type in session["files"]:
                try:
                    if file_type == "photo":
                        await bot.send_photo(chat_id=lyuda_id, photo=file_id,
                            caption=f"📎 Файл от {user_link}")
                    elif file_type == "document":
                        await bot.send_document(chat_id=lyuda_id, document=file_id,
                            caption=f"📎 Файл от {user_link}")
                except:
                    pass
        except Exception as e:
            logger.error(f"Ошибка отправки Люде: {e}")

    await bot.send_message(
        chat_id=chat_id,
        text=(
            "✅ *Заявка принята!*\n\n"
            "Ваши пожелания переданы менеджеру.\n"
            "Мы свяжемся с Вами в ближайшее время.\n\n"
            "Если хотите уточнить детали — напишите менеджеру напрямую 👇"
        ),
        parse_mode="Markdown",
        reply_markup=kb_done()
    )

# ─── ХЭНДЛЕРЫ ────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    name = update.effective_user.first_name or ""

    if username == LYUDA:
        lyuda_chat_ids.add(user_id)
        await update.message.reply_text(
            "✅ Люда, ты подключена!\n"
            "Все заявки от клиентов будут приходить сюда автоматически. 🎉"
        )
        return

    reset_session(user_id)
    session = get_session(user_id)
    session["user_info"] = {"username": username, "name": name, "id": user_id}

    await update.message.reply_text(
        f"👋 Добро пожаловать{', ' + name if name else ''}!\n\n"
        "Мы разрабатываем сайты, Telegram Mini Apps и ботов с ИИ "
        "для малого и среднего бизнеса.\n\n"
        "🔹 Сайты с нуля — не конструктор\n"
        "🔹 Telegram Mini App под ваш бизнес\n"
        "🔹 Боты с искусственным интеллектом\n"
        "🔹 Лендинги и интернет-магазины\n\n"
        "Оставьте заявку — ответим в течение часа! 👇",
        reply_markup=kb_main()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    key = f"btn_{user_id}_{query.id}"
    if key in processing: return
    processing.add(key)

    try:
        session = get_session(user_id)
        chat_id = query.message.chat_id

        if query.data == "start_order":
            reset_session(user_id)
            session = get_session(user_id)
            username = query.from_user.username or ""
            name = query.from_user.first_name or ""
            session["user_info"] = {"username": username, "name": name, "id": user_id}
            await query.message.reply_text(
                "Выберите что нужно разработать:\n\n"
                "_Не знаете? Выберите последний пункт — поможем разобраться_ 👇",
                parse_mode="Markdown",
                reply_markup=kb_services()
            )

        elif query.data.startswith("svc_"):
            service = query.data.replace("svc_", "")
            session["service"] = service
            session["q_index"] = 0
            total = len(get_all_questions(service))
            await query.message.reply_text(
                f"Отлично! Вы выбрали: *{SERVICE_NAMES[service]}*\n\n"
                f"Задам {total} вопросов — займёт около 5 минут.\n"
                f"Любой вопрос можно пропустить.\n\n"
                f"Если нужна помощь — кнопка «Связаться с менеджером» всегда под рукой.\n\n"
                f"Поехали! 👇",
                parse_mode="Markdown"
            )
            await send_question(context.bot, chat_id, session)

        elif query.data in ("yn_yes", "yn_no"):
            idx, q = get_current_question(session)
            if q:
                label, qtype, _ = q
                answer = "Да" if query.data == "yn_yes" else "Нет"
                # Если да и ожидаем файл — просим прислать
                if query.data == "yn_yes" and qtype == "yn_file":
                    session["data"][label] = "Да — ожидаем файл"
                    session["stage"] = f"wait_file_{idx}"
                    await query.message.reply_text(
                        "📎 Пришлите файл, фото или документ:",
                        reply_markup=kb_skip()
                    )
                    return
                await save_answer(session, label, answer)
                await send_question(context.bot, chat_id, session)

        elif query.data == "skip_q":
            idx, q = get_current_question(session)
            if q:
                label, _, _ = q
                await save_answer(session, label, "не указано")
                await send_question(context.bot, chat_id, session)

        elif query.data.startswith("sec_") and query.data != "sec_done":
            section = query.data.replace("sec_", "")
            if section in session["selected_sections"]:
                session["selected_sections"].remove(section)
            else:
                session["selected_sections"].append(section)
            # Обновляем клавиатуру
            await query.message.edit_reply_markup(
                reply_markup=kb_sections(session["service"], session["selected_sections"])
            )

        elif query.data == "sec_done":
            idx, q = get_current_question(session)
            if q:
                label, _, _ = q
                selected = session["selected_sections"]
                answer = ", ".join(selected) if selected else "не выбрано"
                await save_answer(session, label, answer)
                await send_question(context.bot, chat_id, session)

    finally:
        processing.discard(key)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg_id = update.message.message_id
    key = f"msg_{user_id}_{msg_id}"
    if key in processing: return
    processing.add(key)

    try:
        session = get_session(user_id)
        chat_id = update.message.chat_id
        stage = session.get("stage","start")

        if stage == "start":
            await update.message.reply_text(
                "Выберите действие 👇",
                reply_markup=kb_main()
            )
            return

        # Ожидание файла
        if stage.startswith("wait_file_"):
            if update.message.photo or update.message.document:
                if update.message.photo:
                    file_id = update.message.photo[-1].file_id
                    session["files"].append((file_id, "photo"))
                elif update.message.document:
                    file_id = update.message.document.file_id
                    session["files"].append((file_id, "document"))
                await update.message.reply_text("✅ Файл получен!")
            session["q_index"] += 1
            await send_question(context.bot, chat_id, session)
            return

        # Обычный текстовый ответ
        if stage.startswith("q_"):
            idx, q = get_current_question(session)
            if q:
                label, _, _ = q
                await save_answer(session, label, update.message.text)
                await send_question(context.bot, chat_id, session)

    finally:
        processing.discard(key)

async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = get_session(user_id)
    stage = session.get("stage","")

    if stage.startswith("wait_file_") or stage.startswith("q_"):
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            session["files"].append((file_id, "photo"))
        elif update.message.document:
            file_id = update.message.document.file_id
            session["files"].append((file_id, "document"))
        await update.message.reply_text("✅ Файл получен! Можете прислать ещё или продолжить.")
        if stage.startswith("wait_file_"):
            session["q_index"] += 1
            await send_question(context.bot, update.message.chat_id, session)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, file_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    logger.info("Client Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
