-- Drop table

-- DROP TABLE ext.ow_goods;

CREATE TABLE ext.ow_goods (
    owen_id int4 NOT NULL,
    name_short varchar NULL,
    name_full varchar NULL,
    "КодСодержания" int4 NULL,
    who int4 NULL,
    dt_sync timestamp(0) NULL,
    CONSTRAINT ow_goods_pk PRIMARY KEY (owen_id)
);
-- CREATE INDEX trgm_idx ON ext.ow_goods USING gist (name_short gist_trgm_ops);
