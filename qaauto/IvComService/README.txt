IvComService - expose IvCom as python service.
======================================================

IvComService intend to expose IvCom as services, rather than using IvComPy directly.

All services are exposed via zerorpc/0MQ.


code structure as following:
    /          
    |+bin/       
    |+config/       
    |+libs/         
    |+logs/         
    |+scripts/      
    |   |+apps/   
    |+settings/     
    |+tests/        

*config* folder hold all IvCom configuration fills. 
*settings* folder hold IvComService applicaiton configration fills. 
*libs" folder hold external python library.
*scripts"  folder hold all source code 
*tests" folder contain unit tests.


DEPENDENCY
---------------
depend on IvComPy.so and redis for track server-datastream message sequence number.

GS SVN REPO
---------------
svn+ssh://asiaoma.svn.services.gs.com/svnroot/asiaoma/asiacepsupplements/qaautomation/trunk/IvComService

RELEASE
--------------
v1.0 baseline release with 
    - zerorpc request/response
    - zerorpc pub/sub i.e. DSS, ImageLive, TransactionNotification
    - implemented one app instance i.e. QAEAUCEA


v1.1 add internal applicaiton i.e. MessageDumper
    - save dss message to om2 mongodb.
    - save imagelive order/execution to om2 mongodb.

TODO: 


- remove redis dependency to shared memory.
- query imagelive in mongodb.



