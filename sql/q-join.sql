with ow_doc as (select d.basis_num, d.id, d.doc_num, d.doc_date
--, di.item_price
, replace(di.qnt, '.000', '')::integer ow_qnt, di.total_price::numeric
from sbis.docs d
join sbis.doc_items di on di.doc_id = d.id 
where d.doc_date >'2021-03-22'
--and d.basis_num='Д 220321-406'
),
z_doc as (SELECT DISTINCT z.Код, z.Дата, sz.СчетПоставщика, sz."Количество", sz."Количество"*sz."СтоимостьПозицииС_НДС" z_total
--, sz."Счет"
FROM Заказ z JOIN СписокЗаказа sz ON z.Заказ =sz.Заказ
WHERE z.Код=30049
-- AND NOT z.Выполнен AND NOT z.Отменен 
and z."Дата" > '2021-03-22'
and СчетПоставщика IS NOT null)
select zd.*, od.*
from z_doc zd
left join ow_doc od on zd.СчетПоставщика = od.basis_num
and zd.z_total = od.total_price
and zd."Количество" = od.ow_qnt
-- Д 090321-416
-- Д 220321-406
