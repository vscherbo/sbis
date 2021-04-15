select og.*, om.dev_id, om."КодСодержания", om.arc_name, om.art_id
from ext.ow_goods og 
join ow_mods om on om.model_name = og.name_short 
