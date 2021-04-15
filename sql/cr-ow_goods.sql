-- Drop table

-- DROP TABLE ext.ow_goods;

CREATE TABLE ext.ow_goods (
    id serial NOT NULL,
    owen_id int4 NULL,
    name_short varchar NULL,
    name_full varchar NULL,
    "КодСодержания" int4 NULL,
    who int4 NULL,
    dt_sync timestamp(0) NULL,
    mod_id varchar NULL
);
COMMENT ON TABLE ext.ow_goods IS 'no_dump';

-- CREATE INDEX trgm_idx ON ext.ow_goods USING gist (name_short gist_trgm_ops);
