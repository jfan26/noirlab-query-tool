# download_noirlab_results.py

from getpass import getpass
from dl import authClient, storeClient
import argparse
import os

def download_all_results(vos_dir, local_dir, log_file):
    """
    Download all query results from NOIRLab Virtual Storage (VOS).
    
    Reads log_file to find which queries were executed, then downloads
    the corresponding .csv files from the remote VOS directory.
    
    Args:
        vos_dir: Remote VOS directory name
        local_dir: Local directory to save files
        log_file: Query log file to read
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
    
    # Read query log to find completed queries
    if not os.path.exists(log_file):
        raise FileNotFoundError(f"[ERROR] Query log file '{log_file}' not found. Run submit_noirlab_adql.py first.")
    
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
    
    print(f"[RUN] Found {len(csv_files)} completed query results to download.")
    
    # Create local directory if needed
    os.makedirs(local_dir, exist_ok=True)
    
    # Download each CSV file
    failed = []
    for i, filename in enumerate(csv_files, 1):
        try:
            print(f"\n[{i}/{len(csv_files)}] Downloading: {filename}")
            local_path = os.path.join(local_dir, filename)
            storeClient.get(fr=f"{vos_path}/{filename}", to=local_path)
            print(f"[OK] Saved to {local_path}")
        except Exception as e:
            print(f"[ERROR] Failed to download {filename}: {e}")
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
        description="Download all NOIRLab query results from Virtual Object Store (VOS)."
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
        default="query_log.txt",
        help="Query log file to read (default: query_log.txt)"
    )
    
    args = parser.parse_args()
    download_all_results(
        vos_dir=args.vos_dir,
        local_dir=args.local_dir,
        log_file=args.log_file
    )
