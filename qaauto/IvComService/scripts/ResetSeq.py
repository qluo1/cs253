#!/gns/mw/lang/python/python-2.7.2-gns.03/bin/python
import sys
import cfg
from conf import settings
from utils import SeqNumber


if __name__ == "__main__":

    args = sys.argv

    usage = """

    --- set cxa/qae  sending seq to 170
   ./scripts/ResetSeq.py "TESTA->QAECXAA,170
   -- for asx /qae sending seq to 510
   ./scripts/ResetSeq.py "TESTC->QAEASXA,510"
    """
    if len(args) !=2:
        print args
        print usage
        sys.exit()

    seq = args[1]

    if "," in seq:
        name,num = seq.split(",")
        num = int(num)
        print "set %s to %d" %(name,num)
        seqNum = SeqNumber(settings.TMP_DIR,name)
        seqNum.set_next(num)
    else:
        name = seq

    ## check old value
    seq = SeqNumber(settings.TMP_DIR,name)
    print "current: %d" % seq.current



