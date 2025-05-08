# helpers.py

import sys
import os
import tkinter as tk
from tkinter import messagebox

def resource_path(relative_path: str) -> str:
    """
    Get absolute path to a resource, works for dev and for PyInstaller one-file builds.

    - If frozen by PyInstaller, resources are unpacked into sys._MEIPASS.
    - Otherwise, look relative to this helpers.py file.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in normal Python, locate relative to this file
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


def keep_on_screen(window):
    """Ensure the window stays fully on-screen."""
    try:
        sw, sh = window.winfo_screenwidth(), window.winfo_screenheight()
        x = max(0, min(window.winfo_x(), sw - window.winfo_width()))
        y = max(0, min(window.winfo_y(), sh - window.winfo_height()))
        window.geometry(f"+{x}+{y}")
    except tk.TclError:
        print("[helpers] keep_on_screen: Window does not exist.")


def minimize_to_icon(main_window, icon_window):
    """Minimize the main window and show the icon window."""
    try:
        if main_window and main_window.winfo_exists():
            main_window.withdraw()
        if icon_window and icon_window.winfo_exists():
            icon_window.deiconify()
    except tk.TclError:
        print("[helpers] minimize_to_icon: Window does not exist.")


def search_function(query):
    """Dialog to show contents of a named slot."""
    # Import locally to avoid circular import at module‑load time
    from clipboard import clipboard_slots
    if query in clipboard_slots:
        messagebox.showinfo("Search Result", f"Slot {query}:\n{clipboard_slots[query]}")
    else:
        messagebox.showwarning("Search", f"Slot '{query}' not found!")


def on_drag_start(event, window):
    """Capture initial coordinates when dragging begins."""
    event.widget._drag_data = {"x": event.x, "y": event.y, "window": window}


def on_drag_motion(event, window):
    """Move the window as the mouse drags."""
    drag_data = getattr(event.widget, "_drag_data", None)
    if not drag_data or drag_data["window"] is not window:
        return
    try:
        x = window.winfo_x() + event.x - drag_data["x"]
        y = window.winfo_y() + event.y - drag_data["y"]
        window.geometry(f"+{x}+{y}")
    except tk.TclError:
        print("[helpers] on_drag_motion: Window does not exist.")
