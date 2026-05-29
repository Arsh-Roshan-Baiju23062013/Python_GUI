from tkinter import *
from tkinter import scrolledtext
from tkinter import simpledialog
from PIL import Image, ImageTk
from tkinter import messagebox
import google.generativeai as genai
genai.configure(api_key="AIzaSyDsOtXVLBKpUsgJNkpRfMKoctxJlcTAmAc")
model=genai.GenerativeModel("gemini-3.5-flash")

screen_1 = Tk()
screen_1.title("RoshanAI")
screen_1.geometry("900x650")
screen_1.config(background="DeepSkyBlue2")
username=simpledialog.askstring("Name", "Enter your name:")

try:
    img = Image.open("Send_Button-removebg-preview.png")
    img = img.resize((30, 30))
    icon = ImageTk.PhotoImage(img)
    Icon_label = Label(screen_1, bg="DeepSkyBlue2", image=icon)
    Icon_label.pack(pady=1)
except:
    pass

frame_1 = Frame(screen_1, bg="DeepSkyBlue3")
frame_1.pack(fill="x")

title = Label(
    frame_1,
    text="Roshan AI",
    bg="DeepSkyBlue3",
    fg="black",
    font=("Cambria", 40, "bold")
)
title.pack()

output_frame = Frame(screen_1, bg="DeepSkyBlue2", height=200)
output_frame.pack(fill="x", padx=20, pady=10)

output_text = scrolledtext.ScrolledText(
    output_frame,
    bg="white",
    fg="black",
    font=("Cascadia Code", 12),
    state="disabled"
)
output_text.pack(fill="x")

input_frame = Frame(screen_1, bg="DeepSkyBlue2")
input_frame.pack(side="bottom", fill="x", pady=10)

Input = Entry(
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
        output_text.insert(END, f"{username}: {message}\n")
       # output_text.config(state="disabled")
        #output_text.yview(END)
    try:
        response=model.generate_content(message)
        reply=response.text
    except Exception as e:
        reply=f"Error:{e}"
    output_text.insert(END, f"\nRoshanAI: {reply}\n")
    output_text.config(state="disabled")
    output_text.yview(END)
    print(reply) 
    Input.delete(0, END)

def clear_chat():
    output_text.config(state="normal")
    output_text.delete(1.0, END)
    output_text.config(state="disabled")


try:
    send_btn = Button(
        input_frame,
        image=icon,
        bg="DeepSkyBlue2",
        activebackground="DeepSkyBlue2",
        bd=0,
        cursor="hand2",
        command=send_message
    )
    send_btn.pack(side="left")
    clear_btn=Button(
        input_frame,
        image=icon,
        bg="IndianRed1",
        activebackground="yellow",
        bd=0,
        cursor="hand2",
        command=clear_chat
        )
    clear_btn.pack(side="left", padx=10)
except:
    send_btn = Button(
        input_frame,
        text="Send",
        bg="green yellow",
        command=send_message
    )
    send_btn.pack(side="left", padx=10)
    clear_btn=Button(
        input_frame,
        bg="IndianRed1",
        text="CLEAR",
        command=clear_chat
        )
    clear_btn.pack(side="left", padx=10)

Input.bind("<Return>", lambda event: send_message())

screen_1.mainloop()
