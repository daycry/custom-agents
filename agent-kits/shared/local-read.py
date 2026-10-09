#!/usr/bin/env python3
"""Bounded read-only access to regular UTF-8 project files for local views."""
import ntpath
import os
from pathlib import Path
import stat

MAX_BYTES = 256 * 1024


class _ReadStatus(ValueError):
    """Only deliberately assigned status codes may leave this module."""


def _result(status, text=None, size=0):
    return {'status': status, 'text': text, 'bytes': size}


def _redirected(info):
    if stat.S_ISLNK(info.st_mode):
        return True
    if not getattr(info, 'st_file_attributes', 0) & 0x400:
        return False
    # Cloud placeholders describe storage, whereas junctions and symlinks redirect.
    return (getattr(info, 'st_reparse_tag', 0) & 0xFFFF0FFF) != 0x9000001A


def _identity(info):
    return info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode)


def _generation(info):
    return info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _paths(root, relative):
    if not isinstance(relative, str) or not relative or '\x00' in relative:
        raise ValueError('invalid_path')
    relative = relative.replace('\\', '/')
    if ntpath.splitdrive(relative)[0] or relative.startswith('/') or ':' in relative:
        raise ValueError('invalid_path')
    parts = relative.split('/')
    if any(part in ('', '.', '..') for part in parts):
        raise ValueError('invalid_path')
    root = Path(os.path.abspath(root))
    target = root.joinpath(*parts)
    return root, target


def _checked(root, target):
    """Snapshot every ancestor without following redirects; keep directory identities."""
    ancestors = list(reversed(target.parent.parents)) + [target.parent]
    snapshots = []
    for path in ancestors:
        info = os.lstat(path)
        if _redirected(info):
            raise _ReadStatus('redirected_path')
        if not stat.S_ISDIR(info.st_mode):
            raise _ReadStatus('not_regular')
        snapshots.append((path, _identity(info)))
    info = os.lstat(target)
    if _redirected(info):
        raise _ReadStatus('redirected_path')
    return info, snapshots


def _unchanged(snapshots):
    for path, identity in snapshots:
        info = os.lstat(path)
        if _redirected(info) or _identity(info) != identity:
            return False
    return True


def read_text(root, relative, *, max_bytes=MAX_BYTES):
    """Return an explicit status; never echo exception text, write files or follow redirects.

    UTF-8 errors and oversized files remain distinct from absence. File and parent
    identity checks run before reading the descriptor; regular-file reads are bounded.
    """
    if type(max_bytes) is not int or max_bytes <= 0:
        return _result('invalid_limit')
    try:
        root, target = _paths(root, relative)
    except (TypeError, ValueError, OSError):
        return _result('invalid_path')
    fd = None
    read_cost = 0
    try:
        # Distinguish a missing root from a missing entry without following root links.
        root_info = os.lstat(root)
        if _redirected(root_info):
            return _result('redirected_path')
        if not stat.S_ISDIR(root_info.st_mode):
            return _result('root_unavailable')
    except OSError:
        return _result('root_unavailable')
    try:
        info, snapshots = _checked(root, target)
        if not stat.S_ISREG(info.st_mode):
            return _result('not_regular')
        if info.st_size > max_bytes:
            return _result('too_large')
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0)
        fd = os.open(target, flags)
        opened = os.fstat(fd)
        if _identity(opened) != _identity(info) or not _unchanged(snapshots):
            return _result('changed_path')
        if opened.st_size > max_bytes:
            return _result('too_large')
        with os.fdopen(fd, 'rb') as handle:
            fd = None
            # A failed read may have consumed part of this allocation; charge it
            # conservatively instead of allowing callers to retry for free.
            read_cost = max_bytes + 1
            raw = handle.read(max_bytes + 1)
            read_cost = len(raw)
            after = os.fstat(handle.fileno())
            if (_generation(after) != _generation(opened)
                    or not _unchanged(snapshots + [(target, _identity(info))])):
                return _result('changed_path', size=read_cost)
        if len(raw) > max_bytes:
            return _result('too_large', size=read_cost)
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            return _result('invalid_encoding', size=read_cost)
        return _result('ok', text, len(raw))
    except FileNotFoundError:
        return _result('not_found', size=read_cost)
    except _ReadStatus as exc:
        return _result(str(exc), size=read_cost)
    except (OSError, ValueError):
        return _result('unreadable', size=read_cost)
    finally:
        if fd is not None:
            os.close(fd)


def list_names(root, relative, *, max_entries=128):
    """List at most max_entries names, counting every directory entry.

    An incomplete scan is deliberately not a complete sorted inventory: its names
    are the sorted bounded prefix supplied by the filesystem. Identity checks run
    before iteration and after it; this is not an atomic filesystem snapshot.
    """
    def result(status, names=None, complete=False):
        return {'status': status, 'names': [] if names is None else names, 'complete': complete}

    if type(max_entries) is not int or max_entries <= 0:
        return result('invalid_limit')
    try:
        root, target = _paths(root, relative)
    except (TypeError, ValueError, OSError):
        return result('invalid_path')
    try:
        root_info = os.lstat(root)
        if _redirected(root_info):
            return result('redirected_path')
        if not stat.S_ISDIR(root_info.st_mode):
            return result('root_unavailable')
    except OSError:
        return result('root_unavailable')
    try:
        info, snapshots = _checked(root, target)
        if not stat.S_ISDIR(info.st_mode):
            return result('not_regular')
        snapshots.append((target, _identity(info)))
        names = []
        complete = True
        with os.scandir(target) as entries:
            if (not _unchanged(snapshots)
                    or _generation(os.lstat(target)) != _generation(info)):
                return result('changed_path')
            for entry in entries:
                if len(names) == max_entries:
                    complete = False
                    break
                names.append(entry.name)
            if (not _unchanged(snapshots)
                    or _generation(os.lstat(target)) != _generation(info)):
                return result('changed_path')
        return result('ok' if complete else 'incomplete', sorted(names), complete)
    except FileNotFoundError:
        return result('not_found')
    except _ReadStatus as exc:
        return result(str(exc))
    except (OSError, ValueError):
        return result('unreadable')
