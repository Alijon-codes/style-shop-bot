import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

import os
TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])
PRODUCTS = {
    "1": ("Футболка", 10),
    "2": ("Джинсы", 25),
    "3": ("Куртка", 50),
    "4": ("Кроссовки", 40),
}

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Каталог", callback_data="catalog")],
        [InlineKeyboardButton("Корзина", callback_data="cart")],
        [InlineKeyboardButton("Связаться", callback_data="contact")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать в Style Shop!", reply_markup=main_menu())

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    cart = context.user_data.setdefault("cart", [])
    print("BUTTON:", repr(data))

    if data == "menu":
        await q.edit_message_text("Style Shop. Выберите:", reply_markup=main_menu())

    elif data == "catalog":
        kb = [[InlineKeyboardButton(f"{name} - {price}$", callback_data=f"add_{i}")]
              for i, (name, price) in PRODUCTS.items()]
        kb.append([InlineKeyboardButton("Назад", callback_data="menu")])
        await q.edit_message_text("Каталог. Нажмите на товар, чтобы добавить:",
                                  reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("add_"):
        cart.append(data[4:])
        pid = data[4:]
        name, price = PRODUCTS[pid]
        with open(f"{pid}.jpg", "rb") as photo:
            await context.bot.send_photo(
                chat_id=q.message.chat_id,
                photo=photo,
                caption=f"{name} - {price}$\nДобавлено в корзину"
            )

    elif data == "cart":
        if not cart:
            text = "Корзина пуста."
            kb = [[InlineKeyboardButton("Назад", callback_data="menu")]]
        else:
            lines = [f"{PRODUCTS[i][0]} - {PRODUCTS[i][1]}$" for i in cart]
            total = sum(PRODUCTS[i][1] for i in cart)
            text = "Ваша корзина:\n" + "\n".join(lines) + f"\n\nИтого: {total}$"
            kb = [
                [InlineKeyboardButton("Оформить заказ", callback_data="order")],
                [InlineKeyboardButton("Очистить", callback_data="clear")],
                [InlineKeyboardButton("Назад", callback_data="menu")],
            ]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

    elif data == "clear":
        context.user_data["cart"] = []
        await q.edit_message_text("Корзина очищена.", reply_markup=main_menu())

    elif data == "order":
        if not cart:
            return
        lines = [f"{PRODUCTS[i][0]} - {PRODUCTS[i][1]}$" for i in cart]
        total = sum(PRODUCTS[i][1] for i in cart)
        user = q.from_user
        username = f"@{user.username}" if user.username else "без username"
        name_link = f'<a href="tg://user?id={user.id}">{html.escape(user.full_name)}</a>'
        msg = f"Новый заказ!\nОт: {name_link} ({username})\n\n" + "\n".join(lines) + f"\n\nИтого: {total}$"
        await context.bot.send_message(chat_id=OWNER_ID, text=msg, parse_mode="HTML")
        context.user_data["cart"] = []
        await q.edit_message_text("Спасибо! Заказ принят, мы скоро свяжемся с вами.",
                                  reply_markup=main_menu())

    elif data == "contact":
        await q.edit_message_text("Напишите нам: @Loki_l6",
                                  reply_markup=InlineKeyboardMarkup(
                                      [[InlineKeyboardButton("Назад", callback_data="menu")]]))

app = (Application.builder().token(TOKEN)
       .connect_timeout(30).read_timeout(30).write_timeout(30).pool_timeout(30)
       .build())
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.run_polling()