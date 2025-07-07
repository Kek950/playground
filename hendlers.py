from regs import reg_class
import sqlite3
from utils import show_attendance_buttons
from db import get_students
import datetime
from telebot import types
import json

def request_handler(bot, attendance_sessions):
    
    def wrapped_reg_class(msg):
        reg_class(bot, msg)
    
    @bot.message_handler(commands=['start', 'help'])
    def start(message):
        bot.send_message(message.chat.id, f"Welcome {message.from_user.first_name}!\nThis bot helps manage class attendance.\n\nAvailable commands:\n /add_class - Register a new class\n/attendance - Start taking attendance\n/see_attendance - View attendance records")

    # ======================================================================================================================================================

    @bot.message_handler(commands=['add_class'])
    def add_class(message):
        bot.send_message(message.chat.id, "Please enter the class name you want to register:")
        bot.register_next_step_handler(message, wrapped_reg_class)
        
    # ======================================================================================================================================================

    @bot.message_handler(commands=['attendance'])
    def attendance(message):
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT class_name FROM students WHERE user_id = ?', (message.chat.id,))
        classes = cursor.fetchall()
        conn.close()

        if not classes:
            bot.send_message(message.chat.id, "⚠️ No registered classes.")
            return

        markup = types.InlineKeyboardMarkup()
        for (class_name,) in classes:
            markup.add(types.InlineKeyboardButton(text=class_name, callback_data=f"attendance_{class_name}"))

        bot.send_message(message.chat.id, "📘 Select a class to take attendance:", reply_markup=markup)
    
    # ======================================================================================================================================================
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('attendance_'))
    def handle_attendance_callback(call):
        class_name = call.data[len('attendance_'):]
        students = get_students(class_name, call.message.chat.id)
        if not students:
            bot.send_message(call.message.chat.id, "❌ No students found for this class.")
            return

        attendance_sessions[call.message.chat.id] = {
            "class_name": class_name,
            "students": students,
            "status": ["absent"] * len(students)
        }

        show_attendance_buttons(bot, call.message.chat.id, attendance_sessions, call.message.message_id)
        bot.answer_callback_query(call.id)
        
    # ======================================================================================================================================================

    @bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
    def toggle_attendance(call):
        index = int(call.data.split("_")[1])
        session = attendance_sessions.get(call.message.chat.id)
        if not session:
            bot.answer_callback_query(call.id, "⚠️ No active session.")
            return

        session["status"][index] = "present" if session["status"][index] == "absent" else "absent"
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        show_attendance_buttons(bot, call.message.chat.id, attendance_sessions, call.message.message_id)

    # ======================================================================================================================================================
    
    @bot.callback_query_handler(func=lambda call: call.data == "finish_attendance")
    def finish_attendance(call):
        user_id = call.message.chat.id
        session = attendance_sessions.pop(user_id, None)

        if not session:
            bot.answer_callback_query(call.id, "⚠️ No active attendance session found.")
            return

        class_name = session["class_name"]
        students = session["students"]
        status = session["status"]
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        # New row to append: [date, student1_status, student2_status, ...]
        new_row = [today] + status

        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute('SELECT attendance_array FROM students WHERE class_name = ? AND user_id = ? LIMIT 1', (class_name, call.message.chat.id))
            row = cursor.fetchone()

            attendance_array = json.loads(row[0]) if row and row[0] else []

            # Add header row only if array is empty
            if not attendance_array:
                attendance_array.append(["Date"] + students)

            attendance_array.append(new_row)

            cursor.execute('UPDATE students SET attendance_array = ? WHERE class_name = ? AND user_id = ?',
                       (json.dumps(attendance_array), class_name, call.message.chat.id))
            conn.commit()
            conn.close()

            bot.answer_callback_query(call.id)
            bot.send_message(user_id, f"✅ Attendance saved for class *{class_name}* on *{today}*.",
                            parse_mode='Markdown')

        except Exception as e:
            bot.send_message(user_id, f"❌ Error saving attendance: {str(e)}")
    
    # ======================================================================================================================================================
    
    @bot.message_handler(commands=['see_attendance'])
    def see_attendance(message):
        chat_id = message.chat.id
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT class_name FROM students WHERE user_id = ?', (chat_id,))
        classes = cursor.fetchall()
        conn.close()

        if not classes:
            bot.send_message(message.chat.id, "⚠️ No registered classes.")
            return

        markup = types.InlineKeyboardMarkup()
        for (class_name,) in classes:
            markup.add(types.InlineKeyboardButton(text=class_name, callback_data=f"see_attendance_{class_name}"))

        bot.send_message(message.chat.id, "📘 Select a class to see attendance:", reply_markup=markup)

    # ======================================================================================================================================================
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("see_attendance_"))
    def see_attendance(call):
        class_name = call.data.split("_", 2)[2]
        chat_id = call.message.chat.id

        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute('SELECT attendance_array FROM students WHERE class_name = ? AND user_id = ? LIMIT 1', (class_name, chat_id))
            row = cursor.fetchone()
            conn.close()

            if not row or not row[0]:
                bot.send_message(chat_id, f"❌ No attendance found for class: {class_name}")
                return

            attendance_array = json.loads(row[0])

            if not attendance_array or len(attendance_array) < 2:
                bot.send_message(chat_id, f"ℹ️ No attendance sessions recorded yet for {class_name}.")
                return

            # Transpose the array to print students vertically
            transposed = list(map(list, zip(*attendance_array)))

            # Format into a readable table
            table = "📊 *Attendance for " + class_name + "*\n\n"
            col_widths = [max(len(str(cell)) for cell in row) for row in transposed]
            for row in transposed:
                for i, cell in enumerate(row):
                    padded = str(cell).ljust(col_widths[i])
                    table += f"{padded}   "
                table += "\n"

            bot.send_message(chat_id, f"```\n{table}\n```", parse_mode='Markdown')

        except Exception as e:
            bot.send_message(chat_id, f"❌ Error loading attendance: {str(e)}")