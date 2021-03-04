#!/usr/bin/env python
"""
Base classes for online.sbis.ru
"""
import inspect
import os
import time
from datetime import datetime
from datetime import timedelta
#import datetime
import logging
import json
import copy
import codecs

import requests
import responses

from pg_app import PGapp
import log_app


VER = 'v4'
DT_FORMAT = '"%d.%m.%Y %H:%M:%S"'
TS_FORMAT = '%Y%m%d_%H%M%S'
EXP_PERIOD = 24*60*60*1000000

"""
"method": "СБИС.Аутентифицировать"
"method": "СБИС.СписокИзменений"
"""


SBIS_QUERY = {
    "jsonrpc": "2.0",
    "method": "",
    "params": {
    },
    "id": 0
}

CHG_LIST = {
    "Фильтр": {
        "ИдентификаторСобытия": "",
        #"ИдентификаторСобытия": "6b563324-0305-42a6-9db3-f7a2de786db6",
        #"ДатаВремяС": "15.02.2021 00.00.00",
        #"ДатаВремяПо": "16.02.2021 23.59.59",
        "НашаОрганизация": {
            "СвЮЛ": {
                "ИНН": "7802715214",
                "КПП": "780201001"
                }
        },
        #"Навигация": {"Страница": "1"},
        "ПолныйСертификатЭП": "Нет"

    }
}

#def print_arg(url, json, headers):
def print_arg(**kwargs):
    """ Logging requests post/get args """
    #logging.debug('url=%s, json=%s, headers=%s', args[0], args[1], args[2])
    logging.debug('kwargs=%s', kwargs)
    resp = requests.Response()
    resp.status_code = 200
    resp.json_data = {"test": "test"}
    return resp

@responses.activate
def do_nothing():
    """ Test response """
    responses.add(
        responses.POST,
        "https://online.sbis.ru/service/?srv=1",
        json={"ok": "No request"},
        status=200
    )
    responses.add(
        responses.GET,
        "https://online.sbis.ru/service/?srv=1",
        json={"ok": "No request"},
        status=200
    )
    logging.debug('============================================= test response')
    response = requests.get("https://online.sbis.ru/service/?srv=1")
    assert response.status_code == 200
    response_body = response.json()
    assert response_body['ok'] == "No request"

class SbisAPI():
    """
    Base class for api.sbis.ru
    """
    headers = {'Content-type': 'application/json-rpc; charset=utf-8'}
    headers['User-Agent'] = 'Python-urllib/3.3'

    #def __init__(self, login=None, password=None, token=None):
    def __init__(self, config):
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        #self.access_token = config['SBIS']['token']
        self.access_token = None
        self.token_created = datetime.strptime(config['SBIS']['created'],
                                               DT_FORMAT)

        self.auth_url = config['SBIS']['auth_url']
        self.api_url = config['SBIS']['api_url']
        #self.inn = config['SBIS']['inn']

        self.status_code = 200
        self.filename = None

        if self.need_login():
            if config['SBIS']['login'] and config['SBIS']['password']:
                if self.login(config['SBIS']['login'], config['SBIS']['password']):
                    #config['SBIS']['Token'] = self.access_token
                    config['SBIS']['created'] = datetime.now().strftime(DT_FORMAT)
        else:
            logging.info('Do NOT need login. Using saved access_token.')
            self.headers['X-SBISSessionID'] = self.access_token


    def need_login(self):
        """ Returns True if token is expired """
        #return not (self.access_token
        #            and timedelta(datetime.now(), self.token_created) < EXP_PERIOD)
        loc_res = False
        if not self.access_token:
            loc_res = True
            logging.info('Access_token is empty. Need login')
        elif (datetime.now() - self.token_created) > timedelta(days=7):
            loc_res = True
            logging.info('Access_token expired. Need login')
        return loc_res

    @staticmethod
    def __exception_fmt__(tag, exception):
        return '{0} msg={1}'.format(tag, str(exception).encode('utf-8'))

    def sbis_req(self, method, url, payload=None):
        """ POST/GET an request to api.sbis.ru
            Args:
                url - URL on api.sbis.ru
        """
        if method == 'GET':
            loc_method = requests.get
        elif method == 'POST':
            loc_method = requests.post
        else:
            raise 'Wrong value % for argument "method"' % method

        ret = {}  # None
        resp = None
        logging.debug('headers=%s', self.headers)
        try:
            logging.info('url=%s', url)
            logging.info('payload=%s', payload)
            err_msg = None
            resp = loc_method(url=url,
                              json=payload,
                              headers=self.headers)

            self.status_code = resp.status_code
            logging.debug("status_code=%s", resp.status_code)
            resp.raise_for_status()
        except requests.exceptions.Timeout as exc:
            # Maybe set up for a retry, or continue in a retry loop
            err_msg = self.__exception_fmt__('Timeout', exc)
        except requests.exceptions.TooManyRedirects as exc:
            # Tell the user their URL was bad and try a different one
            err_msg = self.__exception_fmt__('TooManyRedirects', exc)
        except requests.exceptions.HTTPError as exc:
            err_msg = self.__exception_fmt__('HTTPError', exc)
        except requests.exceptions.RequestException as exc:
            # catastrophic error. bail.
            err_msg = self.__exception_fmt__('RequestException', exc)
        #else:
        #    ret = resp.json()
            # logging.debug("r.text=%s", r.text)
        finally:
            if self.status_code != 200 or err_msg:
                logging.error("sbis_req failed, method=%s, status_code=%s, err_msg=%s",
                              method,
                              self.status_code,
                              err_msg)
            if method == 'GET':
                # save file
                self.save_file(resp)
                """
                if '.pdf' in self.filename:
                    open(self.filename, 'wb').write(resp.content)
                else:
                    codecs.open(self.filename,
                                'w',
                                'utf-8').write(str(resp.content.decode('cp1251')))
                """
            else:
                ret = resp.json()

        return ret

    def save_file(self, resp):
        """ save file """
        if '.pdf' in self.filename:
            open(self.filename, 'wb').write(resp.content)
        else:
            codecs.open(self.filename,
                        'w',
                        'utf-8').write(str(resp.content.decode('cp1251')))

    def login(self, login, password):
        """ open session """
        loc_payload = copy.deepcopy(SBIS_QUERY)
        loc_payload["method"] = "СБИС.Аутентифицировать"
        loc_payload["params"] = {"Параметр": {
            "Логин": login,
            "Пароль": password
            }
                                }
        ret = self.sbis_req('POST', self.auth_url, loc_payload)
        if ret and 'result' in ret.keys():
            self.access_token = ret['result']
            logging.debug('auth ret=%s', ret)
            self.headers['X-SBISSessionID'] = self.access_token
            result = True
        else:
            result = False
            self.status_code = -1
            logging.error('login failed res=%s', json.dumps(ret,
                                                            ensure_ascii=False,
                                                            indent=4))
        return result

    def logout(self):
        """ close session """
        if self.headers['X-SBISSessionID']:
            loc_payload = copy.deepcopy(SBIS_QUERY)
            loc_payload["method"] = "СБИС.Выход"
            self.sbis_req('POST', self.auth_url, loc_payload)

    def req_chg_list(self, params):
        """ Get changed docs list """
        loc_payload = copy.deepcopy(SBIS_QUERY)
        loc_payload["method"] = "СБИС.СписокИзменений"
        loc_payload["params"] = params
        return self.sbis_req('POST', self.api_url, loc_payload)


class SbisApp(PGapp, log_app.LogApp):
    """ An SBIS app
    """
    def __init__(self, args):
        log_app.LogApp.__init__(self, args=args)
        script_name = os.path.splitext(os.path.basename(__file__))[0]
        config_filename = '{}.conf'.format(script_name)
        self.get_config(config_filename)
        super(SbisApp, self).__init__(self.config['PG']['pg_host'],
                                      self.config['PG']['pg_user'])
        if self.pg_connect():
            self.set_session(autocommit=True)
        self.api = SbisAPI(self.config)
        if self.api:
            with open(config_filename, 'w') as cfgfile:
                self.config.write(cfgfile)
        self.res = None

    @property
    def last_uuid(self):
        """ Read from DB a uuid of the last change
        """
        loc_sql = "SELECT * FROM arc_const('sbis_last_uuid');"
        self.curs.execute(loc_sql)
        return self.curs.fetchone()[0]

    UPD_LAST = """UPDATE arc_constants SET const_value = %s
WHERE const_name =%s;"""

    @last_uuid.setter
    def last_uuid(self, last_value):
        """ Save to DB a uuid of the last change
        """
        loc_sql = self.curs.mogrify(self.UPD_LAST, (last_value, 'sbis_last_uuid'))
        logging.debug('update last_uuid=%s', loc_sql)
        self.do_query(loc_sql, reconnect=True)

    @property
    def timestamp_from(self):
        """ Read from DB a timestamp of the last change
        """
        loc_sql = "SELECT * FROM arc_const('sbis_last_ts');"
        self.curs.execute(loc_sql)
        return self.curs.fetchone()[0]

    @timestamp_from.setter
    def timestamp_from(self, ts_value):
        """ Save to DB a timestamp of the last change
        """
        loc_sql = self.curs.mogrify(self.UPD_LAST, (ts_value, 'sbis_last_ts'))
        logging.debug('update last_ts=%s', loc_sql)
        self.do_query(loc_sql, reconnect=True)

    def get_chg_list(self, page):
        """ Get changed docs list """
        loc_params = copy.deepcopy(CHG_LIST)
        logging.debug('loc_params copied=%s', loc_params)
        """
        loc_params["Фильтр"] = {
            "ИдентификаторСобытия": SBIS.last_uuid,
            "ДатаВремяС": SBIS.timestamp_from,
            }
        """
        if page == 0:
            loc_params["Фильтр"]["ИдентификаторСобытия"] = SBIS.last_uuid
            loc_params["Фильтр"]["ДатаВремяС"] = SBIS.timestamp_from
        else:
            loc_params["Фильтр"]["ИдентификаторСобытия"] = SBIS.last_uuid
            loc_params["Фильтр"]["ДатаВремяС"] = SBIS.timestamp_from
            loc_params["Фильтр"]["Навигация"] = {"Страница": str(page)}

        logging.debug('loc_params=%s', json.dumps(loc_params,
                                                  ensure_ascii=False,
                                                  indent=4))
        self.res = self.api.req_chg_list(loc_params)

    def save_chg_list(self):
        """ Get changed docs list page by page """
        do_loop = True
        last_event_uuid = None
        page = 0
        while do_loop:
            self.get_chg_list(page=page)
            if self.res and 'result' in self.res.keys():
                logging.debug('nav=%s', self.res['result']['Навигация'])
                if self.res['result']['Навигация']['ЕстьЕще'] == "Да":
                    # parse json result
                    last_event_uuid = self.parse_doc_lists(page)
                    page += 1
                    if last_event_uuid:
                        self.last_uuid = last_event_uuid
                    ##################################
                    ##################################
                    ##################################
                    ##################################
                    ##################################
                    #do_loop = False  # DEBUG ONLY!!!!

                else:
                    do_loop = False
            else:
                do_loop = self.api.status_code == 200
        # last doc uuid after loop end

    INSERT_DOC = """INSERT INTO sbis.changes(event_uuid, event_name, event_dt,
doc_uuid, doc_name, dt_create_sbis, doc_num, direction, inn_firm, inn_ca, doc_type, deleted)
VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""

    def parse_doc(self, doc):
        """ Parse doc """


    def parse_doc_lists(self, page):
        """ Parse docs list
Если получено событие:
- не по входящему или исходящему документу
  («Документ.Направление»≠«Входящий»/«Исходящий»), пропустите его;
- с извещением об удалении документа противоположной стороной
  («Документ.Событие.Название»=«Уведомление об удалении на стороне отправителя»),
  остановите документооборот и пометьте документ в вашей ИС как удаленный;
- с запросом на аннулирование
  («Документ.Событие.Название»=«Получение соглашения об аннулировании»),
  предусмотрите в вашей системе возможность ответа. Для этого добавьте в систему
  возможность запросить ответственного по документу на подтверждение/отклонение аннулирования;
- со значением поля «Документ.Событие.Название» отличными от «Получение» — пропустите его.
        """
        doc_list = self.res['result']['Документ']
        with open('sbis-onw-{}-{:03d}.json'.format(time.strftime("%Y-%m-%d-%H-%M"), page),
                  'w') as outf:
            doc = None
            last_event_uuid = None
            last_event_name = None
            last_event_dt = None
            for doc in doc_list:
                if doc["Направление"] not in {"Входящий", "Исходящий"}:
                    logging.debug('SKIP «Документ.Направление»≠«Входящий»/«Исходящий» %s',
                                  doc["Направление"])
                    continue
                if len(doc["Редакция"]) > 1:
                    logging.info('WATCH Несколько редакций: doc["Редакция"]=%s',
                                 doc["Редакция"])
                if doc["Редакция"][0]["Актуален"] == "Да":
                    # write to DB
                    outf.write(json.dumps(doc, ensure_ascii=False, indent=4))
                    last_event_uuid = doc["Событие"][-1]["Идентификатор"]
                    last_event_name = doc["Событие"][-1]["Название"]
                    last_event_dt = doc["Событие"][-1]["ДатаВремя"]
                    loc_sql = self.curs.mogrify(self.INSERT_DOC,
                                                (last_event_uuid,
                                                 last_event_name,
                                                 datetime.strptime(last_event_dt,
                                                                   '%d.%m.%Y %H.%M.%S'),
                                                 doc["Идентификатор"],
                                                 doc["Название"],
                                                 datetime.strptime(doc["ДатаВремяСоздания"],
                                                                   '%d.%m.%Y %H.%M.%S'),
                                                 doc["Номер"],
                                                 doc["Направление"],
                                                 doc['НашаОрганизация']['СвЮЛ']["ИНН"],
                                                 doc['Контрагент']['СвЮЛ']["ИНН"],
                                                 doc["Тип"],
                                                 doc.get("Удален", 'empty')
                                                )
                                               )
                    logging.debug('loc_sql=%s', str(loc_sql, 'utf-8'))
                    self.do_query(loc_sql, reconnect=True)
                else:
                    logging.debug('SKIP Не "Актуален" %s', doc["Редакция"]["Актуален"])
                for events in doc["Событие"]:
                    if len(doc["Событие"]) > 1:
                        logging.info('WATCH Несколько событий: doc["Событие"]=%s',
                                     doc["Событие"])
                    logging.debug('type(events)=%s', type(events))
                    #logging.debug('events["Вложение"]=%s', events["Вложение"])
                    for event in events["Вложение"]:
                        if event["Направление"] == "Входящий" and\
                           event['Тип'] == 'ДокОтгрВх' and\
                           event['Удален'] == 'Нет':
                            #log_dict(event, ['Тип', 'Название', 'Номер', 'Направление', 'Удален'])
                            log_dict(event['Файл'], ['Ссылка'])
                            filename = '{}_{}'.format(event['Тип'],
                                                      event['Номер'].replace('/', '_'))
                            self.get_url(event['Файл']['Ссылка'], '{}.xml'.format(filename))
                            pdf_url = event.get('СсылкаНаPDF')
                            if pdf_url and pdf_url != '':
                                pdffile = '{}.pdf'.format(filename)
                                self.get_url(pdf_url, pdffile)

                """
                if "Вложение" in doc.keys():
                    for att in doc["Вложение"]:
                        logging.debug('type(att)=%s', type(att))
                        logging.debug('att=%s', att)
                        #log_dict(att, ['Тип', 'Название', 'Номер', 'Направление', 'Удален'])
                """
        return last_event_uuid

    def get_event(self, uuid):
        """ Get changes for event uuid """

    def get_url(self, url, filename):
        """ Download from url """
        self.api.filename = filename
        self.api.sbis_req('GET', url)

def log_dict(in_dict, keys):
    """ loging.debug """
    logging.debug('in_dict=%s:%s', inspect.stack()[1].code_context[0], json.dumps(
        {wkey: in_dict[wkey] for wkey in keys if wkey in in_dict.keys()},
        ensure_ascii=False, indent=4))


if __name__ == '__main__':
    """
    URL = 'https://disk.sbis.ru/disk/api/v1/0e41d2fe-f018-4578-b484-aa52665f39f3_\
3de37606-f261-42cd-b4fc-061aa7df7e29?object=simple_file_sd&uuid=9e5\
b4390-fc33-4187-83f4-b5a004db4e7e&diskhmac=zPgfxCbmFbKiY8CSUpT54aNFag0%3D'
    FILENAME = 'nakl.xml'
    """

    URL = 'https://online.sbis.ru/pdfservicepublic/service/?method=%D0%A1%D0%B5%D1%80%D0%B2%D0%B8%D1%81PDF.%D0%A1%D0%B8%D0%BD%D1%85%D1%80%D0%BE%D0%BD%D0%BD%D0%B0%D1%8F%D0%9F%D0%B5%D1%87%D0%B0%D1%82%D1%8C&params=eyJEb2N1bWVudHMiOnsicyI6W3sibiI6ItCY0LTQniIsInQiOiLQp9C40YHQu9C%2BINGG0LXQ%0Au9C%2B0LUifSx7Im4iOiLQoNCw0LfQtNC10LsiLCJ0Ijoi0KfQuNGB0LvQviDRhtC10LvQvtC1%0AIn1dLCJkIjpbWzMzNDI3LG51bGxdXX0sIk9iamVjdE5hbWUiOiJEb2NQcmludCIsIk1ldGhv%0AZE5hbWUiOiJNYXNzTGlzdCIsIlBhcmFtcyI6eyJzIjpbeyJuIjoiUmVxSWQiLCJ0Ijoi0KHR%0AgtGA0L7QutCwIn1dLCJkIjpbIjMzOTQ4Mzg2MzYyNzEzNjUyNTgiXX19&protocol=3&id=0&srv=1'
    """

    URL = 'https://online.sbis.ru/pdfservicepublic/service/?method=%D0%A1%D0%B5%D1%80%D0%B2%D0%B8%D1%81PDF.%D0%A1%D0%B8%D0%BD%D1%85%D1%80%D0%BE%D0%BD%D0%BD%D0%B0%D1%8F%D0%9F%D0%B5%D1%87%D0%B0%D1%82%D1%8C&params=eyJEb2N1bWVudHMiOnsicyI6W3sibiI6ItCY0LTQniIsInQiOiLQp9C40YHQu9C%2BINGG0LXQ%0Au9C%2B0LUifSx7Im4iOiLQoNCw0LfQtNC10LsiLCJ0Ijoi0KfQuNGB0LvQviDRhtC10LvQvtC1%0AIn1dLCJkIjpbWzMzNDI3LG51bGxdXX0sIk9iamVjdE5hbWUiOiJEb2NQcmludCIsIk1ldGhv%0AZE5hbWUiOiJNYXNzTGlzdCIsIlBhcmFtcyI6eyJzIjpbeyJuIjoiUmVxSWQiLCJ0Ijoi0KHR%0AgtGA0L7QutCwIn1dLCJkIjpbIjMzOTQ4Mzg2MzYyNzEzNjUyNTgiXX19&protocol=3&id=0&srv=1'
    """
    FILENAME = 'nakl1.pdf'

    log_app.PARSER.formatter_class = log_app.argparse.ArgumentDefaultsHelpFormatter
    log_app.PARSER.add_argument('--get_last', action='store_true',
                                help='get last changes')
    log_app.PARSER.add_argument('--get_event', type=int,
                                help='get changes for event uuid')
    log_app.PARSER.add_argument('--get_url', type=str,
                                help='download document from url')

    ARGS = log_app.PARSER.parse_args()
    #do_nothing()
    SBIS = SbisApp(args=ARGS)
    if SBIS:
        if ARGS.get_last:
            time.sleep(2)
            SBIS.save_chg_list()
        elif ARGS.get_event:
            SBIS.get_event(ARGS.get_event)
        elif ARGS.get_url:
            #SBIS.get_url(ARGS.get_url)
            #SBIS.get_url(URL, 'nakl.xml')
            SBIS.get_url(URL, FILENAME)

        SBIS.api.logout()
