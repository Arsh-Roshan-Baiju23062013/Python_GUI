import tkinter as tk
from tkinter import scrolledtext, messagebox
import google.generativeai as genai
import json
import os

USER_DB_FILE = "user_db.json"

genai.configure(api_key="")
model = genai.GenerativeModel("gemini-3.5-flash")

username = ""
chats_data = {}        
current_chat_id = None 

def load_user_database():
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, "r") as file:
                return json.load(file)
        except Exception:
            return {}
    return {}

def save_user_database(database):
    try:
        with open(USER_DB_FILE, "w") as file:
            json.dump(database, file, indent=4)
    except Exception as e:
        messagebox.showerror("Database Error", f"Could not save user data: {e}")

user_database = load_user_database()

def sign_up():
    username_input = auth_user_entry.get().strip()
    password_input = auth_pass_entry.get().strip()
    
    if not username_input or not password_input:
        messagebox.showwarning("Incomplete Fields", "Please enter both a username and a password.")
        return
        
    if username_input in user_database:
        messagebox.showerror("Error", "Username already exists! Please try another one.")
    else:
        user_database[username_input] = password_input
        save_user_database(user_database)  # Save permanently to file
        messagebox.showinfo("Success", f"Account successfully created for '{username_input}'!")
        auth_user_entry.delete(0, tk.END)
        auth_pass_entry.delete(0, tk.END)

def sign_in():
    global username
    username_input = auth_user_entry.get().strip()
    password_input = auth_pass_entry.get().strip()
    
    if username_input in user_database and user_database[username_input] == password_input:
        username = username_input
        messagebox.showinfo("Success", f"Welcome back, {username_input}!")
        screen_auth.destroy()
        launch_main_chat_screen()
    else:
        messagebox.showerror("Access Denied", "Invalid username or password.")


def launch_main_chat_screen():
    global Input, output_text, model, history_listbox, chats_data, current_chat_id

    screen_1 = tk.Tk()
    screen_1.title("RoshanAI")
    screen_1.geometry("950x650")
    screen_1.config(background="DeepSkyBlue2")


    frame_chats = tk.Frame(screen_1, bg="dark green", width=250)
    frame_chats.pack(side="left", fill="y", padx=10, pady=10)
    frame_chats.pack_propagate(False)

    title_chat_history = tk.Label(
        frame_chats,
        text="Chat History",
        fg="white",
        bg="dark green",
        font=("Times New Roman", 20, "bold")
    )
    title_chat_history.pack(padx=10, pady=10)

    history_container = tk.Frame(frame_chats, bg="dark green")
    history_container.pack(fill="both", expand=True, padx=10, pady=5)

    history_listbox = tk.Listbox(
        history_container, 
        bg="emerald green", 
        fg="white", 
        selectbackground="green yellow", 
        selectforeground="black",
        font=("Arial", 11),
        bd=0,
        highlightthickness=0
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
        chat_count = len(chats_data) + 1
        new_chat_name = f"Chat Session {chat_count}"
        
        chats_data[new_chat_name] = f"--- Started {new_chat_name} ---\n\n"
        history_listbox.insert(tk.END, new_chat_name)
       
        history_listbox.selection_clear(0, tk.END)
        history_listbox.selection_set(tk.END)
        current_chat_id = new_chat_name
        
        load_selected_chat()

    def delete_selected_chat():
        global current_chat_id
        selection = history_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Missing", "Please select a chat thread to delete.")
            return
            
        chat_title = history_listbox.get(selection[0])
        if messagebox.askyesno("Confirm Deletion", f"Permanently wipe out '{chat_title}'?"):
            history_listbox.delete(selection[0])
            del chats_data[chat_title]
            
            output_text.config(state="normal")
            output_text.delete(1.0, tk.END)
            output_text.config(state="disabled")
            current_chat_id = None

    new_chat_btn = tk.Button(
        sidebar_btn_frame, text="New Chat", bg="green yellow", fg="black",
        font=("Arial", 10, "bold"), width=10, command=create_new_chat
    )
    new_chat_btn.pack(side="left", padx=10, expand=True)

    delete_chat_btn = tk.Button(
        sidebar_btn_frame, text="Delete Chat", bg="IndianRed1", fg="black",
        font=("Arial", 10, "bold"), width=10, command=delete_selected_chat
    )
    delete_chat_btn.pack(side="right", padx=10, expand=True)

    frame_1 = tk.Frame(screen_1, bg="DeepSkyBlue3", width=450)
    frame_1.pack(side="left", expand=True, fill="both")

    title = tk.Label(
        frame_1, text="Roshan AI", bg="DeepSkyBlue3", fg="black", font=("Cambria", 40, "bold")
    )
    title.pack()

    output_frame = tk.Frame(frame_1, bg="DeepSkyBlue2", height=200)
    output_frame.pack(fill="x", padx=20, pady=10)

    output_text = scrolledtext.ScrolledText(
        output_frame, bg="white", fg="black", font=("Cascadia Code", 12), state="disabled"
    )
    output_text.pack(fill="x")

    input_frame = tk.Frame(frame_1, bg="DeepSkyBlue2")
    input_frame.pack(side="bottom", fill="x", pady=10)

    Input = tk.Entry(
        input_frame, bg="green yellow", fg="black", font=("Cascadia Code", 14), width=45
    )
    Input.pack(side="left", padx=(30, 10), ipady=5)

    def send_message():
        global current_chat_id
        if current_chat_id is None:
            create_new_chat()

        message = Input.get()
        if message.strip() != "":
            output_text.config(state="normal")
            
            append_str = f"{username}: {message}\n"
            
            try:
                response = model.generate_content(message)
                reply = response.text
            except Exception as e:
                reply = f"Error: {e}"
            
            append_str += f"\nRoshanAI: {reply}\n\n"
            
            chats_data[current_chat_id] += append_str
            
            # Rerender viewport display area updates
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
            chats_data[current_chat_id] = ""

    send_btn = tk.Button(
        input_frame, bg="ivory2", text="SEND", activebackground="ivory4",
        bd=0, cursor="hand2", command=send_message, font=("Arial", 10, "bold")
    )
    send_btn.pack(side="left", padx=5)
    
    clear_btn = tk.Button(
        input_frame, text="CLEAR", bg="IndianRed1", activebackground="red2",
        bd=0, cursor="hand2", command=clear_chat, font=("Arial", 10, "bold")
    )
    clear_btn.pack(side="left", padx=5)

    Input.bind("<Return>", lambda event: send_message())
    
    create_new_chat()
    screen_1.mainloop()


screen_auth = tk.Tk()
screen_auth.title("RoshanAI - Authentication")
screen_auth.geometry("400x300")
screen_auth.mainloop()

