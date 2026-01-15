#!/usr/bin/env python3
# submit_noirlab_adql_client.py

import argparse
from datetime import datetime
from getpass import getpass
import inspect
import os
import sys
import time

try:
    from dl import authClient, queryClient, storeClient
except Exception as exc:
    print(f"[ERROR] astro-datalab is required to submit queries: {exc}")
    sys.exit(1)

DEFAULT_VOS_DIR = "cool-lamps-fullsky"
DEFAULT_QUERY_DIR = "adql_queries"
DEFAULT_LOG_FILE = "query_log.txt"


def _login(username=None):
    username = username or input("Enter NOIRLab username: ")
    password = getpass("Enter NOIRLab password: ")
    token = authClient.login(username, password)
    if not authClient.isValidToken(token):
        raise RuntimeError("[ERROR] Token is not valid. Please check your username/password.")
    return token




def _logout():
    if hasattr(authClient, "logout"):
        try:
            authClient.logout()
            print("[INFO] Logged out.")
        except Exception as exc:
            print(f"[WARN] Logout failed: {exc}")
    else:
        print("[WARN] authClient.logout() not available; token may remain cached.")

def _ensure_vos_dir(vos_dir, create=False):
    vos_root = f"vos://{vos_dir}"
    if storeClient.access(vos_root):
        return
    if create:
        storeClient.mkdir(vos_root)
        if storeClient.access(vos_root):
            return
    raise RuntimeError(f"[ERROR] Remote VOS directory '{vos_root}' not accessible.")


def _run_query(adql, **kwargs):
    try:
        return queryClient.query(adql=adql, **kwargs)
    except Exception as exc:
        if "No query specified" not in str(exc):
            raise
        return queryClient.query(sql=adql, **kwargs)


def _has_kwargs_param(sig):
    return any(param.kind == param.VAR_KEYWORD for param in sig.parameters.values())


def _pick_param_name(candidates, default):
    try:
        sig = inspect.signature(queryClient.query)
    except Exception:
        return default
    if _has_kwargs_param(sig):
        return default
    for name in candidates:
        if name in sig.parameters:
            return name
    return None


def _build_query_kwargs(vos_path, async_mode, fmt):
    kwargs = {}
    keys = {}
    out_key = _pick_param_name(
        ["out", "out_file", "outfile", "outfn", "output"],
        "out"
    )
    if out_key:
        kwargs[out_key] = vos_path
        keys["out"] = out_key

    if fmt:
        fmt_key = _pick_param_name(["fmt", "format", "outfmt"], "fmt")
        if fmt_key:
            kwargs[fmt_key] = fmt
            keys["fmt"] = fmt_key

    if async_mode:
        async_key = _pick_param_name(
            ["async", "async_", "asyncjob", "async_job", "run_async"],
            "async"
        )
        if async_key:
            kwargs[async_key] = True
            keys["async"] = async_key
    return kwargs, keys


def _extract_job_id(result):
    if result is None:
        return None
    if isinstance(result, str):
        return result.strip()
    if isinstance(result, dict):
        for key in ("jobid", "jobID", "jobId", "id", "jid"):
            if key in result:
                return str(result[key])
    return None


def _submit_query(adql, kwargs, keys):
    attempts = []
    if kwargs:
        attempts.append(kwargs)
        if "fmt" in keys:
            reduced = dict(kwargs)
            reduced.pop(keys["fmt"], None)
            attempts.append(reduced)
        if "async" in keys:
            reduced = dict(kwargs)
            reduced.pop(keys["async"], None)
            attempts.append(reduced)
        if "out" in keys:
            reduced = {keys["out"]: kwargs.get(keys["out"])}
            attempts.append(reduced)
    attempts.append({})

    last_exc = None
    seen = set()
    for attempt in attempts:
        key = tuple(sorted(attempt.items()))
        if key in seen:
            continue
        seen.add(key)
        try:
            return _run_query(adql, **attempt)
        except TypeError as exc:
            last_exc = exc
            continue
    if last_exc:
        raise last_exc
    return _run_query(adql)


def _normalize_status(status):
    if status is None:
        return None
    if isinstance(status, dict):
        for key in ("status", "phase", "job_status", "state"):
            if key in status:
                return str(status[key]).upper()
    return str(status).upper()


def _wait_for_job(job_id, poll_seconds):
    if not hasattr(queryClient, "status"):
        print("[WARN] queryClient.status() not available; skipping wait.")
        return None
    while True:
        status = _normalize_status(queryClient.status(job_id))
        if status:
            print(f"[INFO] Job {job_id} status: {status}")
        if status in {"COMPLETED", "FINISHED", "DONE", "ERROR", "FAILED", "ABORTED"}:
            return status
        time.sleep(poll_seconds)


def submit_queries(
    directory,
    log_file,
    vos_dir,
    create_vos_dir=False,
    async_mode=True,
    wait=False,
    poll_seconds=30,
    fmt="csv",
):
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"[ERROR] Query directory not found: {directory}")

    files = sorted(
        f for f in os.listdir(directory)
        if f.endswith(".adql") and not f.startswith("DONE_")
    )
    if not files:
        print("[OK] No ADQL files to process.")
        return

    print(f"[RUN] Starting to process {len(files)} queries...")
    _login()
    try:
        _ensure_vos_dir(vos_dir, create=create_vos_dir)

        warned_missing_out = False
        for next_file in files:
            filepath = os.path.join(directory, next_file)
            base_filename = os.path.splitext(next_file)[0]
            csv_filename = f"{base_filename}.csv"
            vos_path = f"vos://{vos_dir}/{csv_filename}"

            with open(filepath, "r") as f:
                query = f.read()

            print(f"[RUN] Submitting {next_file} -> {vos_path}")
            kwargs, keys = _build_query_kwargs(vos_path, async_mode=async_mode, fmt=fmt)
            if "out" not in keys and not warned_missing_out:
                print(
                    "[WARN] Unable to determine output parameter for queryClient.query(). "
                    "Results may not be saved to VOS."
                )
                warned_missing_out = True
            try:
                result = _submit_query(query, kwargs, keys)
            except Exception as exc:
                print(f"[ERROR] Query failed for {next_file}: {exc}")
                continue

            job_id = _extract_job_id(result)
            if async_mode and not job_id:
                print(
                    f"[WARN] No job id returned for {next_file}. "
                    "Query may have run synchronously."
                )

            status = None
            if wait and job_id:
                status = _wait_for_job(job_id, poll_seconds=poll_seconds)

            done_path = os.path.join(directory, "DONE_" + next_file)
            os.rename(filepath, done_path)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file, "a") as log:
                log.write(
                    f"{next_file}\tsubmitted\t{timestamp}"
                    f"\t{job_id or '-'}\t{status or '-'}\t{vos_path}\n"
                )

            print(f"[OK] Submitted and marked as done: {next_file}")

        print("\n[OK] All ADQL queries processed and logged.")


    finally:
        _logout()
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Submit ADQL queries to NOIRLab using the Python client."
    )
    parser.add_argument(
        "--query_dir",
        default=DEFAULT_QUERY_DIR,
        help=f"Directory containing .adql files (default: {DEFAULT_QUERY_DIR})",
    )
    parser.add_argument(
        "--log_file",
        default=DEFAULT_LOG_FILE,
        help=f"Log file to append (default: {DEFAULT_LOG_FILE})",
    )
    parser.add_argument(
        "--vos_dir",
        default=DEFAULT_VOS_DIR,
        help=f"Remote VOS directory name/path (default: {DEFAULT_VOS_DIR})",
    )
    parser.add_argument(
        "--create_vos_dir",
        action="store_true",
        help="Create the VOS directory if it does not exist.",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Run queries synchronously instead of async submission.",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for each async job to finish before moving on.",
    )
    parser.add_argument(
        "--poll_seconds",
        type=int,
        default=30,
        help="Polling interval for async job status (default: 30).",
    )
    parser.add_argument(
        "--format",
        default="csv",
        help="Output format to request (default: csv).",
    )

    args = parser.parse_args()
    submit_queries(
        directory=args.query_dir,
        log_file=args.log_file,
        vos_dir=args.vos_dir.strip("/"),
        create_vos_dir=args.create_vos_dir,
        async_mode=not args.sync,
        wait=args.wait,
        poll_seconds=args.poll_seconds,
        fmt=args.format,
    )
