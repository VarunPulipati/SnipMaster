# clipboard.py
import logging
import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog
# --- Add required imports for Gemini ---
import os
try:
    import google.generativeai as genai
except ImportError:
    print("ERROR: google-generativeai library not found.")
    print("Please install it using: pip install -q -U google-generativeai")
    genai = None # Set to None if import fails
# --- End Gemini Imports ---
try:
    import keyboard
    import pyperclip
except ImportError as e: print(f"ERROR: {e}\npip install keyboard pyperclip Pillow"); exit()

# --- Configuration ---
MAX_DEFAULT_SLOTS = 10

# --- Central Data Stores ---
clipboard_slots = {}
valid_identifiers = [chr(i) for i in range(97, 123)]

# --- Refresh Callback Mechanism ---
gui_refresh_callback = None
def set_gui_refresh_callback(callback): global gui_refresh_callback; print("[clipboard.py] Setting GUI refresh callback."); gui_refresh_callback = callback
def trigger_gui_refresh():
    if gui_refresh_callback:
        try: gui_refresh_callback()
        except Exception as e: print(f"[clipboard.py] Error during GUI refresh callback: {e}")

# --- Default Slot Stack Logic ---
def add_to_default_stack(content):
    global clipboard_slots
    print(f"[clipboard.py] Adding to default stack (Max Size: {MAX_DEFAULT_SLOTS})")
    for i in range(MAX_DEFAULT_SLOTS - 1, 0, -1):
        prev_slot_key, next_slot_key = str(i), str(i + 1)
        if prev_slot_key in clipboard_slots and prev_slot_key.isdigit():
                 clipboard_slots[next_slot_key] = clipboard_slots[prev_slot_key]
    clipboard_slots['1'] = content
    # Removed history append
    if str(MAX_DEFAULT_SLOTS + 1) in clipboard_slots and str(MAX_DEFAULT_SLOTS + 1).isdigit():
            del clipboard_slots[str(MAX_DEFAULT_SLOTS + 1)]
    return True

# --- Core Clipboard Functions ---
def clear_clipboard():
    try: pyperclip.copy('')
    except pyperclip.PyperclipException as e: print(f"[clipboard.py] Could not clear system clipboard: {e}")
    clipboard_slots.clear(); return True

def handle_copy(identifier):
    print(f"[clipboard.py] handle_copy TRIGGERED for: '{identifier if identifier else 'DEFAULT STACK'}'")
    def copy_content_thread():
        time.sleep(0.1); data_changed = False
        try:
            content = pyperclip.paste()
            if content and content.strip():
                if identifier in valid_identifiers:
                    clipboard_slots[identifier] = content; print(f"[clipboard.py] Copied to named slot: {identifier}"); data_changed = True
                elif identifier is None:
                    if add_to_default_stack(content): data_changed = True
                else: print(f"[clipboard.py] Invalid identifier received: {identifier}")
            else: print("[clipboard.py] No valid content found on clipboard.")
        except pyperclip.PyperclipException as e: print(f"[clipboard.py] Could not paste from system clipboard: {e}")
        except Exception as e: print(f"[clipboard.py] Error in copy thread: {e}")
        finally:
            if data_changed: trigger_gui_refresh()
    threading.Thread(target=copy_content_thread, daemon=True).start()

def handle_cut(identifier):
     print(f"[clipboard.py] handle_cut TRIGGERED for Slot: '{identifier}'")
     def cut_content_thread():
         data_changed = False
         try:
             keyboard.press_and_release('ctrl+c'); time.sleep(0.1); content = pyperclip.paste()
             if content and content.strip():
                  keyboard.press_and_release('delete'); time.sleep(0.05)
                  if identifier in valid_identifiers:
                      clipboard_slots[identifier] = content; print(f"[clipboard.py] Cut to slot: {identifier}"); data_changed = True
                  else: print(f"[clipboard.py] Invalid identifier for cut: {identifier}")
             else: print("[clipboard.py] No valid content selected to cut to slot.")
         except pyperclip.PyperclipException as e: print(f"[clipboard.py] Clipboard error during cut: {e}")
         except Exception as e: print(f"[clipboard.py] Keyboard simulation error during cut: {e}")
         finally:
             if data_changed: trigger_gui_refresh()
     threading.Thread(target=cut_content_thread, daemon=True).start()

def handle_paste(identifier):
    print(f"[clipboard.py] Paste command triggered for identifier {identifier}")
    slot_key = str(identifier) if isinstance(identifier, int) else identifier
    text_to_paste = clipboard_slots.get(slot_key)
    if text_to_paste:
        try:
            pyperclip.copy(text_to_paste)
            print(f"[clipboard.py] Copied slot {slot_key} content to system clipboard.")
            if identifier in valid_identifiers:
                time.sleep(0.05); keyboard.press_and_release('ctrl+v')
                print(f"[clipboard.py] Simulated paste from slot: {identifier}")
        except pyperclip.PyperclipException as e: print(f"[clipboard.py] Could not copy/paste using system clipboard: {e}")
        except Exception as e: print(f"[clipboard.py] Keyboard/Error during paste setup: {e}")
    else: print(f"[clipboard.py] Slot {slot_key} not found or empty.")

# --- Gemini Integration ---
def call_gemini_api(prompt, text_content):
    """ Helper function to configure and call the Gemini API. """
    if not genai: # Check if import failed
        raise ImportError("google.generativeai library not available.")

    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel('gemini-1.5-flash') # Or use 'gemini-1.5-pro'
        full_prompt = f"{prompt}\n\n{text_content}"
        print(f"[clipboard.py] Sending prompt to Gemini:\n{full_prompt[:100]}...") # Log first part of prompt

        # Add safety settings if needed (optional)
        # safety_settings = [
        #     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        #     {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        #     {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        #     {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        # ]
        # response = model.generate_content(full_prompt, safety_settings=safety_settings)

        response = model.generate_content(full_prompt)

        # Handle potential lack of response text or blocked content
        if response.parts:
             print("[clipboard.py] Received response from Gemini.")
             return response.text
        else:
             print("[clipboard.py] Gemini response blocked or empty.")
             # You might want to inspect response.prompt_feedback here
             # print(response.prompt_feedback)
             return None # Indicate no usable text returned

    except Exception as e:
        print(f"[clipboard.py] Error calling Gemini API: {e}")
        # Re-raise the exception so the calling function can handle it (e.g., show messagebox)
        raise


# --- Updated Rewrite/Rephrase Functions ---
def rewrite_content(identifier):
    """Rewrites the content using Gemini API. Returns True on success."""
    from gui import new_window, root # Local import for parenting messagebox
    parent_win = new_window if new_window and new_window.winfo_exists() else root
    slot_key = str(identifier)

    if slot_key in clipboard_slots:
        current_content = clipboard_slots[slot_key]
        if not current_content.strip():
             messagebox.showwarning("Rewrite", f"Slot '{slot_key}' is empty, nothing to rewrite.", parent=parent_win)
             return False

        print(f"[clipboard.py] Attempting AI rewrite for slot '{slot_key}'...")
        try:
            # Define the prompt for rewriting
            prompt = "Rewrite the following text clearly and concisely:"
            ai_response = call_gemini_api(prompt, current_content)

            if ai_response:
                clipboard_slots[slot_key] = ai_response.strip() # Update slot with AI response
                # Removed history append
                print(f"[clipboard.py] Slot '{slot_key}' updated with AI rewrite.")
                return True # Indicate success
            else:
                 messagebox.showerror("AI Error", "The AI returned an empty or blocked response.", parent=parent_win)
                 return False

        except ImportError as e:
             messagebox.showerror("Import Error", str(e), parent=parent_win)
             return False
        except ValueError as e: # Catch API key error from helper
             messagebox.showerror("Configuration Error", str(e), parent=parent_win)
             return False
        except Exception as e:
            messagebox.showerror("AI Error", f"Failed to get rewrite from AI:\n{e}", parent=parent_win)
            return False

    else: messagebox.showerror("Error", f"Slot '{slot_key}' not found.", parent=parent_win)
    return False

def rephrase_content(identifier):
    """Rephrases the content using Gemini API. Returns True on success."""
    from gui import new_window, root # Local import for parenting messagebox
    parent_win = new_window if new_window and new_window.winfo_exists() else root
    slot_key = str(identifier)

    if slot_key in clipboard_slots:
        content = clipboard_slots.get(slot_key, "")
        if not content.strip():
            messagebox.showwarning("Rephrase", f"Slot '{slot_key}' is empty, nothing to rephrase.", parent=parent_win)
            return False

        print(f"[clipboard.py] Attempting AI rephrase for slot '{slot_key}'...")
        try:
            # Define the prompt for rephrasing
            prompt = "Rephrase the following text to express the same meaning using different wording:"
            ai_response = call_gemini_api(prompt, content)

            if ai_response:
                clipboard_slots[slot_key] = ai_response.strip() # Update slot
                # Removed history append
                print(f"[clipboard.py] Slot '{slot_key}' updated with AI rephrase.")
                return True # Indicate success
            else:
                 messagebox.showerror("AI Error", "The AI returned an empty or blocked response.", parent=parent_win)
                 return False

        except ImportError as e:
             messagebox.showerror("Import Error", str(e), parent=parent_win)
             return False
        except ValueError as e: # Catch API key error
             messagebox.showerror("Configuration Error", str(e), parent=parent_win)
             return False
        except Exception as e:
            messagebox.showerror("AI Error", f"Failed to get rephrase from AI:\n{e}", parent=parent_win)
            return False

    else: messagebox.showerror("Error", f"Slot '{slot_key}' not found.", parent=parent_win)
    return False

# --- Setup Shortcuts ---
def setup_shortcuts():
    print("[clipboard.py] Setting up hotkeys...")
    try:
        try: keyboard.unhook_all_hotkeys()
        except AttributeError: print("[clipboard.py] Note: unhook_all_hotkeys not fully supported.")
        except Exception as e: print(f"[clipboard.py] Error unhooking keys: {e}")
        for identifier in valid_identifiers:
                keyboard.add_hotkey(f'ctrl+c+{identifier}', lambda i=identifier: handle_copy(i))
                keyboard.add_hotkey(f'ctrl+x+{identifier}', lambda i=identifier: handle_cut(i))
                keyboard.add_hotkey(f'ctrl+alt+v+{identifier}', lambda i=identifier: handle_paste(i))
        print("[clipboard.py] Binding: ctrl+c (for default stack)")
        keyboard.add_hotkey('ctrl+c', lambda: handle_copy(None))
        print("[clipboard.py] Keyboard shortcuts set up successfully.")
    except Exception as e:
        print(f"[clipboard.py] FATAL ERROR setting up shortcuts: {e}. Try running as administrator?")
        try: 
            from gui import root
            if root and root.winfo_exists(): messagebox.showerror("Hotkey Error", f"Failed to register hotkeys:\n{e}\n\nPlease try running the application as administrator.")
        except Exception: pass