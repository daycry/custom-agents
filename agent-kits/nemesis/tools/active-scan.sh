#!/usr/bin/env bash
# ============================================================================
# active-scan.sh — dependency-free DAST harness (curl only), localhost-gated.
#
# Usage:   active-scan.sh <target-url> [out-dir]
# Output:  <out-dir>/active-scan.json   (findings, area="dast", source="dast")
#          plus a human summary on stdout.
#
# Passive/safe active checks of an auth-scoped LOCAL web app: security headers,
# cookie flags, exposed sensitive paths, directory listing, HTTP methods, CORS,
# framework debug exposure, server banner. No exploitation, no brute force.
# ============================================================================
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib-guardrail.sh
. "$HERE/lib-guardrail.sh"

TARGET="${1:?usage: active-scan.sh <target-url> [out-dir]}"
OUTDIR="${2:-.}"
mkdir -p "$OUTDIR"
OUT="$OUTDIR/active-scan.json"

guardrail_assert "$TARGET"          # refuse non-local targets

CURL=(curl -k -sS --max-time 15 -A "nemesis/1.0 (authorized-local-scan)")
BASE="${TARGET%/}"

esc(){ local s="$1"; s="${s//\\/\\\\}"; s="${s//\"/\\\"}"; s="${s//	/ }"; s="${s//$'\r'/}"; s="${s//$'\n'/ }"; printf '%s' "$s"; }
FIRST=1
: > "$OUT.tmp"
emit(){  # sev title what why exploit fix evidence  [location]
  local sev="$1" title="$2" what="$3" why="$4" exp="$5" fix="$6" ev="$7" loc="${8:-$BASE}"
  [ $FIRST -eq 0 ] && printf ',\n' >> "$OUT.tmp"; FIRST=0
  printf '    {"check":"active-scan","title":"%s","severity":"%s","confidence":"high","area":"dast","source":"dast","location":"%s","what":"%s","why":"%s","exploit":"%s","fix":"%s","evidence":"%s"}' \
    "$(esc "$title")" "$sev" "$(esc "$loc")" "$(esc "$what")" "$(esc "$why")" "$(esc "$exp")" "$(esc "$fix")" "$(esc "$ev")" >> "$OUT.tmp"
}
PASSED=""
pass(){ PASSED="$PASSED\"$(esc "$1")\","; }

echo ">> active-scan target: $BASE"

# --- 0. reachability + header capture --------------------------------------
HDRS="$("${CURL[@]}" -D - -o /dev/null "$BASE/" 2>/dev/null)"
CODE="$(printf '%s' "$HDRS" | awk 'NR==1{print $2}')"
if [ -z "$CODE" ]; then
  echo "  [!!] target unreachable";
  printf '{\n  "target":"%s","findings":[\n],\n  "passed":[],\n  "error":"unreachable"\n}\n' "$(esc "$BASE")" > "$OUT"
  exit 0
fi
echo "  [i] HTTP $CODE"
low(){ printf '%s' "$1" | tr 'A-Z' 'a-z'; }
HDRS_L="$(low "$HDRS")"
hget(){ printf '%s' "$HDRS" | grep -i "^$1:" | head -1 | sed -E "s/^[^:]*:[[:space:]]*//; s/\r//"; }
hhas(){ printf '%s' "$HDRS_L" | grep -qi "^$1:"; }

# --- 1. security headers ----------------------------------------------------
is_https=0; case "$BASE" in https://*) is_https=1;; esac
if [ $is_https -eq 1 ] && ! hhas "strict-transport-security"; then
  emit medium "Missing HSTS header" "No Strict-Transport-Security response header." "Browsers may be downgraded to HTTP, enabling SSL-strip / cookie interception on the session." "MITM on the same network forces http:// and reads the session cookie." "Add 'Strict-Transport-Security: max-age=31536000; includeSubDomains'." "no STS header on $BASE/"
else [ $is_https -eq 1 ] && pass "HSTS present"; fi
if ! hhas "content-security-policy"; then
  emit medium "Missing Content-Security-Policy" "No CSP header set." "Removes a strong mitigation against reflected/stored XSS and data injection." "Any XSS sink executes freely with no script-source restriction." "Define a CSP (start report-only): default-src 'self'; object-src 'none'; frame-ancestors 'self'." "no CSP header"
else pass "CSP present"; fi
hhas "x-frame-options" || { printf '%s' "$HDRS_L" | grep -q "frame-ancestors" || emit low "Missing X-Frame-Options / frame-ancestors" "No clickjacking protection header." "Page can be framed by a malicious site for clickjacking." "Attacker frames the admin panel and tricks a logged-in user into clicking hidden controls." "Add 'X-Frame-Options: SAMEORIGIN' or CSP frame-ancestors 'self'." "no XFO"; }
hhas "x-content-type-options" || emit low "Missing X-Content-Type-Options" "No 'nosniff' header." "MIME-sniffing can turn an uploaded/user file into executable content." "Uploaded text served as HTML/JS via content sniffing." "Add 'X-Content-Type-Options: nosniff'." "no XCTO"
hhas "referrer-policy" || emit info "Missing Referrer-Policy" "No Referrer-Policy header." "URLs (possibly with tokens) leak to third parties via Referer." "Sensitive query params leak to external sites in the Referer header." "Add 'Referrer-Policy: strict-origin-when-cross-origin'." "no Referrer-Policy"

# --- 2. server banner / tech disclosure ------------------------------------
SRV="$(hget server)"; XPB="$(hget x-powered-by)"
[ -n "$SRV$XPB" ] && emit info "Server/tech version disclosure" "Response advertises stack versions (Server: $SRV${XPB:+, X-Powered-By: $XPB})." "Version banners let attackers match known CVEs to exact versions." "Attacker maps the banner to a public exploit for that version." "Suppress version tokens (expose_php=Off; server_tokens off / mask via proxy)." "Server: $SRV | X-Powered-By: $XPB"

# --- 3. session cookie flags ------------------------------------------------
SC="$(printf '%s' "$HDRS" | grep -i '^set-cookie:' )"
if [ -n "$SC" ]; then
  SESS="$(printf '%s' "$SC" | grep -iE 'session|laravel_session|phpsessid|_session' | head -1)"
  [ -z "$SESS" ] && SESS="$(printf '%s' "$SC" | head -1)"
  scl="$(low "$SESS")"
  case "$scl" in *httponly*) : ;; *) emit medium "Session cookie without HttpOnly" "Session Set-Cookie lacks HttpOnly." "Cookie is readable from JavaScript; any XSS steals the session." "XSS reads document.cookie and hijacks the admin session." "Set HttpOnly on the session cookie (Laravel: SESSION_HTTP_ONLY=true)." "$(printf '%s' "$SESS" | cut -c1-80)";; esac
  case "$scl" in *secure*) : ;; *) [ $is_https -eq 1 ] && emit medium "Session cookie without Secure" "Session cookie lacks the Secure attribute." "Cookie can be sent over plain HTTP and intercepted." "Downgrade to http:// captures the session cookie in cleartext." "Set Secure (SESSION_SECURE_COOKIE=true)." "$(printf '%s' "$SESS" | cut -c1-80)";; esac
  case "$scl" in *samesite*) : ;; *) emit low "Session cookie without SameSite" "No SameSite attribute on the session cookie." "Weakens CSRF defense-in-depth." "Cross-site request rides the session cookie." "Set SameSite=Lax or Strict." "$(printf '%s' "$SESS" | cut -c1-80)";; esac
fi

# --- 4. exposed sensitive paths --------------------------------------------
check_path(){  # path  sev  title  why
  local p="$1" sev="$2" title="$3" why="$4"
  local c ct; c="$("${CURL[@]}" -o /dev/null -w '%{http_code}' "$BASE$p" 2>/dev/null)"
  if [ "$c" = "200" ]; then
    ct="$("${CURL[@]}" "$BASE$p" 2>/dev/null | head -c 200 | tr -d '\0')"
    emit "$sev" "$title" "$BASE$p is publicly reachable (HTTP 200)." "$why" "Attacker downloads $p directly with no auth." "Block the path at the web server / move it outside the web root." "$(printf '%s' "$ct" | cut -c1-120)" "$BASE$p"
  fi
}
check_path "/.env"                    critical "Exposed .env file"            "Leaks APP_KEY, DB and mail credentials, API secrets."
check_path "/.env.backup"             critical "Exposed .env backup"          "Backup of environment secrets is downloadable."
check_path "/.git/config"             high     "Exposed .git directory"       "Full source history/credentials reconstructable from .git."
check_path "/.git/HEAD"               high     "Exposed .git directory"       "Source and secrets recoverable from the git repo."
check_path "/storage/logs/laravel.log" high    "Exposed Laravel log"          "Logs leak stack traces, queries and possibly PII/tokens."
check_path "/composer.lock"           low      "Exposed composer.lock"        "Exact dependency versions ease CVE targeting."
check_path "/phpinfo.php"             high     "Exposed phpinfo()"            "Full PHP config, paths and env disclosed."
check_path "/telescope/requests"      high     "Exposed Laravel Telescope"    "Telescope exposes requests, queries, mail, secrets."
check_path "/horizon"                 medium   "Exposed Laravel Horizon"      "Queue dashboard reachable without auth."
check_path "/_ignition/health-check"  medium   "Ignition debug endpoint live" "Ignition (debug) reachable — historically RCE (CVE-2021-3129)."

# --- 5. directory listing ---------------------------------------------------
for d in "/storage" "/uploads" "/vendor" "/node_modules" "/backup"; do
  body="$("${CURL[@]}" "$BASE$d/" 2>/dev/null | head -c 400)"
  case "$(low "$body")" in *"index of"*) emit medium "Directory listing enabled" "Autoindex on $BASE$d/." "Attackers enumerate files/backups directly." "Browse $d/ to discover backups, keys, source." "Disable autoindex (Options -Indexes / autoindex off)." "Index of at $d/" "$BASE$d/";; esac
done

# --- 6. HTTP methods --------------------------------------------------------
ALLOW="$("${CURL[@]}" -X OPTIONS -D - -o /dev/null "$BASE/" 2>/dev/null | grep -i '^allow:' | sed -E 's/^[^:]*:[[:space:]]*//; s/\r//')"
case "$(low "$ALLOW")" in *trace*|*track*) emit low "Dangerous HTTP method enabled" "TRACE/TRACK allowed (Allow: $ALLOW)." "Enables Cross-Site Tracing / header reflection." "TRACE reflects headers/cookies to an attacker." "Disable TRACE/TRACK at the web server." "Allow: $ALLOW";; esac

# --- 7. CORS reflection -----------------------------------------------------
ACAO="$("${CURL[@]}" -H 'Origin: https://evil.attacker.test' -D - -o /dev/null "$BASE/" 2>/dev/null | grep -i '^access-control-allow-origin:' | sed -E 's/^[^:]*:[[:space:]]*//; s/\r//')"
acl="$(low "$ACAO")"
if [ "$acl" = "https://evil.attacker.test" ] || [ "$acl" = "*" ]; then
  ACC="$("${CURL[@]}" -H 'Origin: https://evil.attacker.test' -D - -o /dev/null "$BASE/" 2>/dev/null | grep -qi '^access-control-allow-credentials:[[:space:]]*true' && echo yes || echo no)"
  emit medium "Permissive CORS policy" "Access-Control-Allow-Origin reflects/allows any origin ($ACAO; credentials=$ACC)." "Any site can read authenticated responses cross-origin." "evil.test performs credentialed cross-origin reads of the API." "Whitelist explicit trusted origins; never reflect Origin with credentials=true." "ACAO: $ACAO"
fi

# --- 8. framework debug exposure -------------------------------------------
ERR="$("${CURL[@]}" "$BASE/$(printf 'zz-%s' 404probe)-nonexistent-$RANDOM" 2>/dev/null | tr -d '\0' | head -c 4000)"
case "$(low "$ERR")" in
  *"whoops"*|*"stack trace"*|*"ignition"*|*"vendor/laravel/framework"*|*"illuminate\\"*|*"symfony\\component"*)
    emit high "Application debug mode exposed (APP_DEBUG=true)" "Error pages render framework stack traces / source." "Debug pages leak file paths, config, DB creds and env values." "Trigger any exception to read secrets from the debug page." "Set APP_DEBUG=false and APP_ENV=production; deploy a generic error page." "$(printf '%s' "$ERR" | tr '\n' ' ' | cut -c1-140)" "$BASE/ (404 page)";;
esac

# --- assemble ---------------------------------------------------------------
{
  printf '{\n  "target":"%s",\n  "findings":[\n' "$(esc "$BASE")"
  cat "$OUT.tmp"
  printf '\n  ],\n  "passed":[%s]\n}\n' "${PASSED%,}"
} > "$OUT"
rm -f "$OUT.tmp"
N="$(grep -c '"check":"active-scan"' "$OUT" 2>/dev/null || echo 0)"
echo "  [i] $N DAST finding(s) -> $OUT"
