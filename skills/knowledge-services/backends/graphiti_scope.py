"""Resolve a logical project scope to its committed physical generation.

Only the published descriptor is authority for this local selection. A pending
descriptor is never promoted by a read. Ownership is cooperative, not authentication
against arbitrary writers with access to project files.
"""
import hashlib
import math
import os
from pathlib import Path
import re
import time


class ScopeError(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise ScopeError(reason)


def _logical(value):
    _need(type(value) is str and 0 < len(value) <= 1024 and value == value.strip()
          and value.isprintable(), 'invalid_logical_scope')
    return value


def _prefix(logical):
    return 'custom_agents_' + hashlib.sha256(_logical(logical).encode('utf8')).hexdigest()[:32] + '_gen_'


def generation_group(logical, nonce):
    _need(type(nonce) is str and re.fullmatch('[a-f0-9]{32}', nonce), 'invalid_generation_nonce')
    return _prefix(logical) + nonce


def _owned_group(logical, physical):
    if physical == logical:
        return True
    return type(physical) is str and re.fullmatch(re.escape(_prefix(logical)) + '[a-f0-9]{32}', physical) is not None


def resolve_config(cfg, manifest):
    _need(type(cfg) is dict and type(manifest) is dict, 'invalid_scope_descriptor')
    logical = _logical(cfg.get('_logical_group_id', cfg.get('group_id')))
    result = dict(cfg)
    result['group_id'] = logical
    result['_logical_group_id'] = logical
    if 'logical_group_id' not in manifest:
        return result  # Existing comparison/archive logic handles a changed legacy group.
    declared = _logical(manifest['logical_group_id'])
    if declared != logical:
        return result  # A newly configured project cannot adopt the previous project's generation.
    _need(type(manifest.get('entradas')) is dict and type(manifest.get('transitions', {})) is dict,
          'incomplete_generation_descriptor')
    physical = manifest.get('group_id')
    _need(_owned_group(logical, physical), 'foreign_generation_scope')
    result['group_id'] = physical
    return result


def read_config(cfg, publication):
    """Read the guarded committed leaf only, without locks, mutation or network."""
    _need(type(cfg) is dict, 'invalid_scope_configuration')
    root = Path(cfg.get('_root') or '.').absolute()
    timeout = cfg.get('timeout_ms', 3000)
    _need(type(timeout) in (int,float) and math.isfinite(timeout) and timeout > 0, 'invalid_scope_budget')
    deadline = time.monotonic() + max(1.0, timeout / 1000.0) * 4
    try:
        reader, state = publication._helper('local-read'), publication._helper('local-state')
        io = state.StateIO(reader, _need, publication._guard, maximum=publication.MAX_MANIFEST_BYTES)
        io.dirs(root)
        parent = root
        for part in ('.claude','knowledge-services'):
            parent = parent / part
            if not os.path.lexists(parent):
                return resolve_config(cfg,{})
            io.dirs(parent)
        path = parent / 'graphiti-manifest.json'
        if not os.path.lexists(path):
            return resolve_config(cfg,{})
        publication._guard(deadline)
        raw, _ = io.read(path, publication.MAX_MANIFEST_BYTES)
        return resolve_config(cfg, publication._decode(raw))
    except ScopeError:
        raise
    except (ValueError,OSError) as error:
        raise ScopeError('scope_descriptor_unavailable') from error
