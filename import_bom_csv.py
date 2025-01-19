import os
import csv
from typedef_bom import BoM_typeDef                                                             #класс BoM

script_dirName  = os.path.dirname(__file__)                                                     #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                               #базовое имя модуля

#Импортирует BoM из формата CSV
def importz(address, **kwargs):
    print('INFO >> BoM importing module running with parameters:')
    print(' ' * 12 + 'input: ' +  os.path.basename(address))

    #параметры
    file_encoding = kwargs.get('encoding',  'cp1251')
    dialect       = kwargs.get('dialect', {})
    print(f"{' ' * 12}encoding: {file_encoding}")
    print(f"{' ' * 12}dialect: {dialect}")

    #создаём объект
    bom = BoM_typeDef()

    #регистрируем диалект
    dialect_name = 'import_bom_csv'
    default_dialect = {
        'delimiter'        : ',',            #разделитель значений
        'doublequote'      : True,           #заменять " на "" в значениях
        'escapechar'       : '\\',           #символ смены регистра
        'lineterminator'   : '\r\n',         #окончание строки
        'quotechar'        : '"',            #"кавычки" для pначений со спецсимволами
        'quoting'          : csv.QUOTE_ALL,  #метод заключения значений в "кавычки"
        'skipinitialspace' : False,          #пропускать пробел следующий сразу за разделителем
        'strict'           : False           #вызывать ошибку при неправильных читаемых данных
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

    #читаем данные из файла
    print('INFO >> Reading data from CSV file', end ="... ", flush = True)
    if os.path.isfile(address):
        with open(address, 'r', encoding=file_encoding) as csvFile:
            BoMreader = csv.DictReader(csvFile, dialect=dialect_name)
            bom.fieldNames = BoMreader.fieldnames
            for entry in BoMreader:
                bom.entries.append(entry)
            csvFile.close()
        print('done. (' + str(len(bom.entries)) + ' entries with ' + str(len(bom.fieldNames)) + ' fields)')
    else:
        print("error: file doesn't exist")

    print('INFO >> BoM import finished.')
    return bom 