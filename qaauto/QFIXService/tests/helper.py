""" calculate price

"""
import math
import decimal

def opposite_side(side):
    """ return opposide side. """

    assert type(side) == str
    assert side.upper() in set(['BUY','B','SELL','S','SHORT SELL','SS','SHORT', 'SSE','SHORT SELL EXEMPT'])
    if side.upper() in set(['BUY','B']):
        return 'Sell'
    return 'Buy'

def norm_side(side):
    """ return nomalized side. """

    assert type(side) == str
    assert side.upper() in set(['BUY','B','SELL','S','SHORT SELL','SS','SHORT', 'SSE','SHORT SELL EXEMPT'])
    if side.upper() in set(['BUY','B']):
        return 'Buy'
    return 'Sell'


### common utils
def tickSize(last,num=1):
    """ return right tickSize based on last price.

    tick size for both ASX/CXA
    input in dollar
    tick rule: 

    >= $2.0   - 1c
    >= 10.0c  - 0.5c
    <  10.0c  - 0.1c

    >>> tickSize(2.13)
    0.01
    >>> tickSize(1.13)
    0.005
    >>> tickSize(0.13)
    0.005
    >>> tickSize(0.097)
    0.001

    ## boundary test

    >>> tickSize(1.995)
    0.005
    >>> tickSize(2.0)
    0.01
    >>> tickSize(0.10)
    0.005
    >>> tickSize(0.099)
    0.001

    ## half tick price

    >>> tickSize(0.0975)
    0.001
    >>> tickSize(2.135)
    0.01

    """
    if last >= 2.00:  # $2.00
        return 0.01 * num # 1cent
    elif last >= 0.1: # $0.1 to $2.00 (not inc)
        return 0.005 * num # half cent
    else:
        return 0.001 * num # 0.1 cent

def halfTick(last):
    """ return half tick.

    >>> halfTick(2.13)
    0.005
    >>> halfTick(1.13)
    0.0025
    >>> halfTick(0.13)
    0.0025
    >>> halfTick(0.097)
    0.0005

    ## boundary test

    >>> halfTick(1.995)
    0.0025
    >>> halfTick(2.0)
    0.005
    >>> halfTick(0.10)
    0.0025
    >>> halfTick(0.099)
    0.0005

    ## half tick price

    >>> halfTick(2.135)
    0.005
    >>> halfTick(0.0975)
    0.0005

    """

    one_t = tickSize(last)
    return one_t * 0.5

def test_tick(price):
    """ test price is in full tick.

    >>> test_tick(2.13)
    True
    >>> test_tick(2.135)
    False
    >>> test_tick(1.13)
    True
    >>> test_tick(1.131)
    False
    >>> test_tick(1.135)
    True

    >>> test_tick(0.11)
    True

    >>> test_tick(0.115)
    True
    >>> test_tick(0.116)
    False

    >>> test_tick(0.097)
    True
    >>> test_tick(0.0975)
    False
    >>> test_tick(0.011)
    True
    >>> test_tick(0.012)
    True
    >>> test_tick(0.0125)
    False

    """
    tick = tickSize(price)
    return  abs(price/tick - int(round(price/tick))) < 0.00001

def test_halfTick(price):
    """ test price is halfTick.

    >>> test_halfTick(2.13)
    False
    >>> test_halfTick(2.135)
    True
    >>> test_halfTick(1.13)
    False
    >>> test_halfTick(1.131)
    False
    >>> test_halfTick(1.135)
    False

    >>> test_halfTick(0.11)
    False

    >>> test_halfTick(0.115)
    False
    >>> test_halfTick(0.116)
    False
    >>> test_halfTick(0.1125)
    True

    >>> test_halfTick(0.097)
    False
    >>> test_halfTick(0.0975)
    True

    >>> test_halfTick(0.011)
    False
    >>> test_halfTick(0.012)
    False
    >>> test_halfTick(0.0125)
    True

    """
    ## rule out full tick 1st.
    if test_tick(price):
        return False
    ## check half tick
    tick = halfTick(price)
    return  abs(price/tick - int(round(price/tick))) < 0.00001


def test_irrugular_tick(price):
    """  test irrugular tick price

    >>> test_irrugular_tick(0.011)
    False
    >>> test_irrugular_tick(0.0112)
    True

    >>> test_irrugular_tick(0.25)
    False
    >>> test_irrugular_tick(0.255)
    False
    >>> test_irrugular_tick(0.2525)
    False
    >>> test_irrugular_tick(0.2526)
    True

    """
    if not test_tick(price) and not test_halfTick(price):
        return True
    return False


def round_price(price,**kw):
    """ return rounded price in the right tickSize.

    input: price in dollar, regardless buy or sell, round upward
    price right tick size
        >= 200   1 cent
        200 ~ 10 0.5 cent
        < 10   0.1 cent


    >>> round_price(0.2525)
    0.25
    >>> round_price(0.2525,side="Sell")
    0.255

    >>> round_price(0.2526)
    0.25
    >>> round_price(0.2526,side="Sell")
    0.255

    >>> round_price(0.25)
    0.25

    >>> round_price(0.251)
    0.25
    >>> round_price(0.258)
    0.255
    >>> round_price(0.258,side="Sell")
    0.26

    >>> round_price(2.01)
    2.01
    >>> round_price(2.011)
    2.01
    >>> round_price(2.019)
    2.01


    """
    side = kw.get("side","Buy")

    ## if price in regular tick, return 
    if  test_tick(price):
        return price
    ## if price is half tick price
    if test_halfTick(price):
        if side == "Buy":
            return price - halfTick(price)
        else:
            return price + halfTick(price)

    ## handle irrgular tick
    assert test_irrugular_tick(price) == True

    ## round price to nearest tick price
    tick = tickSize(price)
    ## round price precision to match input
    num_dec = abs(decimal.Decimal("%s" % price).as_tuple().exponent)
    new_price = round(round(price/tick) * tick,num_dec)

    if side == "Buy":
        if new_price < price:
            return new_price
        else:
            return round(new_price - tick,num_dec)
    else:
        if new_price > price:
            return new_price
        else:
            return round(new_price + tick,num_dec)



