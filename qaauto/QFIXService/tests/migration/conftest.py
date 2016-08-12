import pytest
## local plugin to sort test cases
def pytest_collection_modifyitems(session, config, items):
    """ called after collection has been performed, may filter or re-order 
        the items in-place."""
    items.sort(key=lambda x: int(x.name.split("_")[-1]))

