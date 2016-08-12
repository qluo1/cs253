##  
from common import *
## rf rpc
ORDER_API_URL = "tcp://%s:29021" % IVCOMSERVICE_HOST_REMOTE
## pub/sub endpoint
OM2_PUB_ENDPOINT = "tcp://%s:29020" % IVCOMSERVICE_HOST_REMOTE

DSS_PROVIDER = "PPEAUCEA->QAAUCE_Listener"
IMAGELIVE_PROVIDER = "imageliveserver-PPEAUCEA"
RF_PROVIDER = "engine-PPEAUCEA-requestResponse"



VK_ORDER_ENDPOINT = ORDER_API_URL
VK_PUB_ENDPOINT = OM2_PUB_ENDPOINT

## vk response
VK_ASX_RESP = "PPEASXA->TESTC"
VK_CXA_RESP = "PPECXAA->TESTA"
## vking enqueue provider
VK_ASX_PROVIDER = "TESTC->PPEASXA"
VK_CXA_PROVIDER = "TESTA->PPECXAA"

# RDS hermes command session
RDS_REQ = "QAAUCE-d48965-004.dc.gs.com-PREPROD"

RDS_TEST_DATA= "rdsTestData"
