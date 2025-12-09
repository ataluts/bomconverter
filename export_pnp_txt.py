import copy
from pathlib import Path
from tabulate import tabulate

import assemble
import dict_locale as lcl

_module_dirname  = Path(__file__).parent     #адрес папки со скриптом
_module_basename = Path(__file__).stem       #базовое имя модуля

#Экспортирует перечень элементов в формате TXT
def export(data, address:Path, **kwargs):
    print('INFO >> pnp-txt exporting module running with parameters:')
    print(f"{' ' * 12}output: {address.name}")

    locale              = kwargs.get('locale', lcl.Locale.EN)
    content_mount       = kwargs.get('content_mount', True)
    content_state       = kwargs.get('content_state', True)
    content_partnumber  = kwargs.get('content_partnumber', True)
    content_description = kwargs.get('content_description', True)
    content_comment     = kwargs.get('content_comment', True)
    content_disabled    = kwargs.get('content_disabled', True)
    content_disabled_segregate = kwargs.get('content_disabled_segregate', True)
    format_table        = kwargs.get('format_table', 'plain')
    format_numparse     = kwargs.get('format_numparse', True)
    format_column_designator_align  = kwargs.get('format_column_designator',  {}).get('align', 'left')
    format_column_layer_align       = kwargs.get('format_column_layer',       {}).get('align', 'left')
    format_column_location_align    = kwargs.get('format_column_location',    {}).get('align', 'decimal')
    format_column_location_number   = kwargs.get('format_column_location',    {}).get('number', 'g')
    format_column_rotation_align    = kwargs.get('format_column_rotation',    {}).get('align', 'decimal')
    format_column_rotation_number   = kwargs.get('format_column_rotation',    {}).get('number', 'g')
    format_column_footprint_align   = kwargs.get('format_column_footprint',   {}).get('align', 'left')
    format_column_mount_align       = kwargs.get('format_column_mount',       {}).get('align', 'left')
    format_column_state_align       = kwargs.get('format_column_state',       {}).get('align', 'left')
    format_column_partnumber_align  = kwargs.get('format_column_partnumber',  {}).get('align', 'left')
    format_column_description_align = kwargs.get('format_column_description', {}).get('align', 'left')
    format_column_comment_align     = kwargs.get('format_column_comment',     {}).get('align', 'left')

    file_encoding = kwargs.get('encoding', 'utf-8')
    dialect       = kwargs.get('dialect', {})
    replace       = kwargs.get('replace', {})
    print(f"{' ' * 12}encoding: {file_encoding}")
    print(f"{' ' * 12}dialect: {dialect}")
    print(f"{' ' * 12}replace: {replace}")

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
    colalign = [
        format_column_designator_align,
        format_column_layer_align,
        format_column_location_align,
        format_column_location_align,
        format_column_rotation_align,
        format_column_footprint_align
        ]
    floatfmt = [
        '',
        '',
        format_column_location_number,
        format_column_location_number,
        format_column_rotation_number,
        ''
    ]
    if content_mount:
        header.append(locale.translate(lcl.export_pnp_txt.HEADER_MOUNT))
        colalign.append(format_column_mount_align)
        floatfmt.append('')
    if content_state:
        header.append(locale.translate(lcl.export_pnp_txt.HEADER_STATE))
        colalign.append(format_column_state_align)
        floatfmt.append('')
    if content_partnumber:
        header.append(locale.translate(lcl.export_pnp_txt.HEADER_PARTNUMBER))
        colalign.append(format_column_partnumber_align)
        floatfmt.append('')
    if content_description:
        header.append(locale.translate(lcl.export_pnp_txt.HEADER_DESCRIPTION))
        colalign.append(format_column_description_align)
        floatfmt.append('')
    if content_comment:
        header.append(locale.translate(lcl.export_pnp_txt.HEADER_COMMENT))
        colalign.append(format_column_comment_align)
        floatfmt.append('')
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

    #экспортируем данные в TXT
    with open(address, 'w', encoding = file_encoding, newline = '') as file:
        file.write(tabulate(table, headers=header, disable_numparse=(not format_numparse), tablefmt=format_table, colalign=colalign, floatfmt=floatfmt))

    print('INFO >> pnp-txt export completed.')