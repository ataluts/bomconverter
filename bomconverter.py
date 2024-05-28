import sys
import argparse
import os
import copy
import datetime
import re
import enum

import typedef_bom                      #класс BoM
import typedef_components               #класс базы данных компонентов
import typedef_titleBlock               #класс основной надписи

import import_adproject                 #импорт данных проекта Altium Designer
import import_bom_csv as import_bom     #импорт данных из Bill of Materials
import parse_taluts as parse            #анализ данных под конкретного разработчика
import optimize_mfrNames                #оптимизация имён производителей
import optimize_restol5to1              #оптимизация номиналов резисторов по точности (5%->1%)
import build_cl                         #сборка списка компонентов
import build_pe3                        #сборка перечня элементов
import build_sp                         #сборка спецификации
import export_cl_xlsx                   #экспорт списка компонентов в Excel
import export_pe3_docx                  #экспорт перечня элементов в Word
import export_pe3_pdf                   #экспорт перечня элементов в PDF
import export_sp_csv                    #экспорт спецификации в CSV
from dict_locale import LocaleIndex     #словарь с локализациями

script_dirName = os.path.dirname(__file__)                     #адрес папки со скриптом
script_version = '3.3'
script_date    = datetime.datetime(2024, 9, 28)

#todo: пересмотреть логику группировки компонентов в одну запись во всех сборщиках, например добавлены данные о заменах и это надо учитывать
#todo: CL - в допустимых заменах работа с флагами толком не реализована

# -------------------------------------------------------- Generic functions --------------------------------------------------------

#exit the program
def exit():
    input("Press any key to exit...")
    sys.exit(0)

#====================================================== END Generic functions =======================================================

#-------------------------------------------------------- Class definitions ---------------------------------------------------------

class OutputID(enum.Enum):
    ALL      = 'all'
    CL_XLSX  = 'cl-xlsx'
    PE3_DOCX = 'pe3-docx'
    PE3_PDF  = 'pe3-pdf'
    SP_CSV   = 'sp-csv'
    NONE     = 'none'

class OptimizationID(enum.Enum):
    ALL        = 'all'
    MFRNAMES   = 'mfrnames'
    RESTOL5TO1 = 'restol5to1'
    NONE       = 'none'

#====================================================== END Class definitions =======================================================

#-------------------------------------------------------- Specific functions --------------------------------------------------------

#обрабатываем файл проекта Altium
def process_adproject(address, output_directory = None, **kwargs):
    print(('INFO >> Processing AD project: "' + os.path.basename(address) + '" ').ljust(80, '-'))
    print(' ' * 12 + 'output: ' +  os.path.basename(address))

    #получаем параметры
    noquestions = kwargs.pop('noquestions',  False)

    #импорт проекта Altium Designer
    ADProject = import_adproject.importz(address)
    ADProject.titleBlock = typedef_titleBlock.TitleBlock_typeDef()
    print('')

    #отдаём разработчику проект чтобы он заполнил его параметры
    print("INFO >> Filling project data using designer's parser:")
    parse.parse_project(ADProject)
    print('INFO >> BoMs found: ' + str(len(ADProject.BoMs)))
    for i in range(len(ADProject.BoMs)):
        print(' ' * 12 + str(i + 1).rjust(2)  + ': "' + os.path.basename(ADProject.BoMs[i]) + '" / "' + ADProject.BoMVariantNames[i] + '"')

    #справшиваем какие BoM обрабатывать если их больше одного
    activeBomIndexes = []
    if len(ADProject.BoMs) == 1 or noquestions:
        activeBomIndexes = list(range(len(ADProject.BoMs)))
    elif len(ADProject.BoMs) > 1:
        validAnswer = False
        #запрашиваем данные пока нет правильного ответа 
        while not validAnswer:
            answer = input("REQUEST >> Choose which BoMs to process (0 or <empty> for all, q for abort): ")
            if answer == 'q': exit()
            elif answer == '0' or answer == '':
                activeBomIndexes = list(range(len(ADProject.BoMs)))
                validAnswer = True
            else:
                for idx in filter(None, re.split('[ ,.]', answer)):
                    if idx.isdigit():
                        index = int(idx) - 1
                        if index >= 0 and index < len(ADProject.BoMs):
                            activeBomIndexes.append(index)
                            validAnswer = True
                    else:
                        validAnswer = False
                        break
            if not validAnswer: print("REQUEST >> error: invalid indexes.")
        activeBomIndexes = list(set(activeBomIndexes))   #убираем дубликаты
    print("INFO >> BoM files to process: " + str(len(activeBomIndexes)))

    #обрабатываем все выбранные BoM из проекта
    kwargs['output_name_prefix'] = ADProject.designator
    for i in activeBomIndexes:
        kwargs['output_name_postfix'] = ADProject.BoMVariantNames[i]
        process_bom(os.path.join(ADProject.directory, ADProject.BoMs[i]), ADProject.titleBlock, output_directory, **kwargs)

    print((' ' * 8).ljust(80, '='))

#обрабатываем BoM файлы
def process_bom(address, titleBlock = None, output_directory = None, **kwargs):
    if titleBlock is None: titleBlock = typedef_titleBlock.TitleBlock_typeDef()
    make_cl_xlsx     = False
    make_pe3_docx    = False
    make_pe3_pdf     = False
    make_sp_csv      = False
    optmz_mfrnames   = False
    optmz_restol5to1 = False

    #параметры
    output_name_enclosure = kwargs.get('output_name_enclosure', [' ', ' '])
    output_name_prefix    = kwargs.get('output_name_prefix', '')
    output_name_postfix   = kwargs.get('output_name_postfix', '')
    output    = kwargs.get('output', [OutputID.ALL.value])   #какие документы создавать
    if OutputID.ALL.value      in output: output = [OutputID.CL_XLSX.value, OutputID.PE3_DOCX.value, OutputID.PE3_PDF.value, OutputID.SP_CSV.value]
    if OutputID.NONE.value     in output: output = []
    if OutputID.CL_XLSX.value  in output: make_cl_xlsx  = True
    if OutputID.PE3_DOCX.value in output: make_pe3_docx = True
    if OutputID.PE3_PDF.value  in output: make_pe3_pdf  = True
    if OutputID.SP_CSV.value   in output: make_sp_csv   = True
    optimize  = kwargs.get('optimize', OptimizationID.NONE.value)   #какие оптимизации выполнять
    if OptimizationID.ALL.value        in optimize: optimize = [OptimizationID.MFRNAMES.value, OptimizationID.RESTOL5TO1.value]
    if OptimizationID.NONE.value       in optimize: optimize = []
    if OptimizationID.MFRNAMES.value   in optimize: optmz_mfrnames   = True
    if OptimizationID.RESTOL5TO1.value in optimize: optmz_restol5to1 = True

    make_cl  = make_cl_xlsx
    make_pe3 = make_pe3_docx or make_pe3_pdf
    make_sp  = make_sp_csv

    print('')
    print(('INFO >> Processing BoM: "' + os.path.basename(address) + '" ').ljust(80, '-'))

    #рабочая папка
    if output_directory is None: output_directory = os.path.dirname(address)

    #импорт BoM
    print("INFO >> Importing BoM:")
    bom = import_bom.importz(address, prefix = output_name_prefix, postfix = output_name_postfix)
    print('')

    #создаём базу данных компонентов
    print("INFO >> Creating components database using designer's parser:")
    components = typedef_components.Components_typeDef()                    #создаём объект базы
    parse.parse_components(components, bom)                                 #отдаём разработчику BoM чтобы он заполнил базу данных
    print("INFO >> Sorting components database.")
    components.sort()                                                       #сортируем элементы базы данных (методом по-умолчанию)

    #заменяем имена производителей
    if optmz_mfrnames:
        print("INFO >> Optimizing manufacturers names:")
        optimize_mfrNames.optimize(components)
    
    #оптимизируем номиналы резисторов по точности
    if optmz_restol5to1:
        print("INFO >> Optimizing resistors tolerances:")
        optimize_restol5to1.optimize(components)

    #создание списка компонентов
    if make_cl:
        print('')
        print("INFO >> Building cl:")
        cl = build_cl.build(components,
                                locale_index                            = LocaleIndex.RU.value,
                                #title_book                             = 'Список компонентов', 
                                #title_list_components                  = 'Список компонентов',
                                #title_list_substitutes                 = 'Допустимые замены',
                                sorting_method                          = 'params',
                                sorting_reverse                         = False,
                                assemble_kind                           = False, #пересобирать тип элемента
                                format_kind_capitalize                  = True,  #типы элементов с заглавной буквы
                                assemble_description                    = False, #пересобирать описание (все аргументы ниже относятся к этому сборщику)
                                content_param_basic                     = True,
                                content_param_misc                      = True,
                                format_param_enclosure                  = ['', ''],
                                format_param_decimalPoint               = '.',
                                format_param_rangeSymbol                = '\u2026',
                                format_param_delimiter                  = ', ',
                                format_param_unit_enclosure             = ['', ''],
                                format_param_multivalue_delimiter       = '/',
                                format_param_tolerance_enclosure        = ['\xa0', ''],
                                format_param_tolerance_signDelimiter    = '',
                                format_param_conditions_enclosure       = ['\xa0[', ']'],
                                format_param_conditions_delimiter       = '; ',
                                format_param_temperature_positiveSign   = True)
    #экспорт СК в xlsx
    if make_cl_xlsx:
        print('')
        print("INFO >> Exporting cl as xlsx:")
        file_name = (bom.prefix + output_name_enclosure[0] + 'СК' + output_name_enclosure[1] + bom.postfix).strip() + os.extsep + 'xlsx'
        export_cl_xlsx.export([cl], os.path.join(output_directory, file_name),
                              locale_index = LocaleIndex.RU.value)

    #создание спецификации
    if make_sp:
        #изменяем данные основной надписи для спецификации
        sp_titleBlock = copy.deepcopy(titleBlock)
        #sp_titleBlock.tb01a_DocumentName = ''
        sp_titleBlock.tb01b_DocumentType = 'Спецификация'
        #sp_titleBlock.tb02_DocumentDesignator = ''
        #sp_titleBlock.tb04_Letter_left = ''
        #sp_titleBlock.tb04_Letter_middle = ''
        #sp_titleBlock.tb04_Letter_right = ''
        sp_titleBlock.tb07_SheetIndex = ''
        sp_titleBlock.tb08_SheetsTotal = ''
        #sp_titleBlock.tb09_Organization = ''
        sp_titleBlock.tb10d_ActivityType_Extra = ''
        #sp_titleBlock.tb11a_Name_Designer = ''
        #sp_titleBlock.tb11b_Name_Checker = ''
        sp_titleBlock.tb11c_Name_TechnicalSupervisor = ''
        sp_titleBlock.tb11d_Name_Extra = ''
        #sp_titleBlock.tb11e_Name_NormativeSupervisor = ''
        #sp_titleBlock.tb11f_Name_Approver = ''
        sp_titleBlock.tb13a_SignatureDate_Designer = ''
        sp_titleBlock.tb13b_SignatureDate_Checker = ''
        sp_titleBlock.tb13c_SignatureDate_TechnicalSupervisor = ''
        sp_titleBlock.tb13d_SignatureDate_Extra = ''
        sp_titleBlock.tb13e_SignatureDate_NormativeSupervisor = ''
        sp_titleBlock.tb13f_SignatureDate_Approver = ''
        sp_titleBlock.tb19_OriginalInventoryNumber = ''
        sp_titleBlock.tb21_ReplacedOriginalInventoryNumber = ''
        sp_titleBlock.tb22_DuplicateInventoryNumber = ''
        #sp_titleBlock.tb24_BaseDocumentDesignator = ''
        #sp_titleBlock.tb25_FirstReferenceDocumentDesignator = ''

        print('')
        print("INFO >> Building sp:")
        sp = build_sp.build([components, sp_titleBlock],
                                locale_index                            = LocaleIndex.RU.value,
                                content_value                           = True,
                                content_value_value                     = True,
                                content_value_explicit                  = False,
                                content_mfr                             = True,
                                content_mfr_value                       = True,
                                content_param                           = True,
                                content_param_basic                     = True,
                                content_param_misc                      = True,
                                content_subst                           = True,
                                content_subst_value                     = True,
                                content_subst_manufacturer              = True,
                                content_subst_note                      = True,
                                format_value_enclosure                  = ['', ''],
                                format_mfr_enclosure                    = [' ф.\xa0', ''],
                                format_param_enclosure                  = [' (', ')'],
                                format_param_decimalPoint               = ',',
                                format_param_rangeSymbol                = '\xa0\u2026\xa0',
                                format_param_delimiter                  = ' \u2013 ',
                                format_param_unit_enclosure             = ['\xa0', ''],
                                format_param_multivalue_delimiter       = '\xa0/\xa0',
                                format_param_tolerance_enclosure        = ['\xa0', ''],
                                format_param_tolerance_signDelimiter    = '\xa0',
                                format_param_conditions_enclosure       = ['\xa0(', ')'],
                                format_param_conditions_delimiter       = '; ',
                                format_param_temperature_positiveSign   = True,
                                format_subst_enclosure                  = ['', ''],
                                format_subst_entry_enclosure            = ['доп.\xa0замена ', ''],
                                format_subst_value_enclosure            = ['', ''],
                                format_subst_manufacturer_enclosure     = [' ф.\xa0', ''],
                                format_subst_note_enclosure             = [' (', ')'])

    #экспорт спецификации в CSV
    if make_sp_csv:
        print('')
        print("INFO >> Exporting sp as CSV:")
        file_name = (bom.prefix + output_name_enclosure[0] + 'СП' + output_name_enclosure[1] + bom.postfix).strip() + os.extsep + 'csv'
        export_sp_csv.export(sp, os.path.join(output_directory, file_name))

    #создание перечня элементов
    if make_pe3:
        #изменяем данные основной надписи для перечня элементов
        pe3_titleBlock = copy.deepcopy(titleBlock)
        #pe3_titleBlock.tb01a_DocumentName = ''
        pe3_titleBlock.tb01b_DocumentType = 'Перечень элементов'
        pe3_titleBlock.tb02_DocumentDesignator += " ПЭ3"
        #pe3_titleBlock.tb04_Letter_left = ''
        #pe3_titleBlock.tb04_Letter_middle = ''
        #pe3_titleBlock.tb04_Letter_right = ''
        pe3_titleBlock.tb07_SheetIndex = ''
        pe3_titleBlock.tb08_SheetsTotal = ''
        #pe3_titleBlock.tb09_Organization = ''
        pe3_titleBlock.tb10d_ActivityType_Extra = ''
        #pe3_titleBlock.tb11a_Name_Designer = ''
        #pe3_titleBlock.tb11b_Name_Checker = ''
        pe3_titleBlock.tb11c_Name_TechnicalSupervisor = ''
        pe3_titleBlock.tb11d_Name_Extra = ''
        #pe3_titleBlock.tb11e_Name_NormativeSupervisor = ''
        #pe3_titleBlock.tb11f_Name_Approver = ''
        pe3_titleBlock.tb13a_SignatureDate_Designer = ''
        pe3_titleBlock.tb13b_SignatureDate_Checker = ''
        pe3_titleBlock.tb13c_SignatureDate_TechnicalSupervisor = ''
        pe3_titleBlock.tb13d_SignatureDate_Extra = ''
        pe3_titleBlock.tb13e_SignatureDate_NormativeSupervisor = ''
        pe3_titleBlock.tb13f_SignatureDate_Approver = ''
        pe3_titleBlock.tb19_OriginalInventoryNumber = ''
        pe3_titleBlock.tb21_ReplacedOriginalInventoryNumber = ''
        pe3_titleBlock.tb22_DuplicateInventoryNumber = ''
        #pe3_titleBlock.tb24_BaseDocumentDesignator = ''
        #pe3_titleBlock.tb25_FirstReferenceDocumentDesignator = ''

    #экспорт ПЭ3 в docx
    if make_pe3_docx:
        #создание перечня элементов для docx
        print('')
        print("INFO >> Building pe3:")
        pe3 = build_pe3.build([components, pe3_titleBlock],
                                locale_index                            = LocaleIndex.RU.value,
                                content_value                           = True,
                                content_value_value                     = True,
                                content_value_explicit                  = False,
                                content_mfr                             = True,
                                content_mfr_value                       = True,
                                content_param                           = True,
                                content_param_basic                     = True,
                                content_param_misc                      = True,
                                content_subst                           = True,
                                content_subst_value                     = True,
                                content_subst_manufacturer              = True,
                                content_subst_note                      = True,
                                format_value_enclosure                  = ['', ''],
                                format_mfr_enclosure                    = [' ф.\xa0', ''],
                                format_param_enclosure                  = [' (', ')'],
                                format_param_decimalPoint               = ',',
                                format_param_rangeSymbol                = '\xa0\u2026\xa0',
                                format_param_delimiter                  = ' \u2013 ',
                                format_param_unit_enclosure             = ['\xa0', ''],
                                format_param_multivalue_delimiter       = '\xa0/\xa0',
                                format_param_tolerance_enclosure        = ['\xa0', ''],
                                format_param_tolerance_signDelimiter    = '\xa0',
                                format_param_conditions_enclosure       = ['\xa0(', ')'],
                                format_param_conditions_delimiter       = '; ',
                                format_param_temperature_positiveSign   = True,
                                format_subst_enclosure                  = ['', ''],
                                format_subst_entry_enclosure            = ['доп.\xa0замена ', ''],
                                format_subst_value_enclosure            = ['', ''],
                                format_subst_manufacturer_enclosure     = [' ф.\xa0', ''],
                                format_subst_note_enclosure             = [' (', ')'])
        #экспорт
        print('')
        print("INFO >> Exporting pe3 as docx:")
        file_name = (bom.prefix + output_name_enclosure[0] + 'ПЭ3' + output_name_enclosure[1] + bom.postfix).strip() + os.extsep + 'docx'
        export_pe3_docx.export(pe3, os.path.join(output_directory, file_name), wrapDesignator = False, reSplitLabel = ' \u2013')

    #экспорт ПЭ3 в pdf
    if make_pe3_pdf:
        #создание перечня элементов для pdf
        print('')
        print("INFO >> Building pe3:")
        pe3 = build_pe3.build([components, pe3_titleBlock],
                                locale_index                            = LocaleIndex.RU.value,
                                content_value                           = True,
                                content_value_value                     = True,
                                content_value_explicit                  = False,
                                content_mfr                             = True,
                                content_mfr_value                       = True,
                                content_param                           = True,
                                content_param_basic                     = True,
                                content_param_misc                      = True,
                                content_subst                           = True,
                                content_subst_value                     = True,
                                content_subst_manufacturer              = True,
                                content_subst_note                      = True,
                                format_value_enclosure                  = ['', ''],
                                format_mfr_enclosure                    = [' ф.\xa0', ''],
                                format_param_enclosure                  = [' (', ')'],
                                format_param_decimalPoint               = '.',
                                format_param_rangeSymbol                = '\u2026',
                                format_param_delimiter                  = ', ',
                                format_param_unit_enclosure             = ['', ''],
                                format_param_multivalue_delimiter       = '/',
                                format_param_tolerance_enclosure        = ['\xa0', ''],
                                format_param_tolerance_signDelimiter    = '',
                                format_param_conditions_enclosure       = ['\xa0[', ']'],
                                format_param_conditions_delimiter       = '; ',
                                format_param_temperature_positiveSign   = True,
                                format_subst_enclosure                  = ['', ''],
                                format_subst_entry_enclosure            = ['\nдоп.\xa0замена ', ''],
                                format_subst_value_enclosure            = ['', ''],
                                format_subst_manufacturer_enclosure     = [' ф.\xa0', ''],
                                format_subst_note_enclosure             = [' (', ')'])
        #экспорт
        print('')
        print("INFO >> Exporting pe3 as PDF:")
        file_name = (bom.prefix + output_name_enclosure[0] + 'ПЭ3' + output_name_enclosure[1] + bom.postfix).strip() + os.extsep + 'pdf'
        export_pe3_pdf.export(pe3, os.path.join(output_directory, file_name))

    print((' ' * 8).ljust(80, '='))

#===================================================== END Specific functions =====================================================


#---------------------------------------------------------- Execution -------------------------------------------------------------

#prevent launch when importing
if __name__ == "__main__":
    #catching all errors to display error info and prevent terminal from closing 
    if True:
    #try:
        #specify custom parameters to function call
        inputfiles = []                                                         #input files
        output_directory = None                                                 #output directory
        params = {#'output':                OutputID.ALL.value,                 #какие файлы делать: [OutputID.CL_XLSX.value, OutputID.PE3_DOCX.value, OutputID.PE3_PDF.value, OutputID.SP_CSV.value] или OutputID.ALL
                  #'noquestions':           False                               #ничего не спрашивать при выполнении программы, при возникновении вопросов делать по-умолчанию
                  #'output_name_enclosure': [' ', ' ']                          #заключение для типа документа в имени выходного файла
                  #'output_name_prefix':    ''                                  #префикс имени выходного файла
                  #'output_name_postfix':   ''                                  #суффикс имени выходного файла
        }

        #checking launch from IDE - insert predetermined data files and options for debug into arguments
        #DEBUG->
        if '--debug' in sys.argv:
            sys.argv.remove('--debug')
            #input_basepath = ''
            #input_files = []
            #input_files.append(os.path.join(input_basepath, 'test\\project\\test project.PrjPcb'))
            #sys.argv.extend(input_files)
            #sys.argv.append('--adproject')
            #sys.argv.extend(['--output', 'pe3-docx'])
            #sys.argv.extend(['--optimize', 'all'])
            #sys.argv.append('--noquestions')
            #sys.argv.append('--nohalt')
        #<-DEBUG

        #parse arguments
        parser = argparse.ArgumentParser(description='BoM converter v' + script_version + ' (' + script_date.strftime('%Y-%m-%d') + ') by Alexander Taluts')
        parser.add_argument('inputfiles',                          nargs='+', metavar='data-file',    help='input files to process')
        parser.add_argument('--adproject',          action='store_true',                              help='input files are Altium Designer project')
        parser.add_argument('--titleblock',         type=str,                 metavar='file',         help='file with title block data')
        parser.add_argument('--output-dir',                                   metavar='path',         help='output directory')
        parser.add_argument('--output',             type=str,      nargs='+', action='extend',        help='which output to produce',  choices=[OutputID.CL_XLSX.value, OutputID.PE3_DOCX.value, OutputID.PE3_PDF.value, OutputID.SP_CSV.value, OutputID.ALL.value, OutputID.NONE.value])
        parser.add_argument('--optimize',           type=str,      nargs='+', action='extend',        help='which optimization to perform',  choices=[OptimizationID.MFRNAMES.value, OptimizationID.RESTOL5TO1.value, OptimizationID.ALL.value, OptimizationID.NONE.value])
        parser.add_argument('--noquestions',        action='store_true',                              help='do not ask questions')
        parser.add_argument('--nohalt',             action='store_true',                              help='do not halt terminal')
        args = parser.parse_args()

        #take input data files and options from arguments
        inputfiles = args.inputfiles
        if args.output_dir is not None: output_directory = args.output_dir
        if args.output is not None: params['output'] = args.output
        if args.optimize is not None: params['optimize'] = args.optimize
        params['noquestions'] = args.noquestions
 
        #process data
        print('')
        print('INFO >> BoM converter v' + script_version + ' (' + script_date.strftime('%Y-%m-%d') + ') by Alexander Taluts')
        print('')
        for file in inputfiles:
            if args.adproject is True or os.path.splitext(file)[1].lstrip(os.extsep) == 'PrjPcb':
                process_adproject(file, output_directory, **params)
            else:
                process_bom(file, None, output_directory, **params)
        print('')
        print("INFO >> Job done.")

        if not args.nohalt:
            print('')
            input("Press any key to exit...")

    #except Exception as err:
    #    print("ERROR >>", err)
    #    exit()

#========================================================= END Execution ===========================================================