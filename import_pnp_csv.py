import os
import csv
import re
from pathlib import Path
from datetime import datetime
import typedef_pnp as PickPlace
from typedef_designator import Designator

script_dirName  = Path(__file__).parent     #адрес папки со скриптом
script_baseName = Path(__file__).stem       #базовое имя модуля

#Импортирует PnP из формата CSV
def importz(address:Path, **kwargs):
    print('INFO >> PnP importing module running with parameters:')
    print(' ' * 12 + 'input: ' +  os.path.basename(address))

    #параметры
    file_encoding    = kwargs.get('encoding',  'cp1251')
    dialect          = kwargs.get('dialect', {})
    title            = kwargs.get('title', None)

    print(f"{' ' * 12}encoding: {file_encoding}")
    print(f"{' ' * 12}dialect: {dialect}")

    #создаём объект
    pnp = PickPlace.PnP(title)

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
    if address.is_file():
        with open(address, 'r', encoding=file_encoding) as file:
            header_pos = 0
            lines = file.readlines()
            
            #читаем преамбулу
            dt, date, time = None, None, None
            revision, variant = None, None
            units = None
            for i, line in enumerate(lines):
                if   line.startswith("Date:"):       date = line.split(':', 1)[1].strip()
                elif line.startswith("Time:"):       time = line.split(':', 1)[1].strip()
                elif line.startswith("Revision:"):   revision = line.split(':', 1)[1].strip()
                elif line.startswith("Variant:"):    variant = line.split(':', 1)[1].strip()
                elif line.startswith("Units used:"): units = line.split(':', 1)[1].strip()
                elif "Designator" in line and "Layer" in line and "Center-X" in line and "Center-Y" in line and "Rotation" in line:
                    #нашли строку с началом csv таблицы
                    header_pos = i
                    break

            #разбираем данные из преамбулы
            if date is not None:
                if time is not None:
                    try: dt = datetime.strptime(f"{date} {time}", "%d.%m.%y %H:%M")
                    except ValueError: dt = None
                else:
                    try: dt = datetime.strptime(date, "%d.%m.%y")
                    except ValueError: dt = None
            if dt is not None:
                pnp.datetime = dt
            if units is not None:
                if units.lower() == "mm": pnp.units = PickPlace.LengthUnits.MM
                elif units.lower() == "mil": pnp.units = PickPlace.LengthUnits.MIL
                else: raise ValueError("Units unrecognized")
            pnp.revision = revision
            pnp.variant = variant

            #читаем csv таблицу
            reader = csv.DictReader(lines[header_pos:], dialect=dialect_name)

            #определяем название и присутствие полей
            field_designator, field_layer, field_footprint, field_location_x, field_location_y, field_rotation, field_partnumber, field_comment = [None] * 8
            for field in reader.fieldnames:
                if   field.lower() == "designator": field_designator = field
                elif field.lower() == "layer": field_layer = field
                elif field.lower().startswith("center-x"): field_location_x = field
                elif field.lower().startswith("center-y"): field_location_y = field
                elif field.lower() == "rotation": field_rotation = field
                elif field.lower() == "footprint": field_footprint = field
                elif field.lower() == "BOM_value": field_partnumber = field
                elif field.lower() == "comment": field_comment = field
            
            #проверяем наличие обязательных полей
            if field_designator is not None and field_layer is not None and field_location_x is not None and field_location_y is not None and field_rotation is not None:
                for entry in reader:
                    #парсим запись
                    designator = Designator.parse(entry[field_designator])
                    layer = entry[field_layer].lower()
                    if   layer == "toplayer":    layer = PickPlace.PCBlayer.TOP
                    elif layer == "bottomlayer": layer = PickPlace.PCBlayer.BOTTOM
                    elif layer.startswith("midlayer"): layer = PickPlace.PCBlayer.MIDDLE_1.value() + int(layer[len("midlayer"):]) - 1
                    else: raise ValueError("PCB layer unrecognized")
                    location_x = float(re.sub(rf"[^\d\-\+.eE]", "", entry[field_location_x].strip().replace(',', '.')))
                    location_y = float(re.sub(rf"[^\d\-\+.eE]", "", entry[field_location_y].strip().replace(',', '.')))
                    rotation   = float(re.sub(rf"[^\d\-\+.eE]", "", entry[field_rotation].strip().replace(',', '.'))) % 360
                    if rotation < 0: rotation += 360
                    if field_footprint is not None: footprint = entry[field_footprint]
                    else: footprint = None
                    if field_partnumber is not None: partnumber = entry[field_partnumber]
                    else: partnumber = None
                    if field_comment is not None: comment = entry[field_comment]
                    else: comment = None
                    mount = PickPlace.MountType.UNDEFINED
                    description = None
                    state = PickPlace.PnP.Entry.State()
                    pnp.insert_entry(PickPlace.PnP.Entry(designator, layer, [location_x, location_y], rotation, footprint, mount, partnumber, description, comment, state))
        print(f"done. ({len(pnp.entries)} entries)")
    else:
        print("error: file doesn't exist")

    print('INFO >> PnP import finished.')
    return pnp