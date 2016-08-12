How to run GSET migration test
=================================

issue 1: test account might migrted? 

---------- query Darpan/QA for fix migrated ----------
use qa_client_db
go
select distinct a.client_id, c.access_id
from client_property a, client_property b, client_mapping c
where a.market in ('SYDE','CHIA')
and a.client_id = b.client_id
and a.client_id = c.client_id
and b.property_name = 'ANZMIGRATED'
and b.property_value = 'A'
and c.access_id_type = 1
go


issue 2: market price being rejected

fetchmarket data script actual query real market price
--------------- command to query symbol price ----
bin/FetchMarketData.py --symbol NAB.AX | grep -i close





Depencency:

http://prod.area.services.gs.com/area/public/producers/external.io.redis/packages/redisserver/releases/3.2.0/assets/redis-3.2.0.tar.gz
