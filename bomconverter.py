import sys
import argparse
import os
import copy
import datetime
import re
import enum
from string import Template
from pathlib import Path

from typedef_adproject import ADProject #класс проекта Altium Designer
import typedef_bom                      #класс BoM
import typedef_components as Components #класс базы данных компонентов

import lib_common                       #библиотека с общими функциями
import import_bom_csv as import_bom     #импорт данных из Bill of Materials
import import_pnp_csv as import_pnp     #импорт данных из Pick and Place
import optimize_mfr_name                #оптимизация имени производителя
import optimize_res_tol                 #оптимизация номиналов резисторов по точности
import optimize_pnp_fp                  #оптимизация посадочных мест в файле установщика
import build_cl                         #сборка списка компонентов
import build_pe3                        #сборка перечня элементов
import build_sp                         #сборка спецификации
import build_pnp                        #сборка файла установщика
import export_cl_xlsx                   #экспорт списка компонентов в Excel
import export_pe3_docx                  #экспорт перечня элементов в Word
import export_pe3_pdf                   #экспорт перечня элементов в PDF
import export_pe3_csv                   #экспорт перечня элементов в CSV
import export_sp_csv                    #экспорт спецификации в CSV
import export_pnp_csv                   #экспорт файла установщика в CSV
import export_pnp_txt                   #экспорт файла установщика в текстовой таблице

_module_dirname = os.path.dirname(__file__)                     #адрес папки со скриптом
_module_date    = datetime.datetime(2025, 12, 11)
_halt_on_exit   = True
_debug          = False

#-------------------------------------------------------- Class definitions ---------------------------------------------------------

#Коды выходных файлов
class OutputID(enum.Enum):
    ALL      = 'all'        #все
    CL_XLSX  = 'cl-xlsx'    #список компонентов в Excel
    PE3_DOCX = 'pe3-docx'   #перечень элементов в Word
    PE3_PDF  = 'pe3-pdf'    #перечень элементов в PDF
    PE3_CSV  = 'pe3-csv'    #перечень элементов в CSV
    SP_CSV   = 'sp-csv'     #cпецификация в CSV
    PNP_CSV  = 'pnp-csv'    #файл установщика в CSV
    PNP_TXT  = 'pnp-txt'    #файл установщика в текстовой таблице
    NONE     = 'none'       #никакие

#Коды оптимизаций
class OptimizationID(enum.Enum):
    ALL       = 'all'       #все
    MFR_NAMES = 'mfr-name'  #названия производителей
    RES_TOL   = 'res-tol'   #допуски резисторов
    PNP_FP    = 'pnp-fp'    #посадочные места установщика
    NONE      = 'none'      #никакие

#====================================================== END Class definitions =======================================================

#-------------------------------------------------------- Specific functions --------------------------------------------------------

#обрабатываем файл проекта Altium
def process_adproject(adproject_path:Path, pnp_path:Path = None, titleblock:Path|dict = None, output_directory:Path = None, parser = None, settings = None, **kwargs):
    print((f'INFO >> Processing Altium Designer project: "{adproject_path.name}" ').ljust(80, '-'))

    #получаем параметры
    noquestions = kwargs.get('noquestions',  False)

    #загружаем настройки
    settings = lib_common.import_settings(settings)
    if 'bomconverter' in settings: settings = settings['bomconverter']

    #загружаем анализатор данных (приоритет выбора значения: из аргумента -> из настроек -> по-умолчанию)
    if parser is None: parser = settings.get('parse', {}).get('parser', None)
    parser = lib_common.import_parser(parser)

    #загружаем данные основной надписи для обновления той что в проекте
    titleblock_upd = lib_common.import_titleblock(titleblock)

    #импорт проекта Altium Designer
    print("INFO >> Importing project", end ="... ", flush = True)
    params = settings.get('input', {}).get('adproject', {})
    project = ADProject(adproject_path)
    project.read(**params)
    print(f"done. ({len(project.sourceFiles)} source files, {len(project.generatedFiles)} generated files, {len(project.variants)} variants)")

    #отдаём разработчику проект чтобы он заполнил его параметры
    print("INFO >> Filling project data using designer's parser:")
    params = settings.get('parse', {}).get('project', {})
    parser.parse_project(project, **params)

    #справшиваем какие BoM обрабатывать если их больше одного
    print('INFO >> BoMs found: ' + str(len(project.BoMDoc)))
    for i in range(len(project.BoMDoc)):
        print(f'{" " * 12}{str(i + 1).rjust(2)}: "{project.BoMDoc[i].address.name}" / "{project.BoMDoc[i].variant or ""}"')
    activeBomIndexes = []
    if len(project.BoMDoc) == 1 or noquestions:
        activeBomIndexes = list(range(len(project.BoMDoc)))
    elif len(project.BoMDoc) > 1:
        answer_valid = False
        #запрашиваем данные пока нет правильного ответа 
        while not answer_valid:
            answer = input("REQUEST >> Choose which BoMs to process (0 or <empty> for all, q for abort): ")
            if answer == 'q': exit(3)
            elif answer == '0' or answer == '':
                activeBomIndexes = list(range(len(project.BoMDoc)))
                answer_valid = True
            else:
                for idx in filter(None, re.split('[ ,.]', answer)):
                    if idx.isdigit():
                        index = int(idx) - 1
                        if index >= 0 and index < len(project.BoMDoc):
                            activeBomIndexes.append(index)
                            answer_valid = True
                    else:
                        answer_valid = False
                        break
            if not answer_valid: print("REQUEST >> error: invalid indexes.")
        activeBomIndexes = list(set(activeBomIndexes))   #убираем дубликаты
    print("INFO >> BoM files to process: " + str(len(activeBomIndexes)))

    #определяем активный PnP файл (!!!TODO: написать выбор файла пользователем)
    if pnp_path is None:
        #не задан явно -> ищем в проекте
        if len(project.PnPDoc) > 0:
            # 1. привязан к плате, нет ни конфигурации ни обрамления (идеальный вариант)
            for file in project.PnPDoc:
                if file.PcbDoc is not None and file.variant is None and file.variant_enclosure is None:
                    pnp_path = file.address
                    break
            # 2. привязан к плате и есть реальная конфигурация
            if pnp_path is None:
                for file in project.PnPDoc:
                    if file.PcbDoc is not None and file.variant is not None:
                        pnp_path = file.address
                        break
            # 3. берём первый в списке
            if pnp_path is None:
                pnp_path = project.PnPDoc[0].address
    #получаем абсолютный путь к PnP файлу
    if pnp_path is not None:
        pnp_path = project.directory / pnp_path

    #добавляем данные основной надписи из внешнего модуля в словарь из проекта
    titleblock = copy.deepcopy(project.titleblock)
    if titleblock_upd is not None:
        if titleblock is not None:
            if not isinstance(titleblock_upd, dict): raise ValueError("Invalid titleblock to update from.")
            for key, value in titleblock_upd.items():
                if isinstance(value, (tuple, list)):
                    #если тип значения 'tuple' или 'list' то собираем из него строку и добавляем её к уже имеющейся в полученных данных
                    value = ''.join(value)
                    if key in titleblock:
                        titleblock[key] += value
                        continue
                titleblock[key] = value
        else:
            titleblock = titleblock_upd

    #обрабатываем все выбранные BoM из проекта
    for i in activeBomIndexes:
        postfix = project.BoMDoc[i].variant_enclosure[0] + project.BoMDoc[i].variant + project.BoMDoc[i].variant_enclosure[1]
        process_bom(project.directory / project.BoMDoc[i].address, pnp_path, titleblock, output_directory, project.designator, postfix, parser, settings, **kwargs)

    print((' ' * 8).ljust(80, '='))

#обрабатываем BoM файлы
def process_bom(bom_path:Path, pnp_path:Path = None, titleblock:Path|dict = None, output_directory:Path = None, output_basename = None, output_postfix = None, parser = None, settings = None, **kwargs):
    print('')
    print((f'INFO >> Processing BoM: "{bom_path.name}" ').ljust(80, '-'))

    #загружаем настройки
    settings = lib_common.import_settings(settings)
    if 'bomconverter' in settings: settings = settings['bomconverter']

    #загружаем анализатор данных (приоритет выбора значения: из аргумента -> из настроек -> по-умолчанию)
    if parser is None: parser = settings.get('parse', {}).get('parser', None)
    parser = lib_common.import_parser(parser)
    
    #загружаем данные основной надписи
    titleblock = lib_common.import_titleblock(titleblock)

    #какие документы создавать (приоритет выбора значения: из аргумента -> из настроек -> по-умолчанию)
    make_cl_xlsx  = settings.get('output', {}).get('cl-xlsx',  {}).get('enabled', True)
    make_pe3_docx = settings.get('output', {}).get('pe3-docx', {}).get('enabled', True)
    make_pe3_pdf  = settings.get('output', {}).get('pe3-pdf',  {}).get('enabled', True)
    make_pe3_csv  = settings.get('output', {}).get('pe3-csv',  {}).get('enabled', True)
    make_sp_csv   = settings.get('output', {}).get('sp-csv',   {}).get('enabled', True)
    make_pnp_csv  = settings.get('output', {}).get('pnp-csv',  {}).get('enabled', True)
    make_pnp_csv  = settings.get('output', {}).get('pnp-txt',  {}).get('enabled', True)
    output        = kwargs.get('output')
    if output is not None:
        if   OutputID.ALL.value    in output: output = [member.value for member in OutputID]
        elif OutputID.NONE.value   in output: output = []
        make_cl_xlsx  = OutputID.CL_XLSX.value  in output
        make_pe3_docx = OutputID.PE3_DOCX.value in output
        make_pe3_pdf  = OutputID.PE3_PDF.value  in output
        make_pe3_csv  = OutputID.PE3_CSV.value  in output
        make_sp_csv   = OutputID.SP_CSV.value   in output
        make_pnp_csv  = OutputID.PNP_CSV.value  in output
        make_pnp_txt  = OutputID.PNP_TXT.value  in output

    #проверяем наличие данных для PnP документов
    if make_pnp_csv or make_pnp_txt:
        if pnp_path is None:
            print(f"WARNING >> PnP outputs are enabled but no PnP file provided. Disabling PnP outputs.")
            make_pnp_csv = False
            make_pnp_txt = False

    #какие оптимизации проводить (приоритет выбора значения: из аргумента -> из настроек -> по-умолчанию)
    optmz_mfr_name = settings.get('optimize', {}).get('mfr-name', {}).get('enabled', False)
    optmz_res_tol  = settings.get('optimize', {}).get('res-tol', {}).get('enabled', False)
    optmz_pnp_fp   = settings.get('optimize', {}).get('pnp-fp', {}).get('enabled', False)
    optimize       = kwargs.get('optimize')
    if optimize is not None:
        if   OptimizationID.ALL.value    in optimize: optimize = [member.value for member in OptimizationID]
        elif OptimizationID.NONE.value   in optimize: optimize = []
        optmz_mfr_name = OptimizationID.MFR_NAMES.value in optimize
        optmz_res_tol  = OptimizationID.RES_TOL.value   in optimize
        optmz_pnp_fp   = OptimizationID.PNP_FP.value    in optimize

    #если нет PnP документов то отключаем соответствующие оптимизации
    if optmz_pnp_fp:
        if not make_pnp_csv and not make_pnp_txt:
            optmz_pnp_fp = False

    #имена файлов и папок
    if output_directory is None:
        output_directory_cl  = bom_path.parent
        output_directory_pe3 = bom_path.parent
        output_directory_sp  = bom_path.parent
        output_directory_pnp = pnp_path.parent if pnp_path is not None else None
    else:
        output_directory_cl  = output_directory
        output_directory_pe3 = output_directory
        output_directory_sp  = output_directory
        output_directory_pnp = output_directory if pnp_path is not None else None
    if output_basename is None: output_basename = bom_path.stem
    if output_postfix is None: output_postfix = ''

    #импорт BoM
    print("INFO >> Importing BoM:")
    params = settings.get('input', {}).get('bom-csv', {})
    bom = import_bom.importz(bom_path, **params)
    print('')

    #создаём базу данных компонентов
    print("INFO >> Creating components database using designer's parser:")
    params = settings.get('parse', {}).get('bom', {})
    database = Components.Database()                                        #создаём объект базы данных с компонентами
    parser.parse_bom(database, bom, **params)                               #отдаём разработчику BoM чтобы он заполнил базу данных

    #проверяем базу данных компонентов
    print("INFO >> Checking components database.")
    params = settings.get('parse', {}).get('check', {})
    database.complaints.add(parser.check(database, **params))               #проверяем методами разработчика
    database.complaints.add(database.check())                               #проверяем методами системы
    if database.complaints.critical > 0:
        print("ERROR >> further execution halted due to critical errors in the database.")
        raise RuntimeError("Input data may cause a program crash or corrupted output.")

    print("INFO >> Sorting components database.")
    database.sort()                                                         #сортируем элементы базы данных (методом по-умолчанию)

    #импорт PnP
    if make_pnp_csv or make_pnp_txt:
        print("INFO >> Importing PnP:")
        params = settings.get('input', {}).get('pnp-csv', {})
        base_pnp = import_pnp.importz(pnp_path, **params)
        print('')
    else:
        base_pnp = None

    #оптимизируем имена производителей
    if optmz_mfr_name:
        print("INFO >> Optimizing manufacturers names:")
        params = settings.get('optimize', {}).get('mfr-name', {})
        optimize_mfr_name.optimize(database, **params)
    
    #оптимизируем номиналы резисторов по точности
    if optmz_res_tol:
        print("INFO >> Optimizing resistors tolerances:")
        params = settings.get('optimize', {}).get('res-tol', {})
        optimize_res_tol.optimize(database, **params)

    #оптимизируем посадочные места для установщика компонентов
    if optmz_pnp_fp:
        print("INFO >> Optimizing pnp footprints:")
        params = settings.get('optimize', {}).get('pnp-fp', {})
        optimize_pnp_fp.optimize(base_pnp, **params)

    #список компонентов в xlsx
    if make_cl_xlsx:
        print('')
        print("INFO >> Building cl:")
        params = settings.get('output', {}).get('cl-xlsx', {}).get('build', {})
        cl = build_cl.build(database, **params)
        print('')
        print("INFO >> Exporting cl as xlsx:")
        file_name_template = Template(settings.get('output', {}).get('cl-xlsx', {}).get('filename', "$basename СК $postfix" + os.extsep + "xlsx"))
        file_name = os.path.splitext(file_name_template.substitute(basename = output_basename, postfix = output_postfix))
        file_name = Path(file_name[0].strip() + file_name[1])
        params = settings.get('output', {}).get('cl-xlsx', {}).get('export', {})
        export_cl_xlsx.export([cl], output_directory_cl / file_name, **params)

    #перечень элементов в docx
    if make_pe3_docx:
        print('')
        print("INFO >> Building pe3:")
        params = settings.get('output', {}).get('pe3-docx', {}).get('build', {})
        pe3 = build_pe3.build([database, titleblock], **params)
        print('')
        print("INFO >> Exporting pe3 as docx:")
        file_name_template = Template(settings.get('output', {}).get('pe3-docx', {}).get('filename', "$basename ПЭ3 $postfix" + os.extsep + "docx"))
        file_name = os.path.splitext(file_name_template.substitute(basename = output_basename, postfix = output_postfix))
        file_name = Path(file_name[0].strip() + file_name[1])
        params = settings.get('output', {}).get('pe3-docx', {}).get('export', {})
        export_pe3_docx.export(pe3, output_directory_pe3 / file_name, **params)

    #перечень элементов в pdf
    if make_pe3_pdf:
        print('')
        print("INFO >> Building pe3:")
        params = settings.get('output', {}).get('pe3-pdf', {}).get('build', {})
        pe3 = build_pe3.build([database, titleblock], **params)
        print('')
        print("INFO >> Exporting pe3 as PDF:")
        file_name_template = Template(settings.get('output', {}).get('pe3-pdf', {}).get('filename', "$basename ПЭ3 $postfix" + os.extsep + "pdf"))
        file_name = os.path.splitext(file_name_template.substitute(basename = output_basename, postfix = output_postfix))
        file_name = Path(file_name[0].strip() + file_name[1])
        params = settings.get('output', {}).get('pe3-pdf', {}).get('export', {})
        export_pe3_pdf.export(pe3, output_directory_pe3 / file_name, **params)

    #перечень элементов в csv
    if make_pe3_csv:
        print('')
        print("INFO >> Building pe3:")
        params = settings.get('output', {}).get('pe3-csv', {}).get('build', {})
        pe3 = build_pe3.build([database, None], **params)
        print('')
        print("INFO >> Exporting pe3 as CSV:")
        file_name_template = Template(settings.get('output', {}).get('pe3-csv', {}).get('filename', "$basename ПЭ3 $postfix" + os.extsep + "csv"))
        file_name = os.path.splitext(file_name_template.substitute(basename = output_basename, postfix = output_postfix))
        file_name = Path(file_name[0].strip() + file_name[1])
        params = settings.get('output', {}).get('pe3-csv', {}).get('export', {})
        export_pe3_csv.export(pe3, output_directory_pe3 / file_name, **params)

    #спецификация в csv
    if make_sp_csv:
        print('')
        print("INFO >> Building sp:")
        params = settings.get('output', {}).get('sp-csv', {}).get('build', {})
        sp = build_sp.build([database, titleblock], **params)
        print('')
        print("INFO >> Exporting sp as CSV:")
        file_name_template = Template(settings.get('output', {}).get('sp-csv', {}).get('filename', "$basename СП $postfix" + os.extsep + "csv"))
        file_name = os.path.splitext(file_name_template.substitute(basename = output_basename, postfix = output_postfix))
        file_name = Path(file_name[0].strip() + file_name[1])
        params = settings.get('output', {}).get('sp-csv', {}).get('export', {})
        export_sp_csv.export(sp, output_directory_sp / file_name, **params)

    #файл установщика в csv
    if make_pnp_csv:
        print('')
        print("INFO >> Building pnp:")
        params = settings.get('output', {}).get('pnp-csv', {}).get('build', {})
        pnp = build_pnp.build([database, base_pnp], **params)
        print('')
        print("INFO >> Exporting pnp as CSV:")
        file_name_template = Template(settings.get('output', {}).get('pnp-csv', {}).get('filename', "$basename PnP $postfix" + os.extsep + "csv"))
        file_name = os.path.splitext(file_name_template.substitute(basename = output_basename, postfix = output_postfix))
        file_name = Path(file_name[0].strip() + file_name[1])
        params = settings.get('output', {}).get('pnp-csv', {}).get('export', {})
        export_pnp_csv.export(pnp, output_directory_pnp / file_name, **params)

    #файл установщика в txt
    if make_pnp_txt:
        print('')
        print("INFO >> Building pnp:")
        params = settings.get('output', {}).get('pnp-txt', {}).get('build', {})
        pnp = build_pnp.build([database, base_pnp], **params)
        print('')
        print("INFO >> Exporting pnp as TXT:")
        file_name_template = Template(settings.get('output', {}).get('pnp-txt', {}).get('filename', "$basename PnP $postfix" + os.extsep + "txt"))
        file_name = os.path.splitext(file_name_template.substitute(basename = output_basename, postfix = output_postfix))
        file_name = Path(file_name[0].strip() + file_name[1])
        params = settings.get('output', {}).get('pnp-txt', {}).get('export', {})
        export_pnp_txt.export(pnp, output_directory_pnp / file_name, **params)

    print((' ' * 8).ljust(80, '='))

#===================================================== END Specific functions =====================================================


#---------------------------------------------------------- Execution -------------------------------------------------------------

def main() -> None:
    #parse arguments
    argparser = argparse.ArgumentParser(description=f"BoM converter v. {_module_date.strftime('%Y-%m-%d')} by Alexander Taluts")
    argparser.add_argument('inputfiles',                          nargs='+',  metavar='data-file',   help='input files to process')
    argparser.add_argument('--adproject',          action='store_true',                              help='input files are Altium Designer project')
    argparser.add_argument('--titleblock',         type=Path,                 metavar='file',        help='path to dictionary with title block data')
    argparser.add_argument('--pnp',                type=Path,                 metavar='file',        help='path to dictionary with PnP footprints data')
    argparser.add_argument('--output-dir',         type=Path,                 metavar='path',        help='path to output directory')
    argparser.add_argument('--parser',             type=Path,                 metavar='file',        help='path to parser module')
    argparser.add_argument('--settings',           type=Path,                 metavar='file',        help='path to settings module')
    argparser.add_argument('--output',             type=str,       nargs='+', action='extend',       help='which output to produce',        choices=[member.value for member in OutputID])
    argparser.add_argument('--optimize',           type=str,       nargs='+', action='extend',       help='which optimization to perform',  choices=[member.value for member in OptimizationID])
    argparser.add_argument('--noquestions',        action='store_true',                              help='do not ask questions')
    argparser.add_argument('--nohalt',             action='store_true',                              help='do not halt terminal')
    args = argparser.parse_args()

    #take input data files and options from arguments
    params = {}
    if args.output is not None: params['output'] = args.output
    if args.optimize is not None: params['optimize'] = args.optimize
    if args.nohalt is not None: 
        global _halt_on_exit
        _halt_on_exit = False
    params['noquestions'] = args.noquestions

    #process data
    print('')
    print(f"INFO >> BoM converter v. {_module_date.strftime('%Y-%m-%d')} by Alexander Taluts")
    print('')
    for file in args.inputfiles:
        file = Path(file)
        if args.adproject is True or file.suffix.lstrip(os.extsep).casefold() == 'PrjPcb'.casefold():
            process_adproject(file, args.pnp, args.titleblock, args.output_dir, args.parser, args.settings, **params)
        else:
            process_bom(file, args.pnp, args.titleblock, args.output_dir, None, None, args.parser, args.settings, **params)
    print('')
    print("INFO >> Job done.")

#exit the program
def exit(code:int = 0) -> None:
    print("")
    if _halt_on_exit: input("Press any key to exit...")
    print("Exiting...")
    if code > 0 and _debug:
        print(f"DEBUG >> Exit code: {code}")
        sys.exit(0)
    else:
        sys.exit(code)

#Prevent launch when importing
if __name__ == "__main__":
    lib_common.wrap_stdout_utf8() #force output encoding to be utf-8

    exit_code = 0
    #checking launch from IDE
    if '--debug' in sys.argv:
        sys.argv.remove('--debug')
        _debug = True
        main()
    else:
        #catching all errors to display error info and prevent terminal from closing
        try:
            main()
        except Exception as e:
            exit_code = 1
            print(f"ERROR >> {e}")
            
    exit(exit_code)

#========================================================= END Execution ===========================================================