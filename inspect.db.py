cursor.execute("PRAGMA table_info(chat_room);")
columns_info = cursor.fetchall()
print("Chat Room Table Columns:")
for column in columns_info:
    print(column)
