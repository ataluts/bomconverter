import os
import csv
import copy

from typedef_bom import BoM

script_dirName  = os.path.dirname(__file__)                                                     #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                               #базовое имя модуля

#Экспортирует BoM в формате CSV
def export(data, address, **kwargs):
    print('INFO >> bom-csv exporting module running with parameters:')
    print(' ' * 12 + 'output: ' + os.path.basename(address))

    file_encoding = kwargs.get('encoding',  'cp1251')
    dialect       = kwargs.get('dialect', {})
    replace       = kwargs.get('replace', {})
    print(f"{' ' * 12}encoding: {file_encoding}")
    print(f"{' ' * 12}dialect: {dialect}")
    print(f"{' ' * 12}replace: {replace}")

    #регистрируем диалект
    dialect_name = 'export_bom_csv'
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
    bom = copy.deepcopy(data)

    #делаем замены
    if replace is not None:
        if isinstance(replace, dict):
            for entry in bom.entries:
                for field_index, field_value in enumerate(entry.value):
                    if isinstance(field_value, str):
                        for key, value in replace.items():
                            entry.value[field_index] = entry.value[field_index].replace(key, value)
    
    #экспортируем данные в CSV
    with open(address, 'w', encoding = file_encoding, newline = '') as csvFile:
        writer = csv.DictWriter(csvFile, fieldnames=bom.fields, dialect=dialect_name)
        writer.writeheader()
        for entry in bom.entries:
            writer.writerow(entry.to_dict())
        csvFile.close()

    print('INFO >> bom-scv export completed.')   
