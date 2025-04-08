# clipboard.py
import logging
import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog
try:
    import keyboard
    import pyperclip
except ImportError as e:
    print(f"ERROR: Missing required library: {e}. Please install using:")
    print("pip install keyboard pyperclip Pillow")
    exit()

# --- Configuration ---
MAX_DEFAULT_SLOTS = 10 # Max number of stacked items for default Ctrl+C

# --- Central Data Stores ---
clipboard_slots = {} # Can contain '1', '2', ..., 'a', 'b', ...
clipboard_history = []
valid_identifiers = [chr(i) for i in range(97, 123)] # a-z for named slots

# --- Refresh Callback Mechanism ---
gui_refresh_callback = None

def set_gui_refresh_callback(callback):
    global gui_refresh_callback
    print("[clipboard.py] Setting GUI refresh callback.")
    gui_refresh_callback = callback

def trigger_gui_refresh():
    if gui_refresh_callback:
        try: gui_refresh_callback()
        except Exception as e: print(f"[clipboard.py] Error during GUI refresh callback: {e}")

# --- Stack Logic for Default Slots ---
def add_to_default_stack(content):
    """Adds content to stack slot '1', shifting others down."""
    global clipboard_slots, clipboard_history
    print(f"[clipboard.py] Adding to default stack (Max Size: {MAX_DEFAULT_SLOTS})")
    # Shift existing numbered slots down (from max-1 down to 1)
    for i in range(MAX_DEFAULT_SLOTS - 1, 0, -1):
        prev_slot_key = str(i)
        next_slot_key = str(i + 1)
        if prev_slot_key in clipboard_slots:
            # Check if it's actually a numbered slot before shifting
            if prev_slot_key.isdigit():
                 clipboard_slots[next_slot_key] = clipboard_slots[prev_slot_key]
                 # print(f"[clipboard.py] Shifted '{prev_slot_key}' -> '{next_slot_key}'") # Debug

    # Add the new content to slot '1'
    clipboard_slots['1'] = content
    # print(f"[clipboard.py] Added new content to slot '1'") # Debug
    clipboard_history.append(f"Copied to Stack Slot 1: {content[:30]}...")

    # Clean up any numbered slot beyond the max size (optional)
    if str(MAX_DEFAULT_SLOTS + 1) in clipboard_slots:
        if str(MAX_DEFAULT_SLOTS + 1).isdigit():
            # print(f"[clipboard.py] Removing old slot '{MAX_DEFAULT_SLOTS + 1}'") # Debug
            del clipboard_slots[str(MAX_DEFAULT_SLOTS + 1)]

    return True # Indicate data changed


# --- Core Clipboard Functions ---
def clear_clipboard():
    # (Same as before)
    try: pyperclip.copy('')
    except pyperclip.PyperclipException as e: print(f"[clipboard.py] Could not clear system clipboard: {e}")
    clipboard_slots.clear()
    clipboard_history.append("Cleared All Slots")
    return True

def handle_copy(identifier):
    # Now handles identifier=None for stack, or letter for named slot
    print(f"[clipboard.py] handle_copy TRIGGERED for: '{identifier if identifier else 'DEFAULT STACK'}'")
    def copy_content_thread():
        time.sleep(0.1)
        data_changed = False
        try:
            content = pyperclip.paste()
            if content and content.strip():
                if identifier in valid_identifiers: # Named slot (a-z)
                    clipboard_slots[identifier] = content
                    clipboard_history.append(f"Copied to Slot {identifier}: {content[:30]}...")
                    print(f"[clipboard.py] Copied to named slot: {identifier}")
                    data_changed = True
                elif identifier is None: # Default action (Ctrl+C alone) -> Add to stack
                    if add_to_default_stack(content):
                        data_changed = True
                else:
                    print(f"[clipboard.py] Invalid identifier received: {identifier}")
            else: print("[clipboard.py] No valid content found on clipboard.")
        except pyperclip.PyperclipException as e: print(f"[clipboard.py] Could not paste from system clipboard: {e}")
        except Exception as e: print(f"[clipboard.py] Error in copy thread: {e}")
        finally:
            if data_changed: trigger_gui_refresh()

    threading.Thread(target=copy_content_thread, daemon=True).start()


# handle_cut - Let's keep standard Ctrl+X NOT bound for now.
# If you want Ctrl+X+{letter}, we can add it back.
# If you want Ctrl+X alone to add to stack, similar logic to handle_copy(None) needed.
def handle_cut(identifier):
     # Only called by Ctrl+X+{letter} if bound below
     print(f"[clipboard.py] handle_cut TRIGGERED for Slot: '{identifier}'")
     # (Code remains same as previous version where it handles named slots)
     def cut_content_thread():
         data_changed = False
         try:
             keyboard.press_and_release('ctrl+c')
             time.sleep(0.1)
             content = pyperclip.paste()
             if content and content.strip():
                  keyboard.press_and_release('delete')
                  time.sleep(0.05)
                  if identifier in valid_identifiers:
                      clipboard_slots[identifier] = content
                      clipboard_history.append(f"Cut to Slot {identifier}: {content[:30]}...")
                      print(f"[clipboard.py] Cut to slot: {identifier}")
                      data_changed = True
                  else: print(f"[clipboard.py] Invalid identifier for cut: {identifier}")
             else: print("[clipboard.py] No valid content selected to cut to slot.")
         except pyperclip.PyperclipException as e: print(f"[clipboard.py] Clipboard error during cut: {e}")
         except Exception as e: print(f"[clipboard.py] Keyboard simulation error during cut: {e}")
         finally:
             if data_changed: trigger_gui_refresh()
     threading.Thread(target=cut_content_thread, daemon=True).start()


def handle_paste(identifier):
    # Called by Ctrl+Alt+V+{letter} OR context menu
    print(f"[clipboard.py] Paste command triggered for identifier {identifier}")
    slot_key = identifier
    # If identifier is potentially numeric from GUI, ensure it's string for dict lookup
    if isinstance(identifier, int):
        slot_key = str(identifier)

    text_to_paste = clipboard_slots.get(slot_key)
    if text_to_paste:
        try:
            pyperclip.copy(text_to_paste) # Put slot content onto system clipboard
            print(f"[clipboard.py] Copied slot {slot_key} content to system clipboard.")
            # Check if called via hotkey context (needs paste simulation)
            # This check is imperfect. Assume if identifier is in valid_identifiers (a-z) it was hotkey?
            if identifier in valid_identifiers:
                time.sleep(0.05)
                keyboard.press_and_release('ctrl+v') # Simulate standard paste
                clipboard_history.append(f"Pasted from Slot {identifier}")
                print(f"[clipboard.py] Simulated paste from slot: {identifier}")
            else:
                # If called via context menu, just copying to clipboard is enough
                 clipboard_history.append(f"Copied Slot {slot_key} to system clipboard")
                 # Maybe show info message? Handled in GUI wrapper perhaps.
        except pyperclip.PyperclipException as e: print(f"[clipboard.py] Could not copy/paste using system clipboard: {e}")
        except Exception as e: print(f"[clipboard.py] Keyboard/Error during paste setup: {e}")
    else:
        print(f"[clipboard.py] Slot {slot_key} not found or empty.")


# (rewrite_content, rephrase_content remain the same)
def rewrite_content(identifier):
    from gui import new_window, root
    parent_win = new_window if new_window and new_window.winfo_exists() else root
    slot_key = str(identifier) # Ensure string key
    if slot_key in clipboard_slots:
        current_content = clipboard_slots[slot_key]
        new_content = simpledialog.askstring("Rewrite Content", f"Enter new content for Slot '{slot_key}':",
                                             initialvalue=current_content, parent=parent_win)
        if new_content is not None:
            clipboard_slots[slot_key] = new_content
            clipboard_history.append(f"Rewrote Slot {slot_key}")
            return True
    else: messagebox.showerror("Error", f"Slot '{slot_key}' not found.", parent=parent_win)
    return False

def rephrase_content(identifier):
    from gui import new_window, root
    parent_win = new_window if new_window and new_window.winfo_exists() else root
    slot_key = str(identifier) # Ensure string key
    if slot_key in clipboard_slots:
        content = clipboard_slots.get(slot_key, "")
        if content:
            rephrased = f"(Rephrased) {content}"
            clipboard_slots[slot_key] = rephrased
            clipboard_history.append(f"Rephrased Slot {slot_key}")
            return True
        else: messagebox.showwarning("Rephrase", f"Slot '{slot_key}' is empty.", parent=parent_win)
    else: messagebox.showerror("Error", f"Slot '{slot_key}' not found.", parent=parent_win)
    return False


def setup_shortcuts():
    """Sets up global keyboard shortcuts."""
    print("[clipboard.py] Setting up hotkeys...")
    try:
        try: keyboard.unhook_all_hotkeys()
        except AttributeError: print("[clipboard.py] Note: unhook_all_hotkeys not fully supported.")
        except Exception as e: print(f"[clipboard.py] Error unhooking keys: {e}")

        # === Named Slot Hotkeys ===
        for identifier in valid_identifiers:
                # Using default trigger (on press)
                keyboard.add_hotkey(f'ctrl+c+{identifier}', lambda i=identifier: handle_copy(i))
                keyboard.add_hotkey(f'ctrl+x+{identifier}', lambda i=identifier: handle_cut(i))
                keyboard.add_hotkey(f'ctrl+alt+v+{identifier}', lambda i=identifier: handle_paste(i))

        # === Default Stack Hotkey ===
        # Bind plain Ctrl+C to handle_copy(None)
        print("[clipboard.py] Binding: ctrl+c (for default stack)")
        keyboard.add_hotkey('ctrl+c', lambda: handle_copy(None))

        # *** Standard Ctrl+X and Ctrl+V are NOT bound, they work normally ***

        print("[clipboard.py] Keyboard shortcuts set up successfully.")
    except Exception as e:
        print(f"[clipboard.py] FATAL ERROR setting up shortcuts: {e}. Try running as administrator?")
        try:
            from gui import root
            if root and root.winfo_exists(): messagebox.showerror("Hotkey Error", f"Failed to register hotkeys:\n{e}\n\nPlease try running the application as administrator.")
        except: pass