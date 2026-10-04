import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

user_data = {}

# আপনার Monetag লিঙ্কসমূহ
TASKS = {
    "task_1": {"title": "Task 1", "link": "https://omg10.com/4/11950217"},
    "task_2": {"title": "Task 2", "link": "https://omg10.com/4/11942844"},
    "task_3": {"title": "Task 3", "link": "https://omg10.com/4/11942845"},
    "task_4": {"title": "Task 4", "link": "https://omg10.com/4/11950214"},
    "task_5": {"title": "Task 5", "link": "https://omg10.com/4/11950215"},
}

POINT_PER_TASK = 1
MIN_WITHDRAW = 10


def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "points": 0,
            "completed_tasks": [],
            "status": "idle",
        }
    return user_data[user_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user(user_id)

    keyboard = [
        [InlineKeyboardButton("📋 Task List", callback_data="task_list")],
        [
            InlineKeyboardButton("💰 Balance", callback_data="balance"),
            InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 স্বাগতম! টাস্ক সম্পন্ন করে পয়েন্ট আর্ন করুন এবং বিকাশে পেমেন্ট নিন।",
        reply_markup=reply_markup,
    )


async def button_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user = get_user(user_id)
    data = query.data

    if data == "task_list":
        keyboard = []
        for task_id, task_info in TASKS.items():
            status_icon = "✅" if task_id in user["completed_tasks"] else "📌"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{status_icon} {task_info['title']}",
                        callback_data=f"open_{task_id}",
                    )
                ]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "নিচের তালিকা থেকে টাস্ক বেছে নিন:", reply_markup=reply_markup
        )

    elif data.startswith("open_task_"):
        task_id = data.replace("open_", "")
        task_info = TASKS[task_id]

        if task_id in user["completed_tasks"]:
            await query.edit_message_text(
                f"❌ আপনি ইতোমধ্যে {task_info['title']} সম্পন্ন করেছেন!"
            )
            return

        keyboard = [
            [InlineKeyboardButton("🔗 Open Link & Wait", url=task_info["link"])],
            [
                InlineKeyboardButton(
                    "✅ Claim 1 Point", callback_data=f"claim_{task_id}"
                )
            ],
            [InlineKeyboardButton("🔙 Back to Tasks", callback_data="task_list")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"**{task_info['title']} নির্দেশিকা:**\n1. লিঙ্কে ক্লিক করে ১৫ সেকেন্ড অপেক্ষা করুন।\n2. পয়েন্ট ক্লেইম করুন।",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    elif data.startswith("claim_task_"):
        task_id = data.replace("claim_", "")

        if task_id not in user["completed_tasks"]:
            user["completed_tasks"].append(task_id)
            user["points"] += POINT_PER_TASK
            await query.edit_message_text(
                f"🎉 {TASKS[task_id]['title']} সফল হয়েছে!\nআপনার বর্তমান ব্যালেন্স: {user['points']} পয়েন্ট।"
            )
        else:
            await query.edit_message_text("❌ এই টাস্কের পয়েন্ট ইতোমধ্যে নেওয়া হয়েছে।")

    elif data == "balance":
        await query.edit_message_text(
            f"💳 আপনার বর্তমান ব্যালেন্স: {user['points']} পয়েন্ট।"
        )

    elif data == "withdraw":
        if user["points"] < MIN_WITHDRAW:
            await query.edit_message_text(
                f"❌ সর্বনিম্ন {MIN_WITHDRAW} পয়েন্ট না হলে উইথড্র করা যাবে না।"
            )
        else:
            user["status"] = "awaiting_number"
            await query.edit_message_text(
                f"পয়েন্ট: {user['points']}।\nআপনার **বিকাশ বা নগদ নম্বর** প্রদান করুন:"
            )


async def handle_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id
    user = get_user(user_id)

    if user.get("status") == "awaiting_number":
        account_number = update.message.text
        points = user["points"]

        user["points"] = 0
        user["status"] = "idle"

        await update.message.reply_text(
            f"✅ উইথড্র রিকোয়েস্ট গ্রহণ করা হয়েছে!\nনম্বর: {account_number}\nপরিমাণ: {points} টাকা।"
        )


def main():
    TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
          
