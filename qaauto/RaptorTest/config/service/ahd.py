""" vendor code with modificaiton.

######################################
Arrowhead Message Module\n \
Classes for building and dissecting raw Arrowhead messages\n \
Copyright Fusion Systems 2013, all rights reserved.\n \
By: Jonathan Hope\n \
For use to test Fusion's Raptor Raw product only
"""
## setup local libs
import cfg

from scapy.all import (Packet,
                       StrFixedLenField,ShortField,
                       bind_layers)
import time

from tags import *

################## ESP layer #################

class ESPCommon(Packet):
    name = 'ESPCommon'
    fields_desc = [
        StrFixedLenField('MsgLen', '    0', 5),
        StrFixedLenField('MsgType', '01', 2),
        StrFixedLenField('MsgSeqNum', '       1', 8),
        StrFixedLenField('ResendFlag', '0', 1),
        StrFixedLenField('ParticipantCode', '11560', 5),
        StrFixedLenField('VSNum', 'VS2456', 6),
        StrFixedLenField('ARMSN', '       1', 8),
        StrFixedLenField('SAMSN', '0'*8, 8),
        StrFixedLenField('DataLen', '     ', 5),
        StrFixedLenField('NumDataTrans', '  1', 3),
        StrFixedLenField('TransDate', time.strftime("%Y%m%d", time.localtime()), 8),
        StrFixedLenField('TransTime', time.strftime("%H%M%S000000", time.localtime()), 12),
        StrFixedLenField('Reserved', ' ', 1),
        ]

    # calc and insert data len
    def post_build(self, p, payload):
        p = '%5d'%(len(p)+len(payload)-5) + p[5:43] + \
            '%5d'%(len(payload)) + p[48:]
        return p+payload


class ESPBlankData(Packet):
    name = 'ESPBlankData'
    fields_desc = [
        StrFixedLenField('Reserved', ' '*16, 16)
        ]

class LoginRequest(ESPBlankData):
    name = 'LoginRequest'

class LoginResponse(ESPBlankData):
    name = 'LoginResponse'

class PreLogoutRequest(ESPBlankData):
    name = 'PreLogoutRequest'

class PreLogoutResponse(ESPBlankData):
    name = 'PreLogoutResponse'

class LogoutRequest(Packet):
    name = 'LogoutRequest'
    fields_desc = [
        StrFixedLenField('LogoutReason', '0000', 4),
        StrFixedLenField('Reserved', ' '*12, 12)
        ]

class LogoutResponse(ESPBlankData):
    name = 'LogoutResponse'

class Heartbeat(ESPBlankData):
    name = 'Heartbeat'

class ResendRequest(Packet):
    name = 'ResendRequest'
    fields_desc = [
        StrFixedLenField('StartSeqNum', ' '*8, 8),
        StrFixedLenField('Reserved', ' '*8, 8)
        ]

class Skip(Packet):
    name = 'Skip'
    fields_desc = [
        StrFixedLenField('SkipSeqNum', ' '*8, 8),
        StrFixedLenField('Reserved', ' '*8, 8)
        ]

class Reject(Packet):
    name = 'Reject'
    fields_desc = [
        StrFixedLenField('RejectSeqNum', ' '*8, 8),
        StrFixedLenField('RejectMsgType', ' '*2, 2),
        StrFixedLenField('RejectReasonCode', ' '*4, 4),
        StrFixedLenField('Reserved', ' '*2, 2)
        ]


################### Operations Layer ##############
# Admin Messages
class AdminCommon(Packet):
    name = 'AdminCommon'
    fields_desc = [
        StrFixedLenField('DataLen', '    0', 5),
        StrFixedLenField('DataClassCode', 'T111', 4),
        StrFixedLenField('ExchClassCode', '1', 1),
        StrFixedLenField('MarketClassCode', '10', 2),
        StrFixedLenField('ParticipantCode', '11111', 5),
        StrFixedLenField('VSNum', 'VS2456', 6),
        StrFixedLenField('NumRespRecords', '    1', 5),
        StrFixedLenField('Reserved', ' '*17, 17),
        StrFixedLenField('ReasonCode', ' '*4, 4)
        ]

    # calc and insert data len
    def post_build(self, p, payload):
        p = '%5d'%(len(p)+len(payload)-5) + p[5:]
        return p+payload

class MarketAdmin(Packet):
    name = 'MarketAdmin'
    fields_desc = [
        StrFixedLenField('OpStatus', '1', 1),
        StrFixedLenField('OrderStatus', '1', 1),
        ]

class TradingHalt(Packet):
    name = 'TradingHalt'
    fields_desc = [
        StrFixedLenField('InfoTypeCode', 'A001', 4),
        StrFixedLenField('TargetRangeCode', ' 1', 2),
        StrFixedLenField('ExchClassCode', '1', 1),
        StrFixedLenField('MarketClassCode', '11', 2),
        StrFixedLenField('Reserved', ' '*2, 2),
        StrFixedLenField('IssueCode', ' '*12, 12),
        StrFixedLenField('InfoTime', ' '*9, 9),
        StrFixedLenField('OrdAcceptanceRestartTime', ' '*9, 9),
        StrFixedLenField('EffectiveTime', ' '*9, 9),
        StrFixedLenField('IssueCode1', ' '*12, 12),
        StrFixedLenField('IssueCode2', ' '*12, 12),
        StrFixedLenField('IssueCode3', ' '*12, 12),
        StrFixedLenField('IssueCode4', ' '*12, 12),
        StrFixedLenField('IssueCode5', ' '*12, 12),
        StrFixedLenField('IssueCode6', ' '*12, 12),
        StrFixedLenField('IssueCode7', ' '*12, 12),
        StrFixedLenField('IssueCode8', ' '*12, 12),
        StrFixedLenField('IssueCode9', ' '*12, 12),
        StrFixedLenField('IssueCode10', ' '*12, 12),
        ]

class PriceLimitInfo(Packet):
    name = 'PriceLimitInfo'
    fields_desc = [
        StrFixedLenField('InfoTypeCode', 'A031', 4),
        StrFixedLenField('TargetRangeCode', ' 1', 2),
        StrFixedLenField('ExchClassCode', '1', 1),
        StrFixedLenField('MarketClassCode', '11', 2),
        StrFixedLenField('Reserved', ' '*2, 2),
        StrFixedLenField('IssueCode', ' '*12, 12),
        StrFixedLenField('InfoTime', ' '*9, 9),
        StrFixedLenField('BasePrice', ' '*13, 13),
        StrFixedLenField('PriceUpperLimit', ' '*13, 13),
        StrFixedLenField('PriceLowerLimit', ' '*13, 13),        
        ]

class FreeFormWarning(Packet):
    name = 'FreeFormWarning'
    fields_desc = [
        StrFixedLenField('InfoTypeCode', 'A081', 4),
        StrFixedLenField('TargetRangeCode', ' 1', 2),
        StrFixedLenField('ExchClassCode', '1', 1),
        StrFixedLenField('MarketClassCode', '11', 2),
        StrFixedLenField('Reserved', ' '*2, 2),
        StrFixedLenField('IssueCode', ' '*12, 12),
        StrFixedLenField('InfoTime', ' '*9, 9),
        StrFixedLenField('Title', ' '*60, 60),
        StrFixedLenField('Body', ' '*600, 600),
        ]

class OpStart(Packet):
    name = 'OpStart'
    fields_desc = [
        StrFixedLenField('AcceptNoticeSeqNum', ' '*8, 8),
        StrFixedLenField('ExecutionNoticeSeqNum', ' '*8, 8),
        StrFixedLenField('ProxySourceVSNum1', ' '*6, 6),
        StrFixedLenField('ProxySourceAcceptSeqNum1', ' '*8, 8),
        StrFixedLenField('ProxySourceNoticeSeqNum1', ' '*8, 8),
        StrFixedLenField('ProxySourceVSNum2', ' '*6, 6),
        StrFixedLenField('ProxySourceAcceptSeqNum2', ' '*8, 8),
        StrFixedLenField('ProxySourceNoticeSeqNum2', ' '*8, 8),
        StrFixedLenField('ProxySourceVSNum3', ' '*6, 6),
        StrFixedLenField('ProxySourceAcceptSeqNum3', ' '*8, 8),
        StrFixedLenField('ProxySourceNoticeSeqNum3', ' '*8, 8),
        ]

class OpStartResponse(OpStart):
    name = 'OpStartResponse'
    fields_desc = [
        StrFixedLenField('AcceptNoticeSeqNum', ' '*8, 8),
        StrFixedLenField('ExecutionNoticeSeqNum', ' '*8, 8),
        StrFixedLenField('OrderEntrySeqNum', ' '*8, 8),
        StrFixedLenField('ProxySourceVSNum1', ' '*6, 6),
        StrFixedLenField('ProxySourceAcceptSeqNum1', ' '*8, 8),
        StrFixedLenField('ProxySourceNoticeSeqNum1', ' '*8, 8),
        StrFixedLenField('ProxySourceVSNum2', ' '*6, 6),
        StrFixedLenField('ProxySourceAcceptSeqNum2', ' '*8, 8),
        StrFixedLenField('ProxySourceNoticeSeqNum2', ' '*8, 8),
        StrFixedLenField('ProxySourceVSNum3', ' '*6, 6),
        StrFixedLenField('ProxySourceAcceptSeqNum3', ' '*8, 8),
        StrFixedLenField('ProxySourceNoticeSeqNum3', ' '*8, 8),
        ]

class OpStartErrorResponse(Packet):
    name = 'OpStartErrorResponse'

class OpEnd(Packet):
    name = 'OpEnd'

class OpEndResponse(Packet):
    name = 'OpEndResponse'

class NoticeDestSetupRequest(Packet):
    name = 'NoticeDestSetupRequest'
    fields_desc = [
        StrFixedLenField('VSNum', ' '*6, 6),
        StrFixedLenField('Reserved', ' '*6, 6),
        ]

class NoticeDestSetupResponse(NoticeDestSetupRequest):
    name = 'NoticeDestSetupResponse'

class NoticeDestEnqRequest(Packet):
    name = 'NoticeDestEnqRequest'
    fields_desc = [
        StrFixedLenField('EnquiryTarget', '0', 1),
        StrFixedLenField('VSNum', ' '*6, 6),
        ]

class NoticeDestEnqResponse(Packet):
    name = 'NoticeDestEnqResponse'
    fields_desc = [
        StrFixedLenField('EnquiryTarget', '0', 1),
        StrFixedLenField('VSNum1', ' '*6, 6),
        StrFixedLenField('VSNum2', ' '*6, 6),
        StrFixedLenField('VSNum3', ' '*6, 6),
        ]

class ProxyRequest(Packet):
    name = 'ProxyRequest'
    fields_desc = [
        StrFixedLenField('ProxySrcVSNum', ' '*6, 6),
        StrFixedLenField('ProxyDestVSNum', ' '*6, 6),
        StrFixedLenField('AcceptanceSeqNum', ' '*8, 8),
        StrFixedLenField('ExecutionSeqNum', ' '*8, 8),
        ]

class ProxyResponse(ProxyRequest):
    name = 'ProxyResponse'

class ProxyAbortRequest(Packet):
    name = 'ProxyAbortRequest'
    fields_desc = [
        StrFixedLenField('ProxySrcVSNum', ' '*6, 6),
        ]

class ProxyAbortResponse(ProxyAbortRequest):
    name = 'ProxyAbortResponse'

class ProxyStatusEnqRequest(NoticeDestEnqRequest):
    name = 'ProxyStatusEnqRequest'

class ProxyStatusEnqResponse(NoticeDestEnqResponse):
    name = 'ProxyStatusEnqResponse'

class RetransRequest(Packet):
    name = 'RetransRequest'
    fields_desc = [
        StrFixedLenField('VSNum', ' '*6, 6),
        StrFixedLenField('NoticeType', '0', 1),
        StrFixedLenField('StartSeqNum', ' '*8, 8),
        StrFixedLenField('EndSeqNum', ' '*8, 8),
        ]

class RetransResponse(RetransRequest):
    name = 'RetransResponse'

class OrdSeqNumEnq(Packet):
    name = 'OrdSeqNumEnq'
    fields_desc = [
        StrFixedLenField('VSNum', '0'*6, 6),
        ]

class OrdSeqNumEnqResponse(Packet):
    name = 'OrdSeqNumEnqResponse'
    fields_desc = [
        StrFixedLenField('VSNum', '0'*6, 6),
        StrFixedLenField('LastSeqNum', '0'*8, 8),
        StrFixedLenField('LastOrdClass', '0', 1),
        ]

class NoticeSeqNumEnq(OrdSeqNumEnq):
    name = 'NoticeSeqNumEnq'

class NoticeSeqNumEnqResponse(Packet):
    name = 'NoticeSeqNumEnqResponse'
    fields_desc = [
        StrFixedLenField('VSNum', '0'*6, 6),
        StrFixedLenField('AcceptanceSeqNum', '0'*8, 8),
        StrFixedLenField('ExecutionSeqNum', '0'*8, 8),
        ]
class OrdSuspensionRequest(Packet):
    name = 'OrdSuspensionRequest'
    fields_desc = [
        StrFixedLenField('TargetVSNum', '0'*6, 6),
        ]

class OrdSuspensionResponse(OrdSuspensionRequest):
    name = 'OrdSuspensionResponse'

class OrdSuspensionReleaseRequest(Packet):
    name = 'OrdSuspensionReleaseRequest'
    fields_desc = [
        StrFixedLenField('TargetVSNum', '0'*6, 6),
        ]

class OrdSuspensionReleaseResponse(OrdSuspensionReleaseRequest):
    name = 'OrdSuspensionReleaseResponse'

class HardLimitSetupRequest(Packet):
    name = 'HardLimitSetupRequest'
    fields_desc = [
        StrFixedLenField('VSNum', '0'*6, 6),
        StrFixedLenField('LimitsPerOrder', ' '*20, 20),
        StrFixedLenField('LimitsOnCumulOrder', ' '*20, 20),
        StrFixedLenField('Interval1', ' '*5, 5),
        StrFixedLenField('LimitsOnCumulExec', ' '*20, 20),
        StrFixedLenField('Interval2', ' '*5, 5),
        ]

class HardLimitSetupResponse(HardLimitSetupRequest):
    name = 'HardLimitSetupResponse'

class HardLimitEnquiryRequest(Packet):
    name = 'HardLimitEnquiryRequest'
    fields_desc = [
        StrFixedLenField('TargetVSNum', '0'*6, 6),
        ]

class HardLimitEnquiryResponse(Packet):
    name = 'HardLimitEnquiryRequest'
    fields_desc = [
        StrFixedLenField('TargetVSNum', '0'*6, 6),
        StrFixedLenField('SuspensionStatus', ' ', 1),
        StrFixedLenField('LimitsPerOrder', ' '*20, 20),
        StrFixedLenField('LimitsOnCumulOrder', ' '*20, 20),
        StrFixedLenField('Interval1', ' '*5, 5),
        StrFixedLenField('LastLimitsOnCumulOrder', ' '*20, 20),
        StrFixedLenField('StartTime', ' '*9, 9),
        StrFixedLenField('FirstSeqNumber', ' '*8, 8),
        StrFixedLenField('LastSeqNumber', ' '*8, 8),
        StrFixedLenField('LimitsOnCumulExec', ' '*20, 20),
        StrFixedLenField('Interval2', ' '*5, 5),
        StrFixedLenField('LastLimitsOnCumulExec', ' '*20, 20),
        StrFixedLenField('StartTime', ' '*9, 9),
        StrFixedLenField('FirstSeqNumber', ' '*8, 8),
        StrFixedLenField('LastSeqNumber', ' '*8, 8),
        ]

class SystemError(Packet):
    name = 'SystemError'
    fields_desc = [
        StrFixedLenField('Data', ' '*200, 200), #actually 2000 in spec
        ]

# Order Entry Messages

class OrderCommon(Packet):
    name = 'OrderCommon'
    fields_desc = [
        StrFixedLenField('DataLen', '    0', 5),
        StrFixedLenField('DataClassCode', '1111', 4),
        StrFixedLenField('ExchClassCode', '1', 1),
        StrFixedLenField('MarketClassCode', '11', 2),
        StrFixedLenField('ParticipantCode', '11111', 5),
        StrFixedLenField('VSNum', 'VS2456', 6),
        StrFixedLenField('Reserved', ' '*6, 6),
        StrFixedLenField('OrderEntrySeqNum', '       1', 8),
        StrFixedLenField('Reserved2', ' '*5, 5),
        ]

    # calc and insert data len
    def post_build(self, p, payload):
        p = '%5d'%(len(p)+len(payload)-5) + p[5:]
        return p+payload


class NewOrder(Packet):
    name = 'NewOrder'
    fields_desc = [
        StrFixedLenField('Reserved', ' '*2, 2),
        StrFixedLenField('IssueCode', '2309        ', 12),
        StrFixedLenField('Side', '3', 1), # buy
        StrFixedLenField('ExecCond', '0', 1), # normal order
        StrFixedLenField('Price', ' 0           ', 13), # market order
        StrFixedLenField('Qty', '          100', 13),
        StrFixedLenField('PropBrokerageClass', '0', 1), # brokerage
        StrFixedLenField('CashMarginCode', '0', 1),
        StrFixedLenField('ShortSellFlag', '0', 1), # not ss
        StrFixedLenField('StabArbCode', '0', 1), # none
        StrFixedLenField('OrdAttrClass', '1', 1), # automatic entry
        StrFixedLenField('SuppMemberClass', '0', 1), # none
        StrFixedLenField('IntProcessing', ' '*20, 20),
        StrFixedLenField('Optional', '0000', 4),
        StrFixedLenField('Reserved', ' '*19, 19),
        ]

class ModOrder(Packet):
    name = 'ModOrder'
    fields_desc = [
        StrFixedLenField('Reserved', ' '*2, 2),
        StrFixedLenField('IssueCode', '2309        ', 12),
        StrFixedLenField('OrderAcceptanceNum', ' '*14, 14),
        StrFixedLenField('IntProcessing', ' '*20, 20),
        StrFixedLenField('ExecCond', ' ', 1), # default no changes
        StrFixedLenField('Price', ' '*13, 13),
        StrFixedLenField('Qty', ' '*13, 13),
        StrFixedLenField('Optional', ' '*4, 4),
        ]

class CancelOrder(Packet):
    name = 'CancelOrder'
    fields_desc = [
        StrFixedLenField('Reserved', ' '*2, 2),
        StrFixedLenField('IssueCode', '2309        ', 12),
        StrFixedLenField('OrderAcceptanceNum', ' '*14, 14),
        StrFixedLenField('IntProcessing', ' '*20, 20),
        ]

# Notice Messages
class NoticeCommon(Packet):
    name = 'NoticeCommon'
    fields_desc = [
        StrFixedLenField('DataLen', '    0', 5),
        StrFixedLenField('DataClassCode', 'T111', 4),
        StrFixedLenField('ExchClassCode', '1', 1),
        StrFixedLenField('MarketClassCode', '11', 2),
        StrFixedLenField('ParticipantCode', '11111', 5),
        StrFixedLenField('SourceVSNum', 'VS2456', 6),
        StrFixedLenField('DestVSNum', 'VS2456', 6),
        StrFixedLenField('OrderEntrySeqNum', '       1', 8),
        StrFixedLenField('NoticeSeqNum', '       1', 8),
        StrFixedLenField('ReasonCode', '0000', 4),
        StrFixedLenField('RetransFlag', '0', 1),
        StrFixedLenField('Time', ' '*12, 12),
        StrFixedLenField('Reserved', ' '*2, 2),
        ]

    # calc and insert data len
    def post_build(self, p, payload):
        p = '%5d'%(len(p)+len(payload)-5) + p[5:]
        return p+payload




class NewOrderAcceptanceNotice(Packet):
    name = 'NewOrderAcceptanceNotice'
    fields_desc = [
        StrFixedLenField('Reserved', ' '*2, 2),
        StrFixedLenField('IssueCode', '2309        ', 12),
        StrFixedLenField('Side', '3', 1), # buy
        StrFixedLenField('ExecCond', '0', 1), # normal order
        StrFixedLenField('Price', ' 0           ', 13), # market order
        StrFixedLenField('Qty', '          100', 13),
        StrFixedLenField('PropBrokerageClass', '0', 1), # brokerage
        StrFixedLenField('CashMarginCode', '0', 1),
        StrFixedLenField('ShortSellFlag', '0', 1), # not ss
        StrFixedLenField('StabArbCode', '0', 1), # none
        StrFixedLenField('OrdAttrClass', '1', 1), # automatic entry
        StrFixedLenField('SuppMemberClass', '0', 1), # none
        StrFixedLenField('IntProcessing', ' '*20, 20),
        StrFixedLenField('Optional', '0000', 4),
        StrFixedLenField('OrderAcceptanceNum', ' '*14, 14),
        StrFixedLenField('Reserved2', ' '*19, 19),
        ]


class NewOrderAcceptanceError(NewOrderAcceptanceNotice):
    name = 'NewOrderAcceptanceError'


class NewOrderRegistrationError(NewOrderAcceptanceNotice):
    name = 'NewOrderRegistrationError'



class ModAcceptanceNotice(Packet):
    name = 'ModAcceptanceNotice'
    fields_desc = [
        StrFixedLenField('Reserved', ' '*2, 2),
        StrFixedLenField('IssueCode', '2309        ', 12),
        StrFixedLenField('OrdAcceptanceNum', ' '*14, 14),
        StrFixedLenField('IntProcessing', ' '*20, 20),
        StrFixedLenField('ExecCond', ' ', 1), # default no changes
        StrFixedLenField('Price', ' '*13, 13),
        StrFixedLenField('Qty', ' '*13, 13),
        StrFixedLenField('Optional', ' '*4, 4),
        ]


class ModAcceptanceError(ModAcceptanceNotice):
    name = 'ModAcceptanceError'


class ModRegistrationError(ModAcceptanceNotice):
    name = 'ModRegistrationError'



class ModResultNotice(Packet):
    name = 'ModResultNotice'
    fields_desc = [
        StrFixedLenField('Reserved', ' '*2, 2),
        StrFixedLenField('IssueCode', '2309        ', 12),
        StrFixedLenField('OrdAcceptanceNum', ' '*14, 14),
        StrFixedLenField('IntProcessing', ' '*20, 20),
        StrFixedLenField('Optional', ' '*4, 4),
        StrFixedLenField('ExecCond', ' ', 1), # default no changes
        StrFixedLenField('Price', '         1414', 13),
        StrFixedLenField('Qty', '         1414', 13),
        StrFixedLenField('Optional2', '    ', 4),
        StrFixedLenField('PartialExecQty', '            0', 13),
        StrFixedLenField('RedComplQty', '            0', 13),
        StrFixedLenField('NoticeNum', '            0', 13),
        ]



class CancelAcceptanceNotice(Packet):
    name = 'CancelAcceptanceNotice'
    fields_desc = [
        StrFixedLenField('Reserved', ' '*2, 2),
        StrFixedLenField('IssueCode', '2309        ', 12),
        StrFixedLenField('OrdAcceptanceNum', ' '*14, 14),
        StrFixedLenField('IntProcessing', ' '*20, 20),
        ]


class CancelAcceptanceError(CancelAcceptanceNotice):
    name = 'CancelAcceptanceError'


class CancelRegistrationError(CancelAcceptanceNotice):
    name = 'CancelRegistrationError'



class CancelResultNotice(Packet):
    name = 'CancelResultNotice'
    fields_desc = [
        StrFixedLenField('Reserved', '  ', 2),
        StrFixedLenField('IssueCode', '2309        ', 12),
        StrFixedLenField('OrdAcceptanceNum', '              ', 14),
        StrFixedLenField('IntProcessing', '                    ', 20),
        StrFixedLenField('Optional', '0000', 4),
        StrFixedLenField('PartialExecQty', '            0', 13),
        StrFixedLenField('CancelledQty', '            0', 13),
        StrFixedLenField('NoticeNum', '            0', 13),
        ]

class ExecutionNotice(Packet):
    name = 'ExecutionNotice'
    fields_desc = [
        StrFixedLenField('Reserved', '  ', 2),
        StrFixedLenField('IssueCode', '2309        ', 12),
        StrFixedLenField('Side', '3', 1), # buy
        StrFixedLenField('ExecCond', '0', 1), # normal order
        StrFixedLenField('Price', ' 0           ', 13), # market order
        StrFixedLenField('Qty', '          100', 13),
        StrFixedLenField('PropBrokerageClass', '0', 1), # brokerage
        StrFixedLenField('CashMarginCode', '0', 1),
        StrFixedLenField('ShortSellFlag', '0', 1), # not ss
        StrFixedLenField('StabArbCode', '0', 1), # none
        StrFixedLenField('OrdAttrClass', '1', 1), # automatic entry
        StrFixedLenField('SuppMemberClass', '0', 1), # none
        StrFixedLenField('IntProcessing', '                    ', 20),
        StrFixedLenField('Optional', '0000', 4),
        StrFixedLenField('Reserved2', '                   ', 19),
        StrFixedLenField('ValidOrderQty', '             ', 13),
        StrFixedLenField('CrossFlag', ' ', 1),
        StrFixedLenField('PriceFlag', '0', 1),
        StrFixedLenField('ExecNoticeNum', '        ', 8),
        StrFixedLenField('OrderAcceptanceNum', '              ', 14),
        StrFixedLenField('NoticeNum', '             ', 13),
        ]



class InvalidationResultNotice(Packet):
    name = 'InvalidationResultNotice'
    fields_desc = [
        StrFixedLenField('Reserved', '  ', 2),
        StrFixedLenField('IssueCode', '2309        ', 12),
        StrFixedLenField('Side', '3', 1), # buy
        StrFixedLenField('ExecCond', '0', 1), # normal order
        StrFixedLenField('Price', ' 0           ', 13), # market order
        StrFixedLenField('Qty', '          100', 13),
        StrFixedLenField('PropBrokerageClass', '0', 1), # brokerage
        StrFixedLenField('CashMarginCode', '0', 1),
        StrFixedLenField('ShortSellFlag', '0', 1), # not ss
        StrFixedLenField('StabArbCode', '0', 1), # none
        StrFixedLenField('OrdAttrClass', '1', 1), # automatic entry
        StrFixedLenField('SuppMemberClass', '0', 1), # none
        StrFixedLenField('IntProcessing', ' '*20, 20),
        StrFixedLenField('Optional', '0000', 4),
        StrFixedLenField('OrderAcceptanceNum', ' '*14, 14),
        StrFixedLenField('Reserved', ' '*19, 19),
        StrFixedLenField('PartExecQty', ' '*13, 13),
        StrFixedLenField('LimitFlag', ' ', 1),
        StrFixedLenField('NoticeNum', ' '*13, 13),
        ]


class AcceptanceOutputCompNotice(Packet):
    name = 'AcceptanceOutputCompNotice'
    fields_desc = [
        StrFixedLenField('SessionType', '1', 1),
        ]



class ExecOutputCompNotice(AcceptanceOutputCompNotice):
    name = 'ExecOutputCompNotice'



class Test(Packet):
    name = "Test packet"
    fields_desc = [ ShortField("test1", 1),
                    ShortField("test2", 2),
                    StrFixedLenField("test3", "1234", 4),
                    StrFixedLenField("test4", "5678", 4),
                    ]


    def myShow(self, indent=3, lvl="", label_lvl=""):
        """Prints a hierarchical view of the packet. "indent" = the size of indentation for each layer."""
        ct = conf.color_theme
        string =  "%s%s %s %s\n" % (label_lvl,
                              ct.punct("###["),
                              ct.layer_name(self.name),
                              ct.punct("]###"))
        print string
        for f in self.fields_desc:
            if isinstance(f, ConditionalField) and not f._evalcond(self):
                continue
            if isinstance(f, Emph) or f in conf.emph:
                ncol = ct.emph_field_name
                vcol = ct.emph_field_value
            else:
                ncol = ct.field_name
                vcol = ct.field_value
            fvalue = self.getfieldval(f.name)
            if isinstance(fvalue, Packet) or (f.islist and f.holds_packets and type(fvalue) is list):
                line = "%s  \\%-10s\\" % (label_lvl+lvl, ncol(f.name))
                string += line + '\n'
                string.append
                print line
                fvalue_gen = SetGen(fvalue,_iterpacket=0)
                for fvalue in fvalue_gen:
                    fvalue.myShow(indent=indent, label_lvl=label_lvl+lvl+"   |")
            else:
                begn = "%s  %-10s%s " % (label_lvl+lvl,
                                         ncol(f.name),
                                         ct.punct("="),)
                reprval = f.i2repr(self,fvalue)
                if type(reprval) is str:
                    reprval = reprval.replace("\n", "\n"+" "*(len(label_lvl)
                                                              +len(lvl)
                                                              +len(f.name)
                                                              +4))
                line = "%s%s" % (begn,vcol(reprval))
                string += line + '\n'
                print line
        if not type(self.payload) == scapy.packet.NoPayload: 
            string += self.payload.myShow(indent=indent, lvl=lvl+(" "*indent*self.show_indent), label_lvl=label_lvl) + '\n'
        return string


    def myShow2(self):
        """Prints a hierarchical view of an assembled version of the packet, so that automatic fields are calculated (checksums, etc.)"""
        return self.__class__(str(self)).myShow()



# bindings to payload type for proper dissection
#ESP
bind_layers(ESPCommon, LoginRequest, MsgType='01')
bind_layers(ESPCommon, LoginResponse, MsgType='11')
bind_layers(ESPCommon, PreLogoutRequest, MsgType='02')
bind_layers(ESPCommon, PreLogoutResponse, MsgType='12')
bind_layers(ESPCommon, LogoutRequest, MsgType='13')
bind_layers(ESPCommon, LogoutRequest, MsgType='03')
bind_layers(ESPCommon, LogoutResponse, MsgType='14')
bind_layers(ESPCommon, LogoutResponse, MsgType='04')
bind_layers(ESPCommon, Heartbeat, MsgType='15')
bind_layers(ESPCommon, Heartbeat, MsgType='05')
bind_layers(ESPCommon, ResendRequest, MsgType='16')
bind_layers(ESPCommon, ResendRequest, MsgType='06')
bind_layers(ESPCommon, Skip, MsgType='17')
bind_layers(ESPCommon, Skip, MsgType='07')
bind_layers(ESPCommon, Reject, MsgType='18')
bind_layers(ESPCommon, Reject, MsgType='08')
bind_layers(ESPCommon, OrderCommon, MsgType='40')
bind_layers(ESPCommon, OrderCommon, MsgType='41')
bind_layers(ESPCommon, OrderCommon, MsgType='42')
bind_layers(ESPCommon, NoticeCommon, MsgType='50')
bind_layers(ESPCommon, NoticeCommon, MsgType='51')
bind_layers(ESPCommon, NoticeCommon, MsgType='52')
bind_layers(ESPCommon, AdminCommon, MsgType='80')
bind_layers(ESPCommon, AdminCommon, MsgType='90')
bind_layers(ESPCommon, AdminCommon, MsgType='81')
bind_layers(ESPCommon, AdminCommon, MsgType='91')
bind_layers(ESPCommon, AdminCommon, MsgType='82')
bind_layers(ESPCommon, AdminCommon, MsgType='92')

# Requests
bind_layers(OrderCommon, NewOrder, DataClassCode='1111')
bind_layers(OrderCommon, ModOrder, DataClassCode='5131')
bind_layers(OrderCommon, ModOrder, DataClassCode='9132')
bind_layers(OrderCommon, CancelOrder, DataClassCode='3121')
bind_layers(OrderCommon, CancelOrder, DataClassCode='7122')

# Notices
bind_layers(NoticeCommon, NewOrderAcceptanceNotice, DataClassCode='A111')
bind_layers(NoticeCommon, ModAcceptanceNotice, DataClassCode='B131')
bind_layers(NoticeCommon, CancelAcceptanceNotice, DataClassCode='B121')
bind_layers(NoticeCommon, NewOrderAcceptanceError, DataClassCode='C119')
bind_layers(NoticeCommon, ModAcceptanceError, DataClassCode='D139')
bind_layers(NoticeCommon, CancelAcceptanceError, DataClassCode='D129')
bind_layers(NoticeCommon, AcceptanceOutputCompNotice, DataClassCode='A191')
bind_layers(NoticeCommon, ExecutionNotice, DataClassCode='J211')
bind_layers(NoticeCommon, ModResultNotice, DataClassCode='F231')
bind_layers(NoticeCommon, CancelResultNotice, DataClassCode='F221')
bind_layers(NoticeCommon, NewOrderRegistrationError, DataClassCode='K219')
bind_layers(NoticeCommon, ModRegistrationError, DataClassCode='K239')
bind_layers(NoticeCommon, CancelRegistrationError, DataClassCode='K229')
bind_layers(NoticeCommon, InvalidationResultNotice, DataClassCode='K241')
bind_layers(NoticeCommon, ExecOutputCompNotice, DataClassCode='J291')

# Admin
bind_layers(AdminCommon, MarketAdmin, DataClassCode='T111')
bind_layers(AdminCommon, TradingHalt, DataClassCode='T311')
bind_layers(AdminCommon, PriceLimitInfo, DataClassCode='T321')
bind_layers(AdminCommon, FreeFormWarning, DataClassCode='T331')

bind_layers(AdminCommon, OpStart, DataClassCode='6211')
bind_layers(AdminCommon, OpEnd, DataClassCode='6221')
bind_layers(AdminCommon, RetransRequest, DataClassCode='6231')
bind_layers(AdminCommon, ProxyRequest, DataClassCode='6241')
bind_layers(AdminCommon, ProxyAbortRequest, DataClassCode='6251')
bind_layers(AdminCommon, ProxyStatusEnqRequest, DataClassCode='6261')
bind_layers(AdminCommon, OrdSeqNumEnq, DataClassCode='6271')
bind_layers(AdminCommon, NoticeSeqNumEnq, DataClassCode='6281')
bind_layers(AdminCommon, NoticeDestSetupRequest, DataClassCode='6291')
bind_layers(AdminCommon, NoticeDestEnqRequest, DataClassCode='62A1')

bind_layers(AdminCommon, OpStartResponse, DataClassCode='T211')
bind_layers(AdminCommon, OpStartErrorResponse, DataClassCode='T219')
bind_layers(AdminCommon, OpEndResponse, DataClassCode='T221')
bind_layers(AdminCommon, OpEndResponse, DataClassCode='T229')
bind_layers(AdminCommon, RetransResponse, DataClassCode='T231')
bind_layers(AdminCommon, RetransResponse, DataClassCode='T239')
bind_layers(AdminCommon, ProxyResponse, DataClassCode='T241')
bind_layers(AdminCommon, ProxyResponse, DataClassCode='T249')
bind_layers(AdminCommon, ProxyAbortResponse, DataClassCode='T251')
bind_layers(AdminCommon, ProxyAbortResponse, DataClassCode='T259')
bind_layers(AdminCommon, ProxyStatusEnqResponse, DataClassCode='T261')
bind_layers(AdminCommon, ProxyStatusEnqResponse, DataClassCode='T269')
bind_layers(AdminCommon, OrdSeqNumEnqResponse, DataClassCode='T271')
bind_layers(AdminCommon, OrdSeqNumEnqResponse, DataClassCode='T279')
bind_layers(AdminCommon, NoticeSeqNumEnqResponse, DataClassCode='T281')
bind_layers(AdminCommon, NoticeSeqNumEnqResponse, DataClassCode='T289')
bind_layers(AdminCommon, NoticeDestSetupResponse, DataClassCode='T291')
bind_layers(AdminCommon, NoticeDestSetupResponse, DataClassCode='T299')
bind_layers(AdminCommon, NoticeDestEnqResponse, DataClassCode='T2A1')
bind_layers(AdminCommon, NoticeDestEnqResponse, DataClassCode='T2A9')
bind_layers(AdminCommon, OrdSuspensionRequest, DataClassCode='62B1')
bind_layers(AdminCommon, OrdSuspensionResponse, DataClassCode='T2B1')
bind_layers(AdminCommon, OrdSuspensionReleaseRequest, DataClassCode='62C1')
bind_layers(AdminCommon, OrdSuspensionReleaseResponse, DataClassCode='T2C1')
bind_layers(AdminCommon, HardLimitSetupRequest, DataClassCode='62D1')
bind_layers(AdminCommon, HardLimitSetupResponse, DataClassCode='T2D1')
bind_layers(AdminCommon, HardLimitEnquiryRequest, DataClassCode='62E1')
bind_layers(AdminCommon, HardLimitEnquiryResponse, DataClassCode='T2E1')
bind_layers(AdminCommon, SystemError, DataClassCode='T999')


# Raptor log parser
def parse_line(lines):
    """ parsing raptor log ine."""
    from struct import calcsize,unpack
    #import sys
    #lines = sys.stdin.readlines()
    p = lines[0].rstrip()
    n = len(p)

    headerfmt = '<iiIHH'
    k = 0 # index (pointer)
    j = calcsize(headerfmt) #size of header
    result = ''

    while k<n:
        header = p[k:k+j]
        s = unpack(headerfmt, header) #s[0] is the datalen after header of size j
        print s

        # extract AHD message
        msg = p[k+j: k+j+abs(s[0])]
        #print msg

        # parse AHD message
        # we can't determine the msg type from the header,
        # so just inspect the DataClassCode of the msg and that
        # tells whether it's inbound or outbound
        if msg[5:9] in ['1111', '5131', '9132', '3121', '7122']:
            x = OrderCommon(msg)
        else:
            x = NoticeCommon(msg)

        x.show()
        k = k+j+abs(s[0])

if __name__ == '__main__':
    """ unittest """

    common = ESPCommon()
    print common.show()

    hardLimitSetupRequest = HardLimitSetupRequest()
    print hardLimitSetupRequest.show()



