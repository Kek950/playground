from telebot import types
def show_attendance_buttons(bot, chat_id, attendance_sessions, message_id=None):
    if chat_id not in attendance_sessions:
        return
    session = attendance_sessions[chat_id]
    students = session["students"]
    status = session["status"]
    

    markup = types.InlineKeyboardMarkup(row_width=2)
    for i, student in enumerate(students):
        icon = "✅" if status[i] == "present" else "❌"
        markup.add(types.InlineKeyboardButton(f"{student} {icon}", callback_data=f"toggle_{i}"))

    markup.add(types.InlineKeyboardButton("✅ Finish Attendance", callback_data="finish_attendance"))

    bot.send_message(chat_id, "📝 Tap names to toggle presence. When done, press ✅ Finish Attendance.", reply_markup=markup)