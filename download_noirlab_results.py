# download_noirlab_results.py

from getpass import getpass
from dl import authClient, storeClient
import argparse
import os
import sys
from io import StringIO

def download_all_results(vos_dir, local_dir, log_file=None):
    """
    Download query results from NOIRLab Virtual Storage (VOS).
    
    If log_file is provided, reads it to find which queries were executed,
    then downloads the corresponding .csv files.
    
    If log_file is None, downloads ALL .csv files from the VOS directory.
    
    Args:
        vos_dir: Remote VOS directory name
        local_dir: Local directory to save files
        log_file: (Optional) Query log file to read. If None, downloads all files in VOS.
    """
    
    # Authenticate
    print("[INFO] Authenticating with NOIRLab...")
    username = input("Enter NOIRLab username: ")
    password = getpass("Enter NOIRLab password: ")
    
    token = authClient.login(username, password)
    if not authClient.isValidToken(token):
        raise Exception("[ERROR] Token is not valid. Please check your username/password.")
    print("[OK] Authenticated successfully.")
    
    # Check VOS directory
    vos_path = f'vos://{vos_dir}'
    print(f"[INFO] Checking VOS directory: {vos_path}")
    if not storeClient.access(vos_path):
        raise Exception(f"[ERROR] Remote VOS directory '{vos_path}' does not exist or is not accessible.")
    print(f"[OK] VOS directory accessible.")
    
    # Determine which files to download
    if log_file:
        # Use log file to determine files
        if not os.path.exists(log_file):
            raise FileNotFoundError(f"[ERROR] Query log file '{log_file}' not found.")
        
        csv_files = []
        with open(log_file, "r") as log:
            for line in log:
                parts = line.strip().split()
                if parts and parts[0].endswith(".adql"):
                    csv_file = parts[0].replace(".adql", ".csv")
                    csv_files.append(csv_file)
        
        if not csv_files:
            print("[WARNING] No completed queries found in query log.")
            return
        print(f"[INFO] Found {len(csv_files)} queries in {log_file}")
    else:
        # List all .csv files in VOS directory
        print("[INFO] Listing all files in VOS directory...")
        files = storeClient.ls(vos_path)
        csv_files = [f for f in files if f.endswith(".csv")]
        
        if not csv_files:
            print("[WARNING] No CSV files found in VOS directory.")
            return
        print(f"[INFO] Found {len(csv_files)} CSV files in VOS")
    
    print(f"[RUN] Downloading {len(csv_files)} files...")
    
    # Create local directory if needed
    os.makedirs(local_dir, exist_ok=True)
    
    # Download each CSV file
    failed = []
    for i, filename in enumerate(csv_files, 1):
        try:
            print(f"[{i}/{len(csv_files)}] Downloading: {filename}", end='', flush=True)
            local_path = os.path.join(local_dir, filename)
            
            # Suppress progress output from storeClient.get()
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            try:
                storeClient.get(fr=f"{vos_path}/{filename}", to=local_path)
            finally:
                sys.stdout = old_stdout
            
            print(" [OK]")
        except Exception as e:
            print(f" [ERROR] {e}")
            failed.append(filename)
    
    # Summary
    print(f"\n[OK] Download complete.")
    print(f"[INFO] Successfully downloaded: {len(csv_files) - len(failed)}/{len(csv_files)} files")
    if failed:
        print(f"[WARNING] Failed to download {len(failed)} files:")
        for f in failed:
            print(f"  - {f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download NOIRLab query results from Virtual Object Store (VOS)."
    )
    parser.add_argument(
        "--vos_dir",
        default="cool-lamps-fullsky",
        help="Remote VOS directory name (default: cool-lamps-fullsky)"
    )
    parser.add_argument(
        "--local_dir",
        default=".",
        help="Local directory to save files (default: current directory)"
    )
    parser.add_argument(
        "--log_file",
        default=None,
        help="Query log file to read. If not provided, downloads all CSV files in VOS directory."
    )
    
    args = parser.parse_args()
    download_all_results(
        vos_dir=args.vos_dir,
        local_dir=args.local_dir,
        log_file=args.log_file
    )
