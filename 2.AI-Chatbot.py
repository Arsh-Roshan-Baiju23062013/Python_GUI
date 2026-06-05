import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
from PIL import Image, ImageTk
import google.generativeai as genai
genai.configure(api_key="")
model=genai.GenerativeModel("gemini-3.5-flash")

user_database = {}

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
        messagebox.showinfo("Success", f"Account successfully created for '{username_input}'!")
        auth_user_entry.delete(0, tk.END)
        auth_pass_entry.delete(0, tk.END)

def sign_in():
    global username
    username_input = auth_user_entry.get().strip()
    password_input = auth_pass_entry.get().strip()
    
    if username_input in user_database and user_database[username_input] == password_input:
        messagebox.showinfo("Success", f"Welcome back, {username_input}!")
        screen_auth.destroy()
        launch_main_chat_screen()
    else:
        messagebox.showerror("Access Denied", "Invalid username or password.")

def launch_main_chat_screen():
    global Input, output_text, model


    screen_1 = tk.Tk()
    screen_1.title("RoshanAI")
    screen_1.geometry("900x650")
    screen_1.config(background="DeepSkyBlue2")

    try:
        img = Image.open("Send_Button-removebg-preview.png")
        img = img.resize((30, 30))
        icon = ImageTk.PhotoImage(img)
        Icon_label = tk.Label(screen_1, bg="DeepSkyBlue2", image=icon)
        # Keep a reference to prevent garbage collection
        Icon_label.image = icon 
        Icon_label.pack(pady=1)
    except Exception:
        pass

    frame_1 = tk.Frame(screen_1, bg="DeepSkyBlue3")
    frame_1.pack(fill="x")

    title = tk.Label(
        frame_1,
        text="Roshan AI",
        bg="DeepSkyBlue3",
        fg="black",
        font=("Cambria", 40, "bold")
    )
    title.pack()

    output_frame = tk.Frame(screen_1, bg="DeepSkyBlue2", height=200)
    output_frame.pack(fill="x", padx=20, pady=10)

    output_text = scrolledtext.ScrolledText(
        output_frame,
        bg="white",
        fg="black",
        font=("Cascadia Code", 12),
        state="disabled"
    )
    output_text.pack(fill="x")

    input_frame = tk.Frame(screen_1, bg="DeepSkyBlue2")
    input_frame.pack(side="bottom", fill="x", pady=10)

    Input = tk.Entry(
        input_frame,
        bg="green yellow",
        fg="black",
        font=("Cascadia Code", 14),
        width=50
    )
    Input.pack(side="left", padx=(100, 10), ipady=5)

    def send_message():
        message = Input.get()
        if message.strip() != "":
            output_text.config(state="normal")
            output_text.insert(tk.END, f"{username}: {message}\n")
            
            try:
                response = model.generate_content(message)
                reply = response.text
            except Exception as e:
                reply = f"Error: {e}"
            
            output_text.insert(tk.END, f"\nRoshanAI: {reply}\n\n")
            output_text.config(state="disabled")
            output_text.yview(tk.END)
            print(reply) 
            Input.delete(0, tk.END)

    def clear_chat():
        output_text.config(state="normal")
        output_text.delete(1.0, tk.END)
        output_text.config(state="disabled")

    try:
        send_btn = tk.Button(
            input_frame, bg="ivory2", text="SEND", activebackground="ivory4",
            bd=0, cursor="hand2", command=send_message
        )
        send_btn.pack(side="left")
        
        clear_btn = tk.Button(
            input_frame, text="CLEAR", bg="IndianRed1", activebackground="red2",
            bd=0, cursor="hand2", command=clear_chat
        )
        clear_btn.pack(side="left", padx=10)
    except Exception:
        send_btn = tk.Button(input_frame, text="SEND", bg="green yellow", command=send_message)
        send_btn.pack(side="left", padx=10)
        
        clear_btn = tk.Button(input_frame, bg="IndianRed1", text="CLEAR", command=clear_chat)
        clear_btn.pack(side="left", padx=10)

    Input.bind("<Return>", lambda event: send_message())
    
    screen_1.mainloop()


screen_auth = tk.Tk()
screen_auth.title("RoshanAI - Authentication")
screen_auth.geometry("400x300")
screen_auth.config(background="DeepSkyBlue3")

auth_title = tk.Label(
    screen_auth, 
    text="Welcome to RoshanAI", 
    bg="DeepSkyBlue3", 
    fg="black", 
    font=("Cambria", 18, "bold")
)
auth_title.pack(pady=20)

form_frame = tk.Frame(screen_auth, bg="DeepSkyBlue3")
form_frame.pack(pady=10)

auth_user_label = tk.Label(form_frame, text="Username:", bg="DeepSkyBlue3", font=("Arial", 11, "bold"))
auth_user_label.grid(row=0, column=0, sticky="e", padx=5, pady=5)

auth_user_entry = tk.Entry(form_frame, font=("Arial", 11), width=20)
auth_user_entry.grid(row=0, column=1, padx=5, pady=5)
auth_pass_label = tk.Label(form_frame, text="Password:", bg="DeepSkyBlue3", font=("Arial", 11, "bold"))
auth_pass_label.grid(row=1, column=0, sticky="e", padx=5, pady=5)

auth_pass_entry = tk.Entry(form_frame, font=("Arial", 11), width=20, show="*")
auth_pass_entry.grid(row=1, column=1, padx=5, pady=5)

btn_frame = tk.Frame(screen_auth, bg="DeepSkyBlue3")
btn_frame.pack(pady=20)

signin_btn = tk.Button(
    btn_frame, 
    text="SIGN IN", 
    bg="green yellow", 
    width=10, 
    font=("Arial", 10, "bold"),
    command=sign_in
)
signin_btn.pack(side="left", padx=10)
signup_btn = tk.Button(
    btn_frame, 
    text="SIGN UP", 
    bg="ivory2", 
    width=10, 
    font=("Arial", 10, "bold"),
    command=sign_up
)
signup_btn.pack(side="left", padx=10)

screen_auth.mainloop()
