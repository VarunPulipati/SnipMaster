# helpers.py
from tkinter import messagebox
import tkinter as tk
# Removed incorrect: from logging import root

# Note: clipboard_slots and clipboard_history are defined in clipboard.py
# Avoid redefining them here. If needed, import them specifically.
# clipboard_slots = {}
# clipboard_history = []

def keep_on_screen(window):
    """Ensure the window stays on screen."""
    # Consider adding checks if window exists window.winfo_exists()
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
    # Ensure both windows exist before acting
    try:
        if main_window and main_window.winfo_exists():
            main_window.withdraw()
        if icon_window and icon_window.winfo_exists():
            icon_window.deiconify()
    except tk.TclError:
         print("Minimize_to_icon: Window does not exist.")


def search_function(query):
    """Perform a search and show the result."""
    # Import clipboard_slots here if not passed as an argument
    from clipboard import clipboard_slots
    if query in clipboard_slots:
        messagebox.showinfo("Search Result", f"Slot {query}:\n{clipboard_slots[query]}")
    else:
        messagebox.showwarning("Search", f"Slot '{query}' not found!")

# *** CORRECTED DRAG FUNCTIONS ***
def on_drag_start(event, window):
    """Capture the initial position when the drag starts on the specified window."""
    # Store drag data directly on the widget that received the event
    event.widget._drag_data = {"x": event.x, "y": event.y, "window": window}

def on_drag_motion(event, window):
    """Handle the movement while dragging the specified window."""
    # Retrieve drag data from the widget
    drag_data = getattr(event.widget, '_drag_data', None)
    if not drag_data or drag_data["window"] != window:
         # Safety check: Ensure drag_data exists and is for the correct window
         return

    try:
        if window and window.winfo_exists():
             # Calculate new top-left corner coordinates for the window
             x = window.winfo_x() + event.x - drag_data["x"]
             y = window.winfo_y() + event.y - drag_data["y"]
             window.geometry(f"+{x}+{y}") # Update window position
    except tk.TclError:
        print("On_drag_motion: Window does not exist.")