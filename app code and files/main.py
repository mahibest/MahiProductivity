import customtkinter as ctk
import threading
import time
import os
import json
import datetime as dt
import pygame
import sys
import psutil
import win32gui
import win32process
import traceback
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
pygame.mixer.init()
logo = os.path.join(os.path.dirname(__file__), "logo.ico")
app = ctk.CTk()
app.title("productivity")
app.geometry("1250x600")
app.iconbitmap(logo)
class AppState:
    def __init__(self):
        self.pomo_time = 25
        self.sbreak_time = 5
        self.lbreak_time = 10
        self.color_theme = "green"
        self.appearance = "system"
        self.timer_running = False
        self.stop_event = threading.Event()
        self.current_timer_label = None
        self.timer_thread = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.remaining_seconds = 0
        self.basedir = os.path.dirname(__file__)
        self.blocked_app_name = None
        self.current_mode = "pomo"
class Paths:
    def __init__(self):
        self.settings_json = os.path.join(g.basedir, "settings.json")
        self.distraction_json = os.path.join(g.basedir, "distraction_tracker.json")
        self.journal_json = os.path.join(g.basedir, "journal.json")
        self.list_txt = os.path.join(g.basedir, "list.txt")
        self.note_txt = os.path.join(g.basedir, "note.txt")
        self.piano_mp3 = os.path.join(g.basedir, "piano.mp3")
        self.rain_mp3 = os.path.join(g.basedir, "rain.mp3")
        self.zen_mp3 = os.path.join(g.basedir, "zen.mp3")
        self.sound_mp3 = os.path.join(g.basedir, "sound.mp3")
        self.summ_json = os.path.join(g.basedir, "summ.json")
        self.blocked_txt = os.path.join(g.basedir, "blocked_apps.txt")
g = AppState()
p = Paths()
def run_app_blocker_loop(g, p):
    while True:
        if os.path.exists(p.blocked_txt):
            with open(p.blocked_txt, "r") as f:
                bad_apps = [line.strip().lower() for line in f.readlines() if line.strip()]
            for proc in psutil.process_iter(['name']):
                try:
                    name = proc.info['name']
                    if name.lower() in bad_apps:
                        proc.kill() 
                        g.blocked_app_name = name 
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        time.sleep(5)
def show_default_view(g):
    for widget in g.workspace.winfo_children():
        widget.destroy()
    cw = ctk.CTkFrame(g.workspace)
    cw.pack(fill="both", expand=True, padx=20, pady=20)
    today = dt.datetime.now().strftime("%d/%m/%Y")
    ctk.CTkLabel(cw, text="Daily Summary ⏳", font=("DM Sans", 40)).pack(pady=20)
    ctk.CTkLabel(cw, text=f"Date: {today}", font=("DM Sans", 20)).pack(pady=10)
    try:
        with open(p.summ_json, "r") as f:
            summ_data = json.load(f)
    except:
        summ_data = []
    stats = next((item for item in summ_data if item["Date"] == today), {"tasks done": 0, "entries written": 0})
    task_count = stats.get('tasks done', 0)
    entry_count = stats.get('entries written', 0)
    if task_count != 0 and entry_count != 0:
        ctk.CTkLabel(cw, text=f"You have finished {task_count} tasks! ✅", font=("DM Sans", 25)).pack(pady=10)
        ctk.CTkLabel(cw, text=f"You have written {entry_count} entries! ✍️", font=("DM Sans", 25)).pack(pady=10)
    elif task_count != 0:
        ctk.CTkLabel(cw, text=f"You have finished {task_count} tasks! ✅", font=("DM Sans", 25)).pack(pady=10)
        ctk.CTkLabel(cw, text=f"You have not written any entries today! 📖", font=("DM Sans", 25)).pack(pady=10)
    elif entry_count != 0:
        ctk.CTkLabel(cw, text=f"You have not completed any tasks today! ❌", font=("DM Sans", 25)).pack(pady=10)
        ctk.CTkLabel(cw, text=f"You have written {entry_count} entries! ✍️", font=("DM Sans", 25)).pack(pady=10)
    else:
        ctk.CTkLabel(cw, text=f"You have not completed any tasks today! ❌", font=("DM Sans", 25)).pack(pady=10)
        ctk.CTkLabel(cw, text=f"You have not written any entries today! 📖", font=("DM Sans", 25)).pack(pady=10)            
    try:
        with open(p.distraction_json, "r") as f:
            d_data = json.load(f)
    except:
        d_data = []
    today_stats = next((item for item in d_data if item["Date"] == today), {})
    distr = today_stats.get("Number of distractions", 0) 
    if distr > 0:
        d_msg = f"You have only been distracted {distr} times today! ⭐"
    else:
        d_msg = "You haven't been distracted at all today! 🌟"
    ctk.CTkLabel(cw, text=d_msg, font=("DM Sans", 25)).pack(pady=10)
file_configs = {
    p.settings_json: {"appearance": "system", "color_theme": "green", "pomo_time": 25, "sbreak_time": 5, "lbreak_time": 10},
    p.distraction_json: [],
    p.journal_json: [],
    p.summ_json: []
}
for file_path, default_content in file_configs.items():
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        with open(file_path, "w") as f:
            json.dump(default_content, f, indent=4)
try:
    def theme_settin():
        if os.path.exists(p.settings_json) and os.path.getsize(p.settings_json) > 0:
            with open(p.settings_json, "r") as s:
                set_time = json.load(s)
                g.color_theme = set_time.get("color_theme")
                g.appearance = set_time.get("appearance")
        else:
            g.color_theme = "green"
            g.appearance = "system"
    theme_settin()
    def time_pomo():
        if os.path.exists(p.settings_json) and os.path.getsize(p.settings_json) > 0:
            with open(p.settings_json, "r") as s:
                set_time = json.load(s)
                g.pomo_time = set_time.get("pomo_time")
                g.sbreak_time = set_time.get("sbreak_time")
                g.lbreak_time = set_time.get("lbreak_time")
        else:
            g.pomo_time = 25
            g.sbreak_time = 5
            g.lbreak_time = 10
    time_pomo()
    ctk.set_default_color_theme(g.color_theme)
    ctk.set_appearance_mode(g.appearance)
    def build_app_layout():
        g.title = ctk.CTkLabel(app, text="Mahi Productivity ⏳", font=("DM Sans", 40))
        g.title.pack(pady=20)
        g.main_container = ctk.CTkFrame(app, fg_color="transparent")
        g.main_container.pack(fill="both", expand=True)
        g.sidebar = ctk.CTkFrame(g.main_container, width=200, corner_radius=0)
        g.sidebar.pack(side="left", fill="y")
        g.workspace = ctk.CTkFrame(g.main_container, fg_color="transparent")
        g.workspace.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        ctk.CTkButton(g.sidebar, text="Pomodoro 🍅", fg_color="#2C0808", command=lambda: pomodoro_func(g, p)).pack(pady=20, padx=20)
        ctk.CTkButton(g.sidebar, text="ToDo-List 📋", fg_color="#68570C", command=lambda: list_func(g, p, show_default_view)).pack(pady=20, padx=20)
        ctk.CTkButton(g.sidebar, text="Distraction Checker 📵", fg_color="#041D01", command=lambda: distraction_tracker(g, p)).pack(pady=20, padx=20)
        ctk.CTkButton(g.sidebar, text="Journal 📕", fg_color="#03032E", command=lambda: journal_func(g, p, show_default_view)).pack(pady=20, padx=20)
        ctk.CTkButton(g.sidebar, text="Ambient Sounds 🎶", fg_color="#200431", command=lambda: AmbientSounds_func(g, p)).pack(pady=20, padx=20)
        ctk.CTkButton(g.sidebar, text="Quick Notes 📝", fg_color="#33032F", command=lambda: QuickNotes_func(g, p)).pack(pady=20, padx=20)
        ctk.CTkButton(g.sidebar, text="App Blocker 🚫", fg_color="#50022F", command=lambda: AppBlocker(g, p)).pack(pady=20, padx=20)
        ctk.CTkButton(g.sidebar, text="Settings ⚙️", fg_color="#262726", command=lambda: settings_func(g, p)).pack(pady=20, padx=20)
        show_default_view(g)
    def apply_settings_and_refresh(stay_on_distract=False, stay_on_settings=False):
        for widget in app.winfo_children():
            widget.destroy()
        theme_settin()
        time_pomo()
        ctk.set_appearance_mode(g.appearance)
        ctk.set_default_color_theme(g.color_theme)
        build_app_layout()
        if stay_on_settings:
            settings_func(g, p)
        elif stay_on_distract:
            distraction_tracker(g, p)
        else:
            show_default_view(g)
    def pomodoro_func(g, p):
        for widget in g.workspace.winfo_children():
            widget.destroy()
        pa = ctk.CTkFrame(g.workspace)
        pa.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        pa.grid_columnconfigure((0, 1, 2), weight=1)
        def twa(label):
            if g.timer_thread and g.timer_thread.is_alive():
                g.current_timer_label = label
                mins, secs = divmod(g.remaining_seconds, 60)
                label.configure(text=f"{mins:02d}:{secs:02d}")
        pomodoro_title = ctk.CTkLabel(pa, text="Pomodoro 🍅", font=("DM Sans", 40))
        pomodoro_title.grid(row=0, column=0, columnspan=3, pady=20)
        pomo = ctk.CTkLabel(pa, text=f"{g.pomo_time:02d}:00", font=("DM Sans", 75))
        pomo.grid(row=1, column=0, pady=20)
        short_break = ctk.CTkLabel(pa, text=f"{g.sbreak_time:02d}:00", font=("DM Sans", 75))
        short_break.grid(row=1, column=1, pady=20)
        long_break = ctk.CTkLabel(pa, text=f"{g.lbreak_time:02d}:00", font=("DM Sans", 75))
        long_break.grid(row=1, column=2, pady=20)
        if g.timer_thread and g.timer_thread.is_alive():
            if g.current_mode == "pomo":
                twa(pomo)
            elif g.current_mode == "short":
                twa(short_break)
            elif g.current_mode == "long":
                twa(long_break)
        def run_timer(label, event, pause_event):
            g.current_timer_label = label 
            while g.remaining_seconds > 0:
                if event.is_set():
                    return 
                pause_event.wait() 
                mins, secs = divmod(g.remaining_seconds, 60)
                time_str = f"{mins:02d}:{secs:02d}"
                if g.current_timer_label and g.current_timer_label.winfo_exists():
                    try:
                        g.current_timer_label.configure(text=time_str)
                    except:
                        pass
                time.sleep(1)
                g.remaining_seconds -= 1
            if not event.is_set():
                pygame.mixer.music.load(p.sound_mp3)
                pygame.mixer.music.play(loops=-1) 
                def stop_alarm_after_delay():
                    time.sleep(10)
                    pygame.mixer.music.stop()
                threading.Thread(target=stop_alarm_after_delay, daemon=True).start()
        def toggle_pause():
            if g.pause_event.is_set():
                g.pause_event.clear()
            else:
                g.pause_event.set()
        def start_timer_thread(duration, label, mode): 
            g.stop_event.set()
            if g.timer_thread:
                g.timer_thread.join(timeout=0.1)
            g.current_mode = mode
            g.remaining_seconds = duration * 60 
            g.stop_event = threading.Event()
            g.pause_event.set() 
            g.timer_thread = threading.Thread(target=run_timer, args=(label, g.stop_event, g.pause_event), daemon=True)
            g.timer_thread.start()  
        def reset_all_timers():
            g.stop_event.set()
            pygame.mixer.music.stop()
            g.remaining_seconds = 0
            pomo.configure(text=f"{g.pomo_time:02d}:00")
            short_break.configure(text=f"{g.sbreak_time:02d}:00")
            long_break.configure(text=f"{g.lbreak_time:02d}:00")
        ctk.CTkButton(pa, text="Start Pomodoro", fg_color="#a36064", command=lambda: start_timer_thread(g.pomo_time, pomo, "pomo")).grid(row=2, column=0, pady=20)
        ctk.CTkButton(pa, text="Start Short Break", fg_color="#74b5f2", command=lambda: start_timer_thread(g.sbreak_time, short_break, "short")).grid(row=2, column=1, pady=20)
        ctk.CTkButton(pa, text="Start Long Break", fg_color="#5981f0", command=lambda: start_timer_thread(g.lbreak_time, long_break, "long")).grid(row=2, column=2, pady=20)
        ctk.CTkButton(pa, text="Pause all timers", command=toggle_pause).grid(row=3, column=0, pady=20)
        ctk.CTkButton(pa, text="Reset all timers", command=reset_all_timers).grid(row=3, column=1, pady=20)
    def list_func(g, p, refresh_callback=None):
        for widget in g.workspace.winfo_children():
            widget.destroy()
        la = ctk.CTkScrollableFrame(g.workspace, fg_color="transparent")
        la.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        list_title = ctk.CTkLabel(la, text="ToDo-List ✅", font=("DM Sans", 40))
        list_title.pack(pady=20)
        progress_bar = ctk.CTkProgressBar(la)
        progress_bar.pack(pady=10)
        progress_bar.set(0) 
        def update_progress():
            total = len(checked_tasks)
            if total == 0:
                progress_bar.set(0)
                return
            completed = sum(1 for cb in checked_tasks if cb.get() == 1)
            progress = completed / total
            progress_bar.set(progress)
        checked_tasks = []
        def load_tasks():
            with open(p.list_txt, "r", encoding="utf-8") as f:
                tasks = [line.strip() for line in f.readlines() if line.strip()]
            for task in tasks:
                cb = ctk.CTkCheckBox(la, text=task)
                cb.pack(pady=5, padx=450, anchor="w")
                checked_tasks.append(cb)
                cb.configure(command=update_progress)
            update_progress()
        def add_task():
            new_task = add_task_input.get()
            if new_task:
                with open(p.list_txt, "a", encoding="utf-8") as l:
                    l.write(new_task + "\n")
                add_task_input.delete(0, "end")
                for widget in la.winfo_children():
                    if isinstance(widget, ctk.CTkCheckBox): widget.destroy()
                checked_tasks.clear()
                add_task_input.delete(0, "end")
                load_tasks()
        def delete_checked():
            remaining_tasks = [cb.cget("text") for cb in checked_tasks if not cb.get()]
            with open(p.list_txt, "w", encoding="utf-8") as f:
                for task in remaining_tasks:
                    f.write(task + "\n")
            for widget in la.winfo_children():
                if isinstance(widget, ctk.CTkCheckBox): widget.destroy()
            today = dt.datetime.now().strftime("%d/%m/%Y")
            with open(p.summ_json, "r") as f:
                summ = json.load(f)
            found = False
            for summa in summ:
                if summa.get("Date") == today:
                    summa["tasks done"] += 1
                    found = True
                    break
            if not found:
                summ.append({"Date": today, "tasks done": 1})
            with open(p.summ_json, "w") as f:
                json.dump(summ, f, indent=4)
            load_tasks()
        add_task_input = ctk.CTkEntry(la, placeholder_text="Task name", width=400)
        add_task_input.pack(pady=10)    
        ctk.CTkButton(la, text="Add task", command=add_task).pack(pady=10)
        ctk.CTkButton(la, text="Complete Checked", command=delete_checked).pack(pady=10)
        load_tasks()
    def journal_func(g, p, refresh_callback=None):
        for widget in g.workspace.winfo_children():
            widget.destroy()
        jw = ctk.CTkFrame(g.workspace)
        jw.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        journal_title = ctk.CTkLabel(jw, text="Journal 📕", font=("DM Sans", 40))
        journal_title.grid(row=0, column=0, columnspan=3, pady=20)
        def update_delete_menu():
            if os.path.exists(p.journal_json) and os.path.getsize(p.journal_json) > 0:
                with open(p.journal_json, "r", encoding='utf-8') as f:
                    entries = json.load(f)
                    titles = [e["Title"] for e in entries]
                    if titles:
                        delete_input.configure(values=titles)
                        delete_input.set(titles[0])
                        return
            else:
                err3 = ctk.CTkLabel(jw, text="ERROR: journal.json is not found.", text_color="red")
                err3.pack(pady=20)
                jw.after(2500, lambda: jw.pack_forget())
            delete_input.configure(values=["No entries yet"])
            delete_input.set("No entries yet")
        def CreateEntry():
            update_delete_menu()
            journal_title = title_input.get()
            journal_entry = entry_input.get()
            entry_dict = {
                "Date": dt.datetime.now().strftime("%d/%m/%Y"),
                "Title": journal_title,
                "Entry": journal_entry 
            }
            with open(p.journal_json, "r", encoding='utf-8') as f:
                all_entries = json.load(f)
            all_entries.append(entry_dict)
            with open(p.journal_json, "w", encoding='utf-8') as f:
                json.dump(all_entries, f, indent=4)
            update_delete_menu() 
            today = dt.datetime.now().strftime("%d/%m/%Y")
            with open(p.summ_json, "r") as f:
                summ = json.load(f)
            found = False
            for summa in summ:
                if summa.get("Date") == today:
                    summa["entries written"] += 1
                    found = True
                    break
            if not found:
                summ.append({"Date": today, "entries written": 1})
            with open(p.summ_json, "w") as f:
                json.dump(summ, f, indent=4)
        def ViewEntries():
            for widget in g.workspace.winfo_children():
                widget.destroy()
            vw = ctk.CTkFrame(g.workspace)
            vw.pack(side="right", fill="both", expand=True, padx=20, pady=20)
            with open(p.journal_json, "r", encoding='utf-8') as f:
                entries = json.load(f)
            scroll_frame = ctk.CTkScrollableFrame(vw, width=500, height=300)
            scroll_frame.pack(pady=20, padx=20)
            for entry in entries:
                text = f"Date: {entry['Date']}\nTitle: {entry['Title']}\nEntry: {entry['Entry']}\n"
                lbl = ctk.CTkLabel(scroll_frame, text=text, font=("DM Sans", 14), anchor="w", justify="left")
                lbl.pack(pady=10, padx=10, fill="x")
        def DeleteEntry():
            title_to_delete = delete_input.get()
            if os.path.exists(p.journal_json) and os.path.getsize(p.journal_json) > 0:
                with open(p.journal_json, "r", encoding='utf-8') as f:
                    all_entries = json.load(f)
                new_entries = [e for e in all_entries if e["Title"] != title_to_delete]
                with open(p.journal_json, "w", encoding='utf-8') as f:
                    json.dump(new_entries, f, indent=4)
                update_delete_menu() 
        write_label = ctk.CTkLabel(jw, text="Write an entry", font=("DM Sans", 30))
        write_label.grid(row=1, column=0, pady=10)
        title_input = ctk.CTkEntry(jw, 350, placeholder_text="Entry's title")
        title_input.grid(row=2, column=0, pady=10)
        entry_input = ctk.CTkEntry(jw, 350, placeholder_text="Entry's content")
        entry_input.grid(row=3, column=0, pady=10)
        create_button = ctk.CTkButton(jw, text="Create entry", command=CreateEntry)
        create_button.grid(row=4, column=0, pady=10)
        view_label = ctk.CTkLabel(jw, text="View entries", font=("DM Sans", 30))
        view_label.grid(row=1, column=1, pady=10)
        view_btn = ctk.CTkButton(jw, text="Open Viewer", command=ViewEntries)
        view_btn.grid(row=2, column=1, pady=10)
        delete_label = ctk.CTkLabel(jw, text="Delete an entry", font=("DM Sans", 30))
        delete_label.grid(row=1, column=2, pady=10)
        delete_input = ctk.CTkOptionMenu(jw, width=350, values=["No entries yet"])
        delete_input.grid(row=2, column=2, pady=10)
        delete_btn = ctk.CTkButton(jw, text="Delete Selected", command=DeleteEntry)
        delete_btn.grid(row=3, column=2, pady=10)
        update_delete_menu()
    def AmbientSounds_func(g, p):
        for widget in g.workspace.winfo_children():
            widget.destroy()
        sw = ctk.CTkFrame(g.workspace)
        sw.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        sw.columnconfigure(0, weight=1)
        sw.columnconfigure(1, weight=1)
        sw.columnconfigure(2, weight=1)
        def rain_sound():
            def sound_thread():
                pygame.mixer.music.load(p.rain_mp3)
                pygame.mixer.music.play(loops=-1) 
            threading.Thread(target=sound_thread, daemon=True).start()
        def piano_sound():
            def sound_thread():
                pygame.mixer.music.load(p.piano_mp3)
                pygame.mixer.music.play(loops=-1) 
            threading.Thread(target=sound_thread, daemon=True).start()
        def zen_sound():
            def sound_thread():
                pygame.mixer.music.load(p.zen_mp3)
                pygame.mixer.music.play(loops=-1) 
            threading.Thread(target=sound_thread, daemon=True).start()
        def stop_all():
            pygame.mixer.music.stop()
        ambient_title = ctk.CTkLabel(sw, text="Ambient Sounds 🎶", font=("DM Sans", 40))
        ambient_title.grid(row=0, column=0, columnspan=3, pady=20)
        rain_button = ctk.CTkButton(sw, 140, 35, text="Rain 🌧️", fg_color="#03023D", command=lambda: rain_sound())
        rain_button.grid(row=1, column=0, pady=20)
        piano_button = ctk.CTkButton(sw, 140, 35, text="Piano 🎹", fg_color="#2B023B", command=lambda: piano_sound())
        piano_button.grid(row=1, column=1, pady=20)
        zen_button = ctk.CTkButton(sw, 140, 35, text="Zen 🧘", fg_color="#364938", command=lambda: zen_sound())
        zen_button.grid(row=1, column=2, pady=20)
        stop_sounds = ctk.CTkButton(sw, 140, 35, text="Stop all sounds", command=stop_all)
        stop_sounds.grid(row=2, column=1, pady=20)
    def QuickNotes_func(g, p):
        for widget in g.workspace.winfo_children():
            widget.destroy()
        note_frame = ctk.CTkFrame(g.workspace)
        note_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(note_frame, text="Quick Notes 📝", font=("DM Sans", 40)).pack(pady=20)
        def SaveNote():
            with open(p.note_txt, "a", encoding="utf-8") as n:
                n.write("\n"+note.get("0.0", "end"))
            save_note.configure(text="Saved!")
            app.after(2000, lambda: save_note.configure(text="Save note"))
        def ClearNote():
            note.delete("0.0", "end")
        note = ctk.CTkTextbox(note_frame, 1000, 350)
        note.pack(pady=20)
        with open(p.note_txt, "r", encoding="utf-8") as f:
            note.insert("0.0", f.read())
        btn_frame = ctk.CTkFrame(note_frame, fg_color="transparent")
        btn_frame.pack()
        save_note = ctk.CTkButton(btn_frame, height=35, text="Save note", fg_color="purple", command=lambda: SaveNote())
        save_note.pack(side="left", padx=10)
        clear_btn = ctk.CTkButton(btn_frame, height=35, text="Clear", fg_color="purple", command=ClearNote)
        clear_btn.pack(side="left", padx=10)
    def distraction_tracker(g, p):
        for widget in g.workspace.winfo_children():
            widget.destroy()
        dw = ctk.CTkFrame(g.workspace)
        dw.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        dw.columnconfigure(0, weight=1)
        dw.columnconfigure(1, weight=1)
        dw.columnconfigure(2, weight=1)
        def distract():
            today = dt.datetime.now().strftime("%d/%m/%Y")
            with open(p.distraction_json, "r") as f:
                dis = json.load(f)
            found = False
            for distr in dis:
                if distr.get("Date") == today:
                    distr["Number of distractions"] += 1
                    found = True
                    break
            if not found:
                dis.append({"Date": today, "Number of distractions": 1})
            with open(p.distraction_json, "w") as f:
                json.dump(dis, f, indent=4)
            apply_settings_and_refresh(True)
        ctk.CTkLabel(dw, text="Distraction Tracker 📵", font=("DM Sans", 40)).grid(row=0, column=1, pady=20)
        ctk.CTkButton(dw, 140, 40, text="Click here if you got distracted", command=lambda: distract()).grid(row=1, column=1, pady=20)
        with open(p.distraction_json, "r") as f:
            d = json.load(f)
            found = False
            for distr in d:
                if distr.get("Date") == dt.datetime.now().strftime("%d/%m/%Y"):
                    ctk.CTkLabel(dw, text=f"Date: {distr.get("Date")}", font=("DM Sans", 30)).grid(row=2, column=1, pady=20)
                    ctk.CTkLabel(dw, text=f"No of distracions: {distr.get("Number of distractions")}", font=("DM Sans", 30)).grid(row=3, column=1, pady=20)
                    found = True
                    break
    def AppBlocker(g, p):
        for widget in g.workspace.winfo_children():
            widget.destroy()
        bw = ctk.CTkFrame(g.workspace)
        bw.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        def get_running_process_names():
            user_apps = set()
            def callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if not title:
                        return
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        proc = psutil.Process(pid)
                        name = proc.name().lower()
                        banned_apps = [
                            'systemsettings.exe', 'explorer.exe', 'textinputhost.exe', 
                            'applicationframehost.exe', 'shellexperiencehost.exe',
                            'python.exe', 'searchhost.exe'
                        ]
                        if name not in banned_apps:
                            user_apps.add(proc.name())
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            win32gui.EnumWindows(callback, None)
            return sorted(list(user_apps))
        def update_delete_menu():
            if os.path.exists(p.blocked_txt):
                with open(p.blocked_txt, "r", encoding='utf-8') as f:
                    apps = [line.strip() for line in f.readlines() if line.strip()]
                    if apps:
                        delete_input.configure(values=apps)
                        delete_input.set(apps[0])
                        return
            delete_input.configure(values=["No blocked apps yet"])
            delete_input.set("No blocked apps yet")
        def DeleteApp():
            title_to_delete = delete_input.get().strip().lower()
            if os.path.exists(p.blocked_txt):
                with open(p.blocked_txt, "r", encoding='utf-8') as f:
                    all_apps = [line.strip().lower() for line in f.readlines()]
                new_apps = [a for a in all_apps if a != title_to_delete]
                with open(p.blocked_txt, "w", encoding='utf-8') as f:
                    for app_name in new_apps:
                        f.write(app_name + "\n")
                update_delete_menu()
        def add_app():
            new_app = add_app_input.get().strip().lower()
            if new_app:
                with open(p.blocked_txt, "a", encoding="utf-8") as l:
                    l.write(new_app + "\n")
                add_app_input.delete(0, "end")
                update_delete_menu()
        def check_for_blocks_ui():
            if g.blocked_app_name:
                alert_lbl = ctk.CTkLabel(bw, text=f"🚫 {g.blocked_app_name} was blocked!", text_color="red", font=("DM Sans", 18))
                alert_lbl.pack(pady=10)
                bw.after(3000, lambda: alert_lbl.destroy())
                g.blocked_app_name = None 
            if bw.winfo_exists():
                bw.after(2000, check_for_blocks_ui)
        ctk.CTkLabel(bw, text="App Blocker 🚫", font=("DM Sans", 40)).pack(pady=20)
        if not hasattr(g, 'blocker_thread') or not g.blocker_thread.is_alive():
            g.blocker_thread = threading.Thread(target=run_app_blocker_loop, args=(g, p), daemon=True)
            g.blocker_thread.start()
        running_apps = get_running_process_names()
        add_app_input = ctk.CTkOptionMenu(bw, width=350, values=running_apps)
        add_app_input.set("Select app to block")
        add_app_input.pack(pady=20)
        ctk.CTkButton(bw, text="Add to Block List", command=add_app).pack(pady=10)
        delete_input = ctk.CTkOptionMenu(bw, width=350, values=["No blocked apps yet"])
        delete_input.pack(pady=20)
        ctk.CTkButton(bw, text="Unblock Selected", command=DeleteApp).pack(pady=10)
        update_delete_menu()
        check_for_blocks_ui()
    def settings_func(g, p):
        for widget in g.workspace.winfo_children():
            widget.destroy()
        sw = ctk.CTkFrame(g.workspace)
        sw.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        sw.columnconfigure(0, weight=1)
        sw.columnconfigure(1, weight=1)
        sw.columnconfigure(2, weight=1)
        settings_title = ctk.CTkLabel(sw, text="Settings ⚙️", font=("DM Sans", 40))
        settings_title.grid(row=0, column=0, columnspan=30, pady=20)
        def save_and_refresh():
            new_pomo = g.pomo_time
            new_sbreak = g.sbreak_time
            new_lbreak = g.lbreak_time
            new_appr = theme_input.get() if theme_input.get() != "Change Theme" else g.appearance
            new_color = color_input.get() if color_input.get() != "Change Color Theme" else g.color_theme
            try:
                pomo_val = pomo_input.get()
                if pomo_val.isdigit():
                    new_pomo = int(pomo_val)
                    
                sbreak_val = sbreak_input.get()
                if sbreak_val.isdigit():
                    new_sbreak = int(sbreak_val)
                lbreak_val = lbreak_input.get()
                if lbreak_val.isdigit():
                    new_lbreak = int(lbreak_val)
            except Exception as e:
                print(f"Input error: {e}")
            settings_data = {
                "appearance": new_appr,
                "color_theme": new_color,
                "pomo_time": new_pomo,
                "sbreak_time": new_sbreak,
                "lbreak_time": new_lbreak
            }
            with open(p.settings_json, "w") as f:
                json.dump(settings_data, f)
            apply_settings_and_refresh(stay_on_settings=True)
        def update_and_save(key, value):
            save_and_refresh()
            apply_settings_and_refresh(stay_on_settings=True)
        def delete():
            w = ctk.CTkToplevel()
            w.geometry("450x100")
            w.title("warning")
            w.grid_columnconfigure((0, 1, 2), weight=1)
            def go():
                with open(p.distraction_json, "w") as f:
                    json.dump([], f)
                with open(p.journal_json, "w") as f:
                    json.dump([], f)
                with open(p.summ_json, "w") as f:
                    json.dump([], f)
                with open(p.list_txt, "w") as f:
                    f.write("")
                with open(p.note_txt, "w") as f:
                    f.write("")
                with open(p.blocked_txt, "w") as f:
                    f.write("")
                w.destroy()
            frame = ctk.CTkFrame(w, 400, 50)
            frame.grid(row=0, column=0)
            ctk.CTkLabel(frame, text="⚠️WARNING: THIS WILL DELETE ALL USER INPUT EXCEPT SETTINGS.⚠️\nDO YOU WANT TO DELETE ALL DATA.").grid(row=0, column=0, pady=10)
            frame2 = ctk.CTkFrame(w, 400, 50)
            frame2.grid(row=1, column=0)
            ctk.CTkButton(frame2, 75, text="yes", fg_color="red", command=lambda: go()).grid(row=1, column=0, pady=10)
            ctk.CTkButton(frame2, 75, text="no", command=lambda: w.destroy()).grid(row=1, column=1, pady=10)
        theme_title = ctk.CTkLabel(sw, text="Theme Settings", font=("DM Sans", 30))
        theme_title.grid(row=1, column=0, pady=20)
        color_input = ctk.CTkOptionMenu(sw, values=["Change Color Theme", "dark-blue", "blue", "green"])
        color_input.grid(row=2, column=0, pady=20)
        color_btn = ctk.CTkButton(sw, text="Change Color Theme", command=lambda: update_and_save("appearance", theme_input.get()))
        color_btn.grid(row=3, column=0, pady=20)
        theme_input = ctk.CTkOptionMenu(sw, values=["Change Theme", "system", "dark", "light"])
        theme_input.grid(row=4, column=0, pady=20)
        theme_btn = ctk.CTkButton(sw, text="Change Theme", command=lambda: update_and_save("color_theme", color_input.get()))
        theme_btn.grid(row=5, column=0, pady=20)
        pomodoro_title = ctk.CTkLabel(sw, text="Pomodoro Settings", font=("DM Sans", 30))
        pomodoro_title.grid(row=1, column=2, pady=20)
        pomo_input = ctk.CTkEntry(sw, 300, placeholder_text="Change Pomodoro Time")
        pomo_input.grid(row=2, column=2, pady=20)
        pomo_btn = ctk.CTkButton(sw, text="Change Pomodoro Timing", command=lambda: update_and_save("pomo_time", pomo_input.get()))
        pomo_btn.grid(row=3, column=2, pady=20)
        break_title = ctk.CTkLabel(sw, text="Break Settings", font=("DM Sans", 30))
        break_title.grid(row=1, column=1, pady=20)
        sbreak_input = ctk.CTkEntry(sw, 300, placeholder_text="Change Short Break Time")
        sbreak_input.grid(row=2, column=1, pady=20)
        sbreak_btn = ctk.CTkButton(sw, text="Change Short Break Timing", command=lambda: update_and_save("sbreak_time", sbreak_input.get()))
        sbreak_btn.grid(row=3, column=1, pady=20)
        lbreak_input = ctk.CTkEntry(sw, 300, placeholder_text="Change Long Break Time")
        lbreak_input.grid(row=4, column=1, pady=20)
        lbreak_btn = ctk.CTkButton(sw, text="Change Long Break Timing", command=lambda: update_and_save("lbreak_time", lbreak_input.get()))
        lbreak_btn.grid(row=5, column=1, pady=20)
        file_title = ctk.CTkLabel(sw, text="⚠️Clear all files⚠️", font=("DM Sans", 30))
        file_title.grid(row=4, column=2, pady=20)
        file_btn = ctk.CTkButton(sw, text="Delete all file data", command=lambda: delete())
        file_btn.grid(row=5, column=2, pady=20)          
except Exception as e:
    traceback.print_exc()
build_app_layout()
app.after(100, lambda: show_default_view(g))
app.mainloop()