select om.model_name, og.name_short, * from ow_mods om, ext.ow_goods og 
where
og.mod_id is null
and om.dev_name_short like '%регулятор%' and og.name_full LIKE '%регулятор%'
and om.model_name %> og.name_short 

select count (*) from ow_mods om where om.dev_name_short like '%регулятор%'
select count (*) from ext.ow_goods og where og.name_full LIKE '%регулятор%'

