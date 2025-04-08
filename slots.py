# slots.py
from tkinter import Menu, messagebox, simpledialog
import tkinter as tk

# *** Keep import from clipboard for data stores ***
from clipboard import clipboard_slots, clipboard_history

def delete_slot(identifier):
    """Deletes a slot. Assumes refresh is handled by caller."""
    from gui import new_window, root # Import for parenting dialogs
    parent_win = new_window if new_window and new_window.winfo_exists() else root

    if identifier in clipboard_slots:
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Slot '{identifier}'?", parent=parent_win):
            del clipboard_slots[identifier]
            clipboard_history.append(f"Deleted Slot {identifier}")
            return True
    else:
        messagebox.showwarning("Delete", f"Slot '{identifier}' does not exist.", parent=parent_win)
    return False

# *** assign_default_slot function REMOVED FROM HERE ***

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

    if identifier in clipboard_slots:
        new_name = simpledialog.askstring("Edit Slot Name", f"Enter new name for Slot '{identifier}':",
                                          parent=parent_win)
        if new_name and new_name.strip():
            new_name = new_name.strip()
            if new_name == identifier:
                return False
            if new_name not in clipboard_slots:
                clipboard_slots[new_name] = clipboard_slots.pop(identifier)
                clipboard_history.append(f"Renamed Slot {identifier} to {new_name}")
                return True
            else:
                messagebox.showwarning("Edit Slot", f"Slot name '{new_name}' already exists.", parent=parent_win)
    else:
        messagebox.showwarning("Edit Slot", f"Slot '{identifier}' does not exist.", parent=parent_win)
    return False

def assign_slot(identifier):
    """Assign new content to a slot using a dialog. Returns True on success."""
    from gui import new_window, root
    parent_win = new_window if new_window and new_window.winfo_exists() else root

    new_content = simpledialog.askstring("Assign Content", f"Enter content for Slot '{identifier}':",
                                         parent=parent_win)
    if new_content is not None:
         clipboard_slots[identifier] = new_content
         clipboard_history.append(f"Assigned content to Slot {identifier}")
         return True
    return False