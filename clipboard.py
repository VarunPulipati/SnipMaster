# clipapp/clipboard.py

import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog

# --- Add requests import ---
try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not found or failed to import.")
    print("Please install it using: pip install requests")
    try: messagebox.showerror("Missing Library", "The required 'requests' library is not installed.\nPlease run 'pip install requests' in your terminal.")
    except: pass
    requests = None
    exit() # Exit if requests is not available
# --- End Import Changes ---

try:
    import keyboard
    import pyperclip
except ImportError as e:
    print(f"ERROR: Required library missing: {e}\nPlease run: pip install keyboard pyperclip")
    try: messagebox.showerror("Missing Library", f"Required library missing: {e}")
    except: pass
    exit() # Exit if essential libraries are missing

# --- Configuration ---
MAX_DEFAULT_SLOTS = 10
# *** DEFINE YOUR BACKEND API URL ***
# Use your local Django server URL for testing first. Change before distribution!
BACKEND_AI_ENDPOINT = "http://127.0.0.1:8000/api/ai-process/" # Ensure trailing slash matches urls.py

# --- Central Data Stores ---
clipboard_slots = {}
valid_identifiers = [chr(i) for i in range(97, 123)]

# --- Refresh Callback Mechanism ---
gui_refresh_callback = None
def set_gui_refresh_callback(callback): global gui_refresh_callback; print("[clipapp/clipboard.py] Setting GUI refresh callback."); gui_refresh_callback = callback
def trigger_gui_refresh():
    if gui_refresh_callback:
        try:
            gui_refresh_callback()
        except Exception as e:
            print(f"[clipapp/clipboard.py] Error during GUI refresh callback: {e}")

# --- Default Slot Stack Logic ---
def add_to_default_stack(content):
    global clipboard_slots
    print(f"[clipapp/clipboard.py] Adding to default stack (Max Size: {MAX_DEFAULT_SLOTS})")
    try: # Added try block for safety during dict manipulation
        for i in range(MAX_DEFAULT_SLOTS - 1, 0, -1):
            prev_slot_key, next_slot_key = str(i), str(i + 1)
            if prev_slot_key in clipboard_slots and prev_slot_key.isdigit():
                 clipboard_slots[next_slot_key] = clipboard_slots[prev_slot_key]
        clipboard_slots['1'] = content
        if str(MAX_DEFAULT_SLOTS + 1) in clipboard_slots and str(MAX_DEFAULT_SLOTS + 1).isdigit():
                del clipboard_slots[str(MAX_DEFAULT_SLOTS + 1)]
        return True
    except Exception as e:
        print(f"[clipapp/clipboard.py] Error in add_to_default_stack: {e}")
        return False


# --- Core Clipboard Functions ---
def clear_clipboard():
    try:
        pyperclip.copy('')
    except pyperclip.PyperclipException as e:
        print(f"[clipapp/clipboard.py] Could not clear system clipboard: {e}")
    clipboard_slots.clear()
    return True

def handle_copy(identifier):
    print(f"[clipapp/clipboard.py] handle_copy TRIGGERED for: '{identifier if identifier else 'DEFAULT STACK'}'")
    def copy_content_thread():
        time.sleep(0.1)
        data_changed = False
        try:
            content = pyperclip.paste()
            if content and content.strip():
                if identifier in valid_identifiers:
                    clipboard_slots[identifier] = content
                    print(f"[clipapp/clipboard.py] Copied to named slot: {identifier}")
                    data_changed = True
                elif identifier is None:
                    if add_to_default_stack(content):
                        data_changed = True
                else:
                    print(f"[clipapp/clipboard.py] Invalid identifier received: {identifier}")
            else:
                print("[clipapp/clipboard.py] No valid content found on clipboard.")
        except pyperclip.PyperclipException as e:
            print(f"[clipapp/clipboard.py] Could not paste from system clipboard: {e}")
        except Exception as e:
            print(f"[clipapp/clipboard.py] Error in copy thread: {e}")
        finally:
            if data_changed:
                trigger_gui_refresh()
    # Start thread
    threading.Thread(target=copy_content_thread, daemon=True).start()

def handle_cut(identifier):
    print(f"[clipapp/clipboard.py] handle_cut TRIGGERED for Slot: '{identifier}'")
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
                    print(f"[clipapp/clipboard.py] Cut to slot: {identifier}")
                    data_changed = True
                else:
                    print(f"[clipapp/clipboard.py] Invalid identifier for cut: {identifier}")
            # This else corresponds to 'if content and content.strip():'
            else:
                print("[clipapp/clipboard.py] No valid content selected to cut to slot.")
        except pyperclip.PyperclipException as e:
            print(f"[clipapp/clipboard.py] Clipboard error during cut: {e}")
        except Exception as e:
            print(f"[clipapp/clipboard.py] Keyboard simulation error during cut: {e}")
        finally:
            if data_changed:
                trigger_gui_refresh()
    # Start thread
    threading.Thread(target=cut_content_thread, daemon=True).start()

def handle_paste(identifier):
    print(f"[clipapp/clipboard.py] Handle Paste/Copy to system clipboard for identifier {identifier}")
    slot_key = str(identifier) if isinstance(identifier, int) else identifier
    text_to_paste = clipboard_slots.get(slot_key)
    if text_to_paste:
        try:
            pyperclip.copy(text_to_paste)
            print(f"[clipapp/clipboard.py] Copied slot {slot_key} content to system clipboard.")
            # Only simulate paste if triggered via the specific hotkey
            if isinstance(identifier, str) and identifier in valid_identifiers:
                time.sleep(0.05)
                keyboard.press_and_release('ctrl+v')
                print(f"[clipapp/clipboard.py] Simulated paste from slot: {identifier}")
        except pyperclip.PyperclipException as e:
            print(f"[clipapp/clipboard.py] Could not copy to system clipboard: {e}")
        except Exception as e:
            print(f"[clipapp/clipboard.py] Keyboard/Error during paste action: {e}")
    else:
        print(f"[clipapp/clipboard.py] Slot {slot_key} not found or empty.")


# --- Function to Call Backend AI Proxy ---
def call_backend_ai(action, text_content):
    """ Calls the backend server API to perform AI actions. """
    if not requests:
        raise ImportError("'requests' library not installed or failed to import. Run: pip install requests")

    payload = {"action": action, "text": text_content}
    headers = {'Content-Type': 'application/json'}
    # TODO: Add Authorization header later if backend requires login/token

    print(f"[clipapp/clipboard.py] Sending '{action}' request to backend: {BACKEND_AI_ENDPOINT}")
    try:
        response = requests.post(BACKEND_AI_ENDPOINT, headers=headers, json=payload, timeout=60)
        response.raise_for_status() # Check for HTTP errors (4xx, 5xx)
        response_data = response.json()
        ai_result = response_data.get('result')

        if ai_result is not None:
            print("[clipapp/clipboard.py] Received AI result from backend.")
            return ai_result
        else:
            error_msg = response_data.get('error', 'Backend OK but no valid result/error field.')
            print(f"[clipapp/clipboard.py] Backend error or missing result: {error_msg}")
            raise ValueError(f"AI Processing Failed: {error_msg}")

    except requests.exceptions.Timeout:
        print("[clipapp/clipboard.py] Error: Request to backend timed out.")
        raise TimeoutError("The request to the AI processing server timed out (60s).")
    except requests.exceptions.ConnectionError as e:
        print(f"[clipapp/clipboard.py] Error: Could not connect to backend at {BACKEND_AI_ENDPOINT}: {e}")
        raise ConnectionError(f"Cannot reach processing server at {BACKEND_AI_ENDPOINT}. Check connection and if backend is running.")
    except requests.exceptions.HTTPError as e:
        error_message = f"Server Error: {e.response.status_code}"
        try: error_detail = e.response.json().get('error', '')
        except: error_detail = ''
        if error_detail: error_message = f"Backend Error ({e.response.status_code}): {error_detail}"
        print(f"[clipapp/clipboard.py] HTTP error calling backend API: {error_message}")
        raise ConnectionError(error_message)
    except Exception as e:
         print(f"[clipapp/clipboard.py] Unexpected error during backend call: {type(e).__name__}: {e}")
         raise RuntimeError(f"An unexpected error occurred contacting the backend: {e}")


# --- Functions Using Backend AI ---
def rewrite_content(identifier):
    """Rewrites the content using the Backend AI Proxy. Returns True on success."""
    from gui import new_window, root
    parent_win = new_window if new_window and new_window.winfo_exists() else root
    slot_key = str(identifier)

    if slot_key in clipboard_slots:
        current_content = clipboard_slots[slot_key]
        if not current_content.strip(): messagebox.showwarning("Rewrite", f"Slot '{slot_key}' is empty.", parent=parent_win); return False

        print(f"[clipapp/clipboard.py] Attempting AI rewrite via backend for slot '{slot_key}'...")
        try:
            ai_response = call_backend_ai("rewrite", current_content)
            clipboard_slots[slot_key] = ai_response
            print(f"[clipapp/clipboard.py] Slot '{slot_key}' updated with AI rewrite from backend.")
            trigger_gui_refresh()
            return True
        except (ImportError, ValueError, ConnectionError, TimeoutError, RuntimeError) as e: messagebox.showerror("AI Rewrite Error", str(e), parent=parent_win)
        except Exception as e: messagebox.showerror("Error", f"Failed to get rewrite:\n{type(e).__name__}: {e}", parent=parent_win)
        return False # Return False if any exception occurred
    else: messagebox.showerror("Error", f"Slot '{slot_key}' not found.", parent=parent_win); return False

def rephrase_content(identifier):
    """Rephrases the content using the Backend AI Proxy. Returns True on success."""
    from gui import new_window, root
    parent_win = new_window if new_window and new_window.winfo_exists() else root
    slot_key = str(identifier)

    if slot_key in clipboard_slots:
        content = clipboard_slots.get(slot_key, "")
        if not content.strip(): messagebox.showwarning("Rephrase", f"Slot '{slot_key}' is empty.", parent=parent_win); return False

        print(f"[clipapp/clipboard.py] Attempting AI rephrase via backend for slot '{slot_key}'...")
        try:
            ai_response = call_backend_ai("rephrase", content)
            clipboard_slots[slot_key] = ai_response
            print(f"[clipapp/clipboard.py] Slot '{slot_key}' updated with AI rephrase from backend.")
            trigger_gui_refresh()
            return True
        except (ImportError, ValueError, ConnectionError, TimeoutError, RuntimeError) as e: messagebox.showerror("AI Rephrase Error", str(e), parent=parent_win)
        except Exception as e: messagebox.showerror("Error", f"Failed to get rephrase:\n{type(e).__name__}: {e}", parent=parent_win)
        return False # Return False if any exception occurred
    else: messagebox.showerror("Error", f"Slot '{slot_key}' not found.", parent=parent_win); return False

# --- Setup Shortcuts ---
def setup_shortcuts():
    print("[clipapp/clipboard.py] Setting up hotkeys...")
    try: # Outer try for overall hotkey setup
        try: # Inner try for unhooking
            keyboard.unhook_all_hotkeys()
        except AttributeError: print("[clipapp/clipboard.py] Note: unhook_all_hotkeys not fully supported.")
        except Exception as e: print(f"[clipapp/clipboard.py] Error unhooking keys: {e}") # End inner except

        # Bindings loop
        for identifier in valid_identifiers:
                keyboard.add_hotkey(f'ctrl+c+{identifier}', lambda i=identifier: handle_copy(i))
                keyboard.add_hotkey(f'ctrl+x+{identifier}', lambda i=identifier: handle_cut(i))
                keyboard.add_hotkey(f'ctrl+alt+v+{identifier}', lambda i=identifier: handle_paste(i))

        # Default binding
        print("[clipapp/clipboard.py] Binding: ctrl+c (for default stack)")
        keyboard.add_hotkey('ctrl+c', lambda: handle_copy(None))

        print("[clipapp/clipboard.py] Keyboard shortcuts set up successfully.")

    except Exception as e: # Belongs to the outer try block
        print(f"[clipapp/clipboard.py] FATAL ERROR setting up shortcuts: {e}. Try running as administrator?")
        # Nested try for showing error in GUI
        try:
            from gui import root # Local import for error message
            if root and root.winfo_exists(): messagebox.showerror("Hotkey Error", f"Failed to register hotkeys:\n{e}\n\nPlease try running the application as administrator.")
        except Exception: # Catch potential errors showing the error
             pass # Ignore if GUI isn't available or error occurs showing message