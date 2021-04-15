-- Drop table

-- DROP TABLE sbis.ow_bill_items;

CREATE TABLE sbis.ow_bill_items (
    id serial NOT NULL,
    bill_id integer NOT NULL,
    code varchar NULL,
    item_name varchar NULL,
    kolich numeric NULL,
    price numeric NULL,
    price_skidka numeric NULL,
    summa numeric NULL,
    nds numeric NULL,
    full_name varchar NULL,
    strana varchar NULL,
    gtd varchar NULL,
    CONSTRAINT ow_bill_items_pk PRIMARY KEY (id)
);

