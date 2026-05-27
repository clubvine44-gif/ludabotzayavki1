import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8863152053:AAFsYUTkUP8W20mNquvX8HeP-sro567zrvI"
GROQ_API_KEY = "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"
LYUDA_USERNAME = "@LyudmilaVadimovna1"
LYUDA_CHAT_ID = None  # Заполнится когда Люда напишет /start боту

groq_client = Groq(api_key=GROQ_API_KEY)

# ─── ВОПРОСЫ ПО ЭТАПАМ ───────────────────────────────────────────────────────

SERVICES = [
    ("🌐 Сайт-визитка",        "site_card"),
    ("🛍 Каталог / Магазин",   "site_shop"),
    ("🏨 База отдыха / Отель", "site_hotel"),
    ("🍕 Кафе / Ресторан",     "site_cafe"),
    ("📱 Telegram Mini App",   "site_miniapp"),
    ("🤖 Бот с ИИ",            "site_bot"),
    ("🎨 Лендинг",             "site_landing"),
    ("❓ Не знаю — помогите выбрать", "site_help"),
]

# Общие вопросы — для всех
COMMON_QUESTIONS = [
    ("Имя",              "Как Вас зовут?"),
    ("Бизнес",           "Как называется Ваш бизнес?"),
    ("Город",            "В каком городе находитесь?"),
    ("О бизнесе",        "Расскажите о своём бизнесе своими словами — чем занимаетесь, чем отличаетесь от конкурентов?"),
    ("Клиенты",          "Кто Ваши клиенты — кому продаёте или оказываете услуги?"),
    ("Цель сайта",       "Какая главная цель сайта? Что должен сделать посетитель — позвонить, записаться, купить, узнать о вас?"),
    ("Телефон",          "Укажите Ваш контактный телефон для сайта:"),
    ("Соцсети",          "Есть ли соцсети, мессенджеры, email которые нужно указать на сайте? Напишите все ссылки и контакты:"),
    ("Домен",            "Есть ли у Вас домен (адрес сайта, например vashabaza.ru)? Или нужно помочь выбрать?"),
    ("Хостинг",          "Есть ли хостинг (сервер для сайта)? Или всё нужно с нуля?"),
    ("Логотип",          "Есть ли готовый логотип? Если да — пришлите файл или опишите:"),
    ("Фото",             "Есть ли готовые фотографии — интерьер, товары, команда, процесс работы?"),
    ("Тексты",           "Есть ли готовые тексты об услугах или компании? Хотя бы примерные — можно в любом виде:"),
    ("Видео",            "Есть ли видео которое хотите разместить на сайте?"),
    ("Стиль",            "Какой стиль и цвета предпочитаете — строгий, яркий, минимализм, природный? Есть предпочтения?"),
    ("Примеры",          "Есть ли сайты которые Вам нравятся по дизайну? Пришлите ссылки если есть:"),
    ("Конкуренты",       "Есть ли сайты конкурентов — нравятся или наоборот? Что в них нравится или не нравится?"),
    ("Разделы",          "Какие разделы должны быть на сайте? Например: о нас, услуги, цены, портфолио, отзывы, контакты:"),
    ("Форма связи",      "Нужна ли форма обратной связи или заявки на сайте?"),
    ("Карта",            "Нужна ли карта с адресом на сайте?"),
    ("Онлайн чат",       "Нужен ли онлайн-чат на сайте (например чтобы посетители могли написать сразу)?"),
    ("SEO",              "Нужно ли продвижение в поиске (SEO) — чтобы Вас находили через Google и Яндекс?"),
    ("Аналитика",        "Нужна ли статистика посещений — кто заходит, откуда, что смотрит?"),
    ("Языки",            "Нужен ли сайт на нескольких языках? Если да — на каких?"),
    ("Панель управления","Планируете сами обновлять контент сайта? Нужна ли панель управления?"),
    ("Техподдержка",     "Нужна ли техподдержка после сдачи сайта?"),
    ("Срок",             "Есть ли дедлайн — когда нужно готово?"),
    ("Бюджет",           "Какой бюджет рассматриваете? Примерно:"),
    ("Пожелания",        "Что обязательно должно быть на сайте — что считаете самым важным?"),
    ("Не нужно",         "Что точно НЕ нужно на сайте — чего хотите избежать?"),
    ("Дополнительно",    "Напишите всё что хотите добавить — идеи, вопросы, любые пожелания. Любая информация поможет сделать лучше:"),
]

# Дополнительные вопросы по типу услуги
EXTRA_QUESTIONS = {
    "site_card": [
        ("Услуги",       "Перечислите Ваши услуги и цены (если есть):"),
        ("Запись",       "Как сейчас клиенты записываются к Вам? Нужна ли онлайн-запись на сайте?"),
        ("Портфолио",    "Есть ли портфолио или примеры работ которые нужно показать?"),
    ],
    "site_shop": [
        ("Товары",       "Сколько примерно товаров в каталоге?"),
        ("Оплата",       "Нужна ли онлайн-оплата на сайте?"),
        ("Доставка",     "Есть ли доставка? Как она работает?"),
        ("Остатки",      "Нужен ли учёт остатков товаров на складе?"),
        ("Фильтры",      "Нужны ли фильтры и поиск по каталогу?"),
    ],
    "site_hotel": [
        ("Номера",       "Опишите типы номеров/домиков и цены:"),
        ("Бронирование", "Нужно ли онлайн-бронирование на сайте?"),
        ("Питание",      "Есть ли питание — завтраки, столовая, ресторан?"),
        ("Территория",   "Что есть на территории — бассейн, баня, мангал, детская площадка?"),
        ("Сезон",        "Работаете круглый год или сезонно?"),
    ],
    "site_cafe": [
        ("Меню",         "Есть ли готовое меню? Нужно ли разместить его на сайте?"),
        ("Доставка",     "Есть ли доставка еды? Нужен ли раздел с доставкой?"),
        ("Бронирование", "Нужно ли онлайн-бронирование столика?"),
        ("Режим",        "Режим работы — часы, дни недели:"),
        ("Вместимость",  "Сколько мест в заведении? Есть ли банкетный зал?"),
    ],
    "site_miniapp": [
        ("Функционал",   "Что должно делать Mini App — запись, заказы, каталог, оплата, что-то другое?"),
        ("Оплата",       "Нужна ли оплата внутри приложения?"),
        ("Уведомления",  "Нужны ли уведомления пользователям?"),
        ("Интеграция",   "Нужна ли интеграция с CRM, складом или другими системами?"),
    ],
    "site_bot": [
        ("Назначение",   "Для чего бот — отвечать на вопросы, принимать заявки, консультировать, что-то другое?"),
        ("Вопросы",      "Какие вопросы чаще всего задают Ваши клиенты? Перечислите основные:"),
        ("Интеграция",   "Нужна ли интеграция с CRM, таблицами или другими сервисами?"),
        ("Уведомления",  "Нужны ли уведомления — например когда поступила новая заявка?"),
    ],
    "site_landing": [
        ("Оффер",        "Что продаёт лендинг — услугу, товар, мероприятие, акцию?"),
        ("Целевое действие", "Что должен сделать посетитель — оставить заявку, купить, записаться?"),
        ("Акция",        "Есть ли специальное предложение или дедлайн акции?"),
        ("Отзывы",       "Есть ли отзывы клиентов которые можно разместить?"),
    ],
    "site_help": [
        ("Задача",       "Опишите своими словами что хотите получить — какую задачу должен решить сайт или бот?"),
        ("Примеры",      "Есть ли примеры сайтов/ботов которые Вам нравятся?"),
    ],
}

SERVICE_NAMES = {s[1]: s[0] for s in SERVICES}

sessions = {}
processing = set()
lyuda_chat_ids = set()

def get_session(user_id):
    if user_id not in sessions:
        sessions[user_id] = {
            "stage": "start",
            "service": None,
            "data": {},
            "question_index": 0,
            "extra_index": 0,
            "phase": "common",  # common | extra | done
        }
    return sessions[user_id]

def reset_session(user_id):
    sessions[user_id] = {
        "stage": "start",
        "service": None,
        "data": {},
        "question_index": 0,
        "extra_index": 0,
        "phase": "common",
    }

def kb_start():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Оставить заявку", callback_data="start_order")],
        [InlineKeyboardButton("💬 Связаться с менеджером", url=f"https://t.me/{LYUDA_USERNAME.replace('@','')}")],
    ])

def kb_services():
    rows = []
    for name, data in SERVICES:
        rows.append([InlineKeyboardButton(name, callback_data=f"svc_{data}")])
    return InlineKeyboardMarkup(rows)

def kb_skip_help():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Пропустить", callback_data="skip_question")],
        [InlineKeyboardButton("💬 Помощь — связаться с менеджером", url=f"https://t.me/{LYUDA_USERNAME.replace('@','')}")]
    ])

def kb_done():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Оставить новую заявку", callback_data="start_order")],
        [InlineKeyboardButton("💬 Связаться с менеджером", url=f"https://t.me/{LYUDA_USERNAME.replace('@','')}")],
    ])

async def ask_groq_tz(data, service):
    """Генерирует красивое ТЗ из собранных данных"""
    data_text = "\n".join([f"{k}: {v}" for k, v in data.items()])
    prompt = (
        f"Составь подробное техническое задание на разработку для разработчика.\n\n"
        f"Услуга: {SERVICE_NAMES.get(service, service)}\n"
        f"Данные от клиента:\n{data_text}\n\n"
        f"Оформи чётко по разделам, без лишних слов:\n"
        f"КЛИЕНТ: ...\n"
        f"БИЗНЕС: ...\n"
        f"УСЛУГА: ...\n"
        f"ЦЕЛЬ: ...\n"
        f"ФУНКЦИОНАЛ: ...\n"
        f"ДИЗАЙН: ...\n"
        f"КОНТЕНТ: ...\n"
        f"ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ: ...\n"
        f"КОНТАКТЫ: ...\n"
        f"СРОК: ...\n"
        f"БЮДЖЕТ: ...\n"
        f"ПОЖЕЛАНИЯ: ...\n"
        f"ПРИМЕЧАНИЯ: ..."
    )
    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Ты составляешь техническое задание для разработчика сайта. Пиши чётко, конкретно, без предисловий."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        return resp.choices[0].message.content.strip()
    except:
        return data_text

async def send_to_lyuda(bot, data, service, user_info):
    """Отправляет ТЗ всем зарегистрированным chat_id Люды"""
    tz = await ask_groq_tz(data, service)
    username = user_info.get("username", "")
    user_link = f"@{username}" if username else user_info.get("name", "клиент")

    message = (
        f"🆕 *НОВАЯ ЗАЯВКА*\n\n"
        f"От: {user_link}\n"
        f"Услуга: {SERVICE_NAMES.get(service, service)}\n\n"
        f"📄 *ТЕХНИЧЕСКОЕ ЗАДАНИЕ:*\n\n{tz}"
    )

    sent = False
    for chat_id in lyuda_chat_ids:
        try:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
            sent = True
        except Exception as e:
            logger.error(f"Не удалось отправить Люде {chat_id}: {e}")

    if not sent:
        logger.warning("Люда не зарегистрирована — ТЗ не отправлено")

    return tz

async def send_next_question(update_or_message, context, session, user_id):
    """Отправляет следующий вопрос"""
    bot = context.bot
    chat_id = user_id

    if session["phase"] == "common":
        idx = session["question_index"]
        if idx < len(COMMON_QUESTIONS):
            label, question = COMMON_QUESTIONS[idx]
            total = len(COMMON_QUESTIONS) + len(EXTRA_QUESTIONS.get(session["service"], []))
            current = idx + 1
            await bot.send_message(
                chat_id=chat_id,
                text=f"❓ *Вопрос {current} из {total}*\n\n{question}",
                parse_mode="Markdown",
                reply_markup=kb_skip_help()
            )
            session["stage"] = f"answer_common_{idx}"
        else:
            session["phase"] = "extra"
            session["extra_index"] = 0
            await send_next_question(update_or_message, context, session, user_id)

    elif session["phase"] == "extra":
        extra = EXTRA_QUESTIONS.get(session["service"], [])
        idx = session["extra_index"]
        common_total = len(COMMON_QUESTIONS)

        if idx < len(extra):
            label, question = extra[idx]
            total = common_total + len(extra)
            current = common_total + idx + 1
            await bot.send_message(
                chat_id=chat_id,
                text=f"❓ *Вопрос {current} из {total}*\n\n{question}",
                parse_mode="Markdown",
                reply_markup=kb_skip_help()
            )
            session["stage"] = f"answer_extra_{idx}"
        else:
            session["phase"] = "done"
            await finish_order(bot, session, user_id, context)

async def finish_order(bot, session, user_id, context):
    """Завершает сбор заявки и отправляет ТЗ"""
    await bot.send_message(
        chat_id=user_id,
        text="⏳ Обрабатываю вашу заявку, секунду..."
    )

    user_info = session.get("user_info", {})
    tz = await send_to_lyuda(bot, session["data"], session["service"], user_info)

    await bot.send_message(
        chat_id=user_id,
        text=(
            "✅ *Заявка принята!*\n\n"
            "Ваши пожелания переданы менеджеру — мы свяжемся с вами в ближайшее время.\n\n"
            "Если хотите уточнить детали — напишите менеджеру напрямую 👇"
        ),
        parse_mode="Markdown",
        reply_markup=kb_done()
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    name = update.effective_user.first_name or ""

    # Если Люда написала /start — регистрируем её chat_id
    if username == LYUDA_USERNAME.replace("@", "") or username == "LyudmilaVadimovna1":
        lyuda_chat_ids.add(user_id)
        await update.message.reply_text(
            "✅ Люда, ты зарегистрирована!\n"
            "Все новые заявки от клиентов будут приходить сюда автоматически."
        )
        return

    reset_session(user_id)
    session = get_session(user_id)
    session["user_info"] = {"username": username, "name": name, "id": user_id}

    await update.message.reply_text(
        f"👋 Добро пожаловать{', ' + name if name else ''}!\n\n"
        "Я помогу оформить заявку на разработку сайта, бота или Telegram Mini App.\n\n"
        "Отвечу на несколько вопросов — и ваши пожелания сразу попадут к менеджеру.\n\n"
        "Если в любой момент нужна помощь — нажмите кнопку и менеджер ответит лично.\n\n"
        "Начнём? 👇",
        reply_markup=kb_start()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    key = f"btn_{user_id}_{query.id}"
    if key in processing:
        return
    processing.add(key)

    try:
        session = get_session(user_id)

        if query.data == "start_order":
            reset_session(user_id)
            session = get_session(user_id)
            username = query.from_user.username or ""
            name = query.from_user.first_name or ""
            session["user_info"] = {"username": username, "name": name, "id": user_id}
            session["stage"] = "choose_service"
            await query.message.reply_text(
                "Выберите что вам нужно разработать:\n\n"
                "_Если не знаете — выберите последний пункт, поможем разобраться_ 👇",
                parse_mode="Markdown",
                reply_markup=kb_services()
            )

        elif query.data.startswith("svc_"):
            service = query.data.replace("svc_", "")
            session["service"] = service
            session["phase"] = "common"
            session["question_index"] = 0
            session["extra_index"] = 0

            svc_name = SERVICE_NAMES.get(service, service)
            total = len(COMMON_QUESTIONS) + len(EXTRA_QUESTIONS.get(service, []))
            await query.message.reply_text(
                f"Отлично! Вы выбрали: *{svc_name}*\n\n"
                f"Я задам {total} вопросов — это займёт около 5 минут.\n"
                f"Любой вопрос можно пропустить.\n\n"
                f"Поехали! 👇",
                parse_mode="Markdown"
            )
            await send_next_question(query, context, session, user_id)

        elif query.data == "skip_question":
            stage = session.get("stage", "")
            if stage.startswith("answer_common_"):
                idx = int(stage.replace("answer_common_", ""))
                label, _ = COMMON_QUESTIONS[idx]
                session["data"][label] = "не указано"
                session["question_index"] = idx + 1
                session["phase"] = "common"
                await send_next_question(query, context, session, user_id)

            elif stage.startswith("answer_extra_"):
                idx = int(stage.replace("answer_extra_", ""))
                extra = EXTRA_QUESTIONS.get(session["service"], [])
                if idx < len(extra):
                    label, _ = extra[idx]
                    session["data"][label] = "не указано"
                session["extra_index"] = idx + 1
                session["phase"] = "extra"
                await send_next_question(query, context, session, user_id)

    finally:
        processing.discard(key)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg_id = update.message.message_id
    key = f"msg_{user_id}_{msg_id}"
    if key in processing:
        return
    processing.add(key)

    try:
        session = get_session(user_id)
        text = update.message.text
        stage = session.get("stage", "start")

        if stage == "start":
            await start(update, context)
            return

        if stage == "choose_service":
            await update.message.reply_text(
                "Пожалуйста выберите вариант из кнопок выше 👆",
                reply_markup=kb_services()
            )
            return

        if stage.startswith("answer_common_"):
            idx = int(stage.replace("answer_common_", ""))
            label, _ = COMMON_QUESTIONS[idx]
            session["data"][label] = text
            session["question_index"] = idx + 1
            session["phase"] = "common"
            await send_next_question(update, context, session, user_id)

        elif stage.startswith("answer_extra_"):
            idx = int(stage.replace("answer_extra_", ""))
            extra = EXTRA_QUESTIONS.get(session["service"], [])
            if idx < len(extra):
                label, _ = extra[idx]
                session["data"][label] = text
            session["extra_index"] = idx + 1
            session["phase"] = "extra"
            await send_next_question(update, context, session, user_id)

        elif session["phase"] == "done":
            await update.message.reply_text(
                "Ваша заявка уже принята! 👆\n"
                "Если хотите оставить новую — нажмите кнопку.",
                reply_markup=kb_done()
            )

    finally:
        processing.discard(key)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    logger.info("Client Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
