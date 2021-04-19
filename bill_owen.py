#!/usr/bin/env python
"""
Parse owen bill and save into PG
"""
#import inspect
import os
#import time
#from datetime import datetime
#from datetime import timedelta
#import datetime
import logging
#import copy
#import codecs

import xml.etree.ElementTree as ET

from pg_app import PGapp
import log_app


def parse_xml(root):
    """ Parse XML bill """
    bill = {}
    items_table = []
    bill['schet'] = root.attrib['schet']
    bill['date_sch'] = root.attrib['date_sch']
    bill['tax'] = root.attrib['tax']
    bill['num_nakl'] = root.attrib['num_nakl']
    bill['summa'] = root.attrib['summa']
    bill['nds'] = root.attrib['nds']
    bill['post_summa'] = root.attrib['post_summa']
    bill['post_nds'] = root.attrib['post_nds']

    goods = root.find('items')
    izd_list = goods.findall('izdelia')
    for item in izd_list:
        items_table.append(item.attrib)

    return bill, items_table

class OwenApp(PGapp, log_app.LogApp):
    """ An OWEN app
    """
    def __init__(self, args):
        log_app.LogApp.__init__(self, args=args)
        script_name = os.path.splitext(os.path.basename(__file__))[0]
        config_filename = '{}.conf'.format(script_name)
        self.get_config(config_filename)
        super(OwenApp, self).__init__(self.config['PG']['pg_host'],
                                      self.config['PG']['pg_user'])
        if self.pg_connect():
            self.set_session(autocommit=True)
        self.bill = {}
        self.items_table = []

    def read_xml(self, filename):
        """ read saved xml and prepare to write to PG """
        tree = ET.parse(filename)
        root = tree.getroot()
        self.bill, self.items_table = parse_xml(root)

    INSERT_DOC = """INSERT INTO sbis.ow_bill(schet, date_sch, tax, num_nakl, summa,
nds, post_summa, post_nds) VALUES(%s, %s, %s, %s, %s, %s, %s, %s) RETURNING bill_id;"""

    """
    code="30524" name="ДТС035-100М.В3.2000" kolich="3" price="2015"
    price_skidka="1470.95" summa="4412.85" nds="882.57"
    FULL_NAME="Термопреобразователь сопротивления ДТС035-100М.В3.2000" STRANA="" GTD=""
    """
    INSERT_ITEM = """INSERT INTO sbis.ow_bill_items(bill_id, code, item_name, kolich,
price, price_skidka, summa, nds, full_name, strana, gtd)
VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""

    def xml_db(self):
        """ Save xml doc to PG """
        #logging.debug('bill=%s', self.bill)
        loc_sql = self.curs.mogrify(self.INSERT_DOC,
                                    (self.bill['schet'],
                                     self.bill['date_sch'],
                                     self.bill['tax'],
                                     self.bill['num_nakl'],
                                     self.bill['summa'],
                                     self.bill['nds'],
                                     self.bill['post_summa'],
                                     self.bill['post_nds']
                                    ))
        logging.debug('loc_sql=%s', str(loc_sql, 'utf-8'))
        self.do_query(loc_sql, reconnect=True)
        inserted_id = self.curs.fetchone()[0]
        if inserted_id:
            # items
            """
            code="30524" name="ДТС035-100М.В3.2000" kolich="3" price="2015"
            price_skidka="1470.95" summa="4412.85" nds="882.57"
            FULL_NAME="Термопреобразователь сопротивления ДТС035-100М.В3.2000" STRANA="" GTD=""
            """
            logging.debug('items_table=%s', self.items_table)
            for item_row in self.items_table:
                loc_sql = self.curs.mogrify(self.INSERT_ITEM,
                                            (inserted_id,
                                             item_row['code'],
                                             item_row['name'],
                                             item_row['kolich'],
                                             item_row['price'],
                                             item_row['price_skidka'],
                                             item_row['summa'],
                                             item_row['nds'],
                                             item_row['FULL_NAME'],
                                             item_row['STRANA'],
                                             item_row['GTD']
                                            ))
                logging.debug('loc_sql=%s', str(loc_sql, 'utf-8'))
                self.do_query(loc_sql, reconnect=True)
        else:
            logging.warning('Не удалось получить id добавленной в sbis.ow_bill строки')

if __name__ == '__main__':

    log_app.PARSER.formatter_class = log_app.argparse.ArgumentDefaultsHelpFormatter
    log_app.PARSER.add_argument('--xml', type=str,
                                help='parse XML document')

    ARGS = log_app.PARSER.parse_args()
    #do_nothing()
    OWEN = OwenApp(args=ARGS)
    if OWEN:
        if ARGS.xml:
            OWEN.read_xml(ARGS.xml)
            OWEN.xml_db()
