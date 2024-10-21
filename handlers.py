from telebot import types
from config import client, db, sql, lock, logger
from texts import *

@client.message_handler(commands=['start'])
def start(message):
    try:
        user = message.from_user
        logger.info("המשתמש %s (%s[%s]) התחיל את השיחה.", user.full_name, user.username, user.id)
        cid = message.chat.id
        uid = message.from_user.id

        sql.execute(f"SELECT id, username FROM users WHERE id = {uid}")
        user_record = sql.fetchone()

        if user_record is None:
            sql.execute(f"INSERT INTO users VALUES ({uid}, '{user.username}', 0, 0)")
            db.commit()
            client.send_message(cid, f'{user.full_name} ברוכים הבאים - על מנת לגשת לתפריט לחצו /menu')
        else:
            check_and_update_username(uid, user.username)
            client.send_message(cid, f'🚫 {user.full_name} אתם כבר רשומים - על מנת לגשת לתפריט לחצו /menu 🚫')
    except Exception as e:
        logger.error(f'Error in start function: {str(e)}')
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def check_and_update_username(user_id, current_username):
    try:
        sql.execute(f"SELECT username FROM users WHERE id = {user_id}")
        stored_username = sql.fetchone()[0]

        if stored_username != current_username:
            sql.execute(f"UPDATE users SET username = '{current_username}' WHERE id = {user_id}")
            db.commit()
            logger.info(f"שם המשתמש של {user_id} עודכן מ-'{stored_username}' ל-'{current_username}'")
    except Exception as e:
        logger.error(f"Error updating username for {user_id}: {str(e)}")

@client.message_handler(commands=['block'])
def blockUser(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id

        sql.execute(f"SELECT access FROM users WHERE id = {uid}")
        access = sql.fetchone()[0]

        if access < 444:
            client.send_message(cid, '⚠️ אין לך גישה לפקודה זו ⚠️')
            return

        with lock:
            sql.execute("SELECT id, username FROM users WHERE access != -1")
            users = sql.fetchall()

        if not users:
            client.send_message(cid, '🚫 אין משתמשים לחסום 🚫')
            return

        markup = types.InlineKeyboardMarkup()
        for user in users:
            user_id, username = user
            markup.add(types.InlineKeyboardButton(text=f'{username}', callback_data=f'blockuser_{user_id}'))

        client.send_message(cid, 'בחרו משתמש לחסימה:', reply_markup=markup)

    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.message_handler(commands=['unblock'])
def unblockUser(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id

        sql.execute(f"SELECT access FROM users WHERE id = {uid}")
        access = sql.fetchone()[0]

        if access < 444:
            client.send_message(cid, '⚠️ אין לך גישה לפקודה זו ⚠️')
            return

        with lock:
            sql.execute("SELECT id, username FROM users WHERE access = -1")
            users = sql.fetchall()

        if not users:
            client.send_message(cid, '🚫 אין משתמשים לביטול חסימה 🚫')
            return

        markup = types.InlineKeyboardMarkup()
        for user in users:
            user_id, username = user
            markup.add(types.InlineKeyboardButton(text=f'{username}', callback_data=f'unblockuser_{user_id}'))

        client.send_message(cid, 'בחרו משתמש לביטול חסימה:', reply_markup=markup)

    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.message_handler(commands=['menu'])
def mainMenu(message):
    try:
        user = message.from_user
        logger.info("המשתמש %s (%s[%s]) נכנס לתפריט הראשי.", user.full_name, user.username, user.id)
        cid = message.chat.id
        uid = message.from_user.id
        markup = types.InlineKeyboardMarkup()

        with lock:
            sql.execute("SELECT * FROM categories")
            categories = sql.fetchall()

        for category in categories:
            category_id = category[0]
            category_name = category[1]
            markup.add(types.InlineKeyboardButton(text=category_name, callback_data=f"category_{category_id}"))

        client.send_photo(chat_id=cid, photo=main_pic, caption=starttxt, parse_mode='Markdown', reply_markup=markup)
        check_and_update_username(uid, user.username)
    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

@client.message_handler(commands=['help'])
def showHelp(message):
    try:
        user = message.from_user
        cid = message.chat.id
        uid = message.from_user.id
        sql.execute(f"SELECT access FROM users WHERE id = {uid}")
        access = sql.fetchone()[0]

        help_text = "*⚙️ פקודות זמינות:* \n\n"
        help_text += "/start - התחלת שיחה מחדש עם הבוט\n"
        help_text += "/menu - גישה לתפריט הראשי\n"
        help_text += "/help - הצגת רשימת פקודות\n"
        help_text += "/clear - מחיקת כל ההודעות\n"

        if access == 444:
            help_text += "\n*🔧 פקודות ניהול:* \n"
            help_text += "/users - הצגת כל המשתמשים\n"
            help_text += "/edituser - ערוך משתמש\n"
            help_text += "/block - חסימת משתמש\n"
            help_text += "/unblock - ביטול חסימת משתמש\n"
            help_text += "/addcat - הוספת קטגוריה חדשה\n"
            help_text += "/removecat - מחיקת קטגוריה\n"
            help_text += "/editcat - עריכת קטגוריה\n"
            help_text += "/addprod - הוספת מוצר חדש\n"
            help_text += "/removeprod - מחיקת מוצר\n"
            help_text += "/editprod - ערוך מוצר\n"
        client.send_message(cid, help_text, parse_mode='Markdown')
        check_and_update_username(uid, user.username)
    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')


@client.message_handler(commands=['clear'])
def clearMessages(message):
    try:
        cid = message.chat.id
        client.send_message(cid, '🧹 כל ההודעות נמחקות... לחזרה לתפריט הראשי /menu')
        for i in range(message.message_id, message.message_id - 100, -1):
            try:
                client.delete_message(cid, i)
            except:
                pass
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

@client.message_handler(commands=['getadmin'])
def getAdmin(message):
    if message.from_user.id == aID:
        sql.execute(f"UPDATE users SET access = 444 WHERE id = {aID}")
        db.commit()
        client.send_message(message.chat.id, f"✅ התחברת כמנהל ✅")
    else:
        client.send_message(message.chat.id, '⚠️ אין לך גישה ⚠️')

@client.message_handler(commands=['allusers', 'users'])
def allUsers(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id
        sql.execute(f"SELECT * FROM users WHERE id = {uid}")

        global getaccess
        getaccess = sql.fetchone()[2]
        accessquery = 1
        if getaccess < accessquery:
            client.send_message(cid, '⚠️ אין לך גישה ⚠️')
        else:
            text_chunk = '*🗃 רשימת כל המשתמשים:*\n\n'
            idusernumber = 0
            users_per_message = 25

            user_list = []
            for info in sql.execute(f"SELECT * FROM users"):
                if info[2] == 0:
                    accessname = 'משתמש רגיל'
                elif info[2] == 444:
                    accessname = 'מנהל'
                elif info[2] == 1:
                    accessname = 'עובד'
                verified_status = 'מאומת ✅' if info[3] == 1 else 'לא מאומת ❌'

                # If the user has a username, use t.me link. Otherwise, use tg://user?id=
                if info[1] != 'None':
                    user_link = f"https://t.me/{info[1]}"
                else:
                    user_link = f'tg://user?id={str(info[0])}'

                idusernumber += 1
                user_info = (
                    f"*{idusernumber}. {info[0]} ({info[1]})*\n"
                    f"*👑 | רמת גישות:* {accessname}\n"
                    f"*🛡️ | סטטוס אימות:* {verified_status}\n"
                    f"*✉️ | פרופיל:* [{info[1]}]({user_link})\n"
                )
                user_list.append(user_info)

            # Split the user list into chunks of `users_per_message`
            for i in range(0, len(user_list), users_per_message):
                text_chunk = "".join(user_list[i:i + users_per_message])
                client.send_message(cid, text_chunk, parse_mode='Markdown', disable_web_page_preview=True)

    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.message_handler(commands=['edituser'])
def list_users_to_edit(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id

        sql.execute(f"SELECT access FROM users WHERE id = {uid}")
        access = sql.fetchone()[0]

        if access < 444:
            client.send_message(cid, '⚠️ אין לך גישה לפקודה זו ⚠️')
            return

        send_edit_users_page(cid, page=1)

    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

def send_edit_users_page(chat_id, page=1):
    try:
        users_per_page = 20
        offset = (page - 1) * users_per_page

        sql.execute("SELECT COUNT(*) FROM users")
        total_users = sql.fetchone()[0]
        total_pages = (total_users + users_per_page - 1) // users_per_page

        sql.execute(f"SELECT id, username FROM users LIMIT {users_per_page} OFFSET {offset}")
        users = sql.fetchall()

        markup = types.InlineKeyboardMarkup()

        for user in users:
            user_id, username = user
            markup.add(types.InlineKeyboardButton(text=f'{username} - ID:{user_id}', callback_data=f'edituser_{user_id}'))

        if page > 1:
            markup.add(types.InlineKeyboardButton(text='⏪ הקודם', callback_data=f'editusers_page_{page-1}'))
        if page < total_pages:
            markup.add(types.InlineKeyboardButton(text='הבא ⏩', callback_data=f'editusers_page_{page+1}'))

        client.send_message(chat_id, f'🗃 רשימת משתמשים לעריכה - עמוד {page} מתוך {total_pages}', reply_markup=markup)

    except Exception as e:
        client.send_message(chat_id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.message_handler(commands=['addcat'])
def addCategory(message):
    if message.from_user.id == aID:
        msg = client.send_message(message.chat.id, 'מהו שם הקטגוריה החדשה?', parse_mode='Markdown')
        client.register_next_step_handler(msg, saveCategory)
    else:
        client.send_message(message.chat.id, '⚠️ אין לך גישה ⚠️')

def saveCategory(message):
    try:
        category_name = message.text.strip()
        with lock:
            sql.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
            db.commit()
        client.send_message(message.chat.id, f'✅ קטגוריה "{category_name}" נוספה בהצלחה!')
    except:
        client.send_message(message.chat.id, f'🚫 קטגוריה "{category_name}" כבר קיימת 🚫')

@client.message_handler(commands=['removecat'])
def removeCategory(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id
        with lock:
            sql.execute(f"SELECT * FROM users WHERE id = {uid}")
            getaccess = sql.fetchone()[2]
        if getaccess < 1:
            client.send_message(cid, '⚠️ אין לך גישה ⚠️')
        else:
            sql.execute(f"SELECT * FROM categories")
            result = sql.fetchall()
            markup = types.InlineKeyboardMarkup()
            for info in result:
                markup.add(types.InlineKeyboardButton(text=info[1], callback_data='deletecat_' + str(info[0])))
            client.send_message(chat_id=cid, text="בחרו את הקטגוריה שתרצו למחוק:", parse_mode='Markdown', reply_markup=markup)
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

@client.message_handler(commands=['addprod'])
def addProduct(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id
        with lock:
            sql.execute(f"SELECT * FROM users WHERE id = {uid}")
            accessibility = sql.fetchone()[2]
        if accessibility < 1:
            client.send_message(cid, '⚠️ אין לך גישה ⚠️')
        else:
            msg = client.send_message(cid, 'מהו שם המוצר?', parse_mode='Markdown')
            client.register_next_step_handler(msg, addProductName)
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def addProductName(message):
    try:
        cid = message.chat.id
        global prodnameans
        prodnameans = message.text
        client.delete_message(message.chat.id, message.message_id)
        client.delete_message(message.chat.id, message.message_id-1)
        msg = client.send_message(cid, 'מהו תיאור המוצר?', parse_mode='Markdown')
        client.register_next_step_handler(msg, addProductCaption)
    except:
        client.send_message(cid, '🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def addProductCaption(message):
    try:
        cid = message.chat.id
        global prodcapans
        prodcapans = message.text
        client.delete_message(message.chat.id, message.message_id)
        client.delete_message(message.chat.id, message.message_id-1)
        msg = client.send_message(cid, 'מה הכתובת url של המוצר?', parse_mode='Markdown')
        client.register_next_step_handler(msg, addProductURL)
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def addProductURL(message):
    try:
        cid = message.chat.id
        global produrlans
        produrlans = message.text
        client.delete_message(message.chat.id, message.message_id)
        client.delete_message(message.chat.id, message.message_id-1)
        msg = client.send_message(cid, '-מה הcbdata של המוצר?', parse_mode='Markdown')
        client.register_next_step_handler(msg, addProductCB)
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def addProductCB(message):
    try:
        cid = message.chat.id
        global prodcbans
        prodcbans = message.text
        client.delete_message(message.chat.id, message.message_id)
        client.delete_message(message.chat.id, message.message_id-1)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        with lock:
            sql.execute("SELECT * FROM categories")
            categories = sql.fetchall()

        for category in categories:
            category_name = category[1]
            markup.add(types.KeyboardButton(text=category_name))

        msg = client.send_message(cid, 'בחרו את הקטגוריה של המוצר:', reply_markup=markup)
        client.register_next_step_handler(msg, addProductCategory)
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def addProductCategory(message):
    try:
        cid = message.chat.id
        category_name = message.text
        client.delete_message(message.chat.id, message.message_id)
        client.delete_message(message.chat.id, message.message_id-1)
        with lock:
            sql.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
            category_id = sql.fetchone()

            if category_id is None:
                client.send_message(cid, '🚫 קטגוריות לא קיימות 🚫')
                return

            sql.execute(f"SELECT cbdata FROM products WHERE cbdata = ?", (prodcbans,))
            if sql.fetchone() is None:
                sql.execute(f"""
                    INSERT INTO products (name, caption, url, cbdata, category)
                    VALUES (?, ?, ?, ?, ?)
                """, (prodnameans, prodcapans, produrlans, prodcbans, category_id[0]))
                db.commit()
                client.send_message(cid, '✅ המוצר נוסף בהצלחה למערכת!')
            else:
                client.send_message(cid, '🚫 המוצר כבר קיים במערכת!')
    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.message_handler(commands=['removeprod'])
def removeProduct(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id
        with lock:
            sql.execute(f"SELECT * FROM users WHERE id = {uid}")
            getaccess = sql.fetchone()[2]
        if getaccess < 1:
            client.send_message(cid, '⚠️ אין לך גישה ⚠️')
        else:
            sql.execute(f"SELECT * FROM products")
            result = sql.fetchall()
            if result:
                markup = types.InlineKeyboardMarkup()
                for info in result:
                    markup.add(types.InlineKeyboardButton(text=info[1], callback_data=f'deleteprod_{info[0]}'))
                client.send_message(chat_id=cid, text="בחרו את המוצר שתרצו למחוק:", parse_mode='Markdown', reply_markup=markup)
            else:
                client.send_message(cid, '🚫 אין מוצרים זמינים למחיקה 🚫')
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

@client.message_handler(commands=['editprod'])
def editProduct(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id

        with lock:
            sql.execute(f"SELECT * FROM users WHERE id = {uid}")
            accessibility = sql.fetchone()[2]

        if accessibility < 1:
            client.send_message(cid, '⚠️ אין לך גישה ⚠️')
        else:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            with lock:
                sql.execute("SELECT name FROM products")
                products = sql.fetchall()

            for product in products:
                markup.add(types.KeyboardButton(text=product[0]))

            msg = client.send_message(cid, 'בחרו את המוצר שתרצו לערוך:', reply_markup=markup)
            client.register_next_step_handler(msg, selectProductToEdit)
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def selectProductToEdit(message):
    try:
        client.delete_message(message.chat.id, message.message_id)
        client.delete_message(message.chat.id, message.message_id-1)
        cid = message.chat.id
        global selected_product_name
        selected_product_name = message.text

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton(text='שם המוצר'))
        markup.add(types.KeyboardButton(text='תיאור המוצר'))
        markup.add(types.KeyboardButton(text='כתובת URL'))
        markup.add(types.KeyboardButton(text='קטגוריה'))

        msg = client.send_message(cid, 'מה תרצו לערוך במוצר?', reply_markup=markup)
        client.register_next_step_handler(msg, editProductOptions)
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def editProductOptions(message):
    try:
        client.delete_message(message.chat.id, message.message_id)
        client.delete_message(message.chat.id, message.message_id-1)
        cid = message.chat.id
        edit_option = message.text

        if edit_option == 'שם המוצר':
            msg = client.send_message(cid, 'הכניסו את שם המוצר החדש:', reply_markup=types.ReplyKeyboardRemove())
            client.register_next_step_handler(msg, updateProductName)
        elif edit_option == 'תיאור המוצר':
            msg = client.send_message(cid, 'הכניסו את תיאור המוצר החדש:', reply_markup=types.ReplyKeyboardRemove())
            client.register_next_step_handler(msg, updateProductCaption)
        elif edit_option == 'כתובת URL':
            msg = client.send_message(cid, 'הכניסו את כתובת ה-URL החדשה:', reply_markup=types.ReplyKeyboardRemove())
            client.register_next_step_handler(msg, updateProductURL)
        elif edit_option == 'קטגוריה':
            editProductCategory(cid)
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def updateProductName(message):
    try:
        client.delete_message(message.chat.id, message.message_id)
        client.delete_message(message.chat.id, message.message_id-1)
        cid = message.chat.id
        new_name = message.text
        with lock:
            sql.execute("UPDATE products SET name = ? WHERE name = ?", (new_name, selected_product_name))
            db.commit()
        client.send_message(cid, f'✅ שם המוצר עודכן בהצלחה ל-{new_name}!')
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def updateProductCaption(message):
    try:
        client.delete_message(message.chat.id, message.message_id)
        client.delete_message(message.chat.id, message.message_id-1)
        cid = message.chat.id
        new_caption = message.text
        with lock:
            sql.execute("UPDATE products SET caption = ? WHERE name = ?", (new_caption, selected_product_name))
            db.commit()
        client.send_message(cid, '✅ תיאור המוצר עודכן בהצלחה!')
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def updateProductURL(message):
    try:
        client.delete_message(message.chat.id, message.message_id)
        client.delete_message(message.chat.id, message.message_id-1)
        cid = message.chat.id
        new_url = message.text
        with lock:
            sql.execute("UPDATE products SET url = ? WHERE name = ?", (new_url, selected_product_name))
            db.commit()
        client.send_message(cid, '✅ כתובת ה-URL של המוצר עודכנה בהצלחה!')
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def editProductCategory(cid):
    try:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        with lock:
            sql.execute("SELECT name FROM categories")
            categories = sql.fetchall()

        for category in categories:
            markup.add(types.KeyboardButton(text=category[0]))
        msg = client.send_message(cid, 'בחרו את הקטגוריה החדשה של המוצר:', reply_markup=markup)
        client.register_next_step_handler(msg, updateProductCategory)
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def updateProductCategory(message):
    try:
        cid = message.chat.id
        new_category_name = message.text
        client.delete_message(message.chat.id, message.message_id - 0)
        client.delete_message(message.chat.id, message.message_id - 1)
        with lock:
            sql.execute("SELECT id FROM categories WHERE name = ?", (new_category_name,))
            category_id = sql.fetchone()

            if category_id:
                sql.execute("UPDATE products SET category = ? WHERE name = ?", (category_id[0], selected_product_name))
                db.commit()
                client.send_message(cid, f'✅ קטגוריית המוצר עודכנה בהצלחה ל-{new_category_name}!')
            else:
                client.send_message(cid, '🚫 קטגוריה לא קיימת 🚫')
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

@client.message_handler(commands=['editcat'])
def editCategory(message):
    try:
        cid = message.chat.id
        uid = message.from_user.id

        with lock:
            sql.execute(f"SELECT * FROM users WHERE id = {uid}")
            accessibility = sql.fetchone()[2]

        if accessibility < 1:
            client.send_message(cid, '⚠️ אין לך גישה ⚠️')
        else:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            with lock:
                sql.execute("SELECT name FROM categories")
                categories = sql.fetchall()

            for category in categories:
                markup.add(types.KeyboardButton(text=category[0]))

            msg = client.send_message(cid, 'בחרו את הקטגוריה שתרצו לערוך:', reply_markup=markup)
            client.register_next_step_handler(msg, selectCategoryToEdit)
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def selectCategoryToEdit(message):
    try:
        client.delete_message(message.chat.id, message.message_id)
        client.delete_message(message.chat.id, message.message_id-1)
        cid = message.chat.id
        global selected_category_name
        selected_category_name = message.text

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton(text='שם הקטגוריה'))
        markup.add(types.KeyboardButton(text='מזהה הקטגוריה'))

        msg = client.send_message(cid, 'מה תרצו לערוך בקטגוריה?', reply_markup=markup)
        client.register_next_step_handler(msg, editCategoryOptions)
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def editCategoryOptions(message):
    try:
        client.delete_message(message.chat.id, message.message_id)
        client.delete_message(message.chat.id, message.message_id-1)
        cid = message.chat.id
        edit_option = message.text

        if edit_option == 'שם הקטגוריה':
            msg = client.send_message(cid, 'הכניסו את שם הקטגוריה החדש:', reply_markup=types.ReplyKeyboardRemove())
            client.register_next_step_handler(msg, updateCategoryName)
        elif edit_option == 'מזהה הקטגוריה':
            msg = client.send_message(cid, 'הכניסו את מזהה הקטגוריה החדש:', reply_markup=types.ReplyKeyboardRemove())
            client.register_next_step_handler(msg, updateCategoryID)
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def updateCategoryName(message):
    try:
        client.delete_message(message.chat.id, message.message_id)
        client.delete_message(message.chat.id, message.message_id-1)
        cid = message.chat.id
        new_name = message.text
        with lock:
            sql.execute("UPDATE categories SET name = ? WHERE name = ?", (new_name, selected_category_name))
            db.commit()
        client.send_message(cid, f'✅ שם הקטגוריה עודכן בהצלחה ל-{new_name}!')
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

def updateCategoryID(message):
    try:
        client.delete_message(message.chat.id, message.message_id)
        client.delete_message(message.chat.id, message.message_id-1)
        cid = message.chat.id
        new_id = message.text
        with lock:
            sql.execute("UPDATE categories SET id = ? WHERE name = ?", (new_id, selected_category_name))
            db.commit()
        client.send_message(cid, f'✅ מזהה הקטגוריה עודכן בהצלחה ל-{new_id}!')
    except:
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

@client.message_handler(commands=['startop'])
def startop(message):
    # Create the inline keyboard
    keyboard = types.InlineKeyboardMarkup()

    # Define buttons with URLs
    button_private_group = types.InlineKeyboardButton("🗂️לתפריט והזמנה - לחצו כאן👇🏻", url=privateGlink)

    # Add buttons to the keyboard
    keyboard.add(button_private_group)

    # Send the photo with caption and inline keyboard to the group
    client.send_photo(
        chat_id=TRAFFICGID,
        photo=adminURL,
        caption=posttxt,
        reply_markup=keyboard, parse_mode='Markdown'
    )

# Handler for /verfs command
@client.message_handler(commands=['verfs'])
def showVerificationsList(message, page=0):
    cid = message.chat.id
    user = message.from_user

    try:
        # Fetch verifications from the database (max 10 per page)
        offset = page * 10
        with lock:
            sql.execute("SELECT id, fullname, photo_message_id FROM verifications LIMIT 10 OFFSET ?", (offset,))
            verifications = sql.fetchall()

        if not verifications:
            client.send_message(cid, "🚫 אין אימותים להצגה 🚫")
            return

        # Create inline buttons for the verifications
        markup = types.InlineKeyboardMarkup()
        for verification in verifications:
            verification_id, fullname, photo_message_id = verification
            verification_btn = types.InlineKeyboardButton(text=fullname, callback_data=f'verification_{verification_id}')
            markup.add(verification_btn)

        # Add navigation buttons if there are more than 10 verifications
        if page > 0:
            prev_btn = types.InlineKeyboardButton(text="⏮️ Previous", callback_data=f'verf_page_{page - 1}')
            markup.add(prev_btn)

        next_page = page + 1
        with lock:
            sql.execute("SELECT COUNT(*) FROM verifications")
            total_verifications = sql.fetchone()[0]
        if total_verifications > offset + 10:
            next_btn = types.InlineKeyboardButton(text="⏭️ Next", callback_data=f'verf_page_{next_page}')
            markup.add(next_btn)

        # Send the list of verifications
        client.send_message(cid, "📝 רשימת אימותים:", reply_markup=markup)

    except Exception as e:
        client.send_message(cid, f"🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫")