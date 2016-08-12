from om2Order import Order

def test_new_order():
    """ test order new/amend/cancel."""

    data = {'symbol':'ABC',
            'price': 5.01,
            'side': 'Buy',
            'qty': 100,
            'xref': 'FC1',
            'sor': None,
            'exch': 'SYDE',
            }

    order = Order(**data)
    print order.new()
    print order.events()
    print order.amend(qty=400)
    print order.events()
    print order.cancel()
    print order.events()

def test_order_noval():
    """ test order new/amend/cancel."""

    data = {'symbol':'ABC',
            'price': 5.01,
            'side': 'Buy',
            'qty': 100,
            'xref': 'FC1',
            'sor': None,
            'exch': 'SYDE',
            }

    order = Order(**data)
    print order.new(validate=False)
    print order.events()
    print order.amend(qty=400,validate=False)
    print order.events()
    print order.cancel(validate=False)
    print order.events()


def test_hermes():
    """ """
    hermes = {'cmd': 'ls',
              'handle': 'ls',
              'argumentVector': [{ 'arg': '/' },],
            }
    print Order.sendRdsHermes(hermes)



