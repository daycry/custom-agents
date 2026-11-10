#!/usr/bin/env python3
"""Hook containment owned by the Node launcher, independent of parent exit.

The business script runs in this interpreter after containment is installed.
The non-inheritable job handle belongs to the launcher. Its termination closes
that handle even if the Python process exits before its descendants.
"""
# Keep cleanup startup free of business executors: its caller has a 500 ms deadline.
import os
import sys
import time

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass


def windows_api():
    import ctypes
    from ctypes import wintypes as wt

    class BasicLimits(ctypes.Structure):
        _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                    ("flags", wt.DWORD), ("min_working", ctypes.c_size_t),
                    ("max_working", ctypes.c_size_t), ("active_limit", wt.DWORD),
                    ("affinity", ctypes.c_size_t), ("priority", wt.DWORD), ("scheduling", wt.DWORD)]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [("basic", BasicLimits), ("io", ctypes.c_ulonglong * 6),
                    ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                    ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]

    class Accounting(ctypes.Structure):
        _fields_ = [("user", ctypes.c_longlong), ("kernel", ctypes.c_longlong),
                    ("period_user", ctypes.c_longlong), ("period_kernel", ctypes.c_longlong),
                    ("faults", wt.DWORD), ("total", wt.DWORD), ("active", wt.DWORD),
                    ("terminated", wt.DWORD)]

    class ProcessEntry(ctypes.Structure):
        _fields_ = [("size", wt.DWORD), ("usage", wt.DWORD), ("pid", wt.DWORD),
                    ("heap", ctypes.c_size_t), ("module", wt.DWORD), ("threads", wt.DWORD),
                    ("parent", wt.DWORD), ("priority", wt.LONG), ("flags", wt.DWORD),
                    ("executable", wt.WCHAR * 260)]

    api = ctypes.WinDLL("kernel32", use_last_error=True)
    signatures = {
        "GetCurrentProcess": ([], wt.HANDLE),
        "OpenProcess": ([wt.DWORD, wt.BOOL, wt.DWORD], wt.HANDLE),
        "CreateJobObjectW": ([ctypes.c_void_p, wt.LPCWSTR], wt.HANDLE),
        "SetInformationJobObject": ([wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD], wt.BOOL),
        "QueryInformationJobObject": ([wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD, ctypes.c_void_p], wt.BOOL),
        "AssignProcessToJobObject": ([wt.HANDLE, wt.HANDLE], wt.BOOL),
        "TerminateJobObject": ([wt.HANDLE, wt.UINT], wt.BOOL),
        "DuplicateHandle": ([wt.HANDLE, wt.HANDLE, wt.HANDLE, ctypes.POINTER(wt.HANDLE),
                             wt.DWORD, wt.BOOL, wt.DWORD], wt.BOOL),
        "CloseHandle": ([wt.HANDLE], wt.BOOL),
        "CreateToolhelp32Snapshot": ([wt.DWORD, wt.DWORD], wt.HANDLE),
        "Process32FirstW": ([wt.HANDLE, ctypes.POINTER(ProcessEntry)], wt.BOOL),
        "Process32NextW": ([wt.HANDLE, ctypes.POINTER(ProcessEntry)], wt.BOOL),
    }
    for name, (args, result) in signatures.items():
        function = getattr(api, name)
        function.argtypes, function.restype = args, result
    return ctypes, wt, api, ExtendedLimits, Accounting, ProcessEntry


def checked(value, ctypes):
    if not value:
        raise ctypes.WinError(ctypes.get_last_error())
    return value


def validate_owner(owner_pid, ctypes, api, ProcessEntry):
    """Virtualenv redirectors may insert a parent between Python and Node."""
    if owner_pid == os.getppid():
        return
    snapshot = api.CreateToolhelp32Snapshot(2, 0)  # TH32CS_SNAPPROCESS
    if snapshot == ctypes.c_void_p(-1).value:
        raise OSError("process ancestry unavailable")
    parents = {}
    try:
        entry = ProcessEntry()
        entry.size = ctypes.sizeof(entry)
        more = api.Process32FirstW(snapshot, ctypes.byref(entry))
        while more:
            parents[int(entry.pid)] = int(entry.parent)
            more = api.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        api.CloseHandle(snapshot)
    candidate = os.getpid()
    for _ in range(8):
        candidate = parents.get(candidate)
        if candidate == owner_pid:
            return
        if not candidate:
            break
    raise OSError("supervisor owner is not its ancestor")


def attach(owner_pid):
    ctypes, wt, api, Limits, _, ProcessEntry = windows_api()
    validate_owner(owner_pid, ctypes, api, ProcessEntry)
    owner = checked(api.OpenProcess(0x40, False, owner_pid), ctypes)  # PROCESS_DUP_HANDLE
    job = None
    try:
        job = checked(api.CreateJobObjectW(None, None), ctypes)
        limits = Limits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway flags.
        checked(api.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)), ctypes)
        remote = wt.HANDLE()
        # Transfer ownership before joining: closing a local handle must not kill this interpreter.
        checked(api.DuplicateHandle(api.GetCurrentProcess(), job, owner, ctypes.byref(remote),
                                    0, False, 2), ctypes)  # DUPLICATE_SAME_ACCESS, not inheritable.
        checked(api.AssignProcessToJobObject(job, api.GetCurrentProcess()), ctypes)
        return int(remote.value)
    finally:
        if job:
            api.CloseHandle(job)
        api.CloseHandle(owner)


def close_job(owner_pid, remote_handle):
    ctypes, wt, api, _, Accounting, ProcessEntry = windows_api()
    validate_owner(owner_pid, ctypes, api, ProcessEntry)
    owner = checked(api.OpenProcess(0x40, False, owner_pid), ctypes)
    local = wt.HANDLE()
    try:
        # Atomically take the only launcher-owned reference. No handle is inherited by business children.
        checked(api.DuplicateHandle(owner, wt.HANDLE(remote_handle), api.GetCurrentProcess(), ctypes.byref(local),
                                    0, False, 3), ctypes)  # CLOSE_SOURCE | SAME_ACCESS.
        checked(api.TerminateJobObject(local, 0), ctypes)
        deadline = time.monotonic() + 0.25
        while True:
            accounting = Accounting()
            checked(api.QueryInformationJobObject(local, 1, ctypes.byref(accounting),
                                                  ctypes.sizeof(accounting), None), ctypes)
            if accounting.active == 0:
                return
            if time.monotonic() >= deadline:
                raise OSError("job termination could not be confirmed")
            time.sleep(0.005)
    finally:
        if local.value:
            api.CloseHandle(local)
        api.CloseHandle(owner)


PROC_ROOT = "/proc"


def _proc_accounting():
    """`pid pgid stat` rows from /proc/<pid>/stat, for images without procps."""
    rows = []
    for name in os.listdir(PROC_ROOT):
        if not name.isdigit():
            continue
        try:
            with open(os.path.join(PROC_ROOT, name, "stat"), encoding="utf-8", errors="replace") as handle:
                stat = handle.read()
        except OSError:
            continue  # The process exited between listing and reading.
        # The command name may hold spaces and parentheses: fields resume after the last ')'.
        fields = stat[stat.rfind(")") + 1:].split()
        if len(fields) >= 3:
            rows.append(f"{name} {fields[2]} {fields[0]}")
    return "\n".join(rows)


def close_group(owner_pid):
    """Clean an adapter-owned POSIX group while its Node owner remains alive."""
    import signal
    if owner_pid != os.getppid() or os.getpgid(owner_pid) != owner_pid or os.getpgrp() == owner_pid:
        raise OSError("cleanup group is not owned by its parent")
    ps = next((path for path in ("/bin/ps", "/usr/bin/ps") if os.path.isfile(path)), None)
    if not ps and not os.path.isdir(PROC_ROOT):
        raise OSError("process accounting unavailable")
    if ps:
        import subprocess
    # Never stop the Node owner: it must remain able to enforce its deadline
    # even if accounting fails or this cleanup helper is forcibly terminated.
    # Stop observed children before killing them; repeat accounting to include
    # children created before their parent received SIGSTOP.
    deadline = time.monotonic() + 0.25
    while True:
        if ps:
            accounting = subprocess.run([ps, "-eo", "pid=,pgid=,stat="], capture_output=True,
                                        encoding="utf-8", errors="replace", check=True, timeout=0.2).stdout
        else:
            accounting = _proc_accounting()
        active, seen_owner = [], False
        for row in accounting.splitlines():
            fields = row.split()
            if len(fields) != 3:
                continue
            pid, group = int(fields[0]), int(fields[1])
            seen_owner = seen_owner or pid == owner_pid
            if group == owner_pid and pid != owner_pid and not fields[2].startswith("Z"):
                active.append(pid)
        if not seen_owner:
            # The live owner must appear in any real accounting: an empty or foreign view (no /proc
            # mounted, hidepid) cannot prove the group is gone, so fail closed.
            raise OSError("process accounting unavailable")
        if not active:
            return
        for sig in (signal.SIGSTOP, signal.SIGKILL):
            for pid in active:
                try:
                    if os.getpgid(pid) == owner_pid:
                        os.kill(pid, sig)
                except ProcessLookupError:
                    pass
        if time.monotonic() >= deadline:
            raise OSError("group termination could not be confirmed")
        time.sleep(0.005)


# H-29 (T-14): bit of the exit code that only this supervisor sets. It tells the launcher that its
# job holds no other process when the business code ends (no descendant can join it afterwards:
# only job members create members), so the launcher skips the second Python of `close`.
JOB_EMPTY = 1 << 24


def job_is_empty():
    """True when the immediate job of this process holds only this process."""
    ctypes, _, api, _, Accounting, _ = windows_api()
    accounting = Accounting()
    if not api.QueryInformationJobObject(None, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None):
        return False
    return accounting.active == 1


def with_empty_job(code):
    # Only a code inside the mark's range (JOB_EMPTY..JOB_EMPTY+255) is normalised to 1, so no business
    # code can imitate it; any other code (0xC0000005, negative...) is kept for diagnosis. The mark is
    # added only to 0..255 and only after checking the job (review attempt 1, B5).
    if not isinstance(code, int) or isinstance(code, bool):
        code = 1
    elif JOB_EMPTY <= code < JOB_EMPTY + 256:
        code = 1
    if not 0 <= code < 256:
        return code
    try:
        return code | JOB_EMPTY if job_is_empty() else code
    except Exception:
        return code


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        operation, owner = args[:2]
        owner = int(owner)
        if operation == "close-group" and len(args) == 2:
            close_group(owner)
            return 0
        if operation == "close" and len(args) == 3:
            close_job(owner, int(args[2]))
            return 0
        if operation != "run" or len(args) < 5 or args[2] not in ("python", "exec"):
            raise ValueError("invalid supervisor invocation")
        handle = attach(owner)
        import json
        print(json.dumps({"customAgentsJob": str(handle), "owner": owner}), file=sys.stderr, flush=True)
        mode, command, business_args = args[2], args[3], args[4:]
        try:
            if mode == "exec":
                import subprocess
                code = subprocess.call([command, *business_args])
            else:
                while business_args and business_args[0] in ("-I", "-S"):
                    business_args.pop(0)
                script, *script_args = business_args
                sys.argv = [script, *script_args]
                import runpy
                runpy.run_path(script, run_name="__main__")
                code = 0
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 0
        return with_empty_job(code)
    except Exception:
        # No paths, handles, command arguments or consumer payloads in diagnostics.
        print("custom-agents hooks: process supervision unavailable; hook skipped", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
