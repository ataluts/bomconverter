import os
import csv
from typedef_bom import BoM                                                                     #класс BoM

script_dirName  = os.path.dirname(__file__)                                                     #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                               #базовое имя модуля

#Импортирует BoM из формата CSV
def importz(address, **kwargs):
    print('INFO >> BoM importing module running with parameters:')
    print(' ' * 12 + 'input: ' +  os.path.basename(address))

    #параметры
    file_encoding    = kwargs.get('encoding',  'cp1251')
    dialect          = kwargs.get('dialect', {})
    title            = kwargs.get('title', None)
    conversion_int   = kwargs.get('conversion_int', None)
    conversion_float = kwargs.get('conversion_float', None)
    conversion_bool  = kwargs.get('conversion_bool', None)

    conversion_int_print = '' if conversion_int is None else ','.join(conversion_int)
    conversion_float_print = '' if conversion_float is None else ','.join(conversion_float)
    conversion_bool_print = '' if conversion_bool is None else ','.join(conversion_bool)
    print(f"{' ' * 12}conversion: int[{conversion_int_print}], float [{conversion_float_print}], bool [{conversion_bool_print}]")
    print(f"{' ' * 12}encoding: {file_encoding}")
    print(f"{' ' * 12}dialect: {dialect}")

    #создаём объект
    bom = BoM(title)

    #регистрируем диалект
    dialect_name = 'import_bom_csv'
    default_dialect = {
        'delimiter'        : ',',            #разделитель значений
        'doublequote'      : True,           #заменять " на "" в значениях
        'escapechar'       : None,           #символ смены регистра
        'lineterminator'   : '\r\n',         #окончание строки
        'quotechar'        : '"',            #"кавычки" для значений со спецсимволами
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
            bom.insert_fields(BoMreader.fieldnames)
            for entry in BoMreader:
                if conversion_int is not None and isinstance(conversion_int, (list, tuple)):
                    for field in conversion_int:
                        if field in entry:
                            value = entry[field].strip()
                            try:
                                value = int(value)
                                entry[field] = value
                            except (ValueError, TypeError) as e:
                                pass
                if conversion_float is not None and isinstance(conversion_float, (list, tuple)):
                    for field in conversion_float:
                        if field in entry:
                            value = entry[field].strip().replace(',', '.')
                            try:
                                value = float(value)
                                entry[field] = value
                            except (ValueError, TypeError) as e:
                                pass
                if conversion_bool is not None and isinstance(conversion_bool, (list, tuple)):
                    for field in conversion_bool:
                        if field in entry:
                            value = entry[field].strip().lower()
                            if value in {"true", "1", "yes", "y"}:
                                entry[field] = True
                            elif value in {"false", "0", "no", "n"}:
                                entry[field] = False
                bom.insert_entry(entry)

        print(f"done. ({len(bom.entries)} entries with {len(bom.fields)} fields)")
    else:
        print("error: file doesn't exist")

    print('INFO >> BoM import finished.')
    return bom 