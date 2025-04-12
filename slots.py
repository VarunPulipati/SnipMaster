# slots.py
from tkinter import Menu, messagebox, simpledialog
import tkinter as tk

# *** CORRECTED IMPORT: Removed clipboard_history ***
from clipboard import clipboard_slots # Only import clipboard_slots

def delete_slot(identifier):
    """Deletes a slot. Assumes refresh is handled by caller."""
    from gui import new_window, root # Import for parenting dialogs
    parent_win = new_window if new_window and new_window.winfo_exists() else root

    slot_key = str(identifier) # Ensure string key
    if slot_key in clipboard_slots:
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Slot '{slot_key}'?", parent=parent_win):
            del clipboard_slots[slot_key]
            # Removed history append
            return True # Indicate success
    else:
        messagebox.showwarning("Delete", f"Slot '{slot_key}' does not exist.", parent=parent_win)
    return False # Indicate failure or cancellation

# *** assign_default_slot function REMOVED FROM HERE (it's in clipboard.py) ***

def show_context_menu(event, parent_window, options):
    """Display a context menu."""
    if not parent_window or not parent_window.winfo_exists():
        print("Debug: Cannot show context menu, parent window invalid.")
        return

    menu = Menu(parent_window, tearoff=0,
                bg="#FFFFFF", fg="#333333",
                activebackground="#0078D7", activeforeground="#FFFFFF")
    for label, command in options:
        if label == "---":
             menu.add_separator()
        elif callable(command):
            menu.add_command(label=label, command=command)
        else:
             pass
    try:
        menu.post(event.x_root, event.y_root)
    except tk.TclError as e:
        print(f"Debug: Failed to post context menu: {e}")

def edit_slot(identifier):
    """Edit the slot name using a dialog. Returns True on success."""
    from gui import new_window, root
    parent_win = new_window if new_window and new_window.winfo_exists() else root

    slot_key = str(identifier) # Ensure string key
    if slot_key in clipboard_slots:
        new_name = simpledialog.askstring("Edit Slot Name", f"Enter new name for Slot '{slot_key}':",
                                          parent=parent_win)
        if new_name and new_name.strip():
            new_name = new_name.strip()
            if new_name == slot_key:
                return False # No change
            if new_name not in clipboard_slots:
                clipboard_slots[new_name] = clipboard_slots.pop(slot_key)
                # Removed history append
                return True # Success
            else:
                messagebox.showwarning("Edit Slot", f"Slot name '{new_name}' already exists.", parent=parent_win)
        # else: User cancelled or entered empty string
    else:
        messagebox.showwarning("Edit Slot", f"Slot '{slot_key}' does not exist.", parent=parent_win)
    return False # Failure or cancellation

def assign_slot(identifier):
    """Assign new content to a slot using a dialog. Returns True on success."""
    from gui import new_window, root
    parent_win = new_window if new_window and new_window.winfo_exists() else root

    slot_key = str(identifier) # Ensure string key
    # Ask for new content
    new_content = simpledialog.askstring("Assign Content", f"Enter content for Slot '{slot_key}':",
                                         parent=parent_win)
    if new_content is not None: # User pressed OK (content can be empty string)
         clipboard_slots[slot_key] = new_content
         # Removed history append
         return True # Success
    # else: User cancelled
    return False # Cancellation