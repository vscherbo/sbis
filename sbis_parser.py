#!/usr/bin/env python

""" A JSON parser for SBIS docs
"""

import json
#import logging
import log_app

class SbisParser(log_app.LogApp):
    """ A JSON parser class for SBIS docs
    """
    def __init__(self, args):
        log_app.LogApp.__init__(self, args=args)

"""
doc_keys(['Дата', 'ДатаВремяСоздания', 'Идентификатор', 'ИдентификаторСеанса', 'Контрагент', 'Название', 'Направление', 'НашаОрганизация', 'Номер', 'Подтип', 'Примечание', 'Расширение', 'Регламент', 'Редакция', 'Событие', 'Состояние', 'Срок', 'СсылкаДляКонтрагент', 'СсылкаДляНашаОрганизация', 'СсылкаНаPDF', 'СсылкаНаАрхив', 'Сумма', 'Тип', 'Удален'])
"""

def doc_short(doc, keys):
    """ print short form of document """
    #wanted = set(keys).intersection(doc.keys())  # skip non-existing keys
    res = {wkey: doc[wkey] for wkey in keys if wkey in doc.keys()}
    return res
    #return {wkey: doc[wkey] for wkey in wanted}


def doc_attachment(doc):
    """ returns urls to attached files """
    att_list = [event["Вложение"] for event in doc["Событие"]]
    file_list = []
    for att in att_list:
        #print('=========== att=', att)
        for file_att in att:
            print('----------- att=', file_att["Тип"])
            print('######## att=', doc_short(file_att, ["Название", "Номер", "Тип", "Файл"]))
            print('>>>>>>>> file_att=', file_att["Файл"])
            file_list.append(file_att["Файл"]["Ссылка"])
    #file_list = [file_att["Файл"] for file_att in att1_list]
    return file_list

def main():
    """ Just main """
    #with open('doc-2021-02-15.json', 'r') as jfile:
    with open('20361.json', 'r') as jfile:
        res = json.load(jfile)
        print(res['result'].keys())
        docs = res['result']['Документ']
        prn_keys = [
            'Идентификатор'
            , 'Название'
            , 'ДатаВремяСоздания'
            , 'Номер'
            , 'Направление'
            #, 'Контрагент'
            #, 'НашаОрганизация'
            , 'Тип'
            , 'Удален'
                ]
        for ditem in docs:
            print(ditem.keys())
            print(doc_short(ditem, prn_keys))
            cagent = doc_short(ditem['Контрагент'], ['СвЮЛ'])
            print(cagent['СвЮЛ']['ИНН'])
            firm = doc_short(ditem['НашаОрганизация'], ['СвЮЛ'])
            print(doc_short(firm['СвЮЛ'], ['ИНН']))
            #print('============', doc_attachment(ditem))

if __name__ == '__main__':
    main()
