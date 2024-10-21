# **Telegram Bot for User and Product Management**

## **Project Overview**

This **Telegram Bot** is designed for managing users, products, and categories within a chat-based interface. Built using the **TeleBot API** and **SQLite3**, this bot allows administrators to add, remove, and edit users, products, and categories within a Telegram group or private chat. The bot features user authentication, role-based access, and interaction with an SQLite database for persistent storage. 

It also includes commands for regular users to interact with the bot, such as viewing available products or requesting help. 

The project is perfect for anyone looking to build a Telegram bot with advanced functionality, including database integration and user management.

---

## **Features**

- **User Management**: Add, edit, block, and unblock users.
- **Product Management**: Add, edit, and remove products and categories.
- **Role-Based Access**: Administrator-level commands restricted to specific users.
- **Help Command**: Provides a list of available commands depending on the user’s role.
- **Database Integration**: Persistent storage using SQLite3.
- **Logging**: Automatic logging of bot actions.

---

## **Tech Stack**

- **Python**: Primary programming language.
- **TeleBot**: API for Telegram bot development.
- **SQLite3**: Lightweight database for storing users, products, and categories.
- **Threading**: Ensures non-blocking execution of commands.
- **Logging**: Monitors and logs bot activity.

---

## **Commands List**

### **User Commands**
- `/start`: Start a new conversation with the bot.
- `/menu`: Access the main menu.
- `/help`: Display available commands based on user permissions.
- `/clear`: Delete all messages in the chat.

### **Admin Commands**
*(For users with admin access only)*
- `/users`: View all registered users.
- `/edituser`: Edit user information.
- `/block`: Block a user.
- `/unblock`: Unblock a user.
- `/addcat`: Add a new product category.
- `/removecat`: Remove a product category.
- `/editcat`: Edit a product category.
- `/addprod`: Add a new product.
- `/removeprod`: Remove a product.
- `/editprod`: Edit a product.

---

## **Installation and Setup**

### **Prerequisites**

Before you begin, ensure you have the following installed:

- **Python 3.x**: [Download Python](https://www.python.org/downloads/)
- **SQLite3**: This is often bundled with Python but can also be installed separately.
- **A Telegram Bot Token**: You can obtain this by creating a bot via the BotFather on Telegram.

### **Steps to Run the Bot**

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/levelakc/telegram-shopbot.git
   cd telegram-bot
