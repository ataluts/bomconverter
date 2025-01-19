import os
import subprocess
import csv

from typedef_pe3 import PE3_typeDef                                 #класс перечня элементов

script_dirName  = os.path.dirname(__file__)                                                     #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                               #базовое имя модуля
template_defaultAddress = os.path.join(script_dirName, script_baseName + os.extsep + 'tex')     #адрес шаблона по-умолчанию

#Экспортирует ПЭ3 в формате PDF
def export(data, address, **kwargs):
    print('INFO >> pe3-pdf exporting module running with parameters:')
    print(' ' * 12 + 'output: ' +  os.path.basename(address))

    #адрес шаблона перечня элементов
    template_address = kwargs.get('template', template_defaultAddress)
    print(' ' * 12 + 'template: ' + os.path.basename(template_address))

    print('INFO >> Exporting data to temporary CSV files', end ="... ", flush = True)
    #формирование адресов временных файлов
    outputDirectory = os.path.dirname(address)
    data_tmpAddress  = os.path.join(outputDirectory, script_baseName + '-data' + os.extsep + 'csv')
    tb_tmpAddress   = os.path.join(outputDirectory, script_baseName + '-tb' + os.extsep + 'csv')

    titleblock = data.titleblock if data.titleblock is not None else {}
    #фикс бага что если имя документа пустое то MiKTeX не может собрать комбинированную строку
    tb01a_DocumentName = titleblock.get('01a_product_name', '')
    if len(tb01a_DocumentName) == 0: tb01a_DocumentName = '-'

    #экспортируем данные в CSV для передачи в MiKTeX
    #--- основная надпись
    with open(tb_tmpAddress, 'w', encoding='utf-8', newline='') as csvFile:
        fieldnames = ['Document name', \
                        'Document type', \
                        'Document designator', \
                        'Letter (left)', 'Letter (middle)', 'Letter (right)', \
                        'Sheet index', 'Sheets total', \
                        'Organization', \
                        'Extra activity type', \
                        'Designer name', \
                        'Checker name', \
                        'Technical supervisor name', \
                        'Extra activity name', \
                        'Normative supervisor name', \
                        'Approver name', \
                        'Designer signature date', \
                        'Checker signature date', \
                        'Technical supervisor signature date', \
                        'Extra activity signature date', \
                        'Normative supervisor signature date', \
                        'Approver signature date', \
                        'Original inventory number', \
                        'Replaced original inventory number', \
                        'Duplicate inventory number', \
                        'Base document designator', \
                        'First reference document designator']
        writer = csv.DictWriter(csvFile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'Document name': tb01a_DocumentName,
                        'Document type': titleblock.get('01b_document_type', ''),
                        'Document designator': titleblock.get('02_document_designator', ''),
                        'Letter (left)': titleblock.get('04_letter_left', ''), 'Letter (middle)': titleblock.get('04_letter_middle', ''), 'Letter (right)': titleblock.get('04_letter_right', ''),
                        'Sheet index': titleblock.get('07_sheet_index', ''), 'Sheets total': titleblock.get('08_sheet_total', ''),
                        'Organization': titleblock.get('09_organization', ''),
                        'Extra activity type': titleblock.get('10d_activityType_extra', ''),
                        'Designer name': titleblock.get('11a_name_designer', ''),
                        'Checker name': titleblock.get('11b_name_checker', ''),
                        'Technical supervisor name': titleblock.get('11c_name_technicalSupervisor', ''),
                        'Extra activity name': titleblock.get('11d_name_extra', ''),
                        'Normative supervisor name': titleblock.get('11e_name_normativeSupervisor', ''),
                        'Approver name': titleblock.get('11f_name_approver', ''),
                        'Designer signature date': titleblock.get('13a_signatureDate_designer', ''),
                        'Checker signature date': titleblock.get('13b_signatureDate_checker', ''),
                        'Technical supervisor signature date': titleblock.get('13c_signatureDate_technicalSupervisor', ''),
                        'Extra activity signature date': titleblock.get('13d_signatureDate_extra', ''),
                        'Normative supervisor signature date': titleblock.get('13e_signatureDate_normativeSupervisor', ''),
                        'Approver signature date': titleblock.get('13f_signatureDate_approver', ''),
                        'Original inventory number': titleblock.get('19_original_inventoryNumber', ''), 
                        'Replaced original inventory number': titleblock.get('21_replacedOriginal_inventoryNumber', ''), 
                        'Duplicate inventory number': titleblock.get('22_duplicate_inventoryNumber', ''), 
                        'Base document designator': titleblock.get('24_baseDocument_designator', ''),
                        'First reference document designator': titleblock.get('25_firstReferenceDocument_designator', '')})
        csvFile.close()
    #--- перечень элементов
    with open(data_tmpAddress, 'w', encoding='utf-8', newline='') as csvFile:
        writer = csv.DictWriter(csvFile, fieldnames=['Designator', 'Label', 'Quantity', 'Annotation'])
        writer.writeheader()
        for row in data.rows:
            writer.writerow({'Designator': row.designator,
                             'Label':      row.label.replace('\r', '').replace('\n', '\\\\'),         #заменяем символ новой строки на используемый в LaTeX
                             'Quantity':   row.quantity,
                             'Annotation': row.annotation.replace('\r', '').replace('\n', '\\\\')})   #заменяем символ новой строки на используемый в LaTeX
        csvFile.close()
    print('done.')

    #создание PDF через MiKTeX
    print('INFO >> Executing MiKTeX: ')
    subprocess.run(['texify', '--quiet', '--clean', '--pdf', "--engine=xetex", template_address], cwd = outputDirectory)
    #BUG!!! отсюда и далее нельзя использовать не ascii вывод в cmd windows поскольку это приводит к его падению
    print('INFO >> MiKTeX has finished.')

    print('INFO >> Renaming result', end ="... ", flush = True)
    result_address = os.path.join(outputDirectory, script_baseName + os.extsep + "pdf")
    #если уже есть файл с нужным конечным именем - удаляем его
    if os.path.isfile(address): os.remove(address)
    #переименовываем выходной файл нужным именем
    if os.path.isfile(result_address):
        os.renames(result_address, address)
        print('done.')
    else:
        print('error: MiKTeX output file not found.')

    #удаление временных файлов
    print('INFO >> Deleting temporary files', end ="... ", flush = True)
    os.remove(data_tmpAddress)
    os.remove(tb_tmpAddress)
    print('done.')

    print('INFO >> pe3-pdf export completed.')   
