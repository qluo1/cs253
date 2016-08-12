auto test runner
============================

borrowed original idea from Jim.
- control pytest via external process
- externally schedule job based on available release, date/time.
- capture good test results daily for each release.


implementation:
- using Plumbum control pytest run
- control test run via commandline arguments
- generate htmlreport for human, resultlog for code
- move good results into daily run folder
- move bad/failed results into daily run folder
- can query test run snapshot:
    based on test available 
    current status resultlog




