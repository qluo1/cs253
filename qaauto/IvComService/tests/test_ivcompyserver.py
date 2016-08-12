from IvComPyService import IvComPyService
import time

from pprint import pprint

def test_run_server():

    server = IvComPyService()

    time.sleep(20)

    pprint(server.list_sessions())
    pprint(server.handle_status())
    server.shutdown()


