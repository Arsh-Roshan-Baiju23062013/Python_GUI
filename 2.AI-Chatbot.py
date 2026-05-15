from tkinter import * 
from tkinter import font, scrolledtext
from PIL import Image, ImageTk
import random

screen_1 = Tk()
screen_1.title("RoshanAI")
screen_1.geometry("900x650") 
screen_1.config(background="DeepSkyBlue2")

try:
    img=Image.open("Send_Button-removebg-preview.png")
    img=img.resize((60, 60)) 
    icon=ImageTk.PhotoImage(img)
    Icon_label=Label(screen_1, bg="DeepSkyBlue2", image=icon)
    Icon_label.pack(pady=10)
except:
    pass

frame_1 = Frame(screen_1, bg="DeepSkyBlue3")
frame_1.pack(fill="x")
title = Label(frame_1, text="Roshan AI", bg="DeepSkyBlue3", fg="black", font=("Cambria", 40, "bold"))
title.pack()


output_frame = Frame(screen_1, bg="DeepSkyBlue2")
output_frame.pack(fill="both", expand=True, padx=20, pady=10)

output_text = scrolledtext.ScrolledText(output_frame, bg="white", fg="black", font=("Cascadia Code", 12), state="disabled")
output_text.pack(fill="both", expand=True)


input_frame = Frame(screen_1, bg="DeepSkyBlue2")
input_frame.pack(side="bottom", fill="x", pady=20)

Input = Entry(input_frame, bg="green yellow", fg="black", font=("Cascadia Code", 14), width=50)
Input.pack(side="left", padx=(100, 10), ipady=5) 
try:
    send_btn = Button(input_frame, image=icon, bg="DeepSkyBlue2", activebackground="DeepSkyBlue2", bd=0, cursor="hand2")
    send_btn.pack(side="left")
except:
    send_btn = Button(input_frame, text="Send", bg="green yellow")
    send_btn.pack(side="left")

screen_1.mainloop()
