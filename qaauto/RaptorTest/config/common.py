### common shared seettings
import os

ROOT = os.getenv('BASE_DIR')
LOG_DIR = os.path.join(ROOT,"logs")
SCRIPT_DIR = os.path.join(ROOT,"scripts")
FIX42_DICT = os.path.join(ROOT,"config","FIX42.xml")
PYFIX_MODULE = "pyfix42"

## temp store sequence number
TMP_DIR = os.path.join(ROOT,"data")
REF_DATA = os.path.join(ROOT,"ref_data")

## fix db repository
RDB_API_ENDPOINT = "ipc:///tmp/rdb_service"

## AHD endpoints
AHD_API_ENDPOINT = "ipc:///tmp/AHD_API.sock"
AHD_PUB_ENDPOINT = "ipc:///tmp/AHD_PUB.sock"

## FIX endpoints 
FIX_API_ENDPOINT = "ipc:///tmp/FIX_API.sock"
FIX_PUB_ENDPOINT = "ipc:///tmp/FIX_PUB.sock" 

## ZCMD endpoints
ZCMD_API_ENDPOINT = "ipc:///tmp/ZCMD_API.sock"

## DC endpoints
DC_PUB_ENDPOINT = "ipc:///tmp/DC_PUB.sock"

## api names
## AHD apis are exposed from ahd_client.py
FIX_PUB_METHOD_NAME = "on_message"
AHD_PUB_METHOD_NAME = "on_packet"
DC_PUB_METHOD_NAME = "on_dc_message"

FIX_API_ORDER = "send_fix_order"
FIX_API_STATUS = "check_session_status"

ZCMD_API = "send_zcmd"
