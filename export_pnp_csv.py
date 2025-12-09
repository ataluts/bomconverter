import csv
import copy
from pathlib import Path

import dict_locale as lcl
import assemble

_module_dirname  = Path(__file__).parent     #адрес папки со скриптом
_module_basename = Path(__file__).stem       #базовое имя модуля

#Экспортирует перечень элементов в формате CSV
def export(data, address:Path, **kwargs):
    print('INFO >> pnp-csv exporting module running with parameters:')
    print(f"{' ' * 12}output: {address.name}")

    locale              = kwargs.get('locale', lcl.Locale.EN)
    content_mount       = kwargs.get('content_mount', True)
    content_state       = kwargs.get('content_state', True)
    content_partnumber  = kwargs.get('content_partnumber', True)
    content_description = kwargs.get('content_description', True)
    content_comment     = kwargs.get('content_comment', True)
    content_disabled    = kwargs.get('content_disabled', True)
    content_disabled_segregate = kwargs.get('content_disabled_segregate', True)

    file_encoding = kwargs.get('encoding',  'utf-8')
    dialect       = kwargs.get('dialect', {})
    replace       = kwargs.get('replace', {})
    print(f"{' ' * 12}encoding: {file_encoding}")
    print(f"{' ' * 12}dialect: {dialect}")
    print(f"{' ' * 12}replace: {replace}")

    #регистрируем диалект
    dialect_name = 'export_pnp_csv'
    default_dialect = {
        'delimiter'        : ',',            #разделитель значений
        'doublequote'      : True,           #заменять " на "" в значениях
        'escapechar'       : '\\',           #символ смены регистра
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
    pnp = copy.deepcopy(data)

    #собираем данные в таблицу
    header = [
        locale.translate(lcl.export_pnp_txt.HEADER_DESIGNATOR),
        locale.translate(lcl.export_pnp_txt.HEADER_LAYER),
        locale.translate(lcl.export_pnp_txt.HEADER_LOCATION_X),
        locale.translate(lcl.export_pnp_txt.HEADER_LOCATION_Y),
        locale.translate(lcl.export_pnp_txt.HEADER_ROTATION),
        locale.translate(lcl.export_pnp_txt.HEADER_FOOTPRINT)
        ]
    if content_mount:       header.append(locale.translate(lcl.export_pnp_txt.HEADER_MOUNT))
    if content_state:       header.append(locale.translate(lcl.export_pnp_txt.HEADER_STATE))
    if content_partnumber:  header.append(locale.translate(lcl.export_pnp_txt.HEADER_PARTNUMBER))
    if content_description: header.append(locale.translate(lcl.export_pnp_txt.HEADER_DESCRIPTION))
    if content_comment:     header.append(locale.translate(lcl.export_pnp_txt.HEADER_COMMENT))
    table = []
    table_disabled = []
    for entry in pnp.entries:
        if entry.state.enabled or content_disabled:
            item = [
                assemble.assemble_pnp_designator(entry.designator),
                assemble.assemble_pnp_layer(entry.layer, **kwargs),
                entry.location[0],
                entry.location[1],
                entry.rotation,
                entry.footprint if entry.footprint is not None else '<NONE>'
            ]
            if content_mount:       item.append(assemble.assemble_pnp_mount(entry.mount, **kwargs))
            if content_state:       item.append(assemble.assemble_pnp_state(entry.state, **kwargs))
            if content_partnumber:  item.append(entry.partnumber)
            if content_description: item.append(entry.description)
            if content_comment:     item.append(entry.comment)
            if not entry.state.enabled and content_disabled_segregate: table_disabled.append(item)
            else: table.append(item)
    table.extend(table_disabled)

    #делаем замены
    if replace is not None:
        if isinstance(replace, dict):
            for item in table:
                for i in range(len(item)):
                    if isinstance(item[i], str):
                        for newvalue, oldvalue in replace.items():
                            item[i] = item[i].replace(newvalue, oldvalue)

    #экспортируем данные в CSV
    with open(address, 'w', encoding = file_encoding, newline = '') as file:
        writer = csv.writer(file, dialect=dialect_name)
        writer.writerow(header)
        writer.writerows(table)

    print('INFO >> pnp-csv export completed.')   