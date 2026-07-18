# config.py

# Base URLs
LOBBY_BASE_URL = "https://de3-gw.horances.com"
LCE_BASE_URL = "https://de3-lce.horances.com"

# Headers common to requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Origin": "https://de3-clb.horances.com",
    "Referer": "https://de3-clb.horances.com/",
    "Accept-Language": "en-US,en;q=0.9"
}

# ── Baccarat bet types ──
BACCARAT_PLAYER_BET_TYPE = 18
BACCARAT_BANKER_BET_TYPE = 19

# ── Telegram Bot Integration ──
TELEGRAM_BOT_TOKEN = "8926228936:AAGL1eMo6fl_dJS3qpsgiC0v_m7DbH8nz1s" # Your bot token from BotFather
TELEGRAM_CHAT_ID = ""   # Your personal chat ID, to receive alerts
TELEGRAM_ENABLED = True # Global toggle to turn the bot polling on/off

# ── Proxy Configuration ──
# On India VPS: proxy is NOT needed (direct Indian IP).
# On Render (USA): proxy IS needed for geo-bypass.
# Auto-detect via hostname or env var.
import os, socket as _socket
_PROXY_PRIMARY = "http://59c5680fcd9f590f2857__cr.in:523d198218fc4642@gw.dataimpulse.com:823"
_PROXY_BACKUP  = "http://59c5680fcd9f590f2857__cr.in:523d198218fc4642@gw.dataimpulse.com:823"

PROXY_URL = None
BACKUP_PROXY_URL = None
import logging as _log
_log.getLogger("config").info("🇫🇷 French VPS detected — proxy DISABLED (direct lightning fast connection)")

CURRENT_PROXY_URL = PROXY_URL

def get_current_proxy(session_id=None):
    global CURRENT_PROXY_URL
    if not CURRENT_PROXY_URL:
        return None
    if session_id:
        try:
            # Inject ;sessid.ID into proxy username
            parts = CURRENT_PROXY_URL.split('@')
            cred_part = parts[0].replace("http://", "")
            host_part = parts[1]
            user, pwd = cred_part.split(':')
            if "sessid" in user:
                user = user.split(';sessid')[0]
            sticky_user = f"{user};sessid.{session_id}"
            return f"http://{sticky_user}:{pwd}@{host_part}"
        except Exception:
            return CURRENT_PROXY_URL
    return CURRENT_PROXY_URL

def switch_to_backup_proxy():
    global CURRENT_PROXY_URL
    if CURRENT_PROXY_URL == PROXY_URL:
        CURRENT_PROXY_URL = BACKUP_PROXY_URL
        import logging
        logging.getLogger("ws_manager").info("🔄 PROXY FAILOVER: Switched to BACKUP proxy due to connection issue.")
        return True
    return False

def switch_to_primary_proxy():
    global CURRENT_PROXY_URL
    if CURRENT_PROXY_URL == BACKUP_PROXY_URL:
        CURRENT_PROXY_URL = PROXY_URL
        import logging
        logging.getLogger("ws_manager").info("🔄 PROXY RESET: Returned to PRIMARY proxy.")
        return True
    return False

