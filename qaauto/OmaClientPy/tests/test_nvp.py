from pynvp.MultiDict import OrderedMultiDict
from pynvp.nvpData import NVPData, construct_nvp_raw,construct_nvp_list


def test_nvp():
    ## extracted nvp data
    data = {'opType': 'NoTranType', 'nvp': '1061\x0c10\x0cOmaExecution\x0c1260\x0c10\x0cppe_XDMa320160726\x0c1049\x0c0\x0c0\x0c1001\x0c14\x0c0\x0c1002\x0c9\x0c20\x0c1061\x0c10\x0cProductInformation\x0c1061\x0c10\x0cProductAliasList\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c1\x0c1003\x0c10\x0c*ABC\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c6\x0c1003\x0c10\x0cABC.AX\x0c1486\x0c10\x0cAX\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c6\x0c1003\x0c10\x0cABC.CHA\x0c1486\x0c10\x0cCHA\x0c1665\x0c10\x0cCHIA\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c32\x0c1003\x0c10\x0cABC AT\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c32\x0c1003\x0c10\x0cABC AU\x0c1664\x0c10\x0cAU\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c5\x0c1003\x0c10\x0cAU000000ABC7\x0c1665\x0c10\x0cNASD\x0c1666\x0c10\x0cOTC\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c5\x0c1003\x0c10\x0cAU000000ABC7\x0c1665\x0c10\x0cCHIA\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c5\x0c1003\x0c10\x0cAU000000ABC7\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c22\x0c1003\x0c10\x0cABC\x0c1486\x0c10\x0cAX\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1062\x0c10\x0cProductAliasList\x0c1118\x0c10\x0cADELAIDE BRIGHTON (ORD)(AU)\x0c1250\x0c10\x0cAUD\x0c1410\x0c14\x0c16\x0c1500\x0c14\x0c6\x0c1061\x0c10\x0cMarketMap\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c1\x0c1611\x0c10\x0cSYDE\x0c1688\x0c10\x0cN/A\x0c1382\x0c9\x0c1\x0c1062\x0c10\x0cMarket\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c2\x0c1611\x0c10\x0cCHIA\x0c1688\x0c10\x0cN/A\x0c1382\x0c9\x0c1\x0c1062\x0c10\x0cMarket\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c2\x0c1611\x0c10\x0cNASD\x0c1688\x0c10\x0cOTC\x0c1382\x0c9\x0c100\x0c1062\x0c10\x0cMarket\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c1\x0c1611\x0c10\x0cSYDE\x0c1688\x0c10\x0cN/A\x0c1382\x0c9\x0c1\x0c1062\x0c10\x0cMarket\x0c1062\x0c10\x0cMarketMap\x0c1454\x0c0\x0c0\x0c1637\x0c14\x0c0\x0c1691\x0c0\x0c1000019080\x0c1281\x0c10\x0c\x0c1107\x0c10\x0cSYDE\x0c1446\x0c0\x0c0\x0c1062\x0c10\x0cProductInformation\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cPPEAUCEA\x0c1920\x0c0\x0c1\x0c1147\x0c10\x0cPPEAUCEA120160726E\x0c1302\x0c12\x0c20160725\x0c1039\x0c13\x0c20160725-14:00:00\x0c2269\x0c0\x0c2\x0c1062\x0c10\x0cOmaLocationInformation\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cSYDE\x0c1920\x0c0\x0c1\x0c1147\x0c10\x0c1810000361\x0c1302\x0c12\x0c20160725\x0c1039\x0c13\x0c20160725-00:00:00\x0c2269\x0c0\x0c3\x0c1062\x0c10\x0cOmaLocationInformation\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cPPEASXA\x0c1920\x0c0\x0c1\x0c1147\x0c10\x0cASX1810000361-B\x0c1302\x0c12\x0c20160725\x0c1039\x0c13\x0c20160725-14:00:00\x0c2269\x0c0\x0c9\x0c1062\x0c10\x0cOmaLocationInformation\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cppe_XDMa\x0c1147\x0c10\x0c3\x0c1302\x0c12\x0c20160726\x0c1039\x0c13\x0c20160725-21:59:57\x0c1157\x0c10\x0cppe_XDMa\x0c1062\x0c10\x0cOmaLocationInformation\x0c1304\x0c10\x0cABC.AX\x0c1591\x0c10\x0c260308\x0c1045\x0c9\x0c5.76\x0c1100\x0c9\x0c5.76\x0c1046\x0c10\x0cAUD\x0c1242\x0c9\x0c5.76\x0c1243\x0c9\x0c5.76\x0c1124\x0c10\x0cAUD\x0c1099\x0c0\x0c5\x0c1402\x0c0\x0c5\x0c1219\x0c0\x0c1\x0c1220\x0c0\x0c0\x0c1221\x0c0\x0c1\x0c1222\x0c0\x0c0\x0c1016\x0c14\x0c1\x0c1018\x0c11\x0c0\x0c1122\x0c14\x0c0\x0c1017\x0c13\x0c20160725-21:59:57\x0c1551\x0c13\x0c20160726-07:59:57\x0c1170\x0c14\x0c2\x0c1107\x0c10\x0cSYDE\x0c1119\x0c10\x0cASXT\x0c2258\x0c10\x0cASXT\x0c1972\x0c10\x0cSYDE\x0c2189\x0c10\x0c\x0c1061\x0c10\x0cOmaStatus\x0c1051\x0c14\x0c0\x0c1092\x0c10\x0cppe_XDMa\x0c1135\x0c16\x0c20160725-21:59:57.415\x0c1317\x0c10\x0c20160726\x0c1020\x0c14\x0c1\x0c1136\x0c10\x0civrouter\x0c2158\x0c10\x0cppe_XDMa2016072611\x0c2159\x0c0\x0c0\x0c1062\x0c10\x0cOmaStatus\x0c1406\x0c10\x0c18,20,24\x0c1061\x0c10\x0cOmaExchangeRate\x0c1176\x0c10\x0cAUD\x0c1177\x0c10\x0cUSD\x0c1168\x0c9\x0c0.714591968\x0c1062\x0c10\x0cOmaExchangeRate\x0c1463\x0c11\x0c1\x0c1061\x0c10\x0cOmaCharge\x0c1050\x0c10\x0cOmaCharge\x0c1096\x0c14\x0c6\x0c1098\x0c14\x0c3\x0c1097\x0c9\x0c10\x0c1062\x0c10\x0cOmaCharge\x0c1061\x0c10\x0cOmaCharge\x0c1050\x0c10\x0cOmaCharge\x0c1096\x0c14\x0c1\x0c1098\x0c14\x0c7\x0c1097\x0c9\x0c0\x0c1062\x0c10\x0cOmaCharge\x0c1061\x0c10\x0cPrimaryAccount\x0c1182\x0c14\x0c0\x0c1152\x0c10\x0cGSJP\x0c1062\x0c10\x0cPrimaryAccount\x0c1061\x0c10\x0cSalesRepAccount\x0c1183\x0c14\x0c4\x0c1181\x0c10\x0c8215\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1182\x0c14\x0c2\x0c1152\x0c10\x0cGSJP\x0c1062\x0c10\x0cSalesRepAccount\x0c1061\x0c10\x0cVersusAccount\x0c1183\x0c14\x0c1\x0c1181\x0c10\x0cInvalid Account\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1183\x0c14\x0c3\x0c1181\x0c10\x0cLIJPIL\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1152\x0c10\x0cGSI\x0c1062\x0c10\x0cVersusAccount\x0c1008\x0c9\x0c0\x0c1519\x0c9\x0c0\x0c1534\x0c9\x0c0\x0c1538\x0c9\x0c0\x0c1526\x0c10\x0c\x0c1529\x0c10\x0c\x0c1576\x0c10\x0c\x0c1631\x0c10\x0c\x0c1115\x0c10\x0c\x0c1639\x0c10\x0c\x0c1146\x0c10\x0c\x0c1126\x0c10\x0c\x0c1523\x0c10\x0c\x0c1702\x0c10\x0c\x0c1703\x0c10\x0c\x0c1652\x0c0\x0c0\x0c1124\x0c10\x0cAUD\x0c1046\x0c10\x0cAUD\x0c1061\x0c10\x0cLocalRootParent\x0c1038\x0c10\x0cppe_XDMa\x0c1147\x0c10\x0c3\x0c1302\x0c12\x0c20160726\x0c1062\x0c10\x0cLocalRootParent\x0c1498\x0c9\x0c0\x0c1499\x0c9\x0c0\x0c1021\x0c10\x0cppe_XDMa220160726\x0c1062\x0c10\x0cOmaExecution\x0c1061\x0c10\x0cOmaOrder\x0c1260\x0c10\x0cppe_XDMa220160726\x0c1049\x0c0\x0c2\x0c1001\x0c14\x0c0\x0c1002\x0c9\x0c20\x0c1061\x0c10\x0cProductInformation\x0c1061\x0c10\x0cProductAliasList\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c1\x0c1003\x0c10\x0c*ABC\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c6\x0c1003\x0c10\x0cABC.AX\x0c1486\x0c10\x0cAX\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c6\x0c1003\x0c10\x0cABC.CHA\x0c1486\x0c10\x0cCHA\x0c1665\x0c10\x0cCHIA\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c32\x0c1003\x0c10\x0cABC AT\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c32\x0c1003\x0c10\x0cABC AU\x0c1664\x0c10\x0cAU\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c5\x0c1003\x0c10\x0cAU000000ABC7\x0c1665\x0c10\x0cNASD\x0c1666\x0c10\x0cOTC\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c5\x0c1003\x0c10\x0cAU000000ABC7\x0c1665\x0c10\x0cCHIA\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c5\x0c1003\x0c10\x0cAU000000ABC7\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c22\x0c1003\x0c10\x0cABC\x0c1486\x0c10\x0cAX\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1062\x0c10\x0cProductAliasList\x0c1118\x0c10\x0cADELAIDE BRIGHTON (ORD)(AU)\x0c1250\x0c10\x0cAUD\x0c1410\x0c14\x0c16\x0c1500\x0c14\x0c6\x0c1061\x0c10\x0cMarketMap\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c1\x0c1611\x0c10\x0cSYDE\x0c1688\x0c10\x0cN/A\x0c1382\x0c9\x0c1\x0c1062\x0c10\x0cMarket\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c2\x0c1611\x0c10\x0cCHIA\x0c1688\x0c10\x0cN/A\x0c1382\x0c9\x0c1\x0c1062\x0c10\x0cMarket\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c2\x0c1611\x0c10\x0cNASD\x0c1688\x0c10\x0cOTC\x0c1382\x0c9\x0c100\x0c1062\x0c10\x0cMarket\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c1\x0c1611\x0c10\x0cSYDE\x0c1688\x0c10\x0cN/A\x0c1382\x0c9\x0c1\x0c1062\x0c10\x0cMarket\x0c1062\x0c10\x0cMarketMap\x0c1454\x0c0\x0c0\x0c1637\x0c14\x0c0\x0c1691\x0c0\x0c1000019080\x0c1281\x0c10\x0c\x0c1107\x0c10\x0cSYDE\x0c1446\x0c0\x0c0\x0c1062\x0c10\x0cProductInformation\x0c1101\x0c10\x0cPPEAUCEA\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cppe_XDMa\x0c1147\x0c10\x0c2\x0c1041\x0c10\x0csystem\x0c1302\x0c12\x0c20160726\x0c1039\x0c13\x0c20160725-21:53:13\x0c1042\x0c10\x0cgemini\x0c1131\x0c10\x0cgemini\x0c1157\x0c10\x0cppe_XDMa\x0c1062\x0c10\x0cOmaLocationInformation\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cTSELINK\x0c1147\x0c10\x0c000002\x0c1302\x0c12\x0c20160726\x0c1039\x0c13\x0c20160725-21:53:13\x0c1042\x0c10\x0cInvalid User\x0c1062\x0c10\x0cOmaLocationInformation\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cPPEAUCEA\x0c1920\x0c0\x0c1\x0c1147\x0c10\x0cPPEAUCEA120160726O\x0c1302\x0c12\x0c20160725\x0c1039\x0c13\x0c20160725-14:00:00\x0c2269\x0c0\x0c2\x0c1062\x0c10\x0cOmaLocationInformation\x0c1061\x0c10\x0cOmaFeedSystems\x0c1204\x0c10\x0cSYDEN/A\x0c1205\x0c11\x0c1\x0c1206\x0c14\x0c2\x0c1207\x0c0\x0c0\x0c1209\x0c10\x0cTSELINK\x0c1208\x0c10\x0c\x0c1210\x0c11\x0c0\x0c1223\x0c11\x0c0\x0c1062\x0c10\x0cOmaFeedSystems\x0c1304\x0c10\x0cABC.AX\x0c1984\x0c0\x0c6\x0c1591\x0c10\x0c260108\x0c1023\x0c0\x0c1\x0c1031\x0c9\x0c5.79\x0c1032\x0c10\x0cAUD\x0c1028\x0c10\x0c23,24,34,37\x0c1111\x0c10\x0c15,27,39,83,85\x0c1112\x0c10\x0c3,10\x0c1161\x0c10\x0c11\x0c1099\x0c0\x0c5\x0c1402\x0c0\x0c5\x0c1027\x0c14\x0c0\x0c1018\x0c11\x0c0\x0c1024\x0c14\x0c0\x0c1124\x0c10\x0cAUD\x0c1122\x0c14\x0c0\x0c1415\x0c14\x0c-1\x0c1126\x0c10\x0cGS_ARN_D\x0c1994\x0c10\x0cdapollo-1c->ppe_XDMa\x0c1107\x0c10\x0cSYDE\x0c1119\x0c10\x0cN/A\x0c2217\x0c10\x0cGS_ARN_D\x0c1113\x0c14\x0c0\x0c1160\x0c9\x0c5.74\x0c1061\x0c10\x0cOmaStatus\x0c1051\x0c14\x0c7\x0c1092\x0c10\x0cppe_XDMa\x0c1135\x0c16\x0c20160725-21:59:57.414\x0c1317\x0c10\x0c20160726\x0c1020\x0c14\x0c2\x0c1133\x0c10\x0c1,9,79\x0c1136\x0c10\x0civrouter\x0c2158\x0c10\x0cppe_XDMa2016072611\x0c2159\x0c0\x0c0\x0c1062\x0c10\x0cOmaStatus\x0c1011\x0c9\x0c20\x0c1012\x0c9\x0c5.76\x0c1102\x0c9\x0c5.76\x0c1991\x0c10\x0cAUD\x0c1990\x0c0\x0c1\x0c1989\x0c9\x0c5.76\x0c1046\x0c10\x0cAUD\x0c1240\x0c9\x0c0\x0c1288\x0c9\x0c0\x0c1289\x0c9\x0c0\x0c1282\x0c9\x0c0\x0c1283\x0c9\x0c0\x0c1284\x0c9\x0c0\x0c1229\x0c9\x0c0\x0c1230\x0c9\x0c20\x0c1463\x0c11\x0c1\x0c1061\x0c10\x0cOmaCharge\x0c1050\x0c10\x0cOmaCharge\x0c1096\x0c14\x0c6\x0c1098\x0c14\x0c3\x0c1097\x0c9\x0c10\x0c1062\x0c10\x0cOmaCharge\x0c1061\x0c10\x0cOmaCharge\x0c1050\x0c10\x0cOmaCharge\x0c1096\x0c14\x0c1\x0c1098\x0c14\x0c7\x0c1097\x0c9\x0c0\x0c1062\x0c10\x0cOmaCharge\x0c1061\x0c10\x0cPrimaryAccount\x0c1183\x0c14\x0c1\x0c1181\x0c10\x0cARNHEM INV MGMT PTY LTD - DMA\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1183\x0c14\x0c8\x0c1181\x0c10\x0c11332394\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1183\x0c14\x0c12\x0c1181\x0c10\x0cGS_ARN_D\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1183\x0c14\x0c16\x0c1181\x0c10\x0c90599\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1182\x0c14\x0c0\x0c1152\x0c10\x0cGSJP\x0c1062\x0c10\x0cPrimaryAccount\x0c1061\x0c10\x0cVersusAccount\x0c1183\x0c14\x0c0\x0c1181\x0c10\x0cAUDMA\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1182\x0c14\x0c0\x0c1152\x0c10\x0cGSJP\x0c1062\x0c10\x0cVersusAccount\x0c1061\x0c10\x0cSalesRepAccount\x0c1183\x0c14\x0c4\x0c1181\x0c10\x0c8215\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1182\x0c14\x0c2\x0c1152\x0c10\x0cGSJP\x0c1062\x0c10\x0cSalesRepAccount\x0c3046\x0c10\x0cABC\x0c3185\x0c10\x0cZ82\x0c1543\x0c10\x0cGSAT_DScaling\x0c1544\x0c10\x0csalVis=1,PWPBenchmarkRate=25,baseIndexType="Sector",benchMarkType="PWP",cleanupPercentage=30,cleanupPrice=5.780000,cleanupVolumeLimit=29,endTime=\'2016/07/26 06:15:00 GMT\',executionStyle=2,maxPRate=28,minPRate=26,pRate=10,relativeOffsetPct=31,startTime=\'2016/07/25 21:49:30 GMT\'\x0c1314\x0c9\x0c20\x0c3024\x0c10\x0cDMA\x0c1967\x0c14\x0c3\x0c2214\x0c14\x0c1\x0c1061\x0c10\x0cOmaAccountAllocationList\x0c1575\x0c11\x0c0\x0c1062\x0c10\x0cOmaAccountAllocationList\x0c1903\x0c14\x0c-1\x0c1060\x0c9\x0c0\x0c1077\x0c9\x0c0\x0c1079\x0c9\x0c0\x0c1081\x0c9\x0c0\x0c1414\x0c9\x0c5.79\x0c1928\x0c10\x0c0\x0c1980\x0c10\x0cIOS2APOLLOPP.GSAPOLLO\x0c3059\x0c10\x0c11332394\x0c2194\x0c10\x0cGS_ARN_D\x0c3040\x0c10\x0cAUSHARESCASH\x0c3175\x0c14\x0c1\x0c3185\x0c10\x0cZ82\x0c1004\x0c10\x0cARNHEM INV MGMT PTY LTD - DMA\x0c1120\x0c10\x0c\x0c1304\x0c10\x0cABC.AX\x0c1501\x0c9\x0c20\x0c1502\x0c9\x0c0\x0c1503\x0c9\x0c5.76\x0c1504\x0c9\x0c5.76\x0c1506\x0c10\x0c1,9,79\x0c1505\x0c14\x0c2\x0c1061\x0c10\x0cOmaExchangeRate\x0c1176\x0c10\x0cUSD\x0c1177\x0c10\x0cUSD\x0c1168\x0c9\x0c1\x0c1062\x0c10\x0cOmaExchangeRate\x0c1312\x0c9\x0c0\x0c1313\x0c9\x0c0\x0c1315\x0c9\x0c5.76\x0c1316\x0c9\x0c5.76\x0c1382\x0c9\x0c1\x0c1383\x0c9\x0c0\x0c1061\x0c10\x0cLocalRootParent\x0c1038\x0c10\x0cppe_XDMa\x0c1147\x0c10\x0c1\x0c1302\x0c12\x0c20160726\x0c1062\x0c10\x0cLocalRootParent\x0c1652\x0c0\x0c0\x0c1014\x0c0\x0c4\x0c1013\x0c9\x0c10\x0c1577\x0c10\x0c\x0c1628\x0c0\x0c0\x0c1578\x0c10\x0c\x0c1624\x0c10\x0c\x0c1626\x0c10\x0c\x0c1702\x0c10\x0c\x0c1703\x0c10\x0c\x0c1649\x0c10\x0c\x0c1651\x0c10\x0c\x0c1531\x0c0\x0c10\x0c1653\x0c0\x0c0\x0c1528\x0c10\x0c\x0c1629\x0c0\x0c0\x0c1704\x0c0\x0c0\x0c1019\x0c10\x0c\x0c1242\x0c9\x0c0\x0c1243\x0c9\x0c0\x0c1016\x0c0\x0c-1\x0c1923\x0c10\x0c\x0c1975\x0c9\x0c0\x0c1976\x0c9\x0c0\x0c1831\x0c10\x0c\x0c2180\x0c11\x0c1\x0c1061\x0c10\x0cRootParentWrapper\x0c1260\x0c10\x0cppe_XDMa120160726\x0c1049\x0c0\x0c4\x0c1062\x0c10\x0cRootParentWrapper\x0c1061\x0c10\x0cParentWrapper\x0c1260\x0c10\x0cppe_XDMa120160726\x0c1049\x0c0\x0c4\x0c1062\x0c10\x0cParentWrapper\x0c1414\x0c9\x0c5.79\x0c1382\x0c9\x0c1\x0c1749\x0c9\x0c20\x0c1750\x0c9\x0c0\x0c1062\x0c10\x0cOmaOrder\x0c2185\x0c0\x0c1\x0c1141\x0c3\x0c5\x0c', 'serverName': 'ppe_XDMa', 'tag': 'ppe_XDMa320160726', 'viewId': 'ppe_XDMa_pyview', 'method': 'oma_view_execution'}
    data1 = {'opType': 'NoTranType', 'nvp': '1061\x0c10\x0cOmaOrder\x0c1260\x0c10\x0cppe_XDMa120160726\x0c1049\x0c0\x0c0\x0c1001\x0c14\x0c0\x0c1002\x0c9\x0c20\x0c1061\x0c10\x0cProductInformation\x0c1061\x0c10\x0cProductAliasList\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c1\x0c1003\x0c10\x0c*ABC\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c6\x0c1003\x0c10\x0cABC.AX\x0c1486\x0c10\x0cAX\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c6\x0c1003\x0c10\x0cABC.CHA\x0c1486\x0c10\x0cCHA\x0c1665\x0c10\x0cCHIA\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c32\x0c1003\x0c10\x0cABC AT\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c32\x0c1003\x0c10\x0cABC AU\x0c1664\x0c10\x0cAU\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c5\x0c1003\x0c10\x0cAU000000ABC7\x0c1665\x0c10\x0cNASD\x0c1666\x0c10\x0cOTC\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c5\x0c1003\x0c10\x0cAU000000ABC7\x0c1665\x0c10\x0cCHIA\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c5\x0c1003\x0c10\x0cAU000000ABC7\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c22\x0c1003\x0c10\x0cABC\x0c1486\x0c10\x0cAX\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1062\x0c10\x0cProductAliasList\x0c1118\x0c10\x0cADELAIDE BRIGHTON (ORD)(AU)\x0c1250\x0c10\x0cAUD\x0c1410\x0c14\x0c16\x0c1500\x0c14\x0c6\x0c1061\x0c10\x0cMarketMap\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c1\x0c1611\x0c10\x0cSYDE\x0c1688\x0c10\x0cN/A\x0c1382\x0c9\x0c1\x0c1062\x0c10\x0cMarket\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c2\x0c1611\x0c10\x0cCHIA\x0c1688\x0c10\x0cN/A\x0c1382\x0c9\x0c1\x0c1062\x0c10\x0cMarket\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c2\x0c1611\x0c10\x0cNASD\x0c1688\x0c10\x0cOTC\x0c1382\x0c9\x0c100\x0c1062\x0c10\x0cMarket\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c1\x0c1611\x0c10\x0cSYDE\x0c1688\x0c10\x0cN/A\x0c1382\x0c9\x0c1\x0c1062\x0c10\x0cMarket\x0c1062\x0c10\x0cMarketMap\x0c1454\x0c0\x0c0\x0c1637\x0c14\x0c0\x0c1691\x0c0\x0c1000019080\x0c1281\x0c10\x0c\x0c1107\x0c10\x0cSYDE\x0c1446\x0c0\x0c0\x0c1062\x0c10\x0cProductInformation\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cIOS2APOLLOPP.GSAPOLLO\x0c1920\x0c0\x0c1\x0c1147\x0c10\x0c24590756-001\x0c1041\x0c10\x0cGS_ARN_D\x0c1039\x0c13\x0c20160725-21:53:12\x0c1042\x0c10\x0cGS_ARN_D\x0c1062\x0c10\x0cOmaLocationInformation\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cppe_XDMa\x0c1147\x0c10\x0c1\x0c1041\x0c10\x0cgemini\x0c1302\x0c12\x0c20160726\x0c1039\x0c13\x0c20160725-21:53:12\x0c1042\x0c10\x0cgemini\x0c1131\x0c10\x0cgemini\x0c1157\x0c10\x0cppe_XDMa\x0c1062\x0c10\x0cOmaLocationInformation\x0c1061\x0c10\x0cOmaFeedSystems\x0c1204\x0c10\x0cSYDEN/A\x0c1205\x0c11\x0c1\x0c1206\x0c14\x0c2\x0c1207\x0c0\x0c0\x0c1209\x0c10\x0cTSELINK\x0c1208\x0c10\x0c\x0c1210\x0c11\x0c0\x0c1223\x0c11\x0c0\x0c1062\x0c10\x0cOmaFeedSystems\x0c1304\x0c10\x0cABC.AX\x0c1984\x0c0\x0c6\x0c1591\x0c10\x0c260108\x0c1023\x0c0\x0c1\x0c1031\x0c9\x0c5.79\x0c1032\x0c10\x0cAUD\x0c1028\x0c10\x0c23,24,34,37\x0c1111\x0c10\x0c5,15,27,39,83\x0c1112\x0c10\x0c3,10\x0c1161\x0c10\x0c11\x0c1099\x0c0\x0c5\x0c1402\x0c0\x0c5\x0c1027\x0c14\x0c0\x0c1018\x0c11\x0c0\x0c1024\x0c14\x0c0\x0c1124\x0c10\x0cAUD\x0c1122\x0c14\x0c0\x0c1415\x0c14\x0c-1\x0c1126\x0c10\x0cGS_ARN_D\x0c1994\x0c10\x0cdapollo-1c->ppe_XDMa\x0c1107\x0c10\x0cSYDE\x0c1119\x0c10\x0cN/A\x0c2217\x0c10\x0cGS_ARN_D\x0c1113\x0c14\x0c0\x0c1160\x0c9\x0c5.74\x0c1061\x0c10\x0cOmaStatus\x0c1051\x0c14\x0c0\x0c1092\x0c10\x0cppe_XDMa\x0c1533\x0c10\x0cgemini\x0c1135\x0c16\x0c20160725-21:53:12.989\x0c1317\x0c10\x0c20160726\x0c1020\x0c14\x0c0\x0c1136\x0c10\x0cgemini\x0c3049\x0c0\x0c1\x0c2158\x0c10\x0cppe_XDMa201607267\x0c2159\x0c0\x0c0\x0c1062\x0c10\x0cOmaStatus\x0c1011\x0c9\x0c0\x0c1012\x0c9\x0c0\x0c1102\x0c9\x0c0\x0c1990\x0c0\x0c0\x0c1989\x0c9\x0c0\x0c1240\x0c9\x0c0\x0c1288\x0c9\x0c0\x0c1289\x0c9\x0c0\x0c1282\x0c9\x0c0\x0c1283\x0c9\x0c0\x0c1284\x0c9\x0c0\x0c1229\x0c9\x0c-1\x0c1230\x0c9\x0c-1\x0c1463\x0c11\x0c1\x0c1061\x0c10\x0cOmaCharge\x0c1050\x0c10\x0cOmaCharge\x0c1096\x0c14\x0c6\x0c1098\x0c14\x0c3\x0c1097\x0c9\x0c10\x0c1062\x0c10\x0cOmaCharge\x0c1061\x0c10\x0cOmaCharge\x0c1050\x0c10\x0cOmaCharge\x0c1096\x0c14\x0c1\x0c1098\x0c14\x0c7\x0c1097\x0c9\x0c0\x0c1062\x0c10\x0cOmaCharge\x0c1061\x0c10\x0cPrimaryAccount\x0c1183\x0c14\x0c1\x0c1181\x0c10\x0cARNHEM INV MGMT PTY LTD - DMA\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1183\x0c14\x0c8\x0c1181\x0c10\x0c11332394\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1183\x0c14\x0c12\x0c1181\x0c10\x0cGS_ARN_D\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1183\x0c14\x0c16\x0c1181\x0c10\x0c90599\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1182\x0c14\x0c0\x0c1152\x0c10\x0cGSJP\x0c1062\x0c10\x0cPrimaryAccount\x0c1061\x0c10\x0cVersusAccount\x0c1183\x0c14\x0c0\x0c1181\x0c10\x0cAUDMA\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1182\x0c14\x0c0\x0c1152\x0c10\x0cGSJP\x0c1062\x0c10\x0cVersusAccount\x0c1061\x0c10\x0cSalesRepAccount\x0c1183\x0c14\x0c4\x0c1181\x0c10\x0c8215\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1182\x0c14\x0c2\x0c1152\x0c10\x0cGSJP\x0c1062\x0c10\x0cSalesRepAccount\x0c3046\x0c10\x0cABC\x0c3185\x0c10\x0cZ82\x0c1543\x0c10\x0cGSAT_DScaling\x0c1544\x0c10\x0csalVis=1,PWPBenchmarkRate=25,baseIndexType="Sector",benchMarkType="PWP",cleanupPercentage=30,cleanupPrice=5.780000,cleanupVolumeLimit=29,endTime=\'2016/07/26 06:15:00 GMT\',executionStyle=2,maxPRate=28,minPRate=26,pRate=10,relativeOffsetPct=31,startTime=\'2016/07/25 21:49:30 GMT\'\x0c1314\x0c9\x0c0\x0c3024\x0c10\x0cDMA\x0c2214\x0c14\x0c1\x0c1061\x0c10\x0cOmaAccountAllocationList\x0c1575\x0c11\x0c0\x0c1062\x0c10\x0cOmaAccountAllocationList\x0c1903\x0c14\x0c-1\x0c1060\x0c9\x0c20\x0c1077\x0c9\x0c0\x0c1079\x0c9\x0c0\x0c1081\x0c9\x0c0\x0c1414\x0c9\x0c5.79\x0c1928\x0c10\x0c0\x0c1980\x0c10\x0cIOS2APOLLOPP.GSAPOLLO\x0c3059\x0c10\x0c11332394\x0c2194\x0c10\x0cGS_ARN_D\x0c3040\x0c10\x0cAUSHARESCASH\x0c3175\x0c14\x0c1\x0c3185\x0c10\x0cZ82\x0c1004\x0c10\x0cARNHEM INV MGMT PTY LTD - DMA\x0c1120\x0c10\x0c\x0c1304\x0c10\x0cABC.AX\x0c1501\x0c9\x0c0\x0c1502\x0c9\x0c20\x0c1503\x0c9\x0c0\x0c1504\x0c9\x0c0\x0c1505\x0c14\x0c0\x0c1061\x0c10\x0cOmaExchangeRate\x0c1176\x0c10\x0cUSD\x0c1177\x0c10\x0cUSD\x0c1168\x0c9\x0c1\x0c1062\x0c10\x0cOmaExchangeRate\x0c1312\x0c9\x0c20\x0c1313\x0c9\x0c0\x0c1315\x0c9\x0c0\x0c1316\x0c9\x0c0\x0c1382\x0c9\x0c1\x0c1383\x0c9\x0c0\x0c1061\x0c10\x0cLocalRootParent\x0c1038\x0c10\x0cppe_XDMa\x0c1147\x0c10\x0c1\x0c1302\x0c12\x0c20160726\x0c1062\x0c10\x0cLocalRootParent\x0c1652\x0c0\x0c0\x0c1014\x0c0\x0c4\x0c1013\x0c9\x0c10\x0c1577\x0c10\x0c\x0c1628\x0c0\x0c0\x0c1578\x0c10\x0c\x0c1624\x0c10\x0c\x0c1626\x0c10\x0c\x0c1702\x0c10\x0c\x0c1703\x0c10\x0c\x0c1649\x0c10\x0c\x0c1651\x0c10\x0c\x0c1531\x0c0\x0c10\x0c1653\x0c0\x0c0\x0c1528\x0c10\x0c\x0c1629\x0c0\x0c0\x0c1704\x0c0\x0c0\x0c1019\x0c10\x0c\x0c1242\x0c9\x0c0\x0c1243\x0c9\x0c0\x0c1016\x0c0\x0c-1\x0c1923\x0c10\x0c\x0c1975\x0c9\x0c0\x0c1976\x0c9\x0c0\x0c1831\x0c10\x0c\x0c2180\x0c11\x0c1\x0c1414\x0c9\x0c5.79\x0c1382\x0c9\x0c1\x0c1749\x0c9\x0c20\x0c1750\x0c9\x0c0\x0c1062\x0c10\x0cOmaOrder\x0c2185\x0c0\x0c1\x0c1141\x0c3\x0c0\x0c', 'serverName': 'ppe_XDMa', 'tag': 'ppe_XDMa120160726', 'viewId': 'ppe_XDMa_pyview', 'method': 'oma_view_message'}
    ## failed parsing
    data2 = {'opType': 'NoTranType', 'nvp': '1061\x0c10\x0cOmaOrder\x0c1260\x0c10\x0cppe_XDMa120160726\x0c1049\x0c0\x0c0\x0c1001\x0c14\x0c0\x0c1002\x0c9\x0c20\x0c1061\x0c10\x0cProductInformation\x0c1061\x0c10\x0cProductAliasList\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c1\x0c1003\x0c10\x0c*ABC\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c6\x0c1003\x0c10\x0cABC.AX\x0c1486\x0c10\x0cAX\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c6\x0c1003\x0c10\x0cABC.CHA\x0c1486\x0c10\x0cCHA\x0c1665\x0c10\x0cCHIA\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c32\x0c1003\x0c10\x0cABC AT\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c32\x0c1003\x0c10\x0cABC AU\x0c1664\x0c10\x0cAU\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c5\x0c1003\x0c10\x0cAU000000ABC7\x0c1665\x0c10\x0cNASD\x0c1666\x0c10\x0cOTC\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c5\x0c1003\x0c10\x0cAU000000ABC7\x0c1665\x0c10\x0cCHIA\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c5\x0c1003\x0c10\x0cAU000000ABC7\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c22\x0c1003\x0c10\x0cABC\x0c1486\x0c10\x0cAX\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1062\x0c10\x0cProductAliasList\x0c1118\x0c10\x0cADELAIDE BRIGHTON (ORD)(AU)\x0c1250\x0c10\x0cAUD\x0c1410\x0c14\x0c16\x0c1500\x0c14\x0c6\x0c1061\x0c10\x0cMarketMap\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c1\x0c1611\x0c10\x0cSYDE\x0c1688\x0c10\x0cN/A\x0c1382\x0c9\x0c1\x0c1062\x0c10\x0cMarket\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c2\x0c1611\x0c10\x0cCHIA\x0c1688\x0c10\x0cN/A\x0c1382\x0c9\x0c1\x0c1062\x0c10\x0cMarket\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c2\x0c1611\x0c10\x0cNASD\x0c1688\x0c10\x0cOTC\x0c1382\x0c9\x0c100\x0c1062\x0c10\x0cMarket\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c1\x0c1611\x0c10\x0cSYDE\x0c1688\x0c10\x0cN/A\x0c1382\x0c9\x0c1\x0c1062\x0c10\x0cMarket\x0c1062\x0c10\x0cMarketMap\x0c1454\x0c0\x0c0\x0c1637\x0c14\x0c0\x0c1691\x0c0\x0c1000019080\x0c1281\x0c10\x0c\x0c1107\x0c10\x0cSYDE\x0c1446\x0c0\x0c0\x0c1062\x0c10\x0cProductInformation\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cIOS2APOLLOPP.GSAPOLLO\x0c1920\x0c0\x0c1\x0c1147\x0c10\x0c24590756-001\x0c1041\x0c10\x0cGS_ARN_D\x0c1039\x0c13\x0c20160725-21:53:12\x0c1042\x0c10\x0cGS_ARN_D\x0c1062\x0c10\x0cOmaLocationInformation\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cppe_XDMa\x0c1147\x0c10\x0c1\x0c1041\x0c10\x0cgemini\x0c1302\x0c12\x0c20160726\x0c1039\x0c13\x0c20160725-21:53:12\x0c1042\x0c10\x0cgemini\x0c1131\x0c10\x0cgemini\x0c1157\x0c10\x0cppe_XDMa\x0c1062\x0c10\x0cOmaLocationInformation\x0c1061\x0c10\x0cOmaFeedSystems\x0c1204\x0c10\x0cSYDEN/A\x0c1205\x0c11\x0c1\x0c1206\x0c14\x0c2\x0c1207\x0c0\x0c0\x0c1209\x0c10\x0cTSELINK\x0c1208\x0c10\x0c\x0c1210\x0c11\x0c0\x0c1223\x0c11\x0c0\x0c1062\x0c10\x0cOmaFeedSystems\x0c1304\x0c10\x0cABC.AX\x0c1984\x0c0\x0c6\x0c1591\x0c10\x0c260108\x0c1023\x0c0\x0c1\x0c1031\x0c9\x0c5.79\x0c1032\x0c10\x0cAUD\x0c1028\x0c10\x0c23,24,34,37\x0c1111\x0c10\x0c5,15,27,39,83\x0c1112\x0c10\x0c3,10\x0c1161\x0c10\x0c11\x0c1099\x0c0\x0c5\x0c1402\x0c0\x0c5\x0c1027\x0c14\x0c0\x0c1018\x0c11\x0c0\x0c1024\x0c14\x0c0\x0c1124\x0c10\x0cAUD\x0c1122\x0c14\x0c0\x0c1415\x0c14\x0c-1\x0c1126\x0c10\x0cGS_ARN_D\x0c1994\x0c10\x0cdapollo-1c->ppe_XDMa\x0c1107\x0c10\x0cSYDE\x0c1119\x0c10\x0cN/A\x0c2217\x0c10\x0cGS_ARN_D\x0c1113\x0c14\x0c0\x0c1160\x0c9\x0c5.74\x0c1061\x0c10\x0cOmaStatus\x0c1051\x0c14\x0c0\x0c1092\x0c10\x0cppe_XDMa\x0c1533\x0c10\x0cgemini\x0c1135\x0c16\x0c20160725-21:53:12.989\x0c1317\x0c10\x0c20160726\x0c1020\x0c14\x0c0\x0c1136\x0c10\x0cgemini\x0c3049\x0c0\x0c1\x0c2158\x0c10\x0cppe_XDMa201607267\x0c2159\x0c0\x0c0\x0c1062\x0c10\x0cOmaStatus\x0c1011\x0c9\x0c0\x0c1012\x0c9\x0c0\x0c1102\x0c9\x0c0\x0c1990\x0c0\x0c0\x0c1989\x0c9\x0c0\x0c1240\x0c9\x0c0\x0c1288\x0c9\x0c0\x0c1289\x0c9\x0c0\x0c1282\x0c9\x0c0\x0c1283\x0c9\x0c0\x0c1284\x0c9\x0c0\x0c1229\x0c9\x0c-1\x0c1230\x0c9\x0c-1\x0c1463\x0c11\x0c1\x0c1061\x0c10\x0cOmaCharge\x0c1050\x0c10\x0cOmaCharge\x0c1096\x0c14\x0c6\x0c1098\x0c14\x0c3\x0c1097\x0c9\x0c10\x0c1062\x0c10\x0cOmaCharge\x0c1061\x0c10\x0cOmaCharge\x0c1050\x0c10\x0cOmaCharge\x0c1096\x0c14\x0c1\x0c1098\x0c14\x0c7\x0c1097\x0c9\x0c0\x0c1062\x0c10\x0cOmaCharge\x0c1061\x0c10\x0cPrimaryAccount\x0c1183\x0c14\x0c1\x0c1181\x0c10\x0cARNHEM INV MGMT PTY LTD - DMA\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1183\x0c14\x0c8\x0c1181\x0c10\x0c11332394\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1183\x0c14\x0c12\x0c1181\x0c10\x0cGS_ARN_D\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1183\x0c14\x0c16\x0c1181\x0c10\x0c90599\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1182\x0c14\x0c0\x0c1152\x0c10\x0cGSJP\x0c1062\x0c10\x0cPrimaryAccount\x0c1061\x0c10\x0cVersusAccount\x0c1183\x0c14\x0c0\x0c1181\x0c10\x0cAUDMA\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1182\x0c14\x0c0\x0c1152\x0c10\x0cGSJP\x0c1062\x0c10\x0cVersusAccount\x0c1061\x0c10\x0cSalesRepAccount\x0c1183\x0c14\x0c4\x0c1181\x0c10\x0c8215\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1182\x0c14\x0c2\x0c1152\x0c10\x0cGSJP\x0c1062\x0c10\x0cSalesRepAccount\x0c3046\x0c10\x0cABC\x0c3185\x0c10\x0cZ82\x0c1543\x0c10\x0cGSAT_DScaling\x0c1544\x0c10\x0csalVis=1,PWPBenchmarkRate=25,baseIndexType="Sector",benchMarkType="PWP",cleanupPercentage=30,cleanupPrice=5.780000,cleanupVolumeLimit=29,endTime=\'2016/07/26 06:15:00 GMT\',executionStyle=2,maxPRate=28,minPRate=26,pRate=10,relativeOffsetPct=31,startTime=\'2016/07/25 21:49:30 GMT\'\x0c1314\x0c9\x0c0\x0c3024\x0c10\x0cDMA\x0c2214\x0c14\x0c1\x0c1061\x0c10\x0cOmaAccountAllocationList\x0c1575\x0c11\x0c0\x0c1062\x0c10\x0cOmaAccountAllocationList\x0c1903\x0c14\x0c-1\x0c1060\x0c9\x0c20\x0c1077\x0c9\x0c0\x0c1079\x0c9\x0c0\x0c1081\x0c9\x0c0\x0c1414\x0c9\x0c5.79\x0c1928\x0c10\x0c0\x0c1980\x0c10\x0cIOS2APOLLOPP.GSAPOLLO\x0c3059\x0c10\x0c11332394\x0c2194\x0c10\x0cGS_ARN_D\x0c3040\x0c10\x0cAUSHARESCASH\x0c3175\x0c14\x0c1\x0c3185\x0c10\x0cZ82\x0c1004\x0c10\x0cARNHEM INV MGMT PTY LTD - DMA\x0c1120\x0c10\x0c\x0c1304\x0c10\x0cABC.AX\x0c1501\x0c9\x0c0\x0c1502\x0c9\x0c20\x0c1503\x0c9\x0c0\x0c1504\x0c9\x0c0\x0c1505\x0c14\x0c0\x0c1061\x0c10\x0cOmaExchangeRate\x0c1176\x0c10\x0cUSD\x0c1177\x0c10\x0cUSD\x0c1168\x0c9\x0c1\x0c1062\x0c10\x0cOmaExchangeRate\x0c1312\x0c9\x0c20\x0c1313\x0c9\x0c0\x0c1315\x0c9\x0c0\x0c1316\x0c9\x0c0\x0c1382\x0c9\x0c1\x0c1383\x0c9\x0c0\x0c1061\x0c10\x0cLocalRootParent\x0c1038\x0c10\x0cppe_XDMa\x0c1147\x0c10\x0c1\x0c1302\x0c12\x0c20160726\x0c1062\x0c10\x0cLocalRootParent\x0c1652\x0c0\x0c0\x0c1014\x0c0\x0c4\x0c1013\x0c9\x0c10\x0c1577\x0c10\x0c\x0c1628\x0c0\x0c0\x0c1578\x0c10\x0c\x0c1624\x0c10\x0c\x0c1626\x0c10\x0c\x0c1702\x0c10\x0c\x0c1703\x0c10\x0c\x0c1649\x0c10\x0c\x0c1651\x0c10\x0c\x0c1531\x0c0\x0c10\x0c1653\x0c0\x0c0\x0c1528\x0c10\x0c\x0c1629\x0c0\x0c0\x0c1704\x0c0\x0c0\x0c1019\x0c10\x0c\x0c1242\x0c9\x0c0\x0c1243\x0c9\x0c0\x0c1016\x0c0\x0c-1\x0c1923\x0c10\x0c\x0c1975\x0c9\x0c0\x0c1976\x0c9\x0c0\x0c1831\x0c10\x0c\x0c2180\x0c11\x0c1\x0c1414\x0c9\x0c5.79\x0c1382\x0c9\x0c1\x0c1749\x0c9\x0c20\x0c1750\x0c9\x0c0\x0c1062\x0c10\x0cOmaOrder\x0c2185\x0c0\x0c1\x0c1141\x0c3\x0c0\x0c', 'serverName': 'ppe_XDMa', 'tag': 'ppe_XDMa120160726', 'viewId': 'ppe_XDMa_pyview', 'method': 'oma_view_message'}
    for test in (data,data1,data2):
        nvp = NVPData(test['nvp'])
        print nvp.toFormatedString()

def test_nvp_duplicate_tag():
        ## bad execution with multiple currency
        data = {'opType': 'NoTranType', 'nvp': '1061\x0c10\x0cOmaExecution\x0c1260\x0c10\x0cqa_ADCb223020160728\x0c1049\x0c0\x0c0\x0c1001\x0c14\x0c1\x0c1002\x0c9\x0c999\x0c1061\x0c10\x0cProductInformation\x0c1061\x0c10\x0cProductAliasList\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c1\x0c1003\x0c10\x0c9HH29LC8\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c6\x0c1003\x0c10\x0cORG290G6.AX\x0c1486\x0c10\x0cAX\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c5\x0c1003\x0c10\x0cAU000ORGB396\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c22\x0c1003\x0c10\x0cORGB39\x0c1486\x0c10\x0cAX\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1062\x0c10\x0cProductAliasList\x0c1118\x0c10\x0cCALL ORG SYDE AMER28 JUL 2016 2.9 AUD\x0c1250\x0c10\x0cAUD\x0c1410\x0c14\x0c13\x0c1061\x0c10\x0cMarketMap\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c1\x0c1611\x0c10\x0cSYDE\x0c1688\x0c10\x0cN/A\x0c1382\x0c9\x0c1\x0c1383\x0c9\x0c0.001\x0c1062\x0c10\x0cMarket\x0c1062\x0c10\x0cMarketMap\x0c1454\x0c0\x0c0\x0c1637\x0c14\x0c0\x0c1691\x0c0\x0c364634941\x0c1061\x0c10\x0cUnderlyingAliasList\x0c1061\x0c10\x0cUnderlyingAlias\x0c1458\x0c0\x0c1\x0c1457\x0c10\x0c*ORG\x0c1062\x0c10\x0cUnderlyingAlias\x0c1061\x0c10\x0cUnderlyingAlias\x0c1458\x0c0\x0c6\x0c1457\x0c10\x0cORG.AX\x0c1494\x0c10\x0cAX\x0c1668\x0c10\x0cSYDE\x0c1062\x0c10\x0cUnderlyingAlias\x0c1061\x0c10\x0cUnderlyingAlias\x0c1458\x0c0\x0c6\x0c1457\x0c10\x0cORG.CHA\x0c1494\x0c10\x0cCHA\x0c1668\x0c10\x0cCHIA\x0c1062\x0c10\x0cUnderlyingAlias\x0c1061\x0c10\x0cUnderlyingAlias\x0c1458\x0c0\x0c5\x0c1457\x0c10\x0cAU000000ORG5\x0c1062\x0c10\x0cUnderlyingAlias\x0c1061\x0c10\x0cUnderlyingAlias\x0c1458\x0c0\x0c22\x0c1457\x0c10\x0cORG\x0c1494\x0c10\x0cAX\x0c1668\x0c10\x0cSYDE\x0c1062\x0c10\x0cUnderlyingAlias\x0c1061\x0c10\x0cUnderlyingAlias\x0c1458\x0c0\x0c22\x0c1457\x0c10\x0cOGFGF\x0c1494\x0c10\x0cO\x0c1668\x0c10\x0cNASD\x0c1669\x0c10\x0cOTC\x0c1062\x0c10\x0cUnderlyingAlias\x0c1062\x0c10\x0cUnderlyingAliasList\x0c1376\x0c10\x0cC\x0c1439\x0c10\x0cAMER\x0c1378\x0c9\x0c2.9\x0c1435\x0c1\x0c28\x0c1436\x0c1\x0c7\x0c1437\x0c1\x0c2016\x0c1438\x0c10\x0c20160728\x0c1756\x0c9\x0c100\x0c1507\x0c0\x0c16\x0c1062\x0c10\x0cProductInformation\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cqa_ADCb\x0c1147\x0c10\x0c2230\x0c1302\x0c12\x0c20160728\x0c1039\x0c13\x0c20160728-01:58:05\x0c1157\x0c10\x0cqa_ADCb\x0c1062\x0c10\x0cOmaLocationInformation\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cEXCHANGE-EXEC\x0c1147\x0c10\x0crk999\x0c1041\x0c10\x0cqa_viking\x0c1302\x0c12\x0c20160728\x0c1039\x0c13\x0c20160728-00:42:43\x0c1062\x0c10\x0cOmaLocationInformation\x0c1304\x0c10\x0c\x0c1045\x0c9\x0c1\x0c1100\x0c9\x0c1\x0c1046\x0c10\x0cAUD\x0c1242\x0c9\x0c1\x0c1243\x0c9\x0c1\x0c1124\x0c10\x0cAUD\x0c1099\x0c0\x0c5\x0c1402\x0c0\x0c5\x0c1219\x0c0\x0c0\x0c1220\x0c0\x0c0\x0c1221\x0c0\x0c0\x0c1222\x0c0\x0c0\x0c1016\x0c14\x0c0\x0c1019\x0c10\x0c\x0c1018\x0c11\x0c0\x0c1122\x0c14\x0c0\x0c1017\x0c13\x0c20160728-00:42:42\x0c1170\x0c14\x0c4\x0c1107\x0c10\x0cSYDE\x0c1645\x0c10\x0crk999\x0c2189\x0c10\x0c\x0c1061\x0c10\x0cOmaStatus\x0c1051\x0c14\x0c0\x0c1092\x0c10\x0cqa_ADCb\x0c1135\x0c16\x0c20160728-01:58:05.624\x0c1317\x0c10\x0c20160728\x0c1020\x0c14\x0c1\x0c1136\x0c10\x0csystem\x0c1062\x0c10\x0cOmaStatus\x0c1061\x0c10\x0cOmaExchangeRate\x0c1176\x0c10\x0cAUD\x0c1177\x0c10\x0cAUD\x0c1168\x0c9\x0c1\x0c1062\x0c10\x0cOmaExchangeRate\x0c1463\x0c11\x0c1\x0c1061\x0c10\x0cPrimaryAccount\x0c1183\x0c14\x0c3\x0c1181\x0c10\x0c79250041\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1182\x0c14\x0c2\x0c1152\x0c10\x0cGSJP\x0c1062\x0c10\x0cPrimaryAccount\x0c1008\x0c9\x0c0\x0c1519\x0c9\x0c0\x0c1534\x0c9\x0c0\x0c1538\x0c9\x0c0\x0c1526\x0c10\x0c\x0c1529\x0c10\x0c\x0c1576\x0c10\x0c\x0c1631\x0c10\x0c\x0c1115\x0c10\x0c\x0c1639\x0c10\x0c\x0c1146\x0c10\x0c\x0c1126\x0c10\x0c\x0c1523\x0c10\x0c\x0c1702\x0c10\x0c\x0c1703\x0c10\x0c\x0c1652\x0c0\x0c0\x0c1124\x0c10\x0c\x0c1046\x0c10\x0c\x0c1498\x0c9\x0c0\x0c1499\x0c9\x0c0\x0c3188\x0c10\x0cXT\x0c1021\x0c10\x0cqa_ADCb222920160728\x0c1061\x0c10\x0cAllocLinkOid\x0c1260\x0c10\x0cqa_ADCb223120160728\x0c1049\x0c0\x0c0\x0c1062\x0c10\x0cAllocLinkOid\x0c1061\x0c10\x0cAllocatedStandAloneExecution\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cqa_ADCb\x0c1147\x0c10\x0c2228\x0c1041\x0c10\x0csystem\x0c1302\x0c12\x0c20160728\x0c1039\x0c13\x0c20160728-01:58:05\x0c1062\x0c10\x0cOmaLocationInformation\x0c1062\x0c10\x0cAllocatedStandAloneExecution\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cEXCHANGE-EXEC\x0c1147\x0c10\x0crk999\x0c1041\x0c10\x0cqa_viking\x0c1302\x0c12\x0c20160728\x0c1039\x0c13\x0c20160728-00:42:43\x0c1062\x0c10\x0cOmaLocationInformation\x0c1062\x0c10\x0cOmaExecution\x0c1061\x0c10\x0cOmaOrder\x0c1260\x0c10\x0cqa_ADCb222920160728\x0c1049\x0c0\x0c2\x0c1001\x0c14\x0c1\x0c1002\x0c9\x0c999\x0c1061\x0c10\x0cProductInformation\x0c1061\x0c10\x0cProductAliasList\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c1\x0c1003\x0c10\x0c9HH29LC8\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c6\x0c1003\x0c10\x0cORG290G6.AX\x0c1486\x0c10\x0cAX\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c5\x0c1003\x0c10\x0cAU000ORGB396\x0c1062\x0c10\x0cProductAlias\x0c1061\x0c10\x0cProductAlias\x0c1110\x0c0\x0c22\x0c1003\x0c10\x0cORGB39\x0c1486\x0c10\x0cAX\x0c1665\x0c10\x0cSYDE\x0c1062\x0c10\x0cProductAlias\x0c1062\x0c10\x0cProductAliasList\x0c1118\x0c10\x0cCALL ORG SYDE AMER28 JUL 2016 2.9 AUD\x0c1250\x0c10\x0cAUD\x0c1410\x0c14\x0c13\x0c1061\x0c10\x0cMarketMap\x0c1061\x0c10\x0cMarket\x0c1707\x0c0\x0c1\x0c1611\x0c10\x0cSYDE\x0c1688\x0c10\x0cN/A\x0c1382\x0c9\x0c1\x0c1383\x0c9\x0c0.001\x0c1062\x0c10\x0cMarket\x0c1062\x0c10\x0cMarketMap\x0c1454\x0c0\x0c0\x0c1637\x0c14\x0c0\x0c1691\x0c0\x0c364634941\x0c1061\x0c10\x0cUnderlyingAliasList\x0c1061\x0c10\x0cUnderlyingAlias\x0c1458\x0c0\x0c1\x0c1457\x0c10\x0c*ORG\x0c1062\x0c10\x0cUnderlyingAlias\x0c1061\x0c10\x0cUnderlyingAlias\x0c1458\x0c0\x0c6\x0c1457\x0c10\x0cORG.AX\x0c1494\x0c10\x0cAX\x0c1668\x0c10\x0cSYDE\x0c1062\x0c10\x0cUnderlyingAlias\x0c1061\x0c10\x0cUnderlyingAlias\x0c1458\x0c0\x0c6\x0c1457\x0c10\x0cORG.CHA\x0c1494\x0c10\x0cCHA\x0c1668\x0c10\x0cCHIA\x0c1062\x0c10\x0cUnderlyingAlias\x0c1061\x0c10\x0cUnderlyingAlias\x0c1458\x0c0\x0c5\x0c1457\x0c10\x0cAU000000ORG5\x0c1062\x0c10\x0cUnderlyingAlias\x0c1061\x0c10\x0cUnderlyingAlias\x0c1458\x0c0\x0c22\x0c1457\x0c10\x0cORG\x0c1494\x0c10\x0cAX\x0c1668\x0c10\x0cSYDE\x0c1062\x0c10\x0cUnderlyingAlias\x0c1061\x0c10\x0cUnderlyingAlias\x0c1458\x0c0\x0c22\x0c1457\x0c10\x0cOGFGF\x0c1494\x0c10\x0cO\x0c1668\x0c10\x0cNASD\x0c1669\x0c10\x0cOTC\x0c1062\x0c10\x0cUnderlyingAlias\x0c1062\x0c10\x0cUnderlyingAliasList\x0c1376\x0c10\x0cC\x0c1439\x0c10\x0cAMER\x0c1378\x0c9\x0c2.9\x0c1435\x0c1\x0c28\x0c1436\x0c1\x0c7\x0c1437\x0c1\x0c2016\x0c1438\x0c10\x0c20160728\x0c1756\x0c9\x0c100\x0c1507\x0c0\x0c16\x0c1062\x0c10\x0cProductInformation\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cStandAloneExecution\x0c1920\x0c0\x0c1\x0c1147\x0c10\x0crk9\x0c1041\x0c10\x0csystem\x0c1302\x0c12\x0c20160728\x0c1039\x0c13\x0c20160728-01:58:05\x0c1062\x0c10\x0cOmaLocationInformation\x0c1061\x0c10\x0cOmaLocationInformation\x0c1038\x0c10\x0cqa_ADCb\x0c1147\x0c10\x0c2229\x0c1041\x0c10\x0csystem\x0c1302\x0c12\x0c20160728\x0c1039\x0c13\x0c20160728-01:58:05\x0c1042\x0c10\x0csystem\x0c1131\x0c10\x0csystem\x0c1157\x0c10\x0cqa_ADCb\x0c1062\x0c10\x0cOmaLocationInformation\x0c1061\x0c10\x0cOmaFeedSystems\x0c1204\x0c10\x0cSYDESTKOPT\x0c1205\x0c11\x0c1\x0c1206\x0c14\x0c2\x0c1207\x0c0\x0c0\x0c1209\x0c10\x0cTSELINK\x0c1208\x0c10\x0c\x0c1210\x0c11\x0c0\x0c1223\x0c11\x0c0\x0c1062\x0c10\x0cOmaFeedSystems\x0c1023\x0c0\x0c0\x0c1112\x0c10\x0c0\x0c1161\x0c10\x0c11\x0c1099\x0c0\x0c5\x0c1402\x0c0\x0c5\x0c1027\x0c14\x0c0\x0c1018\x0c11\x0c0\x0c1024\x0c14\x0c0\x0c1124\x0c10\x0cAUD\x0c1122\x0c14\x0c0\x0c1415\x0c14\x0c-1\x0c1107\x0c10\x0cSYDE\x0c1119\x0c10\x0cN/A\x0c1113\x0c14\x0c0\x0c1061\x0c10\x0cOmaStatus\x0c1051\x0c14\x0c7\x0c1092\x0c10\x0cqa_ADCb\x0c1135\x0c16\x0c20160728-01:58:05.624\x0c1317\x0c10\x0c20160728\x0c1020\x0c14\x0c2\x0c1133\x0c10\x0c9\x0c1136\x0c10\x0csystem\x0c1062\x0c10\x0cOmaStatus\x0c1011\x0c9\x0c999\x0c1012\x0c9\x0c1\x0c1102\x0c9\x0c1\x0c1991\x0c10\x0cAUD\x0c1990\x0c0\x0c1\x0c1989\x0c9\x0c1\x0c1046\x0c10\x0cAUD\x0c1240\x0c9\x0c0\x0c1288\x0c9\x0c0\x0c1289\x0c9\x0c0\x0c1282\x0c9\x0c0\x0c1283\x0c9\x0c0\x0c1284\x0c9\x0c0\x0c1229\x0c9\x0c-1\x0c1230\x0c9\x0c-1\x0c1463\x0c11\x0c1\x0c2202\x0c9\x0c0\x0c2223\x0c9\x0c0\x0c2203\x0c9\x0c0\x0c2204\x0c9\x0c0\x0c2205\x0c9\x0c0\x0c2206\x0c9\x0c0\x0c2207\x0c9\x0c0\x0c2208\x0c9\x0c0\x0c2209\x0c9\x0c0\x0c2210\x0c9\x0c0\x0c1061\x0c10\x0cPrimaryAccount\x0c1183\x0c14\x0c3\x0c1181\x0c10\x0c79250041\x0c1389\x0c10\x0c\x0c1532\x0c10\x0c\x0c1182\x0c14\x0c2\x0c1152\x0c10\x0cGSJP\x0c1062\x0c10\x0cPrimaryAccount\x0c1314\x0c9\x0c999\x0c1903\x0c14\x0c-1\x0c1060\x0c9\x0c0\x0c1077\x0c9\x0c0\x0c1079\x0c9\x0c0\x0c1081\x0c9\x0c0\x0c3188\x0c10\x0cXT\x0c3189\x0c12\x0c20160728\x0c1004\x0c10\x0c\x0c1120\x0c10\x0c\x0c1645\x0c10\x0crk9\x0c1501\x0c9\x0c999\x0c1502\x0c9\x0c0\x0c1503\x0c9\x0c1\x0c1504\x0c9\x0c1\x0c1506\x0c10\x0c9\x0c1505\x0c14\x0c2\x0c1061\x0c10\x0cOmaExchangeRate\x0c1176\x0c10\x0cAUD\x0c1177\x0c10\x0cAUD\x0c1168\x0c9\x0c1\x0c1062\x0c10\x0cOmaExchangeRate\x0c1312\x0c9\x0c999\x0c1313\x0c9\x0c0\x0c1315\x0c9\x0c1\x0c1316\x0c9\x0c1\x0c1061\x0c10\x0cLocalRootParent\x0c1038\x0c10\x0cqa_ADCb\x0c1147\x0c10\x0c2229\x0c1302\x0c12\x0c20160728\x0c1062\x0c10\x0cLocalRootParent\x0c1652\x0c0\x0c0\x0c1014\x0c0\x0c4\x0c1577\x0c10\x0c\x0c1628\x0c0\x0c0\x0c1578\x0c10\x0c\x0c1624\x0c10\x0c\x0c1626\x0c10\x0c\x0c1702\x0c10\x0c\x0c1703\x0c10\x0c\x0c1649\x0c10\x0c\x0c1651\x0c10\x0c\x0c1531\x0c0\x0c-1\x0c1653\x0c0\x0c0\x0c1528\x0c10\x0c\x0c1629\x0c0\x0c0\x0c1704\x0c0\x0c0\x0c1019\x0c10\x0c\x0c1242\x0c9\x0c0\x0c1243\x0c9\x0c0\x0c1201\x0c12\x0c20160728\x0c1016\x0c0\x0c0\x0c1923\x0c10\x0c\x0c1975\x0c9\x0c0\x0c1976\x0c9\x0c0\x0c1831\x0c10\x0c\x0c2180\x0c11\x0c1\x0c1029\x0c0\x0c0\x0c1033\x0c9\x0c999\x0c1034\x0c9\x0c0\x0c1414\x0c9\x0c0\x0c1749\x0c9\x0c0\x0c1750\x0c9\x0c0\x0c1062\x0c10\x0cOmaOrder\x0c2185\x0c0\x0c1\x0c1141\x0c3\x0c1206\x0c', 'serverName': 'qa_ADCb', 'tag': 'qa_ADCb223020160728', 'viewId': 'qa_ADCb_pyview', 'method': 'oma_view_execution'}
        nvp = NVPData(data['nvp'])
        #out = nvp._construct()
        print "origin"
        print data['nvp']
        print "reconstructed"
        raw = construct_nvp_raw(nvp.root_)
        print raw

        print nvp.toFormatedString()
        assert raw == data['nvp']


def test_nvp_failed_blank_enum_value():
    ## another parsing failed nvp
    data = "106110OmaOrder126010ppe_XTDd230201607291049001001140100291500106110ProductInformation106110ProductAliasList106110ProductAlias111001100310CBAUF106210ProductAlias106110ProductAlias111006100310CBA.AX148610AX166510SYDE106210ProductAlias106110ProductAlias111006100310CBA.CHA148610CHA166510CHIA106210ProductAlias106110ProductAlias1110032100310CBA AT166510SYDE106210ProductAlias106110ProductAlias1110032100310CBA AU166410AU106210ProductAlias106110ProductAlias111005100310AU000000CBA7106210ProductAlias106110ProductAlias1110022100310CBAUF148610O166510NASD166610OTC106210ProductAlias106110ProductAlias1110022100310CBA148610AX166510SYDE106210ProductAlias106110ProductAlias1110031003106215035166410AU106210ProductAlias106210ProductAliasList111810COMMONWEALTH BANK OF AUSTRALIACMN125010AUD141014161500146106110MarketMap106110Market170701161110SYDE168810N/A138291138391106210Market106110Market170702161110CHIA168810N/A138291138391106210Market106110Market170702161110NASD168810OTC138291001705010138390.000100000106210Market106210MarketMap1454001637140169101000223375128110110710SYDE144600106210ProductInformation106110OmaLocationInformation103810ppe_XTDd114710230104110qa_BOGHOH1302122016072910391320160729-04:59:44104210qa_BOGHOH113110qa_BOGHOH115710ppe_XTDd106210OmaLocationInformation106110OmaFeedSystems120410SYDEN/A12051111206142120700120910TSELINK12081012101101223110106210OmaFeedSystems1023001028100,25,85,1411111104,15,83111210011611011104010109905140205102714010181101024140112410AUD1122140141514-110951011261010261320160729-00:00:00110710SYDE111910N/A1523101113140106110OmaStatus1051140109210ppe_XTDd153310qa_BOGHOH11351620160729-04:59:44.759131710201607291020140113610qa_BOGHOH215810ppe_XTDd20160729360215900106210OmaStatus10119010129011029019900019899012409012889012899012829012839012849012299-112309-11463111106110PrimaryAccount1183140118110AUSTRALIA138910153210118314811811011263252138910153210118314161181103712113891015321011831427118110ARGO1389101532101182140115210GSJP13661011263252AUSTRALIAGSJPARGO37121106210PrimaryAccount2180111218110Broker318510IMS131490302410SS1967142106110OmaAccountAllocationList1575110106210OmaAccountAllocationList190314-11060915001077901079901081901928101109140175310INST318510IMS100410ARGO INVS LTD1120100106110MarketDataList106110MarketDataInformation159791.336434159890117610USD117710AUD106790106890151990106990114490114590184800159910106210MarketDataInformation106210MarketDataList1501901502915001503901504901505140106110OmaExchangeRate117610USD117710USD116891106210OmaExchangeRate131291500131390131590131690138291138391106110LocalRootParent103810ppe_XTDd11471023013021220160729106210LocalRootParent165200101404157710162800157810162410162610170210IMS1703101649101651101531010165300152810Australia16290017040010191012429012439010160-11923101975901976901831102180111141490138291174991500175090106210OmaOrder21850111413539" 
    nvp = NVPData(data)
    print nvp.toFormatedString()

### test send nvp
import sys
import os
import pytest
## check which environment
import localcfg
import zerorpc
from conf import settings

client = zerorpc.Client(settings.OMA_API_URL)


def test_create_gset_nvp_order():
    """
        [OmaNvpObjectStart|10|OmaOrder]
        [OmaNvpHandlingInstructions|10|0]
        [OmaNvpObjectStart|10|OmaStatus]
        [OmaNvpTransactionType|0|0]
        [OmaNvpTransactionCreator|10|gemini]
        [OmaNvpObjectEnd|10|OmaStatus]
        [OmaNvpFIXLineId|10|IOS2APOLLOPP.GSAPOLLO]
        [OmaNvpObjectStart|10|OmaLocationInformation]
        [OmaNvpSystemName|10|IOS2APOLLOPP.GSAPOLLO]
        [OmaNvpSystemType|0|1]
        [OmaNvpTag|10|25023169-001]
        [OmaNvpCreationTime|10|20160731-23:57:11]
        [OmaNvpResponsibilityOf|10|GS_ARN_D]
        [OmaNvpCreator|10|GS_ARN_D]
        [OmaNvpObjectEnd|10|OmaLocationInformation]
        [OmaNvpFIXOrderOwner|10|GS_ARN_D]
        [OmaNvpCustomerCapacity|0|0]
        [OmaNvpOrderCapacity|0|1]
        [OmaNvpQuantity|9|5]
        [OmaNvpOrderType|0|1]
        [OmaNvpTimeInForce|0|0]
        [OmaNvpExecutionCurrency|10|AUD]
        [OmaNvpLimitPriceCurrency|10|AUD]
        [OmaNvpLimitPrice|9|5.72]
        [OmaNvpTradingAlgorithm|10|GSAT_Piccolo]
        [OmaNvpTradingAlgorithmParameters|10|startTime='2016/07/31 23:49:30 GMT',endTime='2016/08/01 06:15:00 GMT',maxWaitMult=0,salVis=1]
        [OmaNvpCustomerUser|10|GS_ARN_D]
        [OmaNvpDiscretionaryOffset|9|0]
        [OmaNvpExecutionInstructions|10|5,27]
        [OmaNvpHandlingInstructions|10|10]
        [OmaNvpClientCustomerPartyType|0|1]
        [OmaNvpObjectStart|10|PrimaryAccount]
        [OmaNvpAccountType|0|0]
        [OmaNvpObjectStart|10|AccountAlias]
        [OmaNvpAccountSynType|0|1]
        [OmaNvpAccountId|10|GS_ARN_D]
        [OmaNvpObjectEnd|10|AccountAlias]
        [OmaNvpObjectStart|10|AccountAlias]
        [OmaNvpAccountSynType|0|12]
        [OmaNvpAccountId|10|GS_ARN_D]
        [OmaNvpObjectEnd|10|AccountAlias]
        [OmaNvpObjectEnd|10|PrimaryAccount]
        [OmaNvpBookingInstructions|10|GS_ARN_D]
        [OmaNvpSide|0|0]
        [OmaNvpClientProductId|10|ABC]
        [OmaNvpObjectStart|10|ProductInformation]
        [OmaNvpObjectStart|10|ProductAliasList]
        [OmaNvpObjectStart|10|ProductAlias]
        [OmaNvpProductIdType|0|6]
        [OmaNvpProductId|10|ABC.AX]
        [OmaNvpObjectEnd|10|ProductAlias]
        [OmaNvpObjectEnd|10|ProductAliasList]
        [OmaNvpObjectEnd|10|ProductInformation]
        [OmaNvpFIXSymbolType|0|6]
        [OmaNvpBookingInstructions|10|GS_ARN_D]
        [OmaNvpOrderFlags|10|23,34]
        [OmaNvpObjectEnd|10|OmaOrder]
    """
    ####################################
    ## OmaNpvTag must unique for the day
    system = "ppe_XDMa"
    account_name = "GS_GCAPE_D"

    order = OrderedMultiDict()
    oma_order = order['OmaOrder'] = OrderedMultiDict()
    oma_order["OmaNvpSide"] = 0
    oma_order["OmaNvpHandlingInstructions"] = "0"

    status = OrderedMultiDict()
    status["OmaNvpTransactionType"] = 0
    status["OmaNvpTransactionCreator"] = "luosam"
    oma_order["OmaStatus"] = status
    oma_order["OmaNvpFIXLineId"] = "IOS2APOLLOPP.GSAPOLLO"
    ## location
    location = OrderedMultiDict()
    location["OmaNvpSystemName"] = "IOS2APOLLOPP.GSAPOLLO"
    location["OmaNvpSystemType"] = 1
    location["OmaNvpTag"] = "1244"
    location["OmaNvpCreationTime"] = "20160731-23:57:11"
    location["OmaNvpResponsibilityOf"] = account_name
    location["OmaNvpCreator"] = account_name
    oma_order["OmaLocationInformation"] = location

    oma_order["OmaNvpFIXOrderOwner"] = account_name
    oma_order["OmaNvpCustomerCapacity"] = 0
    oma_order["OmaNvpOrderCapacity"] = 1
    oma_order["OmaNvpQuantity"] = 23
    oma_order["OmaNvpOrderType"] = 1
    oma_order["OmaNvpTimeInForce"] = 0
    oma_order["OmaNvpExecutionCurrency"] = "AUD"
    oma_order["OmaNvpLimitPriceCurrency"]= "AUD"
    oma_order["OmaNvpLimitPrice"] = 5.72
    oma_order["OmaNvpExecutionPoint"] = "SYDE"
    oma_order["OmaNvpTradingAlgorithm"] = "GSAT_Piccolo"
    oma_order["OmaNvpTradingAlgorithmParameters"] = "startTime='2016/07/31 23:49:30 GMT',endTime='2016/08/01 06:15:00 GMT',maxWaitMult=0,salVis=1"
    oma_order["OmaNvpCustomerUser"] = account_name
    oma_order["OmaNvpDiscretionaryOffset"] = "0"
    oma_order["OmaNvpExecutionInstructions"] = "5,27"
    oma_order["OmaNvpHandlingInstructions"] = "10"
    oma_order["OmaNvpClientCustomerPartyType"] = 1
    ## primary account
    account = OrderedMultiDict()
    account["OmaNvpAccountType"] = 0
    alias = OrderedMultiDict()
    alias["OmaNvpAccountSynType"] = 1
    alias["OmaNvpAccountId"] = account_name
    account["AccountAlias"] = alias
    alias_1 = OrderedMultiDict()
    alias_1["OmaNvpAccountSynType"] = 12
    alias_1["OmaNvpAccountId"] = account_name
    account["AccountAlias"] = alias_1
    oma_order["PrimaryAccount"] = account

    oma_order["OmaNvpBookingInstructions"] = account_name
    oma_order["OmaNvpSide"] = 0
    oma_order["OmaNvpClientProductId"] = "ABC"

    product = OrderedMultiDict()
    p_aliasList = OrderedMultiDict()
    p_alias = OrderedMultiDict()
    p_alias["OmaNvpProductIdType"] = 6
    p_alias["OmaNvpProductId"] = "ABC.AX"
    p_aliasList["ProductAlias"] = p_alias
    product["ProductAliasList"] = p_aliasList
    oma_order["ProductInformation"] = product

    oma_order["OmaNvpFIXSymbol"] = "ABC.AX"
    oma_order["OmaNvpFIXSymbolType"] = 6
    oma_order["OmaNvpOrderFlags"] = "23,24"

    nvplist = construct_nvp_list(order)
    print nvplist

    nvpRaw = construct_nvp_raw(order)
    print nvpRaw
    #############################
    ### display pretty nvp 
    parsed = NVPData(nvpRaw)
    print parsed.toFormatedString()

    ret = client.send_nvp("%s/omad" % system,nvpRaw)
    assert ret

def test_create_gset_manual_fill():
    """
        successful tested GSET manul fill.

        [OmaNvpObjectStart|10|OmaOrder]
        [OmaNvpObjectType|10|OmaOrder]
        [OmaNvpUniqueTag|10|qa_XDMc120160805]
        [OmaNvpVersionNumber|2|1]
        [OmaNvpObjectStart|10|OmaStatus]
        [OmaNvpTransactionType|2|7]
        [OmaNvpObjectEnd|10|OmaStatus]
        [OmaNvpStatusType|2|2]
        [OmaNvpObjectEnd|10|OmaOrder]
        [OmaNvpObjectStart|10|OmaExecution]
        [OmaNvpObjectType|10|OmaExecution]
        [OmaNvpObjectStart|10|OmaStatus]
        [OmaNvpTransactionType|2|7]
        [OmaNvpObjectEnd|10|OmaStatus]
        [OmaNvpStatusType|2|2]
        [OmaNvpCreator|10|gemini]
        [OmaNvpExecutionType|2|3]
        [OmaNvpQuantity|9|3]
        [OmaNvpExecutionPrice|9|25.9]
        [OmaNvpExecutionTime|10|20160805-00:09:00]
        [OmaNvpOffMarketIndicator|2|0]
        [OmaNvpSide|2|8]
        [OmaNvpBasisOfQuotation|10|]
        [OmaNvpBookingInstructions|10|]
        [OmaNvpQuoteBroker|10|]
        [OmaNvpContraBroker|10|2882]
        [OmaNvpObjectStart|10|VersusAccount]
        [OmaNvpAccountSynType|2|3]
        [OmaNvpAccountId|10|EAEE]
        [OmaNvpAccountType|2|2]
        [OmaNvpObjectEnd|10|VersusAccount]
        [OmaNvpTransactionTradeDate|10|20160805]
        [OmaNvpExecutionCurrency|10|AUD]
        [OmaNvpSourceOwner|10|qa_XDMc120160805;15209;3;7]
        [OmaNvpObjectEnd|10|OmaExecution]
        [OmaNvpTransactionType|0|7]
    """
    system = "qa_XDMc"

    manual_fill = OrderedMultiDict()
    oma_order = manual_fill['OmaOrder'] = OrderedMultiDict()
    oma_order["OmaNvpObjectType"] = "OmaOrder"
    oma_order["OmaNvpUniqueTag"] = "qa_XDMc120160805"
    oma_order["OmaNvpVersionNumber"] = 2
    status = OrderedMultiDict()
    status["OmaNvpTransactionType"] = 7
    oma_order["OmaStatus"] = status
    oma_order["OmaNvpStatusType"] = 2

    oma_fill = manual_fill["OmaExecution"] = OrderedMultiDict()
    oma_fill["OmaNvpObjectType"] = "OmaExecution"
    oma_fill["OmaStatus"] = status
    oma_fill["OmaNvpStatusType"] = 2

    oma_fill["OmaNvpCreator"] = "luosam"
    oma_fill["OmaNvpExecutionType"]= 3
    oma_fill["OmaNvpQuantity"] = 4
    oma_fill["OmaNvpExecutionPrice"] = 25.3
    oma_fill["OmaNvpExecutionTime"] = "20160805-00:09:50"
    oma_fill["OmaNvpOffMarketIndicator"] = 0
    oma_fill["OmaNvpSide"] = 8                  ## buyCross
    oma_fill["OmaNvpBasisOfQuotation"] =""
    oma_fill["OmaNvpBookingInstructions"] = ""
    oma_fill["OmaNvpQuoteBroker"] = ""
    oma_fill["OmaNvpContraBroker"] = "2882"
    versus_account = OrderedMultiDict()
    versus_account["OmaNvpAccountSynType"] = 3
    versus_account["OmaNvpAccountId"] = "EAEE"
    versus_account["OmaNvpAccountType"] = 2
    oma_fill["VersusAccount"] = versus_account
    oma_fill["OmaNvpTransactionTradeDate"] = "20160805"
    oma_fill["OmaNvpExecutionCurrency"] = "AUD"
    oma_fill["OmaNvpSourceOwner"]= "qa_XDMc120160805;15209;3;7"

    nvplist = construct_nvp_list(manual_fill)
    print nvplist

    nvpRaw = construct_nvp_raw(manual_fill)
    print nvpRaw
    #############################
    ### display pretty nvp 
    parsed = NVPData(nvpRaw)
    print parsed.toFormatedString()

    ret = client.send_nvp("%s/omad" % system,nvpRaw)
    assert ret

