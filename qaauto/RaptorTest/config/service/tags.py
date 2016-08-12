""" vendor code with modification.

"""

WENUMS = {

    'Side': {
        'Sell': '1',
        'Buy': '3',
        },

    'ExecCond': {
        'None': '0',
        'At Open': '2',
        'At Close': '4',
        'Funari': '6',
        'IOC': '8',
        },

    'PropBrokerageClass': {
        'Brokerage': '0',
        'Proprietary': '9',
        },

    'CashMarginCode': {
        'Cash': '0',
        'Trust': '2',
        'Liquidation': '4',
        },

    'ShortSellFlag': {
        'None': '0',
        'With Price Reg': '5',
        'Without Price Reg': '7',
        },

    'StabArbCode': {
        'None': '0',
        'Stabilization': '6',
        'Arbitrage': '8',
        },

    'OrderAttrCode': {
        'Automatic': '1',
        'Manual': '2',
        },

    'SuppMemberClass': {
        'None' : '0',
        'Support Member Order': '1',
        },

    'DataClassCode': {
        'New Order': '1111',
        'Mod Order': '9132',
        'Cancel Order': '7122',
        },

    'ExchClassCode': {
        'Tokyo': '1',
        'Nagoya': '3',
        'Fukuoka': '6',
        'Sapporo': '8',
        },

    'MarketClassCode': {
        'Common Info': '10',
        'Stocks': '11',
        'CB': '12',
        },

    'ESPMsgTypeUp': {
        # ESP
        'LoginRequest': '01',
        'PreLogoutRequest': '02',
        'LogoutRequest': '03',
        'LogoutResponse': '04',
        'Heartbeat': '05',
        'ResendRequest': '06',
        'Skip': '07',
        'Reject': '08',
        'QueryOp': '41',
        'QueryAdm': '81',
        'DCOp': '42',
        'DCAdm': '82',
        },

    'MsgType': {
        # ESP
        'LoginRequest': '01',
        'PreLogoutRequest': '02',
        'LogoutRequest': '03',
        'LogoutResponse': '04',
        'Heartbeat': '05',
        'ResendRequest': '06',
        'Skip': '07',
        'Reject': '08',
        # Admin
        'MarketAdmin': '90',
        'TradingHalt': '90',
        'PriceLimitInfo': '90',
        'FreeFormWarning': '90',
        'OpStart': '80',
        'OpStartResponse': '90',
        'OpEnd': '80',
        'OpEndResponse': '90',
        'AdminCommon': '80',
        'NoticeDestSetupRequest': '80',
        'NoticeDestSetupResponse': '90',
        'NoticeDestEnqRequest': '80',
        'NoticeDestEnqResponse': '90',
        'ProxyRequest': '80',
        'ProxyResponse': '90',
        'ProxyAbortRequest': '80',
        'ProxyAbortResponse': '90',
        'ProxyStatusEnqRequest': '80',
        'ProxyStatusEnqResponse': '90',
        'RetransRequest': '80',
        'RetransResponse': '90',
        'OrdSeqNumEnq': '80',
        'OrdSeqNumEnqResponse': '90',
        'NoticeSeqNumEnq': '80',
        'NoticeSeqNumEnqResponse': '90',
        'SystemError': '80',
        # Ops
        'OrderCommon': '40',
        'NewOrder': '40',
        'ModOrder': '40',
        'CancelOrder': '40',
        'NewOrderAcceptanceNotice': '50',
        'NewOrderAcceptanceError': '50',
        'NewOrderRegistrationError': '50',
        'ModAcceptanceNotice': '50',
        'ModAcceptanceError': '50',
        'ModRegistrationError': '50',
        'ModResultNotice': '50',
        'CancelAcceptanceNotice': '50',
        'CancelAcceptanceError': '50',
        'CancelRegistrationError': '50',
        'CancelResultNotice': '50',
        'ExecutionNotice': '50',
        'InvalidationResultNotice': '50',
        'AcceptanceOutputCompNotice': '50',
        'ExecOutputCompNotice': '50',
        },

    'ESPMsgTypeDown': {
        'LoginResponse': '11',
        'PreLogoutResponse': '12',
        'LogoutRequest': '13',
        'LogoutResponse': '14',
        'Heartbeat': '15',
        'ResendRequest': '16',
        'Skip': '17',
        'RejectDown': '18',
        'QueryOp': '51',
        'QueryAdm': '91',
        'DCOp': '52',
        'DCAdm': '92'
        },

    'RejectReason': {
        'Incorrect Message Type': '0001',
        'Incorrect Message Sequence Number': '0002',
        'Incorrect Participant Code': '0003',
        'Incorrect Virtual Server Number': '0004',
        'Incorrect Resend Flag': '0005',
        'Incorrect Resend Start Message Seq Num': '0006',
        'MSN is greater than the current SAMSN': '0007',
        'Incorrect ARMSN': '0008',
        'Incorrect SAMSN': '0009',
        'Incorrect Message Length': '0010',
        'Incorrect Num of Data Transacation': '0011',
        'Incorrect Skip Msg Seq Num': '0012',
        'Incorrect Format': '0013'
        },

    'LogoutReason': {
        'Logout request is valid': '0000',
        'Incorrect Msg Length': '0101',
        'Time Out (Pre-Logout Response Timer)': '0102',
        'Time Out (Logout Request Timer)': '0103',
        'Time Out (Heartbeat Receipt Timer)': '0105',
        'Number of Times of Re-resend Request is reached': '0106',
        'Number of Times of Reject Message is reached': '0107',
        'Number of Times Same Message Received Repeatedly is reached': '0108',
        'ESP link released by instructions of the upper layer': '0109',
        'System Error': '0199'
        }

    # TODO: add trading halt codes p. ~36/61 order notice.pdf

}



RENUMS = {}
for tag, vals in WENUMS.iteritems():
        cur = RENUMS.setdefault(tag, {})
        for k, v in vals.iteritems():
                cur[v] = k


