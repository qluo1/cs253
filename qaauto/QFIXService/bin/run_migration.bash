#!/bin/bash
export PATH=/gns/mw/lang/perl/perl-5.10-4/bin:$PATH
export PERLHOME=/gns/mw/lang/perl/perl-5.10-4/
export PERLLIB=/gns/mw/lang/perl/perl-5.10-4/lib/site_perl/5.10.4/
export SYBASE_PATH=/gns/mw/dbclient/sybase/oc/openclient-15.5.0.ESD9.v01/
export LD_LIBRARY_PATH=/gns/mw/dbclient/sybase/oc/openclient-15.7.0.EBF19872.ESD2.v01/OCS-15_0/lib/:$LD_LIBRARY_PATH

. ${SYBASE_PATH}/SYBASE.sh

CUR_DIR=${PWD##}

echo "Converting the Excel TestCase file to Python scripts...."
$CUR_DIR/bin/migrate_apollo_tc.py $@

