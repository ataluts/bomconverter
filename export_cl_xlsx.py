import os
import xlsxwriter
import datetime, pytz
import copy
import collections.abc
import dict_locale as lcl
from typedef_cl import CL_typeDef                                                               #структура списка компонентов

script_dirName  = os.path.dirname(__file__)                                                     #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                               #базовое имя модуля

# ----------------------------------------------------------- Generic functions -------------------------------------------------

#заменяет None значения в данных
def replace_nones(data, replacement = '', edit_in_place = False):
    if data is None: return replacement
    if isinstance(data, list):
        if edit_in_place: result = data
        else: result = copy.deepcopy(data)
        for i in range(len(result)):
            result[i] = replace_nones(result[i], replacement)
        return result
    return data

#обновляет вложенные словари
def dict_nested_update(source, update):
    for key, value in update.items():
        if isinstance(value, collections.abc.Mapping):
            source[key] = dict_nested_update(source.get(key, {}), value)
        else:
            if source is None: source = {}
            source[key] = value
    return source


#========================================================== END Generic functions =================================================

#Экспортирует cl в формате xlsx
def export(data, address, **kwargs):
    print('INFO >> cl-xlsx exporting module running with parameters:')
    print(' ' * 12 + 'output: ' +  os.path.basename(address))

    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры
    content_accs_location = kwargs.get('content_accs_location', 'sheet')
    content_accs_indent = kwargs.get('content_accs_indent', 0)
    format_multivalue_delimiter = kwargs.get('format_multivalue_delimiter', ', ')
    format_singlevalue_delimiter = kwargs.get('format_singlevalue_delimiter', '|')
    print(' ' * 12 + 'accessories location: "' +  content_accs_location + '", indent: ' + str(content_accs_indent))
    print(' ' * 12 + 'delimiter for multi-value columns: "' +  format_multivalue_delimiter + '"')
    print(' ' * 12 + 'delimiter for single-value columns: "' +  format_singlevalue_delimiter + '"')

    #свойства книги
    book_title    = kwargs.get('book_title', '<none>')
    book_subject  = kwargs.get('book_subject', '')
    book_author   = kwargs.get('book_author', '')
    book_manager  = kwargs.get('book_manager', '')
    book_company  = kwargs.get('book_company', '')
    book_category = kwargs.get('book_category', '')
    book_keywords = kwargs.get('book_keywords', '')
    book_created  = kwargs.get('book_created', datetime.datetime.now(pytz.timezone('UTC')))
    book_comments = kwargs.get('book_comments', '')
    book_status   = kwargs.get('book_status', '')
    book_hyperlinkBase = kwargs.get('book_hyperlink', '')
    book_style_arg = kwargs.get('book_style', {})

    #стили
    book_style = {
        'row' : {
            'generic' : None,
            'header'  : {'valign': 'vcenter', 'bold':True, 'font_color':'#000000', 'bg_color':'#99CCFF', 'align':'center'},
            'ok'      : {'valign': 'vcenter', 'bold':False, 'font_color':'green'},
            'warning' : {'valign': 'vcenter', 'bold':False, 'font_color':'orange'},
            'error'   : {'valign': 'vcenter', 'bold':False, 'font_color':'red'}
        },
        'col' : {
            'desig'               : {'width': 50.0, 'valign': 'vcenter'},
            'kind'                : {'width': 25.0, 'valign': 'vcenter'},
            'value'               : {'width': 25.0, 'valign': 'vcenter'},
            'description'         : {'width': 60.0, 'valign': 'vcenter'},
            'package'             : {'width': 15.0, 'valign': 'vcenter'},
            'mfr'                 : {'width': 25.0, 'valign': 'vcenter'},
            'quantity'            : {'width':  8.0, 'valign': 'vcenter'},
            'note'                : {'width': 36.0, 'valign': 'vcenter'},
            'subst_orig_value'    : {'width': 25.0, 'valign': 'vcenter'},
            'subst_orig_mfr'      : {'width': 25.0, 'valign': 'vcenter'},
            'subst_orig_quantity' : {'width': 15.0, 'valign': 'vcenter'},
            'subst_desig'         : {'width': 70.0, 'valign': 'vcenter'},
            'subst_quantity'      : {'width': 15.0, 'valign': 'vcenter'},
            'subst_value'         : {'width': 25.0, 'valign': 'vcenter'},
            'subst_mfr'           : {'width': 25.0, 'valign': 'vcenter'},
            'subst_note'          : {'width': 44.0, 'valign': 'vcenter'}
        }
    }
    #обновляем стили по-умолчанию стилями из аргумента
    book_style = dict_nested_update(book_style, book_style_arg)
    #выделяем высоту строк в отдельный словарь
    row_heights = {}
    for key in book_style['row']:
        if book_style['row'][key] is not None and 'height' in book_style['row'][key]:
            row_heights[key] = book_style['row'][key].pop('height')
            #если словарь с форматом стал пустым то ставим ему значение None
            if not book_style['row'][key]: book_style['row'][key] = None
    #выделяем ширину столбцов в отдельный словарь
    col_widths = {}
    for key in book_style['col']:
        if book_style['col'][key] is not None and 'width' in book_style['col'][key]:
            col_widths[key] = book_style['col'][key].pop('width')
            #если словарь с форматом стал пустым то ставим ему значение None
            if not book_style['col'][key]: book_style['col'][key] = None

    if len(data) > 0:
        with xlsxwriter.Workbook(address, {'in_memory': True, 'strings_to_numbers': False}) as workbook:
            if 'book_title' not in kwargs: book_title = data[0].book_title
            
            #заполняем свойства книги
            workbook.set_properties({
                'title':    book_title,
                'subject':  book_subject,
                'author':   book_author,
                'manager':  book_manager,
                'company':  book_company,
                'category': book_category,
                'keywords': book_keywords,
                'created':  book_created,
                'comments': book_comments,
                'status':   book_status,
                'hyperlink_base':  book_hyperlinkBase})

            #задаём стили
            wb_format_row_generic = None if book_style['row']['generic'] is None else workbook.add_format(book_style['row']['generic'])
            wb_format_row_header  = None if book_style['row']['header']  is None else workbook.add_format(book_style['row']['header'])
            wb_format_row_ok      = None if book_style['row']['ok']      is None else workbook.add_format(book_style['row']['ok'])
            wb_format_row_warning = None if book_style['row']['warning'] is None else workbook.add_format(book_style['row']['warning'])
            wb_format_row_error   = None if book_style['row']['error']   is None else workbook.add_format(book_style['row']['error'])
            wb_format_col_desig       = None if book_style['col']['desig']       is None else workbook.add_format(book_style['col']['desig'])
            wb_format_col_kind        = None if book_style['col']['kind']        is None else workbook.add_format(book_style['col']['kind'])
            wb_format_col_value       = None if book_style['col']['value']       is None else workbook.add_format(book_style['col']['value'])
            wb_format_col_description = None if book_style['col']['description'] is None else workbook.add_format(book_style['col']['description'])
            wb_format_col_package     = None if book_style['col']['package']     is None else workbook.add_format(book_style['col']['package'])
            wb_format_col_mfr         = None if book_style['col']['mfr']         is None else workbook.add_format(book_style['col']['mfr'])
            wb_format_col_quantity    = None if book_style['col']['quantity']    is None else workbook.add_format(book_style['col']['quantity'])
            wb_format_col_note        = None if book_style['col']['note']        is None else workbook.add_format(book_style['col']['note'])
            wb_format_col_subst_orig_value    = None if book_style['col']['subst_orig_value']    is None else workbook.add_format(book_style['col']['subst_orig_value'])
            wb_format_col_subst_orig_mfr      = None if book_style['col']['subst_orig_mfr']      is None else workbook.add_format(book_style['col']['subst_orig_mfr'])
            wb_format_col_subst_orig_quantity = None if book_style['col']['subst_orig_quantity'] is None else workbook.add_format(book_style['col']['subst_orig_quantity'])
            wb_format_col_subst_desig         = None if book_style['col']['subst_desig']         is None else workbook.add_format(book_style['col']['subst_desig'])
            wb_format_col_subst_quantity      = None if book_style['col']['subst_quantity']      is None else workbook.add_format(book_style['col']['subst_quantity'])
            wb_format_col_subst_value         = None if book_style['col']['subst_value']         is None else workbook.add_format(book_style['col']['subst_value'])
            wb_format_col_subst_mfr           = None if book_style['col']['subst_mfr']           is None else workbook.add_format(book_style['col']['subst_mfr'])
            wb_format_col_subst_note          = None if book_style['col']['subst_note']          is None else workbook.add_format(book_style['col']['subst_note'])

            #перебираем списки компонентов
            for cl in data:
                #структурируем подсписки для обработки в цикле
                sublists = []
                if cl.components is None and cl.accessories is not None:
                    sublists.append(cl.accessories)
                elif cl.components is not None and cl.accessories is None:
                    sublists.append(cl.components)
                elif cl.components is not None and cl.accessories is not None:
                    if content_accs_location == 'sheet':
                        sublists.append(cl.components)
                        sublists.append(cl.accessories)
                    elif content_accs_location == 'start':
                        cl_combined = copy.deepcopy(cl.accessories)
                        for i in range(content_accs_indent): cl_combined.entries.append(CL_typeDef.ComponentEntry())     #приводит к 0 в столбце количества
                        cl_combined.entries.extend(cl.components.entries)
                        sublists.append(cl_combined)  
                    elif content_accs_location == 'end':
                        cl_combined = copy.deepcopy(cl.components)
                        for i in range(content_accs_indent): cl_combined.entries.append(CL_typeDef.ComponentEntry())     #приводит к 0 в столбце количества
                        cl_combined.entries.extend(cl.accessories.entries)
                        sublists.append(cl_combined)                  
                    else: 
                        raise ValueError

                for sublist in sublists:
                    #создаём лист в книге с именем подсписка компонентов, если имя неправильное то делаем имя листа по-умолчанию
                    try:
                        worksheet = workbook.add_worksheet(sublist.title)
                    except (xlsxwriter.exceptions.InvalidWorksheetName, xlsxwriter.exceptions.DuplicateWorksheetName):
                        worksheet = workbook.add_worksheet()

                    #запись данных списка компонентов
                    worksheet.write_row(0, 0, [lcl.export_cl_xlsx.HEADER_DESIGNATOR.value[locale_index], lcl.export_cl_xlsx.HEADER_COMPONENT_TYPE.value[locale_index], lcl.export_cl_xlsx.HEADER_VALUE.value[locale_index], lcl.export_cl_xlsx.HEADER_DESCRIPTION.value[locale_index], lcl.export_cl_xlsx.HEADER_PACKAGE.value[locale_index], lcl.export_cl_xlsx.HEADER_MANUFACTURER.value[locale_index], lcl.export_cl_xlsx.HEADER_QUANTITY.value[locale_index], lcl.export_cl_xlsx.HEADER_NOTE.value[locale_index]], wb_format_row_header)
                    row_index = 1    #начальная строка для записи данных
                    for entry in sublist.entries:
                        if entry.flag == entry.flag.OK:
                            row_format = wb_format_row_ok
                            row_height = row_heights.get('ok', None)
                        elif entry.flag == entry.flag.WARNING:
                            row_format = wb_format_row_warning
                            row_height = row_heights.get('warning', None)
                        elif entry.flag == entry.flag.ERROR:
                            row_format = wb_format_row_error
                            row_height = row_heights.get('error', None)
                        else:
                            row_format = wb_format_row_generic
                            row_height = row_heights.get('generic', None)
                        
                        #обрабатываем незаданные поля
                        designator   = replace_nones(entry.designator,   '', False)
                        kind         = replace_nones(entry.kind,         '', False)
                        value        = replace_nones(entry.value,        '', False)
                        description  = replace_nones(entry.description,  '', False)
                        package      = replace_nones(entry.package,      '', False)
                        manufacturer = replace_nones(entry.manufacturer, '', False)
                        quantity     = replace_nones(entry.quantity,     '', False)
                        note         = replace_nones(entry.note,         '', False)
                        
                        worksheet.write_row(row_index, 0, [
                            format_multivalue_delimiter.join(designator),
                            format_singlevalue_delimiter.join(kind),
                            format_singlevalue_delimiter.join(value),
                            format_singlevalue_delimiter.join(description),
                            format_singlevalue_delimiter.join(package),
                            format_singlevalue_delimiter.join(manufacturer),
                            quantity,
                            format_singlevalue_delimiter.join(note)
                            ], row_format)
                        if row_height is not None: worksheet.set_row(row_index, row_height)
                        row_index += 1

                    worksheet.set_column(0, 0, col_widths['desig'],       wb_format_col_desig)        #Поз. обозначение
                    worksheet.set_column(1, 1, col_widths['kind'],        wb_format_col_kind)         #Тип элемента
                    worksheet.set_column(2, 2, col_widths['value'],       wb_format_col_value)        #Номинал
                    worksheet.set_column(3, 3, col_widths['description'], wb_format_col_description)  #Описание
                    worksheet.set_column(4, 4, col_widths['package'],     wb_format_col_package)      #Корпус
                    worksheet.set_column(5, 5, col_widths['mfr'],         wb_format_col_mfr)          #Производитель
                    worksheet.set_column(6, 6, col_widths['quantity'],    wb_format_col_quantity)     #Кол-во
                    worksheet.set_column(7, 7, col_widths['note'],        wb_format_col_note)         #Примечание

                if cl.substitutes is not None:
                    #создаём лист в книге с именем списка замен, если имя неправильное то делаем имя листа по-умолчанию
                    try:
                        worksheet = workbook.add_worksheet(cl.substitutes.title)
                    except (xlsxwriter.exceptions.InvalidWorksheetName, xlsxwriter.exceptions.DuplicateWorksheetName):
                        worksheet = workbook.add_worksheet()

                    #запись данных списка компонентов
                    worksheet.write_row(0, 0, [lcl.export_cl_xlsx.HEADER_ORIGINAL_VALUE.value[locale_index], lcl.export_cl_xlsx.HEADER_ORIGINAL_MANUFACTURER.value[locale_index], lcl.export_cl_xlsx.HEADER_ORIGINAL_QUANTITY.value[locale_index], lcl.export_cl_xlsx.HEADER_DESIGNATOR.value[locale_index], lcl.export_cl_xlsx.HEADER_SUBSTITUTE_QUANTITY.value[locale_index], lcl.export_cl_xlsx.HEADER_SUBSTITUTE_VALUE.value[locale_index], lcl.export_cl_xlsx.HEADER_SUBSTITUTE_MANUFACTURER.value[locale_index], lcl.export_cl_xlsx.HEADER_SUBSTITUTE_NOTE.value[locale_index]], wb_format_row_header)
                    row_index = 1 - 1    #начальная строка для записи данных (-1 из за обратного порядка записи и инкремента строки перед записью)
                    for entry in cl.substitutes.entries:
                        if entry.flag == entry.flag.OK:
                            row_format = wb_format_row_ok
                            row_height = row_heights.get('ok', None)
                        elif entry.flag == entry.flag.WARNING:
                            row_format = wb_format_row_warning
                            row_height = row_heights.get('warning', None)
                        elif entry.flag == entry.flag.ERROR:
                            row_format = wb_format_row_error
                            row_height = row_heights.get('error', None)
                        else:
                            row_format = wb_format_row_generic
                            row_height = row_heights.get('generic', None)
                        
                        entry_height = 0
                        for substitute_group in entry.substitute_group:
                            #--- --- список замен для группы
                            group_height = 0
                            for substitute in substitute_group.substitute:
                                value        = replace_nones(substitute.value,        '', False)
                                manufacturer = replace_nones(substitute.manufacturer, '', False)
                                note         = replace_nones(substitute.note,         '', False)
                                row_index += 1
                                group_height += 1
                                worksheet.write_row(row_index, 5, [value, manufacturer, note], row_format)
                                if row_height is not None: worksheet.set_row(row_index, row_height)

                            #--- список заменных групп
                            designator   = replace_nones(substitute_group.designator,   '', False)
                            quantity     = replace_nones(substitute_group.quantity,     '', False)
                            designator = format_multivalue_delimiter.join(designator)                         #собираем список десигнаторов
                            entry_height += group_height
                            if group_height > 1:
                                worksheet.merge_range(row_index - (group_height - 1), 3, row_index, 3, designator, row_format)
                                worksheet.merge_range(row_index - (group_height - 1), 4, row_index, 4, quantity, row_format)
                            else:
                                worksheet.write_row(row_index, 3, [designator, quantity], row_format)
                        
                        #список изначальных компонентов
                        primary_value        = replace_nones(entry.primary_value,        '', False)
                        primary_manufacturer = replace_nones(entry.primary_manufacturer, '', False)
                        primary_quantity     = replace_nones(entry.primary_quantity,     '', False)
                        if entry_height > 1:
                            worksheet.merge_range(row_index - (entry_height - 1), 0, row_index, 0, primary_value, row_format)
                            worksheet.merge_range(row_index - (entry_height - 1), 1, row_index, 1, primary_manufacturer, row_format)
                            worksheet.merge_range(row_index - (entry_height - 1), 2, row_index, 2, primary_quantity, row_format)
                        else:
                            worksheet.write_row(row_index, 0, [primary_value, primary_manufacturer, primary_quantity], row_format)

                    worksheet.set_column(0, 0, col_widths['subst_orig_value'],    wb_format_col_subst_orig_value)
                    worksheet.set_column(1, 1, col_widths['subst_orig_mfr'],      wb_format_col_subst_orig_mfr)
                    worksheet.set_column(2, 2, col_widths['subst_orig_quantity'], wb_format_col_subst_orig_quantity)
                    worksheet.set_column(3, 3, col_widths['subst_desig'],         wb_format_col_subst_desig)
                    worksheet.set_column(4, 4, col_widths['subst_quantity'],      wb_format_col_subst_quantity)
                    worksheet.set_column(5, 5, col_widths['subst_value'],         wb_format_col_subst_value)
                    worksheet.set_column(6, 6, col_widths['subst_mfr'],           wb_format_col_subst_mfr)
                    worksheet.set_column(7, 7, col_widths['subst_note'],          wb_format_col_subst_note)

        print('INFO >> cl export completed.')  
    else:
        print("ERROR! >> No output data specified.")
