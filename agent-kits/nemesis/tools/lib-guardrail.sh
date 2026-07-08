#!/usr/bin/env bash
# ============================================================================
# lib-guardrail.sh — shared authorization gate for ALL active/DAST tooling.
#
# Active scanning (sending traffic to a live target) is only ever permitted
# against local / private-network hosts. Any public or external target is
# refused, hard. `source` this file and call guardrail_assert "<url>" at the
# top of every scanner before it emits a single request.
# ============================================================================

guardrail_host_of(){  # extract lowercase host from a url or bare host
  printf '%s' "$1" \
    | sed -E 's#^[a-zA-Z][a-zA-Z0-9+.-]*://##; s#^[^@]*@##; s#[/?#].*$##; s#:[0-9]+$##' \
    | tr 'A-Z' 'a-z'
}

guardrail_host_allowed(){  # return 0 if host is a local/private target
  local host; host="$(guardrail_host_of "$1")"
  case "$host" in
    localhost|127.0.0.1|::1|0.0.0.0)            return 0 ;;
    host.docker.internal)                        return 0 ;;
    *.test|*.local|*.localhost|*.internal)       return 0 ;;
    127.*|10.*)                                  return 0 ;;
    192.168.*)                                   return 0 ;;
    172.1[6-9].*|172.2[0-9].*|172.3[0-1].*)      return 0 ;;
    169.254.*)                                   return 0 ;;
    *)                                           return 1 ;;
  esac
}

guardrail_assert(){  # exit 3 unless target is a permitted local/private host
  if ! guardrail_host_allowed "$1"; then
    echo "GUARDRAIL: '$1' is NOT a local/private target — active scanning refused." >&2
    echo "Permitted: localhost, 127.0.0.1, ::1, *.test/*.local/*.internal, 10.x, 172.16-31.x, 192.168.x, 169.254.x, host.docker.internal." >&2
    echo "This toolkit only audits environments you own and are authorized to test." >&2
    exit 3
  fi
}
