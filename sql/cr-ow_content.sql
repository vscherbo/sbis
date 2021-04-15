DROP VIEW arc_energo.ow_content;

CREATE OR REPLACE VIEW arc_energo.ow_content AS
SELECT x."КодНаименования",
    x."КодСодержания",
    REPLACE (x."Кратко", 'ОВЕН', '') as cont_short,
    REPLACE (x."НазваниевСчет",  'ОВЕН', '') as name_in_bill,
    REPLACE (x."ИмяПрибора", 'ОВЕН', '') as device_name
   FROM "Содержание" x
  WHERE x."Поставщик" = 30049 AND x."Активность";
