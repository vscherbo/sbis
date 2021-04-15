select og.*, om.dev_id, om."КодСодержания", om.arc_name, om.art_id
from ext.ow_goods og 
join ow_mods om on om.model_name = og.name_short 

select om.model_name -- , count(om.model_name), om."КодСодержания"
from ext.ow_goods og 
join ow_mods om on om.model_name = og.name_short 
where om."КодСодержания" is not null

select d.dev_id, d.arc_name, d.dev_name, d.dev_name_long 
from device d where d.version_num = 1
and
d.dev_id in
(select distinct dev_id from
(select om.dev_id, om.model_name, count(om.model_name)
from ow_mods om
group by om.dev_id, om.model_name
having count(om.model_name) > 1) dbl
) order by 1


select om.dev_id, om.model_name, count(om.model_name)
from ow_mods om
group by om.dev_id, om.model_name
having count(om.model_name) > 1
order by dev_id

update ext.ow_goods set mod_id = mods.mod_id                                         
from 
(select om.mod_id, model_name, dev_id
from ow_mods om) as mods
where mods.model_name = ext.ow_goods.name_short and mods.dev_id not in (3399, 4636)
