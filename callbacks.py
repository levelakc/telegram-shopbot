from telebot import types
from config import *
from texts import *
from handlers import *
import threading
### Block and unblock
@client.callback_query_handler(lambda call: call.data.startswith('blockuser_'))
def blockUserCallback(call):
    try:
        user_id = int(call.data.split('_')[1])
        cid = call.message.chat.id

        with lock:
            sql.execute("UPDATE users SET access = -1 WHERE id = ?", (user_id,))
            db.commit()

        client.restrict_chat_member(chat_id=cid, user_id=user_id, can_send_messages=False)
        client.send_message(cid, '🚫 המשתמש נחסם בהצלחה.')
    except Exception as e:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.callback_query_handler(lambda call: call.data.startswith('unblockuser_'))
def unblockUserCallback(call):
    try:
        user_id = int(call.data.split('_')[1])
        cid = call.message.chat.id

        with lock:
            sql.execute("UPDATE users SET access = 0 WHERE id = ?", (user_id,))
            db.commit()

        client.unban_chat_member(chat_id=cid, user_id=user_id)
        client.send_message(cid, '✅ המשתמש בוטל בהצלחה.')
    except Exception as e:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

## Edit user
@client.callback_query_handler(lambda call: call.data.startswith('editusers_page_'))
def paginate_edit_users(call):
    try:
        client.delete_message(call.message.chat.id, call.message.message_id)
        page = int(call.data.split('_')[-1])
        send_edit_users_page(call.message.chat.id, page=page)
    except Exception as e:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.callback_query_handler(lambda call: call.data.startswith('edituser_'))
def edit_user_details(call):
    try:
        user_id = int(call.data.split('_')[-1])
        sql.execute(f"SELECT id, username, access, verified FROM users WHERE id = ?", (user_id,))
        user = sql.fetchone()

        if user:
            user_id, username, access, verified = user

            # Set access level and verification status
            accessname = 'משתמש רגיל' if access == 0 else 'מנהל' if access == 444 else 'עובד'
            verified_status = 'מאומת ✅' if verified == 1 else 'לא מאומת ❌'

            # Format the message using HTML instead of Markdown
            text = (
                f"<b>ID:</b> {user_id}\n"
                f"<b>שם משתמש:</b> {username}\n"
                f"<b>רמת גישה:</b> {accessname}\n"
                f"<b>סטטוס אימות:</b> {verified_status}\n"
            )

            # Create the inline keyboard
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text='✏️ ערוך שם משתמש', callback_data=f'editfield_username_{user_id}'))
            markup.add(types.InlineKeyboardButton(text='✏️ ערוך רמת גישה', callback_data=f'editfield_access_{user_id}'))
            markup.add(types.InlineKeyboardButton(text='✏️ ערוך סטטוס אימות', callback_data=f'editfield_verified_{user_id}'))
            markup.add(types.InlineKeyboardButton(text='📜 ערוך אימותים', callback_data=f'edit_verifications_{user_id}'))
            markup.add(types.InlineKeyboardButton(text='📨 שלח הודעה', callback_data=f'message_user_{user_id}'))
            markup.add(types.InlineKeyboardButton(text='🔙 חזרה', callback_data="editusers_page_1"))

            # Edit the message with HTML parse mode
            client.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML', reply_markup=markup)
        else:
            client.send_message(call.message.chat.id, '🚫 משתמש לא נמצא 🚫')

    except Exception as e:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.callback_query_handler(lambda call: call.data.startswith('editfield_'))
def handle_edit_field(call):
    try:
        field, user_id = call.data.split('_')[1], call.data.split('_')[-1]
        cid = call.message.chat.id

        if field == 'username':
            msg = client.send_message(cid, 'הכנס את שם המשתמש החדש:')
            client.register_next_step_handler(msg, lambda m: update_username(m, user_id))
        elif field == 'access':
            msg = client.send_message(cid, 'הכנס את רמת הגישה החדשה (0, 1, 444):')
            client.register_next_step_handler(msg, lambda m: update_access(m, user_id))
        elif field == 'verified':
            msg = client.send_message(cid, 'הכנס את סטטוס האימות החדש (0 או 1):')
            client.register_next_step_handler(msg, lambda m: update_verified(m, user_id))

        client.answer_callback_query(call.id)

    except Exception as e:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

def update_username(message, user_id):
    try:
        new_username = message.text.strip()
        with lock:
            sql.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, user_id))
            db.commit()
        client.send_message(message.chat.id, f'✅ שם המשתמש עודכן בהצלחה ל-{new_username}!')
    except Exception as e:
        client.send_message(message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

def update_access(message, user_id):
    try:
        new_access = int(message.text.strip())
        with lock:
            sql.execute("UPDATE users SET access = ? WHERE id = ?", (new_access, user_id))
            db.commit()
        client.send_message(message.chat.id, f'✅ רמת הגישה עודכנה בהצלחה ל-{new_access}!')
    except Exception as e:
        client.send_message(message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

def update_verified(message, user_id):
    try:
        new_verified = int(message.text.strip())
        with lock:
            sql.execute("UPDATE users SET verified = ? WHERE id = ?", (new_verified, user_id))
            db.commit()
        client.send_message(message.chat.id, f'✅ סטטוס האימות עודכן בהצלחה ל-{new_verified}!')
    except Exception as e:
        client.send_message(message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.callback_query_handler(lambda call: call.data.startswith('edit_verifications_'))
def edit_verifications(call):
    try:
        user_id = int(call.data.split('_')[-1])
        sql.execute(f"SELECT * FROM verifications WHERE id = ?", (user_id,))
        verifications = sql.fetchall()

        if not verifications:
            client.send_message(call.message.chat.id, '🚫 לא נמצאו אימותים עבור המשתמש הזה 🚫')
            return

        text = f"*אימותים עבור משתמש:* {user_id}\n\n"
        markup = types.InlineKeyboardMarkup()

        # Listing all verifications
        for idx, verification in enumerate(verifications):
            verification_text = (
                f"*אימות {idx + 1}:*\n"
                f"📛 שם מלא: {verification[2]}\n"
                f"📞 פלאפון: {verification[3]}\n"
                f"🏠 כתובת: {verification[4]}\n\n"
            )
            text += verification_text
            markup.add(types.InlineKeyboardButton(text=f'ערוך אימות {idx + 1}', callback_data=f'edit_verification_{verification[0]}'))

        client.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=markup)
    except Exception as e:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.callback_query_handler(lambda call: call.data.startswith('edit_verification_'))
def edit_verification(call):
    try:
        verification_id = int(call.data.split('_')[-1])
        sql.execute(f"SELECT * FROM verifications WHERE id = ?", (verification_id,))
        verification = sql.fetchone()

        if verification:
            # Unpack verification details
            _, username, fullname, pnumber, address, verified, photo_message_id, recipe_message_id = verification

            text = (
                f"*עריכת אימות:*\n"
                f"📛 שם מלא: {fullname}\n"
                f"📞 פלאפון: {pnumber}\n"
                f"🏠 כתובת: {address}\n"
            )

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text='✏️ ערוך שם מלא', callback_data=f'editverif_fullname_{verification_id}'))
            markup.add(types.InlineKeyboardButton(text='✏️ ערוך פלאפון', callback_data=f'editverif_phone_{verification_id}'))
            markup.add(types.InlineKeyboardButton(text='✏️ ערוך כתובת', callback_data=f'editverif_address_{verification_id}'))
            markup.add(types.InlineKeyboardButton(text='❌ מחק אימות זה', callback_data=f'delete_verification_{verification_id}'))

            # Add buttons to access and edit the saved photo and recipe
            if photo_message_id:
                markup.add(types.InlineKeyboardButton(text='📸 הצג תמונת אימות', url=f'https://t.me/c/{RecipeGIDorg}/{photo_message_id}'))
                markup.add(types.InlineKeyboardButton(text='✏️ ערוך ID תמונה', callback_data=f'editverif_photoid_{verification_id}'))
            if recipe_message_id:
                markup.add(types.InlineKeyboardButton(text='📄 הצג מסמך מתכון', url=f'https://t.me/c/{RecipeGIDorg}/{recipe_message_id}'))
                markup.add(types.InlineKeyboardButton(text='✏️ ערוך ID מתכון', callback_data=f'editverif_recipeid_{verification_id}'))

            client.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=markup)
        else:
            client.send_message(call.message.chat.id, '🚫 אימות לא נמצא 🚫')
    except Exception as e:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.callback_query_handler(lambda call: call.data.startswith('editverif_'))
def handle_edit_verification_field(call):
    try:
        field, verification_id = call.data.split('_')[1], call.data.split('_')[-1]
        cid = call.message.chat.id

        if field == 'fullname':
            msg = client.send_message(cid, 'הכנס את השם המלא החדש:')
            client.register_next_step_handler(msg, lambda m: update_verif_fullname(m, verification_id))
        elif field == 'phone':
            msg = client.send_message(cid, 'הכנס את מספר הטלפון החדש:')
            client.register_next_step_handler(msg, lambda m: update_verif_phone(m, verification_id))
        elif field == 'address':
            msg = client.send_message(cid, 'הכנס את הכתובת החדשה:')
            client.register_next_step_handler(msg, lambda m: update_verif_address(m, verification_id))
        elif field == 'photoid':
            msg = client.send_message(cid, 'הכנס את ה-ID של תמונת האימות החדש:')
            client.register_next_step_handler(msg, lambda m: update_verif_photoid(m, verification_id))
        elif field == 'recipeid':
            msg = client.send_message(cid, 'הכנס את ה-ID של מסמך המתכון החדש:')
            client.register_next_step_handler(msg, lambda m: update_verif_recipeid(m, verification_id))

        client.answer_callback_query(call.id)
    except Exception as e:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

# Functions to update verification details
def update_verif_fullname(message, verification_id):
    try:
        new_fullname = message.text.strip()
        sql.execute("UPDATE verifications SET fullname = ? WHERE id = ?", (new_fullname, verification_id))
        db.commit()
        client.send_message(message.chat.id, f'✅ השם המלא עודכן בהצלחה ל-{new_fullname}!')
    except Exception as e:
        client.send_message(message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

def update_verif_phone(message, verification_id):
    try:
        new_phone = message.text.strip()
        sql.execute("UPDATE verifications SET pnumber = ? WHERE id = ?", (new_phone, verification_id))
        db.commit()
        client.send_message(message.chat.id, f'✅ מספר הטלפון עודכן בהצלחה ל-{new_phone}!')
    except Exception as e:
        client.send_message(message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

def update_verif_address(message, verification_id):
    try:
        new_address = message.text.strip()
        sql.execute("UPDATE verifications SET address = ? WHERE id = ?", (new_address, verification_id))
        db.commit()
        client.send_message(message.chat.id, f'✅ הכתובת עודכנה בהצלחה ל-{new_address}!')
    except Exception as e:
        client.send_message(message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

def update_verif_photoid(message, verification_id):
    try:
        new_photo_id = int(message.text.strip())
        sql.execute("UPDATE verifications SET photo_message_id = ? WHERE id = ?", (new_photo_id, verification_id))
        db.commit()
        client.send_message(message.chat.id, f'✅ ה-ID של תמונת האימות עודכן בהצלחה ל-{new_photo_id}!')
    except Exception as e:
        client.send_message(message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

def update_verif_recipeid(message, verification_id):
    try:
        new_recipe_id = int(message.text.strip())
        sql.execute("UPDATE verifications SET recipe_message_id = ? WHERE id = ?", (new_recipe_id, verification_id))
        db.commit()
        client.send_message(message.chat.id, f'✅ ה-ID של המסמך המתכון עודכן בהצלחה ל-{new_recipe_id}!')
    except Exception as e:
        client.send_message(message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.callback_query_handler(lambda call: call.data.startswith('delete_verification_'))
def delete_verification(call):
    try:
        verification_id = int(call.data.split('_')[-1])
        sql.execute("DELETE FROM verifications WHERE id = ?", (verification_id,))
        db.commit()

        # Check if any verifications are left for the user
        sql.execute(f"SELECT * FROM verifications WHERE id = ?", (verification_id,))
        remaining_verifications = sql.fetchall()

        if not remaining_verifications:
            # Set the user's verified status to 0
            sql.execute(f"UPDATE users SET verified = 0 WHERE id = ?", (verification_id,))
            db.commit()
            client.send_message(call.message.chat.id, 'כל האימותים נמחקו והמשתמש אינו מאומת יותר ❌')

        client.send_message(call.message.chat.id, 'האימות נמחק בהצלחה ✅')
    except Exception as e:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

# Command to send a message to a specific user
@client.callback_query_handler(lambda call: call.data.startswith('message_user_'))
def send_message_to_user(call):
    try:
        cid = call.message.chat.id
        target_user_id = int(call.data.split('_')[-1])  # Extract the user_id from the command

        msg = client.send_message(cid, "שלח את ההודעה שתרצה להעביר למשתמש")
        client.register_next_step_handler(msg, forward_message_to_user, target_user_id)

    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')


def forward_message_to_user(message, target_user_id):
    try:
        # Send the message to the user
        markup = types.InlineKeyboardMarkup()
        msgAdmin = types.InlineKeyboardButton(text=f'לענות {ADMINtxt}', url=ADMINurl)
        markup.add(msgAdmin)
        client.send_message(target_user_id, f'הודעה מהמנהל: {message.text}', reply_markup=markup)
        # Notify the admin that the message was sent successfully
        client.send_message(message.chat.id, 'ההודעה נשלחה בהצלחה ✅')
        for i in range(message.message_id, message.message_id - 2, -1):
                try:
                    client.delete_message(message.message.chat_id, i)
                except:
                    pass
    except Exception as e:
        client.send_message(message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

## Remove category
@client.callback_query_handler(lambda call: call.data.startswith("deletecat_"))
def removeCatCB(call):
    try:
        cid = call.message.chat.id
        cat_id = call.data.split('_')[1]
        with lock:
            sql.execute(f"DELETE FROM categories WHERE id = ?", (cat_id,))
            db.commit()
        client.delete_message(cid, call.message.message_id)
        client.send_message(cid, '🗑️ הקטגוריה נמחקה מהמערכת!')
    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

## Remove product
@client.callback_query_handler(lambda call: call.data.startswith("deleteprod_"))
def removeProdCB(call):
    try:
        cid = call.message.chat.id
        prod_id = call.data.split('_')[1]
        with lock:
            sql.execute(f"DELETE FROM products WHERE id = ?", (prod_id,))
            db.commit()
        client.delete_message(cid, call.message.message_id)
        client.send_message(cid, '🗑️ המוצר נמחק מהמערכת!')
    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

## Main menu
@client.callback_query_handler(lambda call: call.data == 'menu')
def mainMenu(call):
    try:
        mid = call.message.message_id
        cid = call.message.chat.id
        user = call.from_user
        logger.info("המשתמש %s (%s[%s]) נכנס לתפריט הראשי.", user.full_name, user.username, user.id)

        markup = types.InlineKeyboardMarkup()

        with lock:
            sql.execute("SELECT * FROM categories")
            categories = sql.fetchall()

        for category in categories:
            category_id = category[0]
            category_name = category[1]
            markup.add(types.InlineKeyboardButton(text=category_name, callback_data=f"category_{category_id}"))

        client.edit_message_media(chat_id=cid, message_id=mid, media=types.InputMediaPhoto(media=main_pic, caption=starttxt, parse_mode='Markdown'), reply_markup=markup)
    except Exception as e:
        logger.error(f"שגיאה בתפריט הראשי: {str(e)}")
        client.send_message(cid, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

## Category menu
@client.callback_query_handler(lambda call: call.data.startswith("category_"))
def categoryMenu(call):
    try:
        user = call.from_user
        logger.info("המשתמש %s (%s[%s]) נכנס לקטגוריה %s.", user.full_name, user.username, user.id, call.data.split('_')[1])
        mid = call.message.message_id
        cid = call.message.chat.id
        category_id = call.data.split('_')[1]
        BACKmmbtn = types.InlineKeyboardButton(BACKmmbtntxt, callback_data='menu')

        with lock:
            sql.execute("SELECT * FROM products WHERE category = ?", (category_id,))
            products = sql.fetchall()

        markup = types.InlineKeyboardMarkup()
        for product in products:
            markup.add(types.InlineKeyboardButton(text=product[1], callback_data='prod_' + product[4]))

        markup.add(BACKmmbtn)
        client.edit_message_media(chat_id=cid, message_id=mid, media=types.InputMediaPhoto(media=main_pic, caption=starttxt, parse_mode='Markdown'), reply_markup=markup)
    except:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

## Product menu
@client.callback_query_handler(lambda call: call.data.startswith("prod_"))
def productMenu(call):
    try:
        user = call.from_user
        logger.info("המשתמש %s (%s[%s]) נכנס למוצר %s.", user.full_name, user.username, user.id, call.data.split('_')[1])
        mid = call.message.message_id
        cid = call.message.chat.id
        if call.data == call.data:
            cbname = call.data.split('_')[1]
            with lock:
                sql.execute(f"SELECT * FROM products WHERE cbdata = '{cbname}'")
                result = sql.fetchall()
                sql.execute(f"SELECT cbdata FROM products WHERE category = {result[0][5]}")
                result1 = sql.fetchall()
            markup = types.InlineKeyboardMarkup()
            ORDERbtn = types.InlineKeyboardButton(ORDERtxt, callback_data="order_" + result[0][4])
            GROUPbtn = types.InlineKeyboardButton(GROUPtxt, url=f'{result[0][3]}')
            ADMINbtn = types.InlineKeyboardButton(ADMINtxt, url=ADMINurl)
            markup.add(ORDERbtn)
            markup.add(GROUPbtn, ADMINbtn)
            counter = 0
            for i in result1:
                for j in i:
                    if j == cbname:
                        if counter == 0 and len(result1) == 1:
                            SPACEbtn = types.InlineKeyboardButton(SPACEbtntxt, callback_data="A")
                            markup.add(SPACEbtn, SPACEbtn)
                        elif counter == 0:
                            NEXTbtn = types.InlineKeyboardButton(NEXTbtntxt, callback_data="prod_" + result1[counter + 1][0])
                            SPACEbtn = types.InlineKeyboardButton(SPACEbtntxt, callback_data="A")
                            markup.add(SPACEbtn, NEXTbtn)
                        elif counter == len(result1) - 1:
                            BACKbtn = types.InlineKeyboardButton(BACKbtntxt, callback_data="prod_" + result1[counter - 1][0])
                            SPACEbtn = types.InlineKeyboardButton(SPACEbtntxt, callback_data="A")
                            markup.add(BACKbtn, SPACEbtn)
                        else:
                            NEXTbtn = types.InlineKeyboardButton(NEXTbtntxt, callback_data="prod_" + result1[counter + 1][0])
                            BACKbtn = types.InlineKeyboardButton(BACKbtntxt, callback_data="prod_" + result1[counter - 1][0])
                            markup.add(BACKbtn, NEXTbtn)
                    else:
                        counter = counter + 1
            BACKmbtn = types.InlineKeyboardButton(BACKmbtntxt, callback_data="category_" + result[0][5])
            BACKmmbtn = types.InlineKeyboardButton(BACKmmbtntxt, callback_data='menu')
            markup.add(BACKmbtn)
            markup.add(BACKmmbtn)
            try:
                client.edit_message_media(chat_id=cid, message_id=mid, media=types.InputMediaPhoto(media=f'{result[0][3]}', caption=f'{result[0][2]}'), reply_markup=markup)
            except:
                client.edit_message_media(chat_id=cid, message_id=mid, media=types.InputMediaVideo(media=f'{result[0][3]}', caption=f'{result[0][2]}'), reply_markup=markup)
    except:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

@client.callback_query_handler(lambda call: call.data.startswith("order_"))
def orderMenu(call):
    try:
        user = call.from_user
        logger.info("User %s (%s[%s]) initiated order %s.", user.full_name, user.username, user.id, call.data.split('_')[1])
        
        # Get the chat id and message id
        cid = call.message.chat.id
        mid = call.message.message_id
        
        # Fetch product details from the database
        sql.execute("SELECT * FROM products WHERE cbdata = ?", (call.data.split('_')[1],))
        result = sql.fetchone()
        
        if not result:
            raise ValueError("Product not found.")
        
        finder, cbname = result[2], result[4]
        markup = types.InlineKeyboardMarkup()

        # Finding all occurrences of money icon 💰
        money_indices = [i for i in range(len(finder)) if finder.startswith('💰', i)]
        
        # Loop through each money icon to create buttons
        for i in range(len(money_indices)):
            text = finder[money_indices[i] + 1:money_indices[i + 1] if i < len(money_indices) - 1 else None].strip()
            if text and not text.startswith(('http', 't.me/')):
                button_text = f"💰{text}💰"
                markup.add(types.InlineKeyboardButton(button_text, callback_data=f'confirm_{cbname}_{text}'))

        # Add custom order button
        markup.add(types.InlineKeyboardButton("💳כמות אחרת💳", callback_data=f'customorder_{cbname}'))
        markup.add(types.InlineKeyboardButton(BACKmbtntxt, callback_data='prod_' + call.data.split('_')[1]))
        markup.add(types.InlineKeyboardButton(BACKmmbtntxt, callback_data='menu'))

        # Attempt to edit the media (photo or video) with the new markup
        try:
            client.edit_message_media(
                chat_id=cid,
                message_id=mid,
                media=types.InputMediaPhoto(media=result[3], caption=finder),
                reply_markup=markup
            )
        except:
            client.edit_message_media(
                chat_id=cid,
                message_id=mid,
                media=types.InputMediaVideo(media=result[3]),
                reply_markup=markup
            )
    except Exception as e:
        logger.error("Error in keyboardBuilderOrder: %s", str(e))
        client.send_message(call.message.chat.id, '🚫 שגיאת מערכת, לרשימת הפקודות - /help 🚫')

@client.callback_query_handler(lambda call: call.data.startswith("customorder_"))
def handleCustomOrder(call):
    try:
        cbname = call.data.split('_')[1]
        cid = call.message.chat.id
        msg = client.send_message(cid, 'כמה יחידות תרצו להזמין? (רק מספרים)', parse_mode='Markdown')
        client.register_next_step_handler(msg, calculateCustomPrice, cbname)
    except Exception as e:
        logger.error("Error in handleCustomOrder: %s", str(e))
        client.send_message(call.message.chat.id, '🚫 שגיאת מערכת: לרשימת הפקודות - /help 🚫')

def calculateCustomPrice(message, cbname):
    try:
        amount = int(message.text)
        cid = message.chat.id
        
        # Clean up previous messages
        client.delete_message(cid, message.message_id)
        
        # Fetch product info
        sql.execute("SELECT caption FROM products WHERE cbdata = ?", (cbname,))
        result = sql.fetchone()
        if not result:
            raise ValueError("Product not found.")
        
        finder = result[0]
        money_indices = [i for i in range(len(finder)) if finder.startswith('💰', i)]
        prices, amounts = [100], [1]

        # Extract prices and amounts
        for i in range(len(money_indices)):
            text = finder[money_indices[i] + 1:money_indices[i + 1] if i < len(money_indices) - 1 else None].strip()
            if text and '-' in text:
                amt, price = map(int, text.split('-'))
                amounts.append(amt)
                prices.append(price)

        total_price = calculate_total_price(amount, amounts, prices)
        confirmCustomOrder(cid, cbname, amount, total_price)
    except ValueError as ve:
        logger.error("Invalid input: %s", str(ve))
        client.send_message(message.chat.id, '🚫 אנא הכניסו מספר תקין. 🚫')
    except Exception as e:
        logger.error("Error in calculateCustomPrice: %s", str(e))
        client.send_message(message.chat.id, '🚫 שגיאת מערכת: לרשימת הפקודות - /help 🚫')

def calculate_total_price(amount, amounts, prices):
    if amount <= amounts[0]:
        return calculateSpecialPrice(amount, amounts[1], prices[1])
    elif amount > amounts[-1]:
        return round((amount / amounts[-1]) * prices[-1])
    else:
        for i in range(1, len(amounts)):
            if amounts[i-1] < amount <= amounts[i]:
                return interpolatePrice(amount, amounts[i-1], amounts[i], prices[i-1], prices[i])

def calculateSpecialPrice(amount, base_amount, base_price):
    special_prices = {
        1: 100,
        2: 150,
        3: 200,
        4: 250,
        base_amount: base_price
    }
    return round(special_prices.get(amount, base_price))

def interpolatePrice(amount, lower_amount, upper_amount, lower_price, upper_price):
    price_per_unit = (upper_price - lower_price) / (upper_amount - lower_amount)
    return round(lower_price + price_per_unit * (amount - lower_amount))

def confirmCustomOrder(cid, cbname, amount, total_price):
    try:
        session = get_user_session(cid)
        session['confirmorder'] = f"{cbname}_{amount}-{total_price}"

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("שלח הזמנה ✅", callback_data=f'sendorder_{cbname}_{amount}_{total_price}'),
            types.InlineKeyboardButton("שנה כמות ✏️", callback_data=f'changeamount_{cbname}')
        )

        client.send_message(
            cid,
            f'*אישרו את ההזמנה:*\n\nמוצר:{cbname}\nכמות: {amount}\nמחיר כולל: {total_price}₪',
            parse_mode='Markdown',
            reply_markup=markup
        )
    except Exception as e:
        logger.error("Error in confirmCustomOrder: %s", str(e))
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.callback_query_handler(lambda call: call.data.startswith('changeamount_'))
def handleChangeAmount(call):
    try:
        cbname = call.data.split('_')[1]
        cid = call.message.chat.id

        # Ask the user for a new amount
        msg = client.send_message(cid, 'כמה יחידות תרצו להזמין? (רק מספרים)', parse_mode='Markdown')
        client.register_next_step_handler(msg, calculateCustomPrice, cbname)
    except Exception as e:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.callback_query_handler(lambda call: call.data.startswith('sendorder_'))
def handleSendOrder(call):
    try:
        data = call.data.split('_')
        cbname = data[1]
        amount = int(data[2])
        total_price = int(data[3])

        global confirmorder, customorder
        confirmorder = f"{cbname}_{amount}-{total_price}"
        customorder = 1

        # Proceed with the existing order confirmation flow
        personConfirm(call)
    except Exception as e:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.callback_query_handler(lambda call: call.data.startswith("delete_message_"))
def handleCustomOrder(call):
    try:
        mid = call.data.split('_')[2]
        cid = call.message.chat.id
        client.delete_message(cid, mid)
    except Exception as e:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')
# Handle person confirmation
@client.callback_query_handler(lambda call: call.data.startswith("confirm_"))
def personConfirm(call):
    try:
        cid = call.message.chat.id
        uid = call.from_user.id

        # Get or create user session
        session = get_user_session(uid)

        # Handle different order types
        if call.data.startswith('confirm_') or call.data.startswith('sendorder_'):
            spliter = call.data.split('_')
            session['customorder'] = 0

            if len(spliter) >= 3:  # Ensure spliter has enough elements
                if call.data.startswith('confirm_'):
                    session['confirmorder'] = f"{spliter[1]}_{spliter[2]}"
                elif len(spliter) >= 4 and call.data.startswith('sendorder_'):
                    session['confirmorder'] = f"{spliter[1]}_{spliter[2]}-{spliter[3]}"
                    session['customorder'] = 1
            else:
                client.send_message(cid, '🚫 שגיאה במערכת: נתונים שגויים 🚫')
                return
            
            # Check if user is verified
            with lock:
                sql.execute(f"SELECT verified FROM users WHERE id = {uid}")
                is_verified = sql.fetchone()[0]

            if is_verified == 1:
                # Retrieve verified user data from the database
                with lock:
                    sql.execute(f"SELECT fullname, pnumber, address FROM verifications WHERE id = {uid}")
                    user_info = sql.fetchone()

                if user_info:
                    # Store user information in session
                    session['confirmname'], session['confirmpnumber'], session['confirmaddress'] = user_info

                    # Ask user if they want pickup, delivery to the last address, or to enter a new address
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(text='איסוף עצמי', callback_data='pickup'))
                    markup.add(types.InlineKeyboardButton(text='משלוח לכתובת האחרונה', callback_data='delivery_last'))
                    markup.add(types.InlineKeyboardButton(text='כתובת חדשה', callback_data='new_address'))
                    
                    client.send_message(cid, f'*בחרו אפשרות:*\nכתובת אחרונה: {user_info[2]}', parse_mode='Markdown', reply_markup=markup)
                else:
                    client.send_message(cid, '🚫 שגיאה במערכת: לא נמצאו פרטים מאומתים 🚫')
            else:
                # Unverified users provide details for first-time order
                msg = client.send_message(cid, '*מהו שמכם המלא?*\n\n(לדוגמא: מורדי אוחנה)', parse_mode='Markdown')
                client.register_next_step_handler(msg, personConfirm1)
    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

# Handle order options (pickup, delivery last address, new address)
@client.callback_query_handler(lambda call: call.data in ["pickup", "delivery_last", "new_address"])
def handleOrderOption(call):
    cid = call.message.chat.id
    uid = call.from_user.id

    # Retrieve session for the user
    session = get_user_session(uid)

    client.delete_message(cid, call.message.message_id)
    try:
        if call.data == "pickup":
            sendOrderToGroupWithoutPhoto(cid, uid, call.message.message_id, pickup=True)
        elif call.data == "delivery_last":
            sendOrderToGroupWithoutPhoto(cid, uid, call.message.message_id, pickup=False)
        elif call.data == "new_address":
            msg = client.send_message(cid, '*מהי הכתובת החדשה אליה תרצו להזמין?*\n\n(בפורמט: עיר, רחוב, מספר בית)', parse_mode='Markdown')
            client.register_next_step_handler(msg, personConfirmNewAddress)
    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

# Handle new address input
def personConfirmNewAddress(message):
    try:
        mid = message.message_id
        cid = message.chat.id
        uid = message.from_user.id

        # Retrieve session for the user
        session = get_user_session(uid)

        spliter = message.text.split(' ')
        try:
            if spliter and len(spliter) > 2 and spliter[-1].isdigit():
                session['confirmaddress'] = message.text
                with lock:
                    sql.execute(f"UPDATE verifications SET address = ? WHERE id = ?", (session['confirmaddress'], uid))
                    db.commit()
                sendOrderToGroupWithoutPhoto(cid, uid, mid, pickup=False)
            else:
                msg = client.send_message(cid, f'🚫הכתובת לא ברורה לי... אנא רשמו את הכתובת עם מספר בסוף!🚫')
                client.register_next_step_handler(msg, personConfirmNewAddress)
        except:
            msg = client.send_message(cid, f'🚫הכתובת לא ברורה לי... אנא רשמו את הכתובת עם מספר בסוף!🚫')
            client.register_next_step_handler(msg, personConfirmNewAddress)
    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

# Send order details to group without photo
def sendOrderToGroupWithoutPhoto(cid, uid, mid, pickup=False):
    try:
        # Retrieve session for the user
        session = get_user_session(uid)

        # Ensure necessary data is in the session
        confirmname = session.get('confirmname')
        confirmpnumber = session.get('confirmpnumber')
        confirmaddress = session.get('confirmaddress')
        confirmorder = session.get('confirmorder')

        if not confirmorder:
            client.send_message(cid, '🚫 שגיאה במערכת: לא נמצאו פרטי הזמנה 🚫')
            return

        # Extract order details (product name and price) from confirmorder
        iname, iprice = confirmorder.split('_')

        # Get user info from the chat
        user = client.get_chat_member(cid, uid).user

        # Determine the delivery method
        delivery_method = "איסוף עצמי" if pickup else "משלוח"
        profile_url = f"tg://user?id={uid}" if user.username is None else f"https://t.me/{user.username}"

        # Generate reply markup for order confirmation
        markup = generateOrderReplyMarkup(cid, mid, uid, user)

        # Construct the order information message
        orderinfo = (
            f'🪪שם הלקוח: {confirmname}\n'
            f'📰פרטים: {user.full_name}\n'
            f'🔗פרופיל: {profile_url}\n'
            f'🛒מוצר: {iname}\n'
            f'💰מחיר: {iprice}\n'
            f'🛣כתובת: {confirmaddress if not pickup else "N/A"}\n'
            f'☎️פלאפון: {confirmpnumber}\n'
            f'📦שיטת משלוח: {delivery_method}'
        )

        # Send the order info to the RecipeGID group
        client.send_message(
            chat_id=RecipeGID,
            text=orderinfo,
            reply_markup=markup,
            disable_web_page_preview=True
        )

        # Notify the user that their order has been processed
        client.send_message(cid, text='ההזמנה נקלטה במערכת ומחכה לאימות המנהלים!\n\nמיד יפנו אליכם עם פרטים על המשלוח.')
    
        clear_user_session(uid)
    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

# Generate markup for the order confirmation
def generateOrderReplyMarkup(cid, mid, uid, user):
    try:
        sql.execute(f"SELECT photo_message_id FROM verifications WHERE id = {uid}")
        photoMID = sql.fetchone()[0]
        markup = types.InlineKeyboardMarkup()
        acceptBtn = types.InlineKeyboardButton(text='אשר משלוח✅', callback_data=f'acceptorder_{cid}_{mid+1}_{user.id}')
        photoBtn = types.InlineKeyboardButton(text='📸 הצג תמונת אימות', url=f'https://t.me/c/{RecipeGIDorg}/{photoMID}')
        markup.add(acceptBtn)
        markup.add(photoBtn)
        return markup
    except Exception as e:
        raise e

# Step 1: Start order confirmation
def personConfirm1(message):
    try:
        user_id = message.from_user.id
        cid = message.chat.id

        # Start the session for the user
        session = get_user_session(user_id)

        session['cid'] = cid  # Store chat id in session
        
        spliter = message.text.split(' ')
        if len(spliter) > 1:
            session['confirmname'] = message.text  # Store user name in session
            msg = client.send_message(cid, '*מהו מספר הפלאפון שלך?*\n\n(לדוגמא: 0512345678)', parse_mode='Markdown')
            client.register_next_step_handler(msg, personConfirm2)
        else:
            msg = client.send_message(cid, f'🚫השם לא ברור לי... נסו שוב לרשום שם מלא פרטי ושם משפחה🚫')
            client.register_next_step_handler(msg, personConfirm1)

        for i in range(msg.message_id - 1, msg.message_id - 3, -1):
                try:
                    client.delete_message(chat_id=cid, message_id=i)
                except:
                    pass
    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

# Step 2: Get phone number
def personConfirm2(message):
    try:
        user_id = message.from_user.id
        session = get_user_session(user_id)
        cid = session['cid']
        
        if message.text.startswith('05') and len(message.text) == 10:
            session['confirmpnumber'] = message.text  # Store phone number in session
            msg = client.send_message(cid, '*מהי הכתובת אליה תרצו להזמין?*\n\nבמידה ותרצו איסוף יש לרשום "איסוף"\n\n(בפורמט: עיר, רחוב, מספר בית)', parse_mode='Markdown')
            client.register_next_step_handler(msg, personConfirm3)
        else:
            msg = client.send_message(cid, f'🚫המספר לא ברור לי... נסו להתחיל ב"05XXXXXXXX"🚫')
            client.register_next_step_handler(msg, personConfirm2)

        for i in range(msg.message_id - 1, msg.message_id - 3, -1):
                try:
                    client.delete_message(chat_id=cid, message_id=i)
                except:
                    pass
    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

# Step 3: Get address or pickup option
def personConfirm3(message):
    try:
        user_id = message.from_user.id
        session = get_user_session(user_id)
        cid = session['cid']
        
        spliter = message.text.split(' ')
        try:
            if message.text == 'איסוף':
                session['confirmaddress'] = message.text  # Store address in session
                msg = client.send_message(cid, '*שלחו צילום ברור של תעודת זהות או רשיון נהיגה!*', parse_mode='Markdown')
                client.register_next_step_handler(msg, personConfirm4)
            elif int(spliter[len(spliter) - 1]) > 0 and len(spliter) > 2:
                session['confirmaddress'] = message.text  # Store address in session
                msg = client.send_message(cid, '*שלחו צילום ברור של תעודת זהות או רשיון נהיגה!*', parse_mode='Markdown')
                client.register_next_step_handler(msg, personConfirm4)
            else:
                msg = client.send_message(cid, f'🚫הכתובת לא ברורה לי... אנא רשמו את הכתובת עם מספר בסוף או ׳איסוף׳!🚫')
                client.register_next_step_handler(msg, personConfirm3)

            for i in range(msg.message_id - 1, msg.message_id - 3, -1):
                try:
                    client.delete_message(chat_id=cid, message_id=i)
                except:
                    pass
        except:
            msg = client.send_message(cid, f'🚫הכתובת לא ברורה לי... אנא רשמו את הכתובת עם מספר בסוף או ׳איסוף׳!🚫')
            client.register_next_step_handler(msg, personConfirm3)
            for i in range(msg.message_id - 1, msg.message_id - 3, -1):
                try:
                    client.delete_message(chat_id=cid, message_id=i)
                except:
                    pass
    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

# Step 4: Confirm order with ID photo
def personConfirm4(message):
    user_id = message.from_user.id
    session = get_user_session(user_id)
    cid = session['cid']
    mid = message.message_id
    user = message.from_user
    uid = user.id

    try:
        # Assuming 'confirmorder' (name and price) is stored in the user's session
        if 'confirmorder' in session:
            iname = session['confirmorder'].split('_')[0]  # Product name
            iprice = session['confirmorder'].split('_')[1]  # Product price
        else:
            client.send_message(cid, '🚫 שגיאה במערכת: פרטי הזמנה חסרים 🚫')
            return

        if message.photo:
            markup = types.InlineKeyboardMarkup()
            acceptBtn = types.InlineKeyboardButton(text='אשר משלוח✅', callback_data=f'acceptorder_{cid}_{mid + 1}_{uid}')
            declineBtn = types.InlineKeyboardButton(text='לא מעוניין⛔', callback_data=f'cancelorder_{cid}_{mid + 1}')
            profile_url = f"tg://user?id={uid}" if user.username is None else f"https://t.me/{user.username}"
            markup.add(acceptBtn)
            markup.add(declineBtn)

            # Forward the photo to RecipeGID and get the message ID
            forwardMessage = client.forward_message(RecipeGID, cid, message.message_id)

            # Add the shipping method
            delivery_method = "איסוף עצמי" if session['confirmaddress'] == 'איסוף' else "משלוח"

            orderinfo = (
                f'🪪שם הלקוח: {session["confirmname"]}\n'
                f'📰פרטים: {user.full_name}\n'
                f'🔗פרופיל: {profile_url}\n'
                f'🛒מוצר: {iname}\n'
                f'💰מחיר: {iprice}\n'
                f'🛣כתובת: {session["confirmaddress"]}\n'
                f'☎️פלאפון: {session["confirmpnumber"]}\n'
                f'📦שיטת שילוח: {delivery_method}'
            )

            client.send_message(
                chat_id=RecipeGID,
                text=orderinfo,
                reply_markup=markup,
                disable_web_page_preview=True
            )

            # Update the verifications table with the photo message ID and recipe message ID
            sql.execute(f"SELECT * FROM verifications WHERE id = {user.id}")
            isverified = sql.fetchone()
            if isverified is None:
                with lock:    
                    sql.execute(
                        "INSERT INTO verifications (id, username, fullname, pnumber, address, verified, photo_message_id, recipe_message_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (uid, f'{user.username}', session['confirmname'], session['confirmpnumber'], session['confirmaddress'], 0, int(forwardMessage.message_id), int(forwardMessage.message_id + 1)))
                    db.commit()

            # Notify user and delete temporary messages
            msg = client.send_message(cid, text='ההזמנה נקלטה במערכת ומחכה לאימות המנהלים!\n\nמיד יפנו אליכם עם פרטים על המשלוח.')
            for i in range(msg.message_id - 1, msg.message_id - 3, -1):
                try:
                    client.delete_message(chat_id=cid, message_id=i)
                except:
                    pass

            # Clear session when done
            clear_user_session(user_id)

        else:
            msg = client.send_message(cid, f'🚫צריך לשלוח תצלום תעודת זהות או רשיון נהיגה! זה פשוט...🚫')
            client.register_next_step_handler(msg, personConfirm4)
            for i in range(msg.message_id - 1, msg.message_id - 3, -1):
                try:
                    client.delete_message(chat_id=cid, message_id=i)
                except:
                    pass

    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

## Order acception
@client.callback_query_handler(lambda call: call.data.startswith('acceptorder_'))
def acceptOrderCB(call):
    try:
        cid = call.message.chat.id
        mid = call.message.message_id
        user = call.from_user

         # Send approval message to the user in mainCID
        mainCID = int(call.data.split('_')[1])  # Ensure mainCID is correctly extracted as an integer
        mainMID = int(call.data.split('_')[2])
        uid = int(call.data.split('_')[3])

        if call.data.startswith('acceptorder_'):
            # Fetch photo_message_id and verified status
            sql.execute(f"SELECT photo_message_id, verified FROM verifications WHERE id = {uid}")
            result = sql.fetchone()
            print(result)
            
            if result is not None:  # Ensure that the query returned a result
                photoMID, is_verified = result  # Get photo_message_id and verified status

                # Create buttons for photo link and acceptance
                photoBtn = types.InlineKeyboardButton(text='📸 הצג תמונת אימות', url=f'https://t.me/c/{RecipeGIDorg}/{photoMID}')
                markup = types.InlineKeyboardMarkup()
                acceptedBtn = types.InlineKeyboardButton(text=f'המשלוח אושר על ידי {user.username}✅', url=f't.me/{user.username}')
                markup.add(acceptedBtn)
                markup.add(photoBtn)
                client.edit_message_reply_markup(chat_id=RecipeGID, message_id=mid, reply_markup=markup)
                markupMSG = types.InlineKeyboardMarkup()
                msgAdmin = types.InlineKeyboardButton(text=f'פנייה {ADMINtxt}', url=ADMINurl)
                markupMSG.add(msgAdmin)

                if is_verified == 0:
                    with lock:
                        sql.execute("UPDATE users SET verified = 1 WHERE id = ?", (mainCID,))
                        sql.execute("UPDATE verifications SET verified = 1 WHERE id = ?", (mainCID,))
                        db.commit()

                client.send_message(mainCID, 'המשלוח אושר על ידי מנהל - מיד יצרו אתכם קשר✅', reply_markup=markupMSG)
                client.delete_message(mainCID, mainMID)
                client.answer_callback_query(callback_query_id=call.id)

            else:
                client.send_message(cid, '🚫 לא ניתן למצוא את תמונת האימות. אנא בדקו שהמשתמש אומת כראוי 🚫')

    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

## Order cancellation
@client.callback_query_handler(lambda call: call.data.startswith('cancelorder_'))
def cancelOrderCB(call):
    try:
        cid = call.message.chat.id
        mid = call.message.message_id
        mainMID = int(call.data.split('_')[2])
        mainCID = int(call.data.split('_')[1])
        uid = int(call.data.split('_')[3])


        if call.data.startswith('cancelorder_'):
            markup = types.InlineKeyboardMarkup()
            badPhotoBtn = types.InlineKeyboardButton(text='תמונה לא תקינה 📸', callback_data=f'resendphoto_{mainCID}_{mid}')
            unwantedClientBtn = types.InlineKeyboardButton(text='לקוח לא רצוי 🚫', callback_data=f'blockclient_{mainCID}')
            acceptBtn = types.InlineKeyboardButton(text='אשר משלוח✅', callback_data=f'acceptorder_{mainCID}_{mainMID}_{uid}')
            markup.add(badPhotoBtn)
            markup.add(unwantedClientBtn)
            markup.add(acceptBtn)
            client.edit_message_reply_markup(chat_id=cid, message_id=mid, reply_markup=markup)
            client.answer_callback_query(callback_query_id=call.id)
    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.callback_query_handler(lambda call: call.data.startswith('resendphoto_'))
def resendPhoto(call):
    try:
        mainCID = int(call.data.split('_')[1])  # This is the private chat ID
        recipeMID = int(call.data.split('_')[2])  # The message ID in the group where the photo was forwarded

        requestMessage = client.send_message(mainCID, '📸 התמונה לא הייתה תקינה. אנא שלחו שוב תצלום ברור של תעודת זהות או רשיון נהיגה.')
        client.delete_message(mainCID, requestMessage.message_id-1)
        client.register_next_step_handler_by_chat_id(mainCID, handleNewPhoto, recipeMID)
    except Exception as e:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

def handleNewPhoto(message, recipeMID):
    try:
        cid = message.chat.id  # This should be the private chat ID where the user sends the photo

        if message.photo:

            # Forward the new photo to the group and store the new message ID
            # Reply to the original recipe message with the new photo
            newphoto = client.send_photo(
                chat_id=RecipeGID,
                photo=message.photo[-1].file_id,  # Get the best quality photo
                reply_to_message_id=recipeMID  # Reply to the original recipe message
            )
            with lock:
                sql.execute("UPDATE verifications SET photo_message_id = ? WHERE id = ?", (newphoto.message_id, cid))
                db.commit()
            # Delete the forwarded message and the original photo from the user's chat
            client.delete_message(RecipeGID, recipeMID - 1)
            for i in range(message.message_id, message.message_id - 2, -1):
                try:
                    client.delete_message(cid, i)
                except:
                    pass

            # Update the user that the new photo was accepted and sent for review
            client.send_message(cid, text='ההזמנה נקלטה במערכת ומחכה לאימות המנהלים!\n\nמיד יפנו אליכם עם פרטים על המשלוח.')
        else:
            # If the user didn't send a photo, ask them again
            msg = client.send_message(cid, f'🚫צריך לשלוח תצלום תעודת זהות או רשיון נהיגה! זה פשוט...🚫')
            client.register_next_step_handler(msg, handleNewPhoto, recipeMID)
    except Exception as e:
        client.send_message(cid, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

@client.callback_query_handler(lambda call: call.data.startswith('blockclient_'))
def blockClient(call):
    try:
        cid = int(call.data.split('_')[1])
        user_id = call.from_user.id

        with lock:
            sql.execute("UPDATE users SET access = -1 WHERE id = ?", (user_id,))
            db.commit()

        client.send_message(cid, '🚫 המשתמש נחסם וההזמנה בוטלה.')

        client.restrict_chat_member(chat_id=cid, user_id=user_id, can_send_messages=False)

    except Exception as e:
        client.send_message(call.message.chat.id, f'🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫')

# Handler for pagination
@client.callback_query_handler(lambda call: call.data.startswith('verf_page_'))
def paginateVerifications(call):
    page = int(call.data.split('_')[2])
    showVerificationsList(call.message, page=page)


# Handler for selecting a verification
@client.callback_query_handler(lambda call: call.data.startswith('verification_'))
def showVerificationDetails(call):
    try:
        cid = call.message.chat.id
        verification_id = int(call.data.split('_')[1])

        # Fetch verification details
        with lock:
            sql.execute("SELECT id, fullname, photo_message_id FROM verifications WHERE id = ?", (verification_id,))
            verification = sql.fetchone()

        if verification is None:
            client.send_message(cid, "🚫 אימות לא נמצא 🚫")
            return

        verification_id, fullname, photo_message_id = verification
        photo_url = f"https://t.me/c/{RecipeGIDorg}/{photo_message_id}"

        # Create buttons for Edit, Delete, and Back
        markup = types.InlineKeyboardMarkup()
        edit_btn = types.InlineKeyboardButton(text="✏️ ערוך אימות", callback_data=f'edit_verf_{verification_id}')
        delete_btn = types.InlineKeyboardButton(text="❌ מחק אימות", callback_data=f'delete_verf_{verification_id}')
        back_btn = types.InlineKeyboardButton(text="⬅️ חזור", callback_data=f'back_to_verfs')
        markup.add(edit_btn, delete_btn)
        markup.add(back_btn)

        # Send the verification details
        client.edit_message_text(
            chat_id=cid,
            message_id=call.message.message_id,
            text=f"🔍 פרטי אימות: {fullname}\n📸 תמונה: [הצג תמונה]({photo_url})",
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        client.send_message(cid, f"🚫 שגיאת מערכת: {str(e)} לרשימת הפקודות - /help 🚫")


# Handler for editing a verification
@client.callback_query_handler(lambda call: call.data.startswith('edit_verf_'))
def editVerification(call):
    verification_id = int(call.data.split('_')[2])
    # Add your logic to edit the verification details here
    client.send_message(call.message.chat.id, f"עריכת אימות #{verification_id} עדיין לא נתמך.")


# Handler for deleting a verification
@client.callback_query_handler(lambda call: call.data.startswith('delete_verf_'))
def deleteVerification(call):
    verification_id = int(call.data.split('_')[2])

    try:
        # First, fetch the user ID from the verification record before deleting
        with lock:
            sql.execute("SELECT id FROM verifications WHERE id = ?", (verification_id,))
            user_id = sql.fetchone()

        if user_id is None:
            client.send_message(call.message.chat.id, f"🚫 אימות #{verification_id} לא נמצא.")
            return

        # Delete the verification from the database
        with lock:
            sql.execute("DELETE FROM verifications WHERE id = ?", (verification_id,))
            db.commit()

        # Set the user's 'verified' status to 0 in the 'users' table
        with lock:
            sql.execute("UPDATE users SET verified = 0 WHERE id = ?", (user_id[0],))
            db.commit()

        # Notify the user and refresh the list
        client.send_message(call.message.chat.id, f"✅ אימות #{verification_id} נמחק בהצלחה, והמשתמש מחדש.")
        showVerificationsList(call.message)

    except Exception as e:
        client.send_message(call.message.chat.id, f"🚫 שגיאת מערכת: {str(e)}")