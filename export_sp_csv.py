import os
import csv

from typedef_sp import SP_typeDef                                 #класс спецификации

script_dirName  = os.path.dirname(__file__)                                                     #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                               #базовое имя модуля

#Экспортирует спецификацию в формате CSV
def export(data, address, **kwargs):
    print('INFO >> sp-csv exporting module running with parameters:')
    print(' ' * 12 + 'output: ' + os.path.basename(address)) #Windows CMD crashes here, wtf???

    file_encoding          = kwargs.get('encoding',  'cp1251')
    dialect_delimiter      = kwargs.get('delimiter', ',')
    dialect_doublequote    = kwargs.get('doublequote', True)
    dialect_lineterminator = kwargs.get('lineterminator', '\r\n')
    dialect_quotechar      = kwargs.get('quotechar', '"')
    dialect_quoting        = kwargs.get('quoting', csv.QUOTE_ALL)
    print(' ' * 12 + 'encoding: ' + file_encoding)
    #print(' ' * 12 + 'delimiter: ' + dialect_delimiter)
    #print(' ' * 12 + 'doublequote: ' + str(dialect_doublequote))
    #print(' ' * 12 + 'lineterminator: ' + dialect_lineterminator)
    #print(' ' * 12 + 'quotechar: ' + dialect_quotechar)
    #print(' ' * 12 + 'quoting: ' + str(dialect_quoting))

    #разворачиваем данные
    sp = data

    #фиксим проблему с юникод-символами заменяя их на что-нибудь другое
    for entry in sp.entries:
        entry.label = entry.label.replace('²', '^2')
        entry.label = entry.label.replace('℃', '°C')

    #регистрируем диалект как в BoM Altium Designer
    csv.register_dialect('ADBoM',
                         delimiter        = dialect_delimiter,
                         doublequote      = dialect_doublequote,
                         lineterminator   = dialect_lineterminator,
                         quotechar        = dialect_quotechar,
                         quoting          = dialect_quoting,
                         skipinitialspace = False)

    #экспортируем данные в CSV
    #--- список элементов
    with open(address, 'w', encoding = file_encoding, newline = '') as csvFile:
        writer = csv.DictWriter(csvFile, fieldnames=['Label', 'Quantity', 'Designator'], dialect='ADBoM')
        writer.writeheader()
        for entry in sp.entries:
            writer.writerow({'Label':      entry.label,
                             'Quantity':   entry.quantity,
                             'Designator': ', '.join(entry.designator)})
        csvFile.close()

    print('INFO >> sp-scv export completed.')   
