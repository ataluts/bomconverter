import os
import csv
import copy

import dict_locale as lcl

script_dirName  = os.path.dirname(__file__)                                                     #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                               #базовое имя модуля

#Экспортирует спецификацию в формате CSV
def export(data, address, **kwargs):
    print('INFO >> sp-csv exporting module running with parameters:')
    print(' ' * 12 + 'output: ' + os.path.basename(address)) #Windows CMD crashes here, wtf???

    #locale
    locale = kwargs.get('locale', lcl.Locale.EN)

    file_encoding = kwargs.get('encoding',  'cp1251')
    dialect       = kwargs.get('dialect', {})
    replace       = kwargs.get('replace', {})
    print(f"{' ' * 12}encoding: {file_encoding}")
    print(f"{' ' * 12}dialect: {dialect}")
    print(f"{' ' * 12}replace: {replace}")

    format_desig_delimiter = kwargs.get('format_desig_delimiter',  ', ')

    #регистрируем диалект
    dialect_name = 'export_sp_csv'
    default_dialect = {
        'delimiter'        : ',',            #разделитель значений
        'doublequote'      : True,           #заменять " на "" в значениях
        'escapechar'       : None,           #символ экранирования
        'lineterminator'   : '\r\n',         #окончание строки
        'quotechar'        : '"',            #"кавычки" для pначений со спецсимволами
        'quoting'          : csv.QUOTE_ALL,  #метод заключения значений в "кавычки"
        'skipinitialspace' : False           #пропускать пробел следующий сразу за разделителем
    }
    if isinstance(dialect, csv.Dialect):
        #получили диалект в качестве параметра -> его и регистрируем
        csv.register_dialect(dialect_name, dialect)
    elif isinstance(dialect, dict):
        #получили словарь в качестве параметра -> регистрируем диалект по-умолчанию с изменениями из словаря
        default_dialect.update(dialect)
        csv.register_dialect(dialect_name, **default_dialect)
    elif isinstance(dialect, str):
        #получили название диалекта в качестве параметра -> меняем имя используемого диалекта
        dialect_name = dialect
    else:
        #получили непоятно что -> ошибка
        raise ValueError("Invalid dialect.")

    #разворачиваем данные
    sp = copy.deepcopy(data)

    #делаем замены
    if replace is not None:
        if isinstance(replace, dict):
            for entry in sp.entries:
                for key, value in replace.items():
                    entry.label = entry.label.replace(key, value)
    

    #экспортируем данные в CSV
    #--- список элементов
    with open(address, 'w', encoding = file_encoding, newline = '') as csvFile:
        writer = csv.DictWriter(csvFile, fieldnames=[locale.translate(lcl.export_sp_csv.HEADER_LABEL), locale.translate(lcl.export_sp_csv.HEADER_QUANTITY), locale.translate(lcl.export_sp_csv.HEADER_DESIGNATOR)], dialect=dialect_name)
        writer.writeheader()
        for entry in sp.entries:
            designator = ''
            for desig in entry.designator:
                if len(desig) > 0:
                    designator += format_desig_delimiter + desig
            if designator:
                designator = designator[len(format_desig_delimiter):]

            writer.writerow({locale.translate(lcl.export_sp_csv.HEADER_LABEL):      entry.label,
                             locale.translate(lcl.export_sp_csv.HEADER_QUANTITY):   entry.quantity,
                             locale.translate(lcl.export_sp_csv.HEADER_DESIGNATOR): designator})
        csvFile.close()

    print('INFO >> sp-csv export completed.')   
