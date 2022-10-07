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
    file_encoding     = kwargs.get('encoding',  'cp1251')
    dialect_delimiter = kwargs.get('delimiter', ',')
    dialect_quotechar = kwargs.get('quotechar', '"')
    prefix            = kwargs.get('prefix', '')
    postfix           = kwargs.get('postfix', '')
    print(' ' * 12 + 'encoding: ' + file_encoding)
    print(' ' * 12 + 'delimiter: ' + dialect_delimiter)
    print(' ' * 12 + 'quotechar: ' + dialect_quotechar)
    print(' ' * 12 + 'prefix: ' + prefix)
    print(' ' * 12 + 'postfix: ' + postfix)

    #создаём объект
    bom = BoM_typeDef(prefix, postfix)

    #читаем данные из файла
    print('INFO >> Reading data from CSV file', end ="... ", flush = True)
    if os.path.isfile(address):
        with open(address, 'r', encoding=file_encoding) as csvFile:
            BoMreader = csv.DictReader(csvFile, delimiter=dialect_delimiter, quotechar=dialect_quotechar)
            bom.fieldNames = BoMreader.fieldnames
            for entry in BoMreader:
                bom.entries.append(entry)
            csvFile.close()
        print('done. (' + str(len(bom.entries)) + ' entries with ' + str(len(bom.fieldNames)) + ' fields)')
    else:
        print("error: file doesn't exist")

    print('INFO >> BoM import finished.')
    return bom 