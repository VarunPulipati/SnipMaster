# gui.py
import sys
import tkinter as tk
from tkinter import ttk, messagebox, Menu, simpledialog
try:
    from PIL import Image, ImageTk
except ImportError as e: print(f"ERROR: {e}\npip install Pillow"); exit()
# Import modules
import clipboard
import helpers
import slots
# Import specific items needed
from clipboard import ( clear_clipboard, handle_paste, rewrite_content, rephrase_content, setup_shortcuts, set_gui_refresh_callback, clipboard_slots )
from slots import ( delete_slot, edit_slot, assign_slot, show_context_menu )
from helpers import search_function, on_drag_start, on_drag_motion
import os

# --- Globals ---
root = None; close_button = None; new_window = None
delete_icon_img = None; options_icon_img = None

# --- Color Constants ---
BG_COLOR = '#F0F0F0'
FRAME_BG_COLOR = '#E0E0E0'
TEXT_COLOR = '#333333'
BUTTON_BG = '#D0D0D0'
BUTTON_FG = '#000000'
ACCENT_COLOR = '#0078D7'
CLOSE_BUTTON_BG = '#E81123'
GO_BUTTON_BG = '#107C10'
SLOT_ITEM_BG = '#FFFFFF'
SLOT_ITEM_HOVER_BG = '#E5F1FB'

# --- Refresh Scheduling ---
def schedule_refresh():
    if new_window and new_window.winfo_exists(): new_window.after(50, lambda: refresh_clipboard_window(new_window))

# --- Style Configuration ---
def configure_styles(target_root):
    global delete_icon_img, options_icon_img
    style = ttk.Style()
    try: default_font, bold_font, title_font = ('Segoe UI', 10), ('Segoe UI', 10, 'bold'), ('Segoe UI', 12, 'bold')
    except tk.TclError: default_font, bold_font, title_font = ('Helvetica', 10), ('Helvetica', 10, 'bold'), ('Helvetica', 12, 'bold')
    style.configure('.', font=default_font); style.theme_use('clam')

    if target_root and target_root.winfo_exists(): target_root.configure(bg=BG_COLOR)
    style.configure('TFrame', background=FRAME_BG_COLOR)
    style.configure('SlotItem.TFrame', background=SLOT_ITEM_BG)
    style.map('SlotItem.TFrame', background=[('active', SLOT_ITEM_HOVER_BG)])
    style.configure('TLabel', background=FRAME_BG_COLOR, foreground=TEXT_COLOR, padding=(5, 2))
    style.configure('SlotItem.TLabel', background=SLOT_ITEM_BG, foreground=TEXT_COLOR)
    style.map('SlotItem.TLabel', background=[('active', SLOT_ITEM_HOVER_BG)])
    style.configure('Title.TLabel', font=title_font, foreground=ACCENT_COLOR, background=FRAME_BG_COLOR)
    style.configure('Header.TLabel', font=bold_font, background=FRAME_BG_COLOR)
    style.configure('Link.TLabel', foreground=ACCENT_COLOR, background=SLOT_ITEM_BG, font=default_font + ('underline',))
    style.map('Link.TLabel', background=[('active', SLOT_ITEM_HOVER_BG)])
    style.configure('TButton', font=bold_font, padding=(10, 5))
    style.map('TButton', background=[('!active', BUTTON_BG), ('active', '#B0B0B0')], foreground=[('!active', BUTTON_FG), ('active', '#000000')])
    style.configure('Close.TButton', background=CLOSE_BUTTON_BG, foreground='white'); style.map('Close.TButton', background=[('active', '#F1707A')])
    style.configure('Go.TButton', background=GO_BUTTON_BG, foreground='white'); style.map('Go.TButton', background=[('active', '#3B9D3B')])

    # --- Action Button Style (Load Icons) ---
    assets_dir = 'assets'; delete_icon_path = os.path.join(assets_dir, 'delete_icon.png'); options_icon_path = os.path.join(assets_dir, 'options_icon.png')
    delete_icon_img = None; options_icon_img = None; delete_text = '🗑️'; options_text = '≡'
    try: img = Image.open(delete_icon_path).resize((16, 16), Image.Resampling.LANCZOS); delete_icon_img = ImageTk.PhotoImage(img); print("[GUI Style] Delete icon loaded."); delete_text = ''
    except FileNotFoundError: print(f"[GUI Style] Warning: '{delete_icon_path}' not found. Using text fallback '{delete_text}'.")
    except Exception as e: print(f"[GUI Style] Error loading delete icon: {e}")
    try: img = Image.open(options_icon_path).resize((16, 16), Image.Resampling.LANCZOS); options_icon_img = ImageTk.PhotoImage(img); print("[GUI Style] Options icon loaded."); options_text = ''
    except FileNotFoundError: print(f"[GUI Style] Warning: '{options_icon_path}' not found. Using text fallback '{options_text}'.")
    except Exception as e: print(f"[GUI Style] Error loading options icon: {e}")

    # *** FIXED: Removed image=None from style configuration ***
    style.configure('ActionButton.TButton',
                    font=('Segoe UI Symbol', 10) if (delete_text or options_text) else default_font,
                    padding=(2, 0), background=SLOT_ITEM_BG, relief='flat', borderwidth=0,
                    compound='center', width=-1) # Compound tells button how to show text+image later if needed
    style.map('ActionButton.TButton', background=[('active', SLOT_ITEM_HOVER_BG), ('!active', SLOT_ITEM_BG)], relief=[('pressed', 'flat'), ('active', 'flat')])

    style.configure('TCombobox', padding=(5, 2))
    if target_root and target_root.winfo_exists():
        target_root.option_add('*TCombobox*Listbox.font', default_font); target_root.option_add('*TCombobox*Listbox.background', '#FFFFFF')
        target_root.option_add('*TCombobox*Listbox.foreground', TEXT_COLOR); target_root.option_add('*TCombobox*Listbox.selectBackground', ACCENT_COLOR)
        target_root.option_add('*TCombobox*Listbox.selectForeground', '#FFFFFF')


# --- Icon Click & Setup ---
# (on_icon_click, setup_floating_icon remain the same)
def on_icon_click(event):
    if root: root.withdraw(); open_new_window()
def setup_floating_icon():
    global root, close_button; print("[gui.py] Setting up floating icon...")
    root = tk.Tk(); root.title("ClipApp Icon"); root.overrideredirect(True); root.attributes("-topmost", True)
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight(); ww, wh = 50, 50; xo, yo = sw - ww - 20, 20
    root.geometry(f"{ww}x{wh}+{xo}+{yo}"); root.resizable(False, False); configure_styles(root); root.configure(bg='white', highlightthickness=1, highlightbackground='grey')
    icon_widget = None; icon_path = "assets/cert.jpeg" # *** YOUR ICON PATH ***
    try: print(f"[gui.py] Loading icon: {icon_path}"); img = Image.open(icon_path).resize((ww-10, wh-10), Image.Resampling.LANCZOS); ph = ImageTk.PhotoImage(img); lbl = tk.Label(root, image=ph, bg="white", bd=0); lbl.image = ph; lbl.pack(expand=True, fill='both', padx=5, pady=5); icon_widget = lbl
    except Exception as e: print(f"[gui.py] Icon load error: {e}"); lbl = tk.Label(root, text="CA", font=("Arial", 16, "bold"), bg="white", fg="#0078D7"); lbl.pack(expand=True, fill='both'); icon_widget = lbl
    if icon_widget: icon_widget.bind("<ButtonRelease-1>", on_icon_click); icon_widget.bind("<Button-1>", lambda e, r=root: on_drag_start(e, r)); icon_widget.bind("<B1-Motion>", lambda e, r=root: on_drag_motion(e, r)); icon_widget.bind("<Enter>", on_hover); icon_widget.bind("<Leave>", on_leave)
    close_button = tk.Button(root, text="✕", command=close_icon, bg="#E81123", fg="white", relief="flat", font=("Arial", 8, "bold"), bd=0, activebackground="#F1707A", activeforeground="white", padx=0, pady=0, borderwidth=0, highlightthickness=0)
    root.bind("<Leave>", on_leave)
    print("[gui.py] Registering GUI refresh callback..."); set_gui_refresh_callback(schedule_refresh); setup_shortcuts()
    print("[gui.py] Starting Tkinter main loop..."); root.mainloop(); print("[gui.py] Tkinter main loop finished.")


# --- Main Window ---
# (open_new_window remains the same - includes scrollable canvas setup)
def open_new_window():
    global new_window; print("[gui.py] Opening main window...")
    if new_window and new_window.winfo_exists(): new_window.lift(); return
    if not root: print("[gui.py] Error: Root window not found."); return
    new_window = tk.Toplevel(root); new_window.title("ClipApp Dashboard")
    init_w, init_h = 450, 550
    sw, sh = new_window.winfo_screenwidth(), new_window.winfo_screenheight()
    ix, iy = root.winfo_x(), root.winfo_y(); idx, idy = ix - init_w - 10, iy
    fx, fy = max(0, min(idx, sw - init_w)), max(0, min(idy, sh - init_h))
    new_window.geometry(f"1x1+{fx}+{fy}"); new_window.attributes("-topmost", True); new_window.resizable(True, True); new_window.minsize(350, 300)
    configure_styles(new_window)

    mf = ttk.Frame(new_window, padding="10 10 10 10", style='TFrame'); mf.pack(expand=True, fill="both")
    mf.grid_columnconfigure(0, weight=1); mf.grid_rowconfigure(0, weight=0); mf.grid_rowconfigure(1, weight=0); mf.grid_rowconfigure(2, weight=1) # Row 2 expands
    mf.grid_rowconfigure(3, weight=0); mf.grid_rowconfigure(4, weight=0); mf.grid_rowconfigure(5, weight=0)

    new_window.slots_canvas = None; new_window.slots_frame = None; new_window.search_dropdown = None

    ttk.Label(mf, text="ClipApp Dashboard", style='Title.TLabel').grid(row=0, column=0, pady=(0, 15), sticky='ew')
    ttk.Label(mf, text="Clipboard Slots:", style='Header.TLabel').grid(row=1, column=0, sticky='w', pady=(0, 5))

    canvas_container = ttk.Frame(mf, style='TFrame', padding=0); canvas_container.grid(row=2, column=0, sticky='nsew', pady=(0, 15))
    canvas_container.grid_rowconfigure(0, weight=1); canvas_container.grid_columnconfigure(0, weight=1)
    slots_canvas = tk.Canvas(canvas_container, bg=FRAME_BG_COLOR, highlightthickness=0)
    slots_canvas.grid(row=0, column=0, sticky='nsew'); new_window.slots_canvas = slots_canvas
    vsb = ttk.Scrollbar(canvas_container, orient="vertical", command=slots_canvas.yview); vsb.grid(row=0, column=1, sticky='ns')
    slots_canvas.configure(yscrollcommand=vsb.set)
    inner_slots_frame = ttk.Frame(slots_canvas, style='TFrame', padding=0); new_window.slots_frame = inner_slots_frame
    canvas_window = slots_canvas.create_window((0, 0), window=inner_slots_frame, anchor="nw", tags="inner_frame")

    def update_scroll_region(event):
        canvas_width = event.width; slots_canvas.itemconfig(canvas_window, width=canvas_width)
        slots_canvas.configure(scrollregion=slots_canvas.bbox("all"))
    def on_mousewheel(event):
        scroll_dir = 0;
        if event.num == 5 or event.delta < 0: scroll_dir = 1
        elif event.num == 4 or event.delta > 0: scroll_dir = -1
        slots_canvas.yview_scroll(scroll_dir, "units")

    slots_canvas.bind("<Configure>", update_scroll_region)
    slots_canvas.bind_all('<MouseWheel>', on_mousewheel); slots_canvas.bind_all('<Button-4>', on_mousewheel); slots_canvas.bind_all('<Button-5>', on_mousewheel)

    populate_slots_frame(inner_slots_frame)

    cb = ttk.Button(mf, text="Clear All Slots", command=lambda nw=new_window: clear_all_and_refresh(nw), style='Close.TButton'); cb.grid(row=3, column=0, pady=(5, 5), sticky='ew')
    sc = ttk.Frame(mf, padding="0", style='TFrame'); sc.grid(row=4, column=0, sticky='ew', pady=(0, 5)); sc.grid_columnconfigure(1, weight=1); ttk.Label(sc, text="Search Slot:", style='TLabel').grid(row=0, column=0, padx=(0, 5), sticky='w'); sv = tk.StringVar()
    dd = ttk.Combobox(sc, textvariable=sv, state="readonly", style='TCombobox')
    try: dd['values'] = sorted(list(clipboard_slots.keys()), key=lambda k: (k.isdigit(), int(k) if k.isdigit() else k))
    except Exception as e: print(f"Error populating dropdown: {e}")
    dd.grid(row=0, column=1, padx=(0, 5), sticky='ew'); new_window.search_dropdown = dd
    sb = ttk.Button(sc, text="Go", command=lambda sv=sv: search_function(sv.get()), style='Go.TButton'); sb.grid(row=0, column=2, sticky='e')
    cmb = ttk.Button(mf, text="Close Window", command=lambda nw=new_window: close_new_window(nw), style='TButton'); cmb.grid(row=5, column=0, pady=(10, 0), sticky='ew')
    new_window.protocol("WM_DELETE_WINDOW", lambda nw=new_window: close_new_window(nw));
    animate_window(new_window, init_w, init_h, fx, fy)


# --- Helper Functions for Slot Actions ---
# (confirm_and_delete, show_slot_options_menu remain the same)
def confirm_and_delete(slot_key, parent_window):
    valid_parent = parent_window if parent_window and parent_window.winfo_exists() else root
    if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Slot '{slot_key}'?", parent=valid_parent):
        delete_slot_and_refresh(slot_key, valid_parent)
def show_slot_options_menu(event, slot_key, parent_window):
    valid_parent = parent_window if parent_window and parent_window.winfo_exists() else root
    menu = Menu(valid_parent, tearoff=0, bg="#FFFFFF", fg="#333333", activebackground="#0078D7", activeforeground="#FFFFFF")
    menu.add_command(label="Paste Content (to System)", command=lambda sk=slot_key: handle_paste(sk))
    menu.add_separator()
    menu.add_command(label="Assign New Content", command=lambda sk=slot_key, p=valid_parent: assign_slot_and_refresh(sk, p))
    menu.add_command(label="Edit Slot Name", command=lambda sk=slot_key, p=valid_parent: edit_slot_and_refresh(sk, p))
    menu.add_command(label="Rewrite Content", command=lambda sk=slot_key, p=valid_parent: rewrite_content_and_refresh(sk, p))
    menu.add_command(label="Rephrase Content (Basic)", command=lambda sk=slot_key, p=valid_parent: rephrase_content_and_refresh(sk, p))
    try: widget = event.widget; menu.post(widget.winfo_rootx(), widget.winfo_rooty() + widget.winfo_height())
    except tk.TclError as e: print(f"Debug: Failed to post options menu: {e}")


# --- Populate Slots Frame ---
# (populate_slots_frame remains the same - uses icons/symbols defined in configure_styles)
def populate_slots_frame(frame):
    global delete_icon_img, options_icon_img
    if not frame or not frame.winfo_exists(): return
    for widget in frame.winfo_children(): widget.destroy()
    def sort_key(item): key = item[0]; return (0, int(key)) if key.isdigit() else (1, key)
    sorted_items = sorted(clipboard_slots.items(), key=sort_key)
    if not sorted_items:
        ttk.Label(frame, text="No clipboard slots saved yet.", style='TLabel', anchor='center').pack(pady=20, fill='x'); frame.update_idletasks(); return
    parent_win_for_dialogs = new_window if new_window and new_window.winfo_exists() else root
    for idx, (slot_key, content) in enumerate(sorted_items):
        item_frame = ttk.Frame(frame, padding=(5, 3), style='SlotItem.TFrame'); item_frame.pack(fill='x', pady=(0, 1), padx=1)
        item_frame.bind("<Enter>", lambda e, w=item_frame: w.state(['active'])); item_frame.bind("<Leave>", lambda e, w=item_frame: w.state(['!active']))
        def on_child_enter(e, parent_frame): parent_frame.state(['active'])
        def on_child_leave(e, parent_frame): parent_frame.state(['!active'])
        item_frame.grid_columnconfigure(0, weight=0); item_frame.grid_columnconfigure(1, weight=1); item_frame.grid_columnconfigure(2, weight=0); item_frame.grid_columnconfigure(3, weight=0)
        slot_label = ttk.Label(item_frame, text=f"Slot {slot_key}:", style='Link.TLabel', cursor="hand2", anchor="w"); slot_label.grid(row=0, column=0, padx=(0, 10), sticky='w'); slot_label.bind("<Button-1>", lambda e, sk=slot_key: handle_paste(sk)); slot_label.bind("<Enter>", lambda e, p=item_frame: on_child_enter(e, p)); slot_label.bind("<Leave>", lambda e, p=item_frame: on_child_leave(e, p))
        display_content = content.replace('\n', ' ').replace('\r', ''); display_content = display_content if len(display_content) < 60 else display_content[:57] + "..."; content_label = ttk.Label(item_frame, text=display_content, style='SlotItem.TLabel', anchor="w"); content_label.grid(row=0, column=1, sticky='ew'); content_label.bind("<Button-1>", lambda e, sk=slot_key: handle_paste(sk)); content_label.bind("<Enter>", lambda e, p=item_frame: on_child_enter(e, p)); content_label.bind("<Leave>", lambda e, p=item_frame: on_child_leave(e, p))
        delete_btn = ttk.Button(item_frame, style='ActionButton.TButton', cursor="hand2", command=lambda sk=slot_key, p=parent_win_for_dialogs: confirm_and_delete(sk, p));
        if delete_icon_img: delete_btn.configure(image=delete_icon_img)
        else: delete_btn.configure(text='🗑️')
        delete_btn._image_ref = delete_icon_img; delete_btn.grid(row=0, column=2, padx=(5, 0)); delete_btn.bind("<Enter>", lambda e, p=item_frame: on_child_enter(e, p)); delete_btn.bind("<Leave>", lambda e, p=item_frame: on_child_leave(e, p))
        options_btn = ttk.Button(item_frame, style='ActionButton.TButton', cursor="hand2");
        if options_icon_img: options_btn.configure(image=options_icon_img)
        else: options_btn.configure(text='≡') # Changed fallback symbol
        options_btn._image_ref = options_icon_img; options_btn.bind("<Button-1>", lambda e, sk=slot_key, p=parent_win_for_dialogs: show_slot_options_menu(e, sk, p)); options_btn.grid(row=0, column=3, padx=(0, 2)); options_btn.bind("<Enter>", lambda e, p=item_frame: on_child_enter(e, p)); options_btn.bind("<Leave>", lambda e, p=item_frame: on_child_leave(e, p))
    frame.update_idletasks()

# --- Animation ---
# (animate_window remains the same)
def animate_window(window, target_width, target_height, final_x, final_y):
    if not window or not window.winfo_exists(): return
    current_width, current_height = window.winfo_width(), window.winfo_height()
    step = 30
    if current_width < target_width or current_height < target_height:
        new_width, new_height = min(current_width + step, target_width), min(current_height + step, target_height)
        pos_x, pos_y = int(final_x + (target_width - new_width) / 2), int(final_y + (target_height - new_height) / 2)
        try: window.geometry(f"{new_width}x{new_height}+{pos_x}+{pos_y}"); window.after(10, lambda: animate_window(window, target_width, target_height, final_x, final_y))
        except tk.TclError: pass
    else:
        try: window.geometry(f"{target_width}x{target_height}+{final_x}+{final_y}"); window.resizable(True, True)
        except tk.TclError: pass

# --- Refresh Main Window ---
# (refresh_clipboard_window remains the same)
def refresh_clipboard_window(win_to_refresh):
    if not (win_to_refresh and win_to_refresh.winfo_exists()): return
    try:
        inner_slots_frame = getattr(win_to_refresh, 'slots_frame', None)
        dropdown = getattr(win_to_refresh, 'search_dropdown', None)
        if inner_slots_frame: populate_slots_frame(inner_slots_frame)
        if dropdown:
             sorted_keys = sorted(list(clipboard_slots.keys()), key=lambda k: (k.isdigit(), int(k) if k.isdigit() else k))
             dropdown['values'] = sorted_keys
        win_to_refresh.update_idletasks()
        slots_canvas = getattr(win_to_refresh, 'slots_canvas', None)
        if slots_canvas and inner_slots_frame: slots_canvas.configure(scrollregion=slots_canvas.bbox("all"))
    except Exception as e: print(f"[gui.py] Error during refresh: {e}"); import traceback; traceback.print_exc()

# --- Wrappers for Actions + Refresh ---
# (Wrappers remain the same)
def clear_all_and_refresh(parent_window):
    if clear_clipboard(): schedule_refresh()
def delete_slot_and_refresh(identifier, parent_window):
    if delete_slot(identifier): schedule_refresh()
def assign_slot_and_refresh(identifier, parent_window):
    if assign_slot(identifier): schedule_refresh()
def edit_slot_and_refresh(identifier, parent_window):
    if edit_slot(identifier): schedule_refresh()
def rewrite_content_and_refresh(identifier, parent_window):
    if rewrite_content(identifier): schedule_refresh()
def rephrase_content_and_refresh(identifier, parent_window):
    if rephrase_content(identifier): schedule_refresh()

# --- Window Management ---
# (close_new_window, on_hover, on_leave, close_icon remain the same)
def close_new_window(win_to_close):
    global new_window; print("[gui.py] Closing main window...")
    if win_to_close and win_to_close.winfo_exists():
        try: win_to_close.destroy()
        except tk.TclError: pass
    new_window = None
    if root:
        try:
            if root.winfo_exists(): root.deiconify()
        except tk.TclError: pass
def on_hover(event):
    if close_button:
        try:
             if root and root.winfo_exists(): close_button.place(x=root.winfo_width() - 20, y=0, width=20, height=20)
        except tk.TclError: pass
def on_leave(event):
    if not root or not root.winfo_exists(): return
    try:
        widget_under_mouse = root.winfo_containing(event.x_root, event.y_root)
        if widget_under_mouse is None:
             if close_button and close_button.winfo_exists(): close_button.place_forget(); return
        if widget_under_mouse != root and widget_under_mouse != close_button:
             if close_button and close_button.winfo_exists(): close_button.place_forget()
    except (tk.TclError, AttributeError):
         if close_button and close_button.winfo_exists():
             try: close_button.place_forget()
             except tk.TclError: pass
def close_icon():
    global root, new_window; print("[gui.py] Closing application via icon...")
    if new_window and new_window.winfo_exists():
        try: new_window.destroy()
        except tk.TclError: pass
    new_window = None
    if root:
        try:
            print("[gui.py] Unhooking hotkeys..."); import keyboard; keyboard.unhook_all_hotkeys()
            print("[gui.py] Destroying root window..."); root.destroy()
        except AttributeError: print("[gui.py] Note: unhook_all_hotkeys not fully supported.")
        except tk.TclError: pass
        except Exception as e: print(f"[gui.py] Error during cleanup: {e}")
        root = None