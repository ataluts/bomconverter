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

    #фикс бага что если имя документа пустое то MiKTeX не может собрать комбинированную строку
    tb01a_DocumentName = data.titleBlock.tb01a_DocumentName
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
                        'Document type': data.titleBlock.tb01b_DocumentType,
                        'Document designator': data.titleBlock.tb02_DocumentDesignator,
                        'Letter (left)': data.titleBlock.tb04_Letter_left, 'Letter (middle)': data.titleBlock.tb04_Letter_middle, 'Letter (right)': data.titleBlock.tb04_Letter_right,
                        'Sheet index': data.titleBlock.tb07_SheetIndex, 'Sheets total': data.titleBlock.tb08_SheetsTotal,
                        'Organization': data.titleBlock.tb09_Organization,
                        'Extra activity type': data.titleBlock.tb10d_ActivityType_Extra,
                        'Designer name': data.titleBlock.tb11a_Name_Designer,
                        'Checker name': data.titleBlock.tb11b_Name_Checker,
                        'Technical supervisor name': data.titleBlock.tb11c_Name_TechnicalSupervisor,
                        'Extra activity name': data.titleBlock.tb11d_Name_Extra,
                        'Normative supervisor name': data.titleBlock.tb11e_Name_NormativeSupervisor,
                        'Approver name': data.titleBlock.tb11f_Name_Approver,
                        'Designer signature date': data.titleBlock.tb13a_SignatureDate_Designer,
                        'Checker signature date': data.titleBlock.tb13b_SignatureDate_Checker,
                        'Technical supervisor signature date': data.titleBlock.tb13c_SignatureDate_TechnicalSupervisor,
                        'Extra activity signature date': data.titleBlock.tb13d_SignatureDate_Extra,
                        'Normative supervisor signature date': data.titleBlock.tb13e_SignatureDate_NormativeSupervisor,
                        'Approver signature date': data.titleBlock.tb13f_SignatureDate_Approver,
                        'Original inventory number': data.titleBlock.tb19_OriginalInventoryNumber, 
                        'Replaced original inventory number': data.titleBlock.tb21_ReplacedOriginalInventoryNumber, 
                        'Duplicate inventory number': data.titleBlock.tb22_DuplicateInventoryNumber, 
                        'Base document designator': data.titleBlock.tb24_BaseDocumentDesignator,
                        'First reference document designator': data.titleBlock.tb25_FirstReferenceDocumentDesignator})
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
