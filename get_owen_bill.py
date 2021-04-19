#!/usr/bin/env python
""" Read emails from folder "owen_bill@kipspb.ru/INBOX"
which contain Счета....xml
Parse and save them into PG
"""

import os
#import datetime
import imaplib
import email
import email.message
from email.header import decode_header
#from imapclient import imap_utf7

import log_app
from log_app import logging

SUBJ = ('запрос', 'заявка',
        'заказ', 'прошу', 'просим', 'выставить',
        'оборудовани', 'счет', 'счёт', 'подобрать', 'вопрос', 'оплату', 'поставку',
        'стоимост', 'срок', 'закуп'
        )

def mk_or_crit(crits):
    """make OR criteria"""
    res = '(SUBJECT "{}")'.format(crits[0])
    for subj in crits[1:]:
        res = '(OR (SUBJECT "{}") {})'.format(subj, res)
    return res

class BillApp(log_app.LogApp):
    """ An application to copy and move emails via IMAP """

    def __init__(self, args, description):
        super(BillApp, self).__init__(args, description)
        script_name = os.path.splitext(os.path.basename(__file__))[0]
        self.get_config('{}.conf'.format(script_name))
        #logging.debug(self.config['imap source']['login'])
        self.imap_src = imaplib.IMAP4_SSL(self.config['imap source']['imap_srv'])
        self.msg = None

    def connect(self):
        """ Connect to IMAP servers: source and destination"""
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
            """
            if data[0]:
                loc_data = data[0][1]
                if isinstance(loc_data, bytes):
                    msg = email.message_from_bytes(loc_data)
                else:
                    msg = None
                    logging.warning('Wrong type(loc_data)=%s', type(loc_data))
            else:
                loc_data = 'no data[0]'
                msg = None
            """

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
            else:
                logging.info('Empty msg')

            # MOVE
            src_type, src_data = self.imap_src.uid('MOVE', num, 'Archive')
            if src_type == 'OK':
                logging.info('MOVED to folder Archive num=%s', num)
            else:
                logging.error('MOVE error %s: %s', src_type, src_data)

        self.imap_src.close()


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

if __name__ == '__main__':
    ARGS = log_app.PARSER.parse_args()
    BILL_APP = BillApp(args=ARGS, description='Read emails with bill')
    logging.info('Start app')
    BILL_APP.connect()
    BILL_APP.extract_xml()
    BILL_APP.disconnect()
    logging.info('Finish app')
