from tkinter import ttk ,messagebox
import os , json , tkinter as tk

def insert_into_list_box():
    course_name = string_course.get()
    if course_name :
        listbox.insert(tk.END, course_name)
        e_course.delete(0, 'end')

def load_required_info():
    required_info_path = os.path.join(os.path.dirname(__file__), 'required_info.json')
    if os.path.isfile(required_info_path) and os.access(required_info_path, os.R_OK):
        with open(required_info_path) as f: return json.loads(f.read())
    else:
        return  {'linkedin_email':'','linkedin_password':'','courses_links':[""]}

def save_data():
    required_info_path = os.path.join(os.path.dirname(__file__), 'required_info.json')
    email    = string_email.get()
    password = string_pass.get()
    courses  = list(lb1_values.get())
    data  = {'linkedin_email':email,'linkedin_password':password,'courses_links':courses}
    with open(required_info_path , 'w') as f:
        f.write(json.dumps(data))
    messagebox.showinfo("File Saving", "File required_info.json saved Succesfully\nYou can Run the downloader now ^_^")
    master.quit()

cached_info = load_required_info()

master = tk.Tk()

tk.Label(master,text="Email").grid(row=0)
tk.Label(master,text="Password").grid(row=1)
tk.Label(master,text="Courses").grid(row=3)

string_email    = tk.StringVar(value=cached_info['linkedin_email'])
e_email         = tk.Entry(master,width=40,textvariable=string_email)
string_pass     = tk.StringVar(value=cached_info['linkedin_password'])
e_pass          = tk.Entry(master,width=40,textvariable=string_pass)
string_course   = tk.StringVar()
e_course        = tk.Entry(master,width=35,textvariable=string_course)
lb1_values      = tk.Variable()
listbox         = tk.Listbox(master,width=40,listvariable=lb1_values)
for course in cached_info['courses_links']:
    course = course.split('/learning/')[1] if '/learning/' in course else course
    listbox.insert(tk.END, course)

e_email.grid(row=0, column=1)
e_pass.grid(row=1, column=1)
e_course.grid(row=2, column=1)
listbox.grid(row=3, column=1)


# tk.Button(master, text='Quit', command=master.quit).grid(row=8, column=0, sticky=tk.W,pady=4)
tk.Button(master, text='addToCourses',command=insert_into_list_box).grid(row=2, column=0, sticky=tk.W, pady=4)
tk.Button(master, text='Save All the data To required_info.json',command=save_data).grid(row=4, column=1, sticky=tk.W, pady=4)


master.resizable(False, False)
window_height = 280
window_width = 350
screen_width = master.winfo_screenwidth()
screen_height = master.winfo_screenheight()
x_cordinate = int((screen_width/2) - (window_width/2))
y_cordinate = int((screen_height/2) - (window_height/2))
master.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))

master.title('Saving Required info')
master.mainloop()