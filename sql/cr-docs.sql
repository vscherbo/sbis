-- Drop table

-- DROP TABLE sbis.docs;

CREATE TABLE sbis.docs (
    id serial NOT NULL,
    doc_num varchar NULL,
    doc_date date NULL,
    basis_num varchar NULL,
    basis_date date NULL,
    CONSTRAINT docs_pk PRIMARY KEY (id)
);
COMMENT ON TABLE sbis.docs IS 'XML downloaded';

