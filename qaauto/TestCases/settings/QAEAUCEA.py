## QAEAUCEA test settings
from common import *
## rf rpc
ORDER_API_URL = "tcp://%s:29011" % IVCOMSERVICE_HOST_REMOTE
## pub/sub endpoint
OM2_PUB_ENDPOINT = "tcp://%s:29010" % IVCOMSERVICE_HOST_REMOTE

DSS_PROVIDER = "QAEAUCEA->QAAUCE_Listener"
IMAGELIVE_PROVIDER = "imageliveserver-QAEAUCEA"
RF_PROVIDER = "engine-QAEAUCEA-requestResponse"


VK_ORDER_ENDPOINT = ORDER_API_URL
VK_PUB_ENDPOINT = OM2_PUB_ENDPOINT

VK_ASX_RESP = "QAEASXA->TESTC"
VK_CXA_RESP = "QAECXAA->TESTA"

VK_ASX_PROVIDER = "TESTC->QAEASXA"
VK_CXA_PROVIDER = "TESTA->QAECXAA"


# RDS hermes command session
RDS_REQ = "QAAUCE-d48965-004.dc.gs.com-PRODVER"

RDS_TEST_DATA= "rdsTestData"
