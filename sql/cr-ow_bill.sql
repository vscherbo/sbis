-- Drop table

-- DROP TABLE sbis.ow_bill;

CREATE TABLE sbis.ow_bill (
    bill_id serial NOT NULL,
    schet varchar NULL,
    date_sch date NULL,
    tax numeric NULL,
    num_nakl varchar NULL,
    summa numeric NULL,
    nds numeric NULL,
    post_summa numeric NULL,
    post_nds numeric NULL,
    CONSTRAINT ow_bill_pk PRIMARY KEY (bill_id)
);

