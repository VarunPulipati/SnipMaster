# helpers.py
from tkinter import messagebox
import tkinter as tk
# --- Added imports needed for resource_path ---
import sys
import os
# ---------------------------------------------

# Note: clipboard_slots defined in clipboard.py
# from clipboard import clipboard_slots # Avoid top-level import if possible


# --- NEW: Function to handle asset paths for PyInstaller ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # sys._MEIPASS is a string containing the path to the temp folder
        base_path = sys._MEIPASS
    except Exception:
        # _MEIPASS attribute not found, running in normal development mode
        # Use the directory of the current file (helpers.py) as base? Or project root?
        # Let's assume helpers.py is in the main clipapp directory.
        # If assets folder is also directly inside clipapp, this works.
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# --- END NEW Function ---


def keep_on_screen(window):
    """Ensure the window stays on screen."""
    try:
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = max(0, min(window.winfo_x(), screen_width - window.winfo_width()))
        y = max(0, min(window.winfo_y(), screen_height - window.winfo_height()))
        window.geometry(f"+{x}+{y}")
    except tk.TclError:
        print("Keep_on_screen: Window does not exist.")


def minimize_to_icon(main_window, icon_window):
    """Minimize the main window to an icon."""
    try:
        if main_window and main_window.winfo_exists():
            main_window.withdraw()
        if icon_window and icon_window.winfo_exists():
            icon_window.deiconify()
    except tk.TclError:
         print("Minimize_to_icon: Window does not exist.")


def search_function(query):
    """Perform a search and show the result."""
    # Import locally to avoid potential circular issues
    from clipboard import clipboard_slots
    if query in clipboard_slots:
        messagebox.showinfo("Search Result", f"Slot {query}:\n{clipboard_slots[query]}")
    else:
        messagebox.showwarning("Search", f"Slot '{query}' not found!")


def on_drag_start(event, window):
    """Capture the initial position when the drag starts on the specified window."""
    event.widget._drag_data = {"x": event.x, "y": event.y, "window": window}

def on_drag_motion(event, window):
    """Handle the movement while dragging the specified window."""
    drag_data = getattr(event.widget, '_drag_data', None)
    if not drag_data or drag_data["window"] != window:
         return
    try:
        if window and window.winfo_exists():
             x = window.winfo_x() + event.x - drag_data["x"]
             y = window.winfo_y() + event.y - drag_data["y"]
             window.geometry(f"+{x}+{y}")
    except tk.TclError:
        print("On_drag_motion: Window does not exist.")