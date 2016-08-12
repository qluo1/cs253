import csv
from config.service.ahd import *

class CSVExportHelper(object):
    def __init__(self, csv_file):
        self.csv_file = open(csv_file, 'w')
        self.csv_file.write('Test Case Name, Request Message, Received Message, Expected Message, Pass/Fail, Orig Request Msg, Orig Received Msg, Error Msg\n')

    def close(self):
        self.csv_file.close()

    ## orig_msg is the scapy format of orig_msg
    ## orig_msg_pretty is the pretty format for printing
    ## recv_msg is the scapy format of arhd message
    ## recv_msg_pretty is the pretty format for printing
    ## <- to keep compatibility for migration ->
    def expect(self, orig_msg, orig_msg_pretty, recv_msg, recv_msg_pretty, expected_resp_type, expected_reason_code, name, serial_num):
        assert orig_msg is not None
        assert recv_msg is not None
        resp_type = recv_msg.payload.payload.name
        reason_code = recv_msg.getfieldval('ReasonCode')
        passes = 'OK' if resp_type == expected_resp_type and reason_code == expected_reason_code else 'FAIL'
        line = '%s,\"%s\",\"%s\",%s,%s,\"%s\",\"%s\"\n' % \
                    (name, orig_msg_pretty, recv_msg_pretty, resp_type, passes, str(orig_msg), str(recv_msg))
        self.csv_file.write(line)

    def write(self, line):
        self.csv_file.write(line)
