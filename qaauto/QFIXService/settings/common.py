### common shared seettings
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT,"logs")
FIX42_DICT = os.path.join(ROOT,"etc","FIX42.xml")

## temp store sequence number
TMP_DIR = os.path.join(ROOT,"tmp")

### api
PUBSUB_API_NAME = "on_message"
SERVICE_API_ORDER = "send_fix_order"
SERVICE_API_STATUS = "check_session_status"

