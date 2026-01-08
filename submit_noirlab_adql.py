# submit_noirlab_adql.py

import os
import webbrowser
import pyperclip
import sys
import platform
from datetime import datetime

# Platform-specific imports
if platform.system() != "Windows":
    import tty
    import termios
else:
    import msvcrt

# Config parameters
PREVIEW_LIMIT = 10
STORAGE_LIMIT = 10000000
CSV_OUTPUT_PREFIX = "cool-lamps-fullsky/"  # Edit this to add a prefix to your CSV filenames (we will use "cool-lamps-fullsky/")

def wait_for_key(prompt, valid_keys):
    """Wait for a specific keypress (e.g. ' ' for space, '\r' for enter). Cross-platform."""
    print(prompt, end='', flush=True)
    
    if platform.system() == "Windows":
        # Windows implementation using msvcrt
        while True:
            ch = msvcrt.getch().decode('utf-8', errors='ignore')
            if ch == '\x03':  # Ctrl+C
                raise KeyboardInterrupt
            if ch.lower() == 'q':
                print("\n[QUIT] Quit by user request.")
                sys.exit(0)
            if ch in valid_keys or (ch == '\r' and '\r' in valid_keys):
                print()  # New line after keypress
                return ch
    else:
        # Unix/macOS implementation using termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            buffer = ''
            while True:
                ch = sys.stdin.read(1)
                if ch == '\x03':  # Ctrl+C
                    raise KeyboardInterrupt
                if ch in valid_keys:
                    print('\r')  # Carriage return to reset cursor position
                    return ch
                buffer += ch
                # If user types full word like "quit"
                if buffer.lower() in ['q', 'quit']:
                    print("\n[QUIT] Quit by user request.")
                    sys.exit(0)
                # Reset if the buffer gets too long or if there's a newline
                if len(buffer) > 5 or ch in ['\r', '\n']:
                    print(f"\n[ERROR] Invalid input. Press only {repr(valid_keys)} or 'q' to quit.")
                    print(prompt, end='', flush=True)
                    buffer = ''
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def paste_next_query_and_log(directory="adql_queries", log_file="query_log.txt"):
    files = sorted(f for f in os.listdir(directory) if f.endswith(".adql") and not f.startswith("DONE_"))
    
    if not files:
        print("[OK] No ADQL files to process.")
        return

    print(f"[RUN] Starting to process {len(files)} queries...")

    for next_file in files:
        filepath = os.path.join(directory, next_file)
        # Generate CSV base filename from query filename (without .adql extension)
        base_filename = CSV_OUTPUT_PREFIX + os.path.splitext(next_file)[0]

        # Read and copy query to clipboard
        with open(filepath, "r") as f:
            query = f.read()
        pyperclip.copy(query)
        print(f"\n[CLIPBOARD] Copied {next_file} to clipboard.")

        # Open browser
        # webbrowser.open("https://datalab.noirlab.edu/legacy/query.php")
        webbrowser.open("https://datalab.noirlab.edu/data-explorer")
        print("[INFO] Opened NOIRLab Data Explorer.")
        print("[HELP] Paste the query manually into the ADQL field (Ctrl+V / Cmd+V).")

        # Copy Preview Limit to clipboard
        wait_for_key("[WAIT] Press [space] after you've pasted the query to copy the Preview Limit ({0}): ".format(PREVIEW_LIMIT), valid_keys=[' '])
        pyperclip.copy(str(PREVIEW_LIMIT))
        print("[CLIPBOARD] Copied Preview Limit: {0}".format(PREVIEW_LIMIT))

        # Copy .csv base file name (and directory) to clipboard
        wait_for_key("[WAIT] Press [space] after you've pasted the Preview Limit to get your .csv base filename: ", valid_keys=[' '])
        print("[HELP] Click \"Virtual Storage\" to show the \"Result Name\" field.")
        print("[INFO] Filename for CSV export: '{0}'".format(base_filename))
        pyperclip.copy(base_filename)
        print("[CLIPBOARD] Copied CSV filename to clipboard.")

        # Copy Storage Limit to clipboard
        wait_for_key("[WAIT] Press [space] to copy the Storage Limit ({0:,}): ".format(STORAGE_LIMIT), valid_keys=[' '])
        pyperclip.copy(str(STORAGE_LIMIT))
        print("[CLIPBOARD] Copied Storage Limit: {0:,}".format(STORAGE_LIMIT))

        # Submit the query
        wait_for_key("[WAIT] Press [Enter] after you've submitted the query (hit 'Process') to submit the query... ", valid_keys=['\r'])
        
        # Rename the file to mark as done
        done_path = os.path.join(directory, "DONE_" + next_file)
        os.rename(filepath, done_path)

        # Log it
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a") as log:
            log.write(f"{next_file}\texecuted\t{timestamp}\n")

        print(f"[OK] Logged and marked as done: {next_file}")

    print("\n[OK] All ADQL queries processed and logged.")

# Run
if __name__ == "__main__":
    paste_next_query_and_log()
