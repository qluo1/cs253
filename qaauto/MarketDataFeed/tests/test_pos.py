import zerorpc
import gevent


def test_query_position():
    """ """
    RPC_ENDPOINT = "tcp://localhost:21195"

    client = zerorpc.Client()
    client.connect(RPC_ENDPOINT)

    starIds = ['11304213', '11330021', '11304218', '11282612']

    for starId in starIds:
        pos = client.get_position(starId)
        print pos
        assert pos



