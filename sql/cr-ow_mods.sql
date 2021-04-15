DROP VIEW arc_energo.ow_mods;

CREATE OR REPLACE VIEW arc_energo.ow_mods
AS SELECT 
    m.dev_id,
    d.arc_name,
    d.description,
    d.dev_name,
    d.dev_name_short,
    d.dev_name_long,
    m.mod_id,
    m.mod_name,
    m.model_name,
    m.art_id,
    m."КодСодержания"
   FROM device d
     JOIN modifications m ON m.dev_id = d.dev_id AND m.version_num = 1
  WHERE d."Поставщик" = 30049 and d.version_num = 1
