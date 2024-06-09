import os
import xlsxwriter
import datetime, pytz
import copy
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

#========================================================== END Generic functions =================================================

#Экспортирует cl в формате xlsx
def export(data, address, **kwargs):
    print('INFO >> cl-xlsx exporting module running with parameters:')
    print(' ' * 12 + 'output: ' +  os.path.basename(address))

    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры
    content_accessories_location = kwargs.get('content_accessories_location', 'sheet')
    content_accessories_indent = kwargs.get('content_accessories_indent', 0)
    format_multivalue_delimiter = kwargs.get('format_multivalue_delimiter', ', ')
    format_singlevalue_delimiter = kwargs.get('format_singlevalue_delimiter', '|')
    print(' ' * 12 + 'accessories location: "' +  content_accessories_location + '", indent: ' + str(content_accessories_indent))
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
    #print(' ' * 12 + 'book title: ' + book_title)
    #print(' ' * 12 + 'book subject: ' + book_subject)
    #print(' ' * 12 + 'book author: ' + book_author)
    #print(' ' * 12 + 'book manager: ' + book_manager)
    #print(' ' * 12 + 'book company: ' + book_company)
    #print(' ' * 12 + 'book category: ' + book_category)
    #print(' ' * 12 + 'book keywords: ' + book_keywords)
    #print(' ' * 12 + 'book created: ' + str(book_created))
    #print(' ' * 12 + 'book comments: ' + book_comments)
    #print(' ' * 12 + 'book status: ' + book_status)
    #print(' ' * 12 + 'book hyperlink base: ' + book_hyperlinkBase)
    #print(' ' * 12 + 'sheet title: ' + sheet_title)

    if len(data) > 0 and len(address) > 0:
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

            #определяем стили
            format_normal  = workbook.add_format({'valign': 'vcenter'})
            format_header  = workbook.add_format({'valign': 'vcenter', 'bold':True, 'font_color':'#000000', 'bg_color':'#99CCFF', 'align':'center'})
            format_ok      = workbook.add_format({'valign': 'vcenter', 'bold':False, 'font_color':'green'})
            format_warning = workbook.add_format({'valign': 'vcenter', 'bold':False, 'font_color':'orange'})
            format_error   = workbook.add_format({'valign': 'vcenter', 'bold':False, 'font_color':'red'})

            #перебираем списки компонентов
            for cl in data:
                #структурируем подсписки для обработки в цикле
                sublists = []
                if cl.components is None and cl.accessories is not None:
                    sublists.append(cl.accessories)
                elif cl.components is not None and cl.accessories is None:
                    sublists.append(cl.components)
                elif cl.components is not None and cl.accessories is not None:
                    if content_accessories_location == 'sheet':
                        sublists.append(cl.components)
                        sublists.append(cl.accessories)
                    elif content_accessories_location == 'start':
                        cl_combined = copy.deepcopy(cl.accessories)
                        for i in range(content_accessories_indent): cl_combined.entries.append(CL_typeDef.ComponentEntry())     #приводит к 0 в столбце количества
                        cl_combined.entries.extend(cl.components.entries)
                        sublists.append(cl_combined)  
                    elif content_accessories_location == 'end':
                        cl_combined = copy.deepcopy(cl.components)
                        for i in range(content_accessories_indent): cl_combined.entries.append(CL_typeDef.ComponentEntry())     #приводит к 0 в столбце количества
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
                    worksheet.write_row(0, 0, [lcl.export_cl_xlsx.HEADER_DESIGNATOR.value[locale_index], lcl.export_cl_xlsx.HEADER_COMPONENT_TYPE.value[locale_index], lcl.export_cl_xlsx.HEADER_VALUE.value[locale_index], lcl.export_cl_xlsx.HEADER_DESCRIPTION.value[locale_index], lcl.export_cl_xlsx.HEADER_PACKAGE.value[locale_index], lcl.export_cl_xlsx.HEADER_MANUFACTURER.value[locale_index], lcl.export_cl_xlsx.HEADER_QUANTITY.value[locale_index], lcl.export_cl_xlsx.HEADER_NOTE.value[locale_index]], format_header)
                    rowIndex = 1    #начальная строка для записи данных
                    for entry in sublist.entries:
                        if entry.flag == entry.flag.OK: rowFormat = format_ok
                        elif entry.flag == entry.flag.WARNING: rowFormat = format_warning
                        elif entry.flag == entry.flag.ERROR: rowFormat = format_error
                        else: rowFormat = format_normal
                        
                        #обрабатываем незаданные поля
                        designator   = replace_nones(entry.designator,   '', False)
                        kind         = replace_nones(entry.kind,         '', False)
                        value        = replace_nones(entry.value,        '', False)
                        description  = replace_nones(entry.description,  '', False)
                        package      = replace_nones(entry.package,      '', False)
                        manufacturer = replace_nones(entry.manufacturer, '', False)
                        quantity     = replace_nones(entry.quantity,     '', False)
                        note         = replace_nones(entry.note,         '', False)
                        
                        worksheet.write_row(rowIndex, 0, [
                            format_multivalue_delimiter.join(designator),
                            format_singlevalue_delimiter.join(kind),
                            format_singlevalue_delimiter.join(value),
                            format_singlevalue_delimiter.join(description),
                            format_singlevalue_delimiter.join(package),
                            format_singlevalue_delimiter.join(manufacturer),
                            quantity,
                            format_singlevalue_delimiter.join(note)
                            ], rowFormat)
                        rowIndex += 1

                    worksheet.set_column(0, 0, 50.0)    #Поз. обозначение
                    worksheet.set_column(1, 1, 25.0)    #Тип элемента
                    worksheet.set_column(2, 2, 25.0)    #Номинал
                    worksheet.set_column(3, 3, 60.0)    #Описание
                    worksheet.set_column(4, 4, 15.0)    #Корпус
                    worksheet.set_column(5, 5, 25.0)    #Производитель
                    worksheet.set_column(6, 6,  8.0)    #Кол-во
                    worksheet.set_column(7, 7, 36.0)    #Примечание

                if cl.substitutes is not None:
                    #создаём лист в книге с именем списка замен, если имя неправильное то делаем имя листа по-умолчанию
                    try:
                        worksheet = workbook.add_worksheet(cl.substitutes.title)
                    except (xlsxwriter.exceptions.InvalidWorksheetName, xlsxwriter.exceptions.DuplicateWorksheetName):
                        worksheet = workbook.add_worksheet()

                    #запись данных списка компонентов
                    worksheet.write_row(0, 0, [lcl.export_cl_xlsx.HEADER_ORIGINAL_VALUE.value[locale_index], lcl.export_cl_xlsx.HEADER_ORIGINAL_MANUFACTURER.value[locale_index], lcl.export_cl_xlsx.HEADER_QUANTITY.value[locale_index], lcl.export_cl_xlsx.HEADER_DESIGNATOR.value[locale_index], lcl.export_cl_xlsx.HEADER_QUANTITY.value[locale_index], lcl.export_cl_xlsx.HEADER_SUBSTITUTE_VALUE.value[locale_index], lcl.export_cl_xlsx.HEADER_SUBSTITUTE_MANUFACTURER.value[locale_index], lcl.export_cl_xlsx.HEADER_SUBSTITUTE_NOTE.value[locale_index]], format_header)
                    rowIndex = 1 - 1    #начальная строка для записи данных (-1 из за обратного порядка записи и инкремента строки перед записью)
                    for entry in cl.substitutes.entries:
                        if entry.flag == entry.flag.OK: rowFormat = format_ok
                        elif entry.flag == entry.flag.WARNING: rowFormat = format_warning
                        elif entry.flag == entry.flag.ERROR: rowFormat = format_error
                        else: rowFormat = format_normal
                        
                        entry_height = 0
                        for substitute_group in entry.substitute_group:
                            #--- --- список замен для группы
                            group_height = 0
                            for substitute in substitute_group.substitute:
                                value        = replace_nones(substitute.value,        '', False)
                                manufacturer = replace_nones(substitute.manufacturer, '', False)
                                note         = replace_nones(substitute.note,         '', False)
                                rowIndex += 1
                                group_height += 1
                                worksheet.write_row(rowIndex, 5, [value, manufacturer, note], rowFormat)

                            #--- список заменных групп
                            designator   = replace_nones(substitute_group.designator,   '', False)
                            quantity     = replace_nones(substitute_group.quantity,     '', False)
                            designator = format_multivalue_delimiter.join(designator)                         #собираем список десигнаторов
                            entry_height += group_height
                            if group_height > 1:
                                worksheet.merge_range(rowIndex - (group_height - 1), 3, rowIndex, 3, designator, rowFormat)
                                worksheet.merge_range(rowIndex - (group_height - 1), 4, rowIndex, 4, quantity, rowFormat)
                            else:
                                worksheet.write_row(rowIndex, 3, [designator, quantity], rowFormat)
                        
                        #список значальных компонентов
                        primary_value        = replace_nones(entry.primary_value,        '', False)
                        primary_manufacturer = replace_nones(entry.primary_manufacturer, '', False)
                        primary_quantity     = replace_nones(entry.primary_quantity,     '', False)
                        if entry_height > 1:
                            worksheet.merge_range(rowIndex - (entry_height - 1), 0, rowIndex, 0, primary_value, rowFormat)
                            worksheet.merge_range(rowIndex - (entry_height - 1), 1, rowIndex, 1, primary_manufacturer, rowFormat)
                            worksheet.merge_range(rowIndex - (entry_height - 1), 2, rowIndex, 2, primary_quantity, rowFormat)
                        else:
                            worksheet.write_row(rowIndex, 0, [primary_value, primary_manufacturer, primary_quantity], rowFormat)

                    worksheet.set_column(0, 0, 25.0)
                    worksheet.set_column(1, 1, 25.0)
                    worksheet.set_column(2, 2,  8.0)
                    worksheet.set_column(3, 3, 70.0)
                    worksheet.set_column(4, 4,  8.0)
                    worksheet.set_column(5, 5, 25.0)
                    worksheet.set_column(6, 6, 25.0)
                    worksheet.set_column(7, 7, 42.0)

        print('INFO >> cl export completed.')  
    else:
        print("ERROR! >> No output data or file specified.")
