import sqlite3
import random
import json
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.db_path = 'datastore.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                              (user_id TEXT, name TEXT, email TEXT, phone TEXT,type TEXT,code TEXT,status TEXT,next_date TEXT, password TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS models
                              (model_id TEXT,user_id TEXT,name TEXT,table_name TEXT,model TEXT,n INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS chats
                              (chat_id TEXT,user_id TEXT,name TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                              (chat_id TEXT,user_id TEXT,user TEXT,system TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS media
                              (chat_id TEXT,user_id TEXT,file TEXT,content TEXT)''')

        conn.commit()

    def add_user(self, name, email, phone,atype,code, password):
        user_id = "user" + str(random.randint(1000, 9999))
        status="trial"
        current_datetime = datetime.now()
        nextd=current_datetime + timedelta(days=7)
        next_date=str(nextd.date())
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email=?", (email,))
                existing_user = cursor.fetchone()
                if existing_user:
                    return {"status": "Email already exists"}
                cursor.execute("INSERT INTO users (user_id, name, email, phone, type, code, status, next_date, password) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                               (user_id, name, email, phone,atype, code, status, next_date, password))
                conn.commit()
                return {"status": "success","user":user_id}
        except Exception as e:
            return {"status": "Error: " + str(e)}

    def login(self, email, password):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
                user = cursor.fetchone()
                if user:
                    user_id = user[0]
                    next_billing_date = user[7]  # Assuming the next_billing_date is at the 6th index
                    current_date = datetime.now().date()
                    
                    if current_date < datetime.strptime(next_billing_date, "%Y-%m-%d").date():
                        return {"status": "success", "user": user_id}
                    else:
                        return {"status": "billing required"}
                else:
                    return {"status": "Invalid email or password"}
        except Exception as e:
            return {"status": "Error: " + str(e)}

    def adminlogin(self, email, password):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
                user = cursor.fetchone()
                if user:
                	user_id = user[0]
                	return {"status": "success","user":user_id}
                else:
                    return {"status": "Invalid email or password"}
        except Exception as e:
            return {"status": "Error: " + str(e)}

    def passchange(self, user_id, oldpassword, newpassword):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE user_id=? AND password=?", (user_id, oldpassword))
                user = cursor.fetchone()
                if user:
                    cursor.execute("UPDATE users SET password=? WHERE user_id=?", (newpassword, user_id))
                    conn.commit()
                    return {"status": "success"}
                else:
                    return {"status": "Invalid Password"}
        except Exception as e:
            return {"status": "Error: " + str(e)}

    def subscribe_user(self, user_id, next_date):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET next_date=?, status='Subscribed' WHERE user_id=?", (next_date, user_id))
                conn.commit()
                return {'status':'success'}
        except Exception as e:
            return {"status": "Error: " + str(e)}

    def subscribe_org(self, code, next_date):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET next_date=?, status='Subscribed' WHERE code=?", (next_date, code))
                conn.commit()
                return {'status':'success'}
        except Exception as e:
            return {"status": "Error: " + str(e)}

    def user_profile(self,user_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
                user = cursor.fetchone()
                if user:
                    #user_id TEXT, name TEXT, email TEXT, phone TEXT,type TEXT,code TEXT,status TEXT,next_date TEXT
                    return {"status":"success","name":user[1],"email":user[2],"phone":user[3],"type":user[4],"code":user[5],"state":user[6],"next_date":user[7]}
                else:
                    return {"status": "Invalid email or password"}
        except Exception as e:
            print("Error on loading profile : " + str(e))
            return {"status": "Error: " + str(e)}

    def profiles(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
                users = cursor.fetchall()
                users_=[]
                for user in users:
                    #user_id TEXT, name TEXT, email TEXT, phone TEXT,type TEXT,code TEXT,status TEXT,next_date TEXT
                    users_.append({"user_id":user[0],"name":user[1],"email":user[2],"phone":user[3],"type":user[4],"code":user[5],"state":user[6],"next_date":user[7]})

                return users_
        except Exception as e:
            print("Error on loading profiles : " + str(e))
            return []

    def deli_user(self, user_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
                conn.commit()
                return {"status":"success"}
        except Exception as e:
            return {"status":"Error: "+str(e)}

    def add_model(self,user_id,name,table_name,model):
        model_id = "model" + str(random.randint(1000, 9999))
        n=random.randint(100,999)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM models WHERE name=? AND user_id=?", (name,user_id))
                existing_model = cursor.fetchone()
                if existing_model:
                    return {"status": "Model already exists"}
                cursor.execute("INSERT INTO models (model_id,user_id, name,table_name,model,n) VALUES (?, ?, ?, ?, ?,0)",
                               (model_id,user_id, name,table_name,model))
                conn.commit()
            return {"status": "success"}
        except Exception as e:
            return {"status": "Error: " + str(e)}

    def models(self, user_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM models WHERE user_id=? ", (user_id,))
                models_pre = cursor.fetchall()
                models=[]
                for model in models_pre:
                	models.append({"name":model[2],"tool":model[4],"table":model[3],'model_id':model[0]})

                return models
        except Exception as e:
            print("error: "+str(e))
            return []

    def model(self, model_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM models WHERE model_id=? ", (model_id,))
                model = cursor.fetchone()
                if model:
                    return {"name":model[2],"tool":model[4],"table":model[3],'model_id':model[0]}
                else:
                    print("No row")
                    return {}
        except Exception as e:
            print("Error: "+str(e))
            return {}

    def delete_table(self, table_name):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS " + table_name)
                return {"status":"success"}
        except Exception as e:
            return {"status":"Error: "+str(e)}

    def deli_model(self, model_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM models WHERE model_id=?", (model_id,))
                conn.commit()
                return {"status":"success"}
        except Exception as e:
            return {"status":"Error: "+str(e)}

    #add new chat
    def add_chat(self, user_id,name):
        chat_id = user_id + str(random.randint(1000, 9999))
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO chats (chat_id,user_id, name) VALUES (?, ?, ?)",
                               (chat_id,user_id, name))
                conn.commit()
            return {"status": "success","chat":chat_id}
        except Exception as e:
            return {"status": "Error: " + str(e)}

    #view all chats belonging to a user
    def chats(self, user_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chats WHERE user_id=? ", (user_id,))
                chats_pre = cursor.fetchall()
                chats=[]
                for chat in chats_pre:
                    chats.append({"chat_id":chat[0],"name":chat[2]})

                return chats
        except Exception as e:
            print("error: "+str(e))
            return []

    #view all chats belonging to a user
    def allchats(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chats")
                chats_pre = cursor.fetchall()
                chats=[]
                for chat in chats_pre:
                    chats.append({"chat_id":chat[0],"user_id":chat[1],"name":chat[2]})

                return chats
        except Exception as e:
            print("error: "+str(e))
            return []

    #delete a chat, including all its messages
    def deli_chat(self, chat_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chats WHERE chat_id=?", (chat_id,))
                cursor.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
                cursor.execute("DELETE FROM media WHERE chat_id=?", (chat_id,))
                conn.commit()
                return {"status":"success"}
        except Exception as e:
            return {"status":"Error: "+str(e)}

    #add new message
    def add_message(self,chat_id,user_id,user,system):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO messages (chat_id,user_id,user,system) VALUES (?, ?, ?,?)",
                               (chat_id,user_id,user,system))
                conn.commit()
            return {"status": "success","chat":chat_id}
        except Exception as e:
            return {"status": "Error: " + str(e)}

    #view all messages belonging to a chat
    def messages(self, chat_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM messages WHERE chat_id=? ", (chat_id,))
                messages_pre = cursor.fetchall()
                messages=[]
                for message in messages_pre:
                    msg=message[2]
                    msg=msg.replace('\n', '')
                    msg=json.loads(msg)
                    messages.append({"system":msg,"user":message[3]})

                return messages
        except Exception as e:
            print("error: "+str(e))
            return []

    #add new media file
    def add_file(self, chat_id,user_id,file,content):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO media (chat_id,user_id, file,content) VALUES (?, ?, ?, ?)",
                               (chat_id,user_id, file, content))
                conn.commit()
            return {"status": "success","chat":chat_id}
        except Exception as e:
            return {"status": "Error: " + str(e)}

    #view all chats belonging to a user
    def files(self, chat_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM media WHERE chat_id=? ", (chat_id,))
                files_pre = cursor.fetchall()
                files=[]
                for file in files_pre:
                    file.append({"file":file[2],"content":file[3]})

                return files
        except Exception as e:
            print("error: "+str(e))
            return []

    #delete a chat, including all its messages
    def deli_file(self, chat_id, file):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM media WHERE chat_id=? AND file=?", (chat_id,file))
                conn.commit()
                return {"status":"success"}
        except Exception as e:
            return {"status":"Error: "+str(e)}

    #view file
    def file(self, chat_id, file):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM media WHERE chat_id=? AND file=?", (chat_id, file))
                file = cursor.fetchone()
                if file:
                    content = file[3]
                    return {"status": "success","content":content}
                else:
                    return {"status":"none"}
        except Exception as e:
            return {"status": "Error: " + str(e)}
