#!/usr/bin/env python
""" Read emails from folder "owen_bill@kipspb.ru/INBOX"
which contain Счета....xml
Parse and save them into PG
"""
import os
import logging

import xml.etree.ElementTree as ET
import imaplib
import email
import email.message
from email.header import decode_header

from pg_app import PGapp
import log_app
from log_app import logging


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

def decode_header_field(arg_field):
    """ Decode SMTP Header's filed"""
    _field = decode_header(arg_field)
    logging.debug('arg_field=%s, type(_field)=%s, _field=%s', arg_field, type(_field), _field)

    str_list = []
    for tup in _field:
        try:
            tup0 = tup[0].decode(tup[1] or 'ASCII')
        except (UnicodeDecodeError, AttributeError):
            tup0 = tup[0]
        str_list.append(str(tup0))
    _str = ''.join(str_list).replace('\n', '')
    return _str

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
        self.imap_src = imaplib.IMAP4_SSL(self.config['imap source']['imap_srv'])
        self.msg = None
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

    def connect(self):
        """ Connect to IMAP server"""
        src_type, src_data = self.imap_src.login(self.config['imap source']['login'],
                                                 self.config['imap source']['password'])
        if src_type != 'OK':
            logging.error('Login error %s: %s', src_type, src_data[0][1])

        logging.info('Logged in with result: src=%s', src_type)

    def disconnect(self):
        """ logout from IMAP server """
        self.imap_src.logout()

    def get_msg(self, data):
        """ get msg object """
        if data[0]:
            loc_data = data[0][1]
            if isinstance(loc_data, bytes):
                self.msg = email.message_from_bytes(loc_data)
            else:
                self.msg = None
                logging.warning('Wrong type(loc_data)=%s', type(loc_data))
        else:
            loc_data = 'no data[0]'
            self.msg = None

    def extract_xml(self):
        """ Move found emails """
        self.imap_src.select(mailbox='INBOX', readonly=False)
        #res, data = self.imap_src.uid('search', None, '(BEFORE "25-Sep-2020")')
        #criteria_or = mk_or_crit(SUBJ)
        #dt_crit = (datetime.date.today() -
        #           datetime.timedelta(days=5)).strftime('%d-%b-%Y')
        #criteria = '((BEFORE "{}") {})'.format(dt_crit, criteria_or)
        criteria = '(UNSEEN)'
        # WORKS! criteria = '((BEFORE "25-Oct-2020") (OR (SUBJECT "заявка") (SUBJECT "заказ")))'
        res, data = self.imap_src.uid('search', 'CHARSET UTF-8', criteria.encode())
        logging.info('Source search result:%s', res)
        for num in data[0].split():
            res, data = self.imap_src.uid('FETCH', num, '(RFC822)')
            self.get_msg(data)
            logging.info('Message found result=%s: num=%s', res, num)
            if self.msg:
                subj_str = decode_header_field(self.msg.get('Subject', 'no_Subject'))
                from_str = decode_header_field(self.msg.get('From', 'no_From'))
                to_str = decode_header_field(self.msg.get('To', 'no_To'))
                logging.info('From=%s To=%s Subject=%s', from_str.replace('\n', ''),
                             to_str.replace('\n', ''),
                             subj_str.replace('\n', ''))
                # downloading attachments
                for part in self.msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue
                    file_name = decode_header_field(part.get_filename())
                    logging.info('attachment file_name="%s"', file_name)
                    if file_name.startswith('Счет_Д') and file_name.endswith('.xml'):
                        file_path = os.path.join('bills/', file_name)
                        if not os.path.isfile(file_path):
                            fpart = open(file_path, 'wb')
                            fpart.write(part.get_payload(decode=True))
                            fpart.close()
                        #subject = str(msg).split("Subject: ", 1)[1].split("\nTo:", 1)[0]
                        logging.info('Downloaded "%s" from email titled "%s".', file_name, subj_str)
                        self.read_xml(file_path)
                        self.xml_db()
            else:
                logging.info('Empty msg')

            # MOVE
            src_type, src_data = self.imap_src.uid('MOVE', num, 'Archive')
            if src_type == 'OK':
                logging.info('MOVED to folder Archive num=%s', num)
            else:
                logging.error('MOVE error %s: %s', src_type, src_data)

        self.imap_src.close()
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
        else:
            logging.info('Start app')
            OWEN.connect()
            OWEN.extract_xml()
            OWEN.disconnect()
            logging.info('Finish app')
