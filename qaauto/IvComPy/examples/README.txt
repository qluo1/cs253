IvComPy - Instructions for running tests and demonstration

The tests are located on tests/ folder. These use Python's built in unit testing library, unittest,
to run them, please tneture that you are using Python 2.x, x >= 7. To run them, use:

$ python <test_file.py>

Since the tests use GS logging, the summary of the runs is also redirected to the logs. These can
be found at the logs/ folder.

It is also possible to use the generic client and server provided as a demonstration application.
To do so, first run the server with

$ python genericServer.py

and then the client, in another bash session, with 

$ python genericClient.py

When the client starts, it will notify the server and both will communicate using all provided ways.

