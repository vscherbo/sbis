-- sbis.changes definition

-- Drop table DROP TABLE sbis.changes;

CREATE TABLE sbis.changes (
    id serial NOT NULL,
    event_uuid uuid NULL,
    event_name varchar NULL,
    event_dt timestamp(0) NULL,
    doc_uuid uuid NULL,
    doc_name varchar NULL,
    dt_create_sbis timestamp(0) NULL,
    doc_num varchar NULL,
    direction varchar NULL,
    inn_firm varchar NULL,
    inn_ca varchar NULL,
    doc_type varchar NULL,
    deleted varchar NULL,
    CONSTRAINT changes_pk PRIMARY KEY (id)
);
