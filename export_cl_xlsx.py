import os
import xlsxwriter
import datetime
import copy
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

    #параметры объединения разных значений в одной ячейке
    delimiter_grouped    = kwargs.get('delimGrouped', ', ')
    delimiter_single = kwargs.get('delimSingle', '|')
    print(' ' * 12 + 'delimiter for grouped columns: "' +  delimiter_grouped + '"')
    print(' ' * 12 + 'delimiter for single-value columns: "' +  delimiter_single + '"')

    #свойства книги
    book_title    = kwargs.get('bookTitle', 'Список компонентов')
    book_subject  = kwargs.get('bookSubject', '')
    book_author   = kwargs.get('bookAuthor', '')
    book_manager  = kwargs.get('bookManager', '')
    book_company  = kwargs.get('bookCompany', '')
    book_category = kwargs.get('bookCategory', '')
    book_keywords = kwargs.get('bookKeywords', '')
    book_created  = kwargs.get('bookCreated', datetime.datetime.now())
    book_comments = kwargs.get('bookComments', '')
    book_status   = kwargs.get('bookStatus', '')
    book_hyperlinkBase = kwargs.get('bookHyperlinkBase', '')
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
                if cl.comp_entries is not None:
                    #создаём лист в книге с именем списка компонентов, если имя неправильное то делаем имя листа по-умолчанию
                    try:
                        worksheet = workbook.add_worksheet(cl.component_list_name)
                    except (xlsxwriter.exceptions.InvalidWorksheetName, xlsxwriter.exceptions.DuplicateWorksheetName):
                        worksheet = workbook.add_worksheet()

                    #запись данных списка компонентов
                    worksheet.write_row(0, 0, ['Поз. обозначение', 'Тип элемента', 'Номинал', 'Описание', 'Корпус', 'Производитель', 'Кол-во'], format_header)
                    rowIndex = 1    #начальная строка для записи данных
                    for entry in cl.comp_entries:
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
                        
                        worksheet.write_row(rowIndex, 0, [
                            delimiter_grouped.join(designator),
                            delimiter_single.join(kind),
                            delimiter_single.join(value),
                            delimiter_single.join(description),
                            delimiter_single.join(package),
                            delimiter_single.join(manufacturer),
                            quantity
                            ], rowFormat)
                        rowIndex += 1

                    worksheet.set_column(0, 0, 70.0)
                    worksheet.set_column(1, 1, 25.0)
                    worksheet.set_column(2, 2, 25.0)
                    worksheet.set_column(3, 3, 60.0)
                    worksheet.set_column(4, 4, 15.0)
                    worksheet.set_column(5, 5, 25.0)
                    worksheet.set_column(6, 6,  7.0)

                if cl.subs_entries is not None:
                    #создаём лист в книге с именем списка замен, если имя неправильное то делаем имя листа по-умолчанию
                    try:
                        worksheet = workbook.add_worksheet(cl.substitute_list_name)
                    except (xlsxwriter.exceptions.InvalidWorksheetName, xlsxwriter.exceptions.DuplicateWorksheetName):
                        worksheet = workbook.add_worksheet()

                    #запись данных списка компонентов
                    worksheet.write_row(0, 0, ['Изнач. номинал', 'Изнач. производитель', 'Кол-во', 'Поз. обозначение', 'Кол-во', 'Зам. номинал', 'Зам. производитель', 'Зам. примечание'], format_header)
                    rowIndex = 1 - 1    #начальная строка для записи данных (-1 из за обратного порядка записи и инкремента строки перед записью)
                    for entry in cl.subs_entries:
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
                            designator = delimiter_grouped.join(designator)                         #собираем список десигнаторов
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
                    worksheet.set_column(2, 2,  7.0)
                    worksheet.set_column(3, 3, 70.0)
                    worksheet.set_column(4, 4,  7.0)
                    worksheet.set_column(5, 5, 25.0)
                    worksheet.set_column(6, 6, 25.0)
                    worksheet.set_column(7, 7, 42.0)

        print('INFO >> cl export completed.')  
    else:
        print("ERROR! >> No output data or file specified.")

 