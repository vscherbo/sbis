-- Drop table

-- DROP TABLE sbis.doc_items;

CREATE TABLE sbis.doc_items (
    id serial NOT NULL,
    doc_id int4 NOT NULL,
    pos_num varchar NULL,
    item_name varchar NULL,
    qnt varchar NULL,
    okei varchar NULL,
    vat varchar NULL,
    item_price varchar NULL,
    total_no_vat varchar NULL,
    total_price varchar NULL,
    ow_article varchar NULL,
    CONSTRAINT doc_items_pk PRIMARY KEY (id)
);
