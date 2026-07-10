import tkinter as tk
from tkinter import scrolledtext, messagebox
import google.generativeai as genai
import hashlib
import json
import os
import datetime
import socket
import threading
import webbrowser
import http.server
import urllib.parse
import requests

#paths
script_direct=os.path.dirname(os.path.abspath(__file__))
config_file=os.path.join(script_direct, "config.json")
USER_DB_FILE = os.path.join(script_direct, "user_db.json" )
print(script_direct)
default_config={
    "geminiAPIKey": "",
  "firebaseApiKey": "",
  "projectId": "",
  "firebasedatabaseURL": "",
  "googleClientId": "",
  "googleClientSecret": "",
  "geminimodel": "gemini-2.5-flash"    
}

def load_config():
    global model
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                data = json.load(f)
                # Update default_config with the data read from config.json
                default_config.update(data)
        except Exception as e:
            messagebox.showerror("Config Error", f"Could not read config file: {e}")
            return

    api_key = default_config.get("geminiAPIKey")
    model_name = default_config.get("geminimodel", "gemini-2.5-flash")

    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
    else:
        messagebox.showwarning("API Key Missing", "Gemini API Key not found in configuration.")

username        = ""
chats_data      = {}        
chat_sessions   = {}       
current_chat_id = None

def hash_password(pw: str) -> str:           
    return hashlib.sha256(pw.encode()).hexdigest()

def load_user_database():
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_user_database(database):
    try:
        with open(USER_DB_FILE, "w") as f:
            json.dump(database, f, indent=4)
    except Exception as e:
        messagebox.showerror("Database Error", f"Could not save user data: {e}")
class FirebaseClient:
    def __init__(self, api_key, project_id, database_url=None):
        self.api_key=api_key
        self.project_id=project_id
        self.database_url=database_url or f"https://{project_id}-default-rtdb.firebaseio.com"
        if not self.database_url.endswith("/"):
            self.database_url+="/"
        self.id_token=None
        self.local_id=None
        self.email=None
    def is_configured(self):
        return bool(self.api_key and self.project_id)
    def sign_up(self, email, password):
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
        payload={"email": email,
                 "password":password,
                 "returnSecureToken": True}
        r=requests.post(url, json=payload)
        r.raise_for_status()
        data=r.json()
        self.id_token = data["idToken"]
        self.local_id=data["localId"]
        self.email=data["email"]
        return data
    def sign_in(self, email, password):
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
        payload={"email": email,
                 "password":password,
                 "returnSecureToken": True}
        r=requests.post(url, json=payload)
        r.raise_for_status()
        data=r.json()
        self.id_token = data["idToken"]
        self.local_id=data["localId"]
        self.email=data["email"]
        return data
    def sign_in_with_google_token(self, google_id_token, redirect_port):
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdP?key={self.api_key}"
        payload = {
            "postBody": f"id_token={google_id_token}&providerId=google.com",
            "requestUri": f"http://localhost:{redirect_port}",
            "returnSecureToken": True
        }
        r=requests.post(url, json=payload)
        r.raise_for_status()
        data=r.json()
        self.id_token = data["idToken"]
        self.local_id=data["localId"]
        self.email=data["email"]
        return data    
    def load_chats(self):
        url = f"{self.database_url}users/{self.local_id}/chats.json?auth={self.id_token}"
        r=requests.get(url)
        r.raise_for_status()
        return r.json() or{}
    def create_chat(self, chat_id, title, created_at):
        url = f"{self.database_url}users/{self.local_id}/chats/{chat_id}/metadata.json?auth={self.id_token}"
        payload={
            "title": title,
            "created_at":created_at
        }
        r=requests.put(url, json=payload)
        r.raise_for_status()
    def append_message(self, chat_id, sender, message, timestamp):
        url = f"{self.database_url}users/{self.local_id}/chats/{chat_id}/messages.json?auth={self.id_token}"
        payload={
            "sender": sender,
            "message":message,
            "timestamp":timestamp
                          }
        r=requests.post(url, json=payload)
        r.raise_for_status()
    def delete_chat(self, chat_id):
        url = f"{self.database_url}users/{self.local_id}/chats/{chat_id}.json?auth={self.id_token}"
        r=requests.delete(url)
        r.raise_for_status()

#Google OAuth Loopback -> 

class OAuthCallBackHandler(http.server.BaseH11PRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        query=urllib.parse.urlparse(self.path).query
        params=urllib.parse.parse_qs(query)
        if "code" in params:
            self.server.auth_code = params["code"][0]
            self.wfile.write(b"<html><body style='font-family:sans-serif;text-align:center;padding-top:50px;'>"
                             b"<h1>RoshanAI Authentication Successful!</h1>"
                             b"<p>You can close this tab and return to the application.</p>"
                             b"</body></html>")
        else:
            self.wfile.write(b"<html><body style='font-family:sans-serif;text-align:center;padding-top:50px;'>"
                             b"<h1>Authentication Failed</h1>"
                             b"<p>Authorization code not found.</p>"
                             b"</body></html>")
    def log_message(self, format, *args):
        pass
def find_free_port():
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", 0))
    port = s.getsockname()[1]
    s.close()
    return port

class StorageManager:
    def __init__(self, local_username=None, firebase_client=None):
        self.local_username=local_username
        self.firebase_client=firebase_client
        self.is_firebase=firebase_client is not None

    def get_display_name(self):
        if self.is_firebase:
            return self.firebase_client.email or "Cloud User"
        return self.local_username
    def load_chats(self):
        if self.is_firebase:
            try:
                return self.firebase_client.load_chats()
            except Exception as e:
                messagebox.showerror("Error", f"FAILED TO LOAD CHATS FROM FIREBAE: {e}")
                return{}
        else:
            local_file = os.path.join(LOCAL_CHATS_DIR, f"{self.local_username}_chats.json")
            if os.path.exists(local_file):
                try:
                    with open(local_file, "r") as f:
                        return json.load(f)
                except Exception:
                    return{}
                return{}
    def save_local_chats(self, chats):
        if not self.is_firebase:
            local_file=os.path.join(LOCAL_CHATS_DIR, f"{self.local_username}_chats.json")
            try:
                with open(local_file, "w") as f:
                    json.dump(chats, f, indent=4)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save local chats{e}")
    def create_chat(self, chat_id, title, created_at):
        if self.is_firebase:
            try:
                self.firebase_client.create_chat(chat_id, title, created_at)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create chat in Firebase{e}")
        else:
            chats=self.load_chats()
            chats[chat_id]={
                "metadata":{"title":title, "created_at":created_at},
                "messages":{}
            }
            self.save_local_chats(chats)
    def append_message(self, chat_id, sender, message, timestamp):
        if self.is_firebase:
            try:
                self.firebase_client.append_message(chat_id, sender, message, timestamp)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create save message in Firebase{e}")
        else:
            chats=self.load_chats()
            if chat_id not in chats:
                chats[chat_id]={
                    "metadata":{"title":chat_id, "created_at":timestamp},
                    "messages":{}
                }
            msg_id=f"msg_{int(datetime.datetime.now().timestamp()*1000)}"
            if "messages" not in chats[chat_id] or not isinstance(chats[chat_id]["messages"], dict):
                chats[chat_id]["messages"] = {}
            chats[chat_id]["messages"][msg_id] = {
                "sender": sender,
                "message": message,
                "timestamp": timestamp
            }
            self.save_local_chats(chats)
    def delete_chat(self, chat_id):
        if self.is_firebase:
            try:
                self.firebase_client.delete_chat(chat_id)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete chat from Firebase: {e}")
        else:
            chats = self.load_chats()
            if chat_id in chats:
                del chats[chat_id]
                self.save_local_chats(chats)

user_database = load_user_database()

def sign_up():
    username_input = auth_user_entry.get().strip()
    password_input = auth_pass_entry.get().strip()

    if not username_input or not password_input:
        messagebox.showwarning("Incomplete Fields", "Please enter both a username and password.")
        return

    if username_input in user_database:
        messagebox.showerror("Error", "Username already exists! Please try another one.")
    else:
        user_database[username_input] = hash_password(password_input)
        save_user_database(user_database)
        messagebox.showinfo("Success", f"Account created for '{username_input}'!")
        auth_user_entry.delete(0, tk.END)
        auth_pass_entry.delete(0, tk.END)


def sign_in():
    global username
    username_input = auth_user_entry.get().strip()
    password_input = auth_pass_entry.get().strip()

    if username_input in user_database and \
       user_database[username_input] == hash_password(password_input):
        username = username_input
        messagebox.showinfo("Success", f"Welcome back, {username_input}!")
        screen_auth.destroy()
        launch_main_chat_screen()
    else:
        messagebox.showerror("Access Denied", "Invalid username or password.")



def launch_main_chat_screen():
    global Input, output_text, history_listbox, chats_data, current_chat_id

    screen_1 = tk.Tk()
    screen_1.title("RoshanAI")
    screen_1.geometry("950x650")
    screen_1.config(background="DeepSkyBlue2")
    frame_chats = tk.Frame(screen_1, bg="dark green", width=250)
    frame_chats.pack(side="left", fill="y", padx=10, pady=10)
    frame_chats.pack_propagate(False)

    tk.Label(
        frame_chats, text="Chat History",
        fg="white", bg="dark green", font=("Times New Roman", 20, "bold")
    ).pack(padx=10, pady=10)

    history_container = tk.Frame(frame_chats, bg="dark green")
    history_container.pack(fill="both", expand=True, padx=10, pady=5)

    history_listbox = tk.Listbox(
        history_container,
        bg="dark green",            
        fg="white",
        selectbackground="green yellow",
        selectforeground="black",
        font=("Arial", 11),
        bd=0, highlightthickness=0
    )
    history_listbox.pack(fill="both", expand=True, side="left")

    scrollbar = tk.Scrollbar(history_container, orient="vertical", command=history_listbox.yview)
    scrollbar.pack(side="right", fill="y")
    history_listbox.config(yscrollcommand=scrollbar.set)

    sidebar_btn_frame = tk.Frame(frame_chats, bg="dark green")
    sidebar_btn_frame.pack(fill="x", side="bottom", pady=15)

    def load_selected_chat(event=None):
        global current_chat_id
        selection = history_listbox.curselection()
        if not selection:
            return
        chat_title = history_listbox.get(selection[0])
        current_chat_id = chat_title
        output_text.config(state="normal")
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, chats_data[current_chat_id])
        output_text.config(state="disabled")
        output_text.yview(tk.END)

    history_listbox.bind("<<ListboxSelect>>", load_selected_chat)

    def create_new_chat():
        global current_chat_id
        chat_count   = len(chats_data) + 1
        new_chat_name = f"Chat Session {chat_count}"

        chats_data[new_chat_name]    = f"--- Started {new_chat_name} ---\n\n"
        chat_sessions[new_chat_name] = model.start_chat(history=[])  # FIX #2: fresh session

        history_listbox.insert(tk.END, new_chat_name)
        history_listbox.selection_clear(0, tk.END)
        history_listbox.selection_set(tk.END)
        current_chat_id = new_chat_name
        load_selected_chat()

    def delete_selected_chat():
        global current_chat_id
        selection = history_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Missing", "Please select a chat to delete.")
            return
        chat_title = history_listbox.get(selection[0])
        if messagebox.askyesno("Confirm Deletion", f"Permanently delete '{chat_title}'?"):
            history_listbox.delete(selection[0])
            del chats_data[chat_title]
            del chat_sessions[chat_title]           # FIX #2: clean up session too
            output_text.config(state="normal")
            output_text.delete(1.0, tk.END)
            output_text.config(state="disabled")
            current_chat_id = None

    tk.Button(
        sidebar_btn_frame, text="New Chat", bg="green yellow", fg="black",
        font=("Arial", 10, "bold"), width=10, command=create_new_chat
    ).pack(side="left", padx=10, expand=True)

    tk.Button(
        sidebar_btn_frame, text="Delete Chat", bg="IndianRed1", fg="black",
        font=("Arial", 10, "bold"), width=10, command=delete_selected_chat
    ).pack(side="right", padx=10, expand=True)

    frame_1 = tk.Frame(screen_1, bg="DeepSkyBlue3", width=450)
    frame_1.pack(side="left", expand=True, fill="both")

    tk.Label(
        frame_1, text="Roshan AI", bg="DeepSkyBlue3", fg="black",
        font=("Cambria", 40, "bold")
    ).pack()

    output_frame = tk.Frame(frame_1, bg="DeepSkyBlue2", height=200)
    output_frame.pack(fill="both", expand=True, padx=20, pady=10)

    output_text = scrolledtext.ScrolledText(
        output_frame, bg="white", fg="black",
        font=("Cascadia Code", 12), state="disabled"
    )
    output_text.pack(fill="both", expand=True)

    input_frame = tk.Frame(frame_1, bg="DeepSkyBlue2")
    input_frame.pack(side="bottom", fill="x", pady=10)

    Input = tk.Entry(
        input_frame, bg="green yellow", fg="black",
        font=("Cascadia Code", 14), width=45
    )
    Input.pack(side="left", padx=(30, 10), ipady=5)

    def send_message():
        global current_chat_id
        if current_chat_id is None:
            create_new_chat()

        message = Input.get().strip()
        if not message:
            return

        output_text.config(state="normal")
        try:
            reply = chat_sessions[current_chat_id].send_message(message).text
        except Exception as e:
            reply = f"Error: {e}"

        append_str = f"{username}: {message}\n\nRoshanAI: {reply}\n\n"
        chats_data[current_chat_id] += append_str
        output_text.insert(tk.END, append_str)
        output_text.config(state="disabled")
        output_text.yview(tk.END)
        Input.delete(0, tk.END)

    def clear_chat():
        global current_chat_id
        output_text.config(state="normal")
        output_text.delete(1.0, tk.END)
        output_text.config(state="disabled")
        if current_chat_id:
            chats_data[current_chat_id]    = ""
            chat_sessions[current_chat_id] = model.start_chat(history=[]) 

    tk.Button(
        input_frame, text="SEND", bg="ivory2", activebackground="ivory4",
        bd=0, cursor="hand2", command=send_message, font=("Arial", 10, "bold")
    ).pack(side="left", padx=5)

    tk.Button(
        input_frame, text="CLEAR", bg="IndianRed1", activebackground="red2",
        bd=0, cursor="hand2", command=clear_chat, font=("Arial", 10, "bold")
    ).pack(side="left", padx=5)

    Input.bind("<Return>", lambda event: send_message())

    create_new_chat()
    screen_1.mainloop()


screen_auth = tk.Tk()
screen_auth.title("RoshanAI - Authentication")
screen_auth.geometry("400x300")
screen_auth.config(bg="DeepSkyBlue2")
screen_auth.resizable(False, False)

tk.Label(screen_auth, text="RoshanAI", bg="DeepSkyBlue2",
         font=("Cambria", 28, "bold")).pack(pady=(20, 5))

tk.Label(screen_auth, text="Username:", bg="DeepSkyBlue2",
         font=("Arial", 11)).pack()
auth_user_entry = tk.Entry(screen_auth, font=("Arial", 12), width=25)
auth_user_entry.pack(pady=(2, 8))

tk.Label(screen_auth, text="Password:", bg="DeepSkyBlue2",
         font=("Arial", 11)).pack()
auth_pass_entry = tk.Entry(screen_auth, font=("Arial", 12), width=25, show="*")
auth_pass_entry.pack(pady=(2, 15))

btn_frame = tk.Frame(screen_auth, bg="DeepSkyBlue2")
btn_frame.pack()
tk.Button(btn_frame, text="Sign In", command=sign_in,
          font=("Arial", 11, "bold"), bg="green yellow", width=10).pack(side="left", padx=10)
tk.Button(btn_frame, text="Sign Up", command=sign_up,
          font=("Arial", 11, "bold"), bg="ivory2", width=10).pack(side="left", padx=10)
tk.Button(btn_frame, text="Sign In with Google", command=sign_in,
          font=("Arial", 11, "bold"), bg="green2", width=20).pack(padx=10)


load_config()


user_database = load_user_database()

auth_pass_entry.bind("<Return>", lambda e: sign_in())

screen_auth.mainloop()
