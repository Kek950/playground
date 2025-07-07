import sqlite3
import json
# in regs.py
def reg_class(bot, message):
    class_name = message.text.strip()
    if not class_name:
        bot.send_message(message.chat.id, "❗ Class name cannot be empty.")
        bot.register_next_step_handler(message, lambda msg: reg_class(bot, msg))
        return

    bot.send_message(message.chat.id, f"✅ Class `{class_name}` registered.\nEnter student names separated by commas:", parse_mode='Markdown')
    bot.register_next_step_handler(message, lambda msg: reg_students(bot, msg, class_name))

def reg_students(bot, message, class_name):
    students = [s.strip() for s in message.text.split(',') if s.strip()]
    if not students:
        bot.send_message(message.chat.id, "❗ Student list cannot be empty.")
        bot.register_next_step_handler(message, lambda msg: reg_students(bot, msg, class_name))
        return

    full_name = message.from_user.first_name
    user_id = message.from_user.id
    if message.from_user.last_name:
        full_name += ' ' + message.from_user.last_name

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO students (user_id, full_name, class_name, class_array) VALUES (?, ?, ?, ?)',
                       (user_id, full_name, class_name, json.dumps(students)))
        conn.commit()
        bot.send_message(message.chat.id, f"👨‍🎓 Students added: {', '.join(students)}\n\nUse /attendance to begin marking.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")
    finally:
        conn.close()

