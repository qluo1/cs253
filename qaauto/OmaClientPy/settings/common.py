""" common settings.


"""
import os

TIMEZONE = "Australia/Sydney"

cur_dir = os.path.dirname(os.path.abspath(__file__))
SETTING_DIR = cur_dir
ROOT = os.path.dirname(cur_dir)
LOG_DIR = os.path.join(ROOT,"logs")
TMP_DIR = os.path.join(ROOT,"tmp")

OMA_SVRS = {
        ## single share OMA
        'qa_XTDb': {

            'user': "system",
            'pwd': "qa_omaclient",
            'service': "qa_XTDb/omad",
            #'host': "hkomqla27.hk.eq.gs.com",
            'host': 'xtdb-1.qa.oma.services.gs.com',
            'view': 'qa_XTDb_pyview',
            'seqfile': os.path.join(TMP_DIR,"qa_XTDd.dat"),
            'active': True,
            },

        ## sales OMA
        "qa_HSAa": {
            'user': "system",
            'pwd': "qa_omaclient",
            'service': "qa_HSAa/omad",
            #'host': "hkomqla02.hk.eq.gs.com",
            'host': 'hsaa-1.qa.oma.services.gs.com',
            'view': 'qa_HSAa_pyview',
            'seqfile': os.path.join(TMP_DIR,"qa_HSAa.dat"),
            'active': True,
            },

       "qa_ASRb":{
           'user': "system",
           'pwd': "qa_omaclient",
           'service': "qa_ASRb/omad",
           #'host': "hkomqla02.hk.eq.gs.com",
           'host': 'asrb-1.qa.oma.services.gs.com',
           'view': 'qa_ASRb_pyview',
           'seqfile': os.path.join(TMP_DIR,"qa_ASRb.dat"),
           'active': True,

       },
       ## atp OMA
       "qa_XTDd": {
            'user': "qa_aplgwy",
            'pwd': "qa_omaclient",
            'service': "qa_XTDd/omad",
            'host':"xtdd-1.qa.oma.services.gs.com",
            'view': 'qa_XTDd_pyview',
            'seqfile': os.path.join(TMP_DIR,"qa_XTDd.dat"),
            'active': True,
            },
        ## GSET OMA -- disable too noisy
        "ppe_XDMa": {
            'user': "qa_aplgwy",
            'pwd': "qa_omaclient",
            'service': "ppe_XDMa/omad",
            'host':"xdma-1.ppe.oma.services.gs.com",
            'view': 'ppe_XDMa_pyview',
            'seqfile': os.path.join(TMP_DIR,"ppe_XDMa.dat"),
            'active': True,
            },
        ## legacy 
        "qa_XDMb": {
            'user': "system",
            'pwd': "qa_omaclient",
            'service': "qa_XDMb/omad",
            'host':"xdmb-1.qa.oma.services.gs.com",
            'view': 'qa_XDMb_pyview',
            'seqfile': os.path.join(TMP_DIR,"qa_XDMb.dat"),
            'active': True,
            },
        ## gset DMA
        "qa_XDMc": {
            'user': "system",
            'pwd': "qa_omaclient",
            'service': "qa_XDMc/omad",
            'host':"xdmc-1.qa.oma.services.gs.com",
            'view': 'qa_XDMc_pyview',
            'seqfile': os.path.join(TMP_DIR,"qa_XDMc.dat"),
            'active': True,
            },
        ## atp PPE
        "ppe_XTDd": {
            'user': "qa_aplgwy",
            'pwd': "qa_omaclient",
            'service': "ppe_XTDd/omad",
            'host':"xtdd-1.ppe.oma.services.gs.com",
            'view': 'ppe_XTDd_pyview',
            'seqfile': os.path.join(TMP_DIR,"ppe_XTDd.dat"),
            'active': True,
            },

        ## pt OMA
        "qa_XPSa": {
            'user':'system',
            'pwd': 'system',
            'service': "qa_XPSa/omad",
            'host': "XPSa-1.qa.oma.services.gs.com",
            'view': 'qa_XPSa_pyview',
            'seqfile': os.path.join(TMP_DIR,"qa_XPSa.dat"),
            'active': True,
        },

        ## pt OMA
        "ppe_XPXz": {
            'user':'listener',
            'pwd': 'qa_omaclient',
            'service': "ppe_XPXz/omad",
            'host': "XPXz-1.ppe.oma.services.gs.com",
            'view': 'ppe_XPXz_pyview',
            'seqfile': os.path.join(TMP_DIR,"ppe_XPXz.dat"),
            'active': True,
        },
        ## pt OMA
        "qa_XPXz": {
            'user':'listener',
            'pwd': 'qa_omaclient',
            'service': "qa_XPXz/omad",
            'host': "XPXz-1.qa.oma.services.gs.com",
            'view': 'qa_XPXz_pyview',
            'seqfile': os.path.join(TMP_DIR,"qa_XPXz.dat"),
            'active': True,
        },
        ## 
        "qa_ADCb": {
            'user': "system",
            'pwd': "qa_omaclient",
            'service': "qa_ADCb/omad",
            'host': 'ADCb-1.qa.oma.services.gs.com',
            'view': 'qa_ADCb_pyview',
            'seqfile': os.path.join(TMP_DIR,"qa_ADcb.dat"),
            'active': True,
    },

}
## debug only
OMA_SVRS = {
        ## GSET OMA -- disable too noisy
        "ppe_XDMa": {
            'user': "qa_aplgwy",
            'pwd': "qa_omaclient",
            'service': "ppe_XDMa/omad",
            'host':"xdma-1.ppe.oma.services.gs.com",
            'view': 'ppe_XDMa_pyview',
            'seqfile': os.path.join(TMP_DIR,"ppe_XDMa.dat"),
            'active': True,
            },
#        ## legacy 
#        "qa_ADCb": {
#            'user': "system",
#            'pwd': "qa_omaclient",
#            'service': "qa_ADCb/omad",
#            'host': 'ADCb-1.qa.oma.services.gs.com',
#            'view': 'qa_ADCb_pyview',
#            'seqfile': os.path.join(TMP_DIR,"qa_ADcb.dat"),
#            'active': True,
#    },
#
        ## gset DMA
        "qa_XDMc": {
            'user': "system",
            'pwd': "qa_omaclient",
            'service': "qa_XDMc/omad",
            'host':"xdmc-1.qa.oma.services.gs.com",
            'view': 'qa_XDMc_pyview',
            'seqfile': os.path.join(TMP_DIR,"qa_XDMc.dat"),
            'active': True,
            },
}
