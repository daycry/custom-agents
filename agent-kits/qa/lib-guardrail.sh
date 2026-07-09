#!/usr/bin/env bash
# ============================================================================
# lib-guardrail.sh — gate de autorización para el agente `qa`.
# Los E2E solo se ejecutan contra hosts LOCALES/PRIVADOS. Cualquier objetivo
# público/externo se rechaza. `source` este fichero y llama a
# guardrail_assert "<url>" antes de lanzar Playwright.
# ============================================================================

guardrail_host_of(){  # extrae el host en minúsculas de una url o host suelto
  printf '%s' "$1" \
    | sed -E 's#^[a-zA-Z][a-zA-Z0-9+.-]*://##; s#^[^@]*@##; s#[/?#].*$##; s#:[0-9]+$##' \
    | tr 'A-Z' 'a-z'
}

guardrail_host_allowed(){  # 0 si el host es local/privado
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

guardrail_assert(){  # exit 3 salvo que el objetivo sea local/privado
  if ! guardrail_host_allowed "$1"; then
    echo "GUARDRAIL: '$1' NO es un objetivo local/privado — E2E rechazado." >&2
    echo "Permitidos: localhost, 127.0.0.1, ::1, *.test/*.local/*.internal, 10.x, 172.16-31.x, 192.168.x, 169.254.x, host.docker.internal." >&2
    echo "qa solo prueba entornos tuyos y autorizados." >&2
    exit 3
  fi
}
