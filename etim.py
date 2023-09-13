#!/usr/bin/env python

""" Load into PG Owen's catalog in ETIM format
https://products-list.owen.ru/etim/owen_etim_json.zip
"""

import os
import logging
import json


from pg_app import PGapp
import log_app


class EtimApp(PGapp, log_app.LogApp):
    """ An ETIM app
    """
    def __init__(self, args):
        log_app.LogApp.__init__(self, args=args)
        script_name = os.path.splitext(os.path.basename(__file__))[0]
        config_filename = '{}.conf'.format(script_name)
        self.get_config(config_filename)
        super(EtimApp, self).__init__(self.config['PG']['pg_host'],
                                      self.config['PG']['pg_user'])
        if self.pg_connect():
            self.set_session(autocommit=True)
        self.j_fname = args.json

    INSERT = """INSERT INTO ext.ow_goods(owen_id, name_short, name_full)
VALUES(%s, %s, %s);"""
    COPY = r"""\copy ext.ow_goods(owen_id, name_short, name_full) from
    """

    def load_json(self):
        """ load goods from json file into PG """
        with open(self.j_fname, 'r') as jfile:
            goods = json.load(jfile)
            logging.debug('len(goods)=%s', len(goods))
            for item in goods:
                logging.info('%s::%s::%s',
                             item["supplierId"], item["descriptionShort"], item["descriptionFull"])
                loc_sql = self.curs.mogrify(self.INSERT, (item["supplierId"],
                                                          item["descriptionShort"],
                                                          item["descriptionFull"]))
                logging.debug('loc_sql=%s', str(loc_sql, 'utf-8'))
                self.do_query(loc_sql, reconnect=True)


if __name__ == '__main__':
    log_app.PARSER.add_argument('--json', type=str, required=True, help='json file')
    ARGS = log_app.PARSER.parse_args()
    ETIM = EtimApp(args=ARGS)
    if ETIM:
        ETIM.load_json()
