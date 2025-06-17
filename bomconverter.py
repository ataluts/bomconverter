import sys
import argparse
import os
import copy
import datetime
import re
import enum
import types
from string import Template

import typedef_bom                      #класс BoM
import typedef_components               #класс базы данных компонентов

import import_adproject                 #импорт данных проекта Altium Designer
import import_bom_csv as import_bom     #импорт данных из Bill of Materials
import optimize_mfr_name                #оптимизация имени производителя
import optimize_res_tol                 #оптимизация номиналов резисторов по точности
import build_cl                         #сборка списка компонентов
import build_pe3                        #сборка перечня элементов
import build_sp                         #сборка спецификации
import export_cl_xlsx                   #экспорт списка компонентов в Excel
import export_pe3_docx                  #экспорт перечня элементов в Word
import export_pe3_pdf                   #экспорт перечня элементов в PDF
import export_pe3_csv                   #экспорт перечня элементов в CSV
import export_sp_csv                    #экспорт спецификации в CSV
from dict_locale import LocaleIndex     #словарь с локализациями

_module_dirname = os.path.dirname(__file__)                     #адрес папки со скриптом
_module_version = '3.6'
_module_date    = datetime.datetime(2025, 6, 17)
_halt_on_exit   = True
_debug          = False

default_parser   = "parse_taluts.py"
default_settings = "dict_settings.py"

#-------------------------------------------------------- Class definitions ---------------------------------------------------------

class OutputID(enum.Enum):
    ALL      = 'all'
    CL_XLSX  = 'cl-xlsx'
    PE3_DOCX = 'pe3-docx'
    PE3_PDF  = 'pe3-pdf'
    PE3_CSV  = 'pe3-csv'
    SP_CSV   = 'sp-csv'
    NONE     = 'none'

class OptimizationID(enum.Enum):
    ALL       = 'all'
    MFR_NAMES = 'mfr-name'
    RES_TOL   = 'res-tol'
    NONE      = 'none'

#====================================================== END Class definitions =======================================================

# ------------------------------------------------------- Generic functions ---------------------------------------------------------
#Ensures sys.stdout and sys.stderr use UTF-8 encoding with safe wrapping, avoiding double-wrapping or breaking the buffer.
def wrap_stdout_utf8():
    import io
    def wrap(stream):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
                return stream
            except Exception:
                pass
        if isinstance(stream, io.TextIOWrapper) and hasattr(stream, "buffer"):
            try:
                return io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace")
            except Exception:
                pass
        return stream  # fallback to original if all else fails

    sys.stdout = wrap(sys.stdout)
    sys.stderr = wrap(sys.stderr)

#======================================================= END Generic functions ======================================================

#-------------------------------------------------------- Specific functions --------------------------------------------------------

#обрабатываем файл проекта Altium
def process_adproject(address, titleblock = None, output_directory = None, parser = None, settings = None, **kwargs):
    print(('INFO >> Processing AD project: "' + os.path.basename(address) + '" ').ljust(80, '-'))
    print(' ' * 12 + 'output: ' +  os.path.basename(address))

    #получаем параметры
    noquestions = kwargs.get('noquestions',  False)

    #загружаем настройки
    settings = _import_settings(settings)

    #загружаем анализатор данных (приоритет выбора значения: из аргумента -> из настроек -> по-умолчанию)
    if parser is None: parser = settings.get('parse', {}).get('parser', None)
    parser = _import_parser(parser)

    #загружаем данные основной надписи для обновления той что в проекте
    titleblock_upd = _import_titleblock(titleblock)

    #импорт проекта Altium Designer
    params = settings.get('input', {}).get('adproject', {})
    ADProject = import_adproject.importz(address, **params)
    print('')

    #отдаём разработчику проект чтобы он заполнил его параметры
    print("INFO >> Filling project data using designer's parser:")
    params = settings.get('parse', {}).get('project', {})
    parser.parse_project(ADProject, **params)

    #справшиваем какие BoM обрабатывать если их больше одного
    print('INFO >> BoMs found: ' + str(len(ADProject.BoMs)))
    for i in range(len(ADProject.BoMs)):
        print(' ' * 12 + str(i + 1).rjust(2)  + ': "' + os.path.basename(ADProject.BoMs[i]) + '" / "' + ADProject.BoMVariantNames[i] + '"')
    activeBomIndexes = []
    if len(ADProject.BoMs) == 1 or noquestions:
        activeBomIndexes = list(range(len(ADProject.BoMs)))
    elif len(ADProject.BoMs) > 1:
        answer_valid = False
        #запрашиваем данные пока нет правильного ответа 
        while not answer_valid:
            answer = input("REQUEST >> Choose which BoMs to process (0 or <empty> for all, q for abort): ")
            if answer == 'q': exit(3)
            elif answer == '0' or answer == '':
                activeBomIndexes = list(range(len(ADProject.BoMs)))
                answer_valid = True
            else:
                for idx in filter(None, re.split('[ ,.]', answer)):
                    if idx.isdigit():
                        index = int(idx) - 1
                        if index >= 0 and index < len(ADProject.BoMs):
                            activeBomIndexes.append(index)
                            answer_valid = True
                    else:
                        answer_valid = False
                        break
            if not answer_valid: print("REQUEST >> error: invalid indexes.")
        activeBomIndexes = list(set(activeBomIndexes))   #убираем дубликаты
    print("INFO >> BoM files to process: " + str(len(activeBomIndexes)))

    #добавляем данные основной надписи из внешнего модуля в словарь из проекта
    titleblock = copy.deepcopy(ADProject.titleblock)
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
        process_bom(os.path.join(ADProject.directory, ADProject.BoMs[i]), titleblock, output_directory, ADProject.designator, ADProject.BoMVariantNames[i], parser, settings, **kwargs)

    print((' ' * 8).ljust(80, '='))

#обрабатываем BoM файлы
def process_bom(address, titleblock = None, output_directory = None, output_basename = None, output_postfix = None, parser = None, settings = None, **kwargs):
    print('')
    print(('INFO >> Processing BoM: "' + os.path.basename(address) + '" ').ljust(80, '-'))

    #загружаем настройки
    settings = _import_settings(settings)

    #загружаем анализатор данных (приоритет выбора значения: из аргумента -> из настроек -> по-умолчанию)
    if parser is None: parser = settings.get('parse', {}).get('parser', None)
    parser = _import_parser(parser)
    
    #загружаем данные основной надписи
    titleblock = _import_titleblock(titleblock)

    #какие документы создавать (приоритет выбора значения: из аргумента -> из настроек -> по-умолчанию)
    make_cl_xlsx  = settings.get('output', {}).get('cl-xlsx',  {}).get('enabled', True)
    make_pe3_docx = settings.get('output', {}).get('pe3-docx', {}).get('enabled', True)
    make_pe3_pdf  = settings.get('output', {}).get('pe3-pdf',  {}).get('enabled', True)
    make_pe3_csv  = settings.get('output', {}).get('pe3-csv',  {}).get('enabled', True)
    make_sp_csv   = settings.get('output', {}).get('sp-csv',   {}).get('enabled', True)
    output        = kwargs.get('output')
    if output is not None:
        if   OutputID.ALL.value    in output: output = [OutputID.CL_XLSX.value, OutputID.PE3_DOCX.value, OutputID.PE3_PDF.value, OutputID.PE3_CSV.value, OutputID.SP_CSV.value]
        elif OutputID.NONE.value   in output: output = []
        make_cl_xlsx  = OutputID.CL_XLSX.value  in output
        make_pe3_docx = OutputID.PE3_DOCX.value in output
        make_pe3_pdf  = OutputID.PE3_PDF.value  in output
        make_pe3_csv  = OutputID.PE3_CSV.value  in output
        make_sp_csv   = OutputID.SP_CSV.value   in output
    
    #какие оптимизации проводить (приоритет выбора значения: из аргумента -> из настроек -> по-умолчанию)
    optmz_mfr_name = settings.get('optimize', {}).get('mfr-name', {}).get('enabled', False)
    optmz_res_tol   = settings.get('optimize', {}).get('res-tol', {}).get('enabled', False)
    optimize        = kwargs.get('optimize')
    if optimize is not None:
        if   OptimizationID.ALL.value    in optimize: optimize = [OptimizationID.MFR_NAMES.value, OptimizationID.RES_TOL.value]
        elif OptimizationID.NONE.value   in optimize: optimize = []
        optmz_mfr_name = OptimizationID.MFR_NAMES.value in optimize
        optmz_res_tol  = OptimizationID.RES_TOL.value   in optimize

    #имена файлов и папок
    if output_directory is None: output_directory = os.path.dirname(address)
    if output_basename is None: output_basename = os.path.splitext(os.path.basename(address))[0]
    if output_postfix is None: output_postfix = ''

    #импорт BoM
    print("INFO >> Importing BoM:")
    params = settings.get('input', {}).get('bom-csv', {})
    bom = import_bom.importz(address, **params)
    print('')

    #создаём базу данных компонентов
    print("INFO >> Creating components database using designer's parser:")
    params = settings.get('parse', {}).get('bom', {})
    components = typedef_components.Components_typeDef()                    #создаём объект базы
    parser.parse_bom(components, bom, **params)                             #отдаём разработчику BoM чтобы он заполнил базу данных

    #проверяем базу данных компонентов
    print("INFO >> Checking components database.")
    params = settings.get('parse', {}).get('check', {})
    check_complaints = parser.check(components, **params)                   #проверяем методами разработчика
    check_complaints.add(components.check())                                #проверяем методами системы
    if check_complaints.critical > 0:
        print("ERROR >> further execution halted due to critical errors in the database.")
        raise RuntimeError("Input data may cause a program crash or corrupted output.")

    print("INFO >> Sorting components database.")
    components.sort()                                                       #сортируем элементы базы данных (методом по-умолчанию)

    #оптимизируем имена производителей
    if optmz_mfr_name:
        print("INFO >> Optimizing manufacturers names:")
        params = settings.get('optimize', {}).get('mfr-name', {})
        optimize_mfr_name.optimize(components, **params)
    
    #оптимизируем номиналы резисторов по точности
    if optmz_res_tol:
        print("INFO >> Optimizing resistors tolerances:")
        params = settings.get('optimize', {}).get('res-tol', {})
        optimize_res_tol.optimize(components, **params)

    #список компонентов в xlsx
    if make_cl_xlsx:
        print('')
        print("INFO >> Building cl:")
        params = settings.get('output', {}).get('cl-xlsx', {}).get('build', {})
        cl = build_cl.build(components, **params)
        print('')
        print("INFO >> Exporting cl as xlsx:")
        file_name_template = Template(settings.get('output', {}).get('cl-xlsx', {}).get('filename', "$basename СК $postfix" + os.extsep + "xlsx"))
        file_name = os.path.splitext(file_name_template.substitute(basename = output_basename, postfix = output_postfix))
        file_name = file_name[0].strip() + file_name[1]
        params = settings.get('output', {}).get('cl-xlsx', {}).get('export', {})
        export_cl_xlsx.export([cl], os.path.join(output_directory, file_name), **params)

    #перечень элементов в docx
    if make_pe3_docx:
        print('')
        print("INFO >> Building pe3:")
        params = settings.get('output', {}).get('pe3-docx', {}).get('build', {})
        pe3 = build_pe3.build([components, titleblock], **params)
        print('')
        print("INFO >> Exporting pe3 as docx:")
        file_name_template = Template(settings.get('output', {}).get('pe3-docx', {}).get('filename', "$basename ПЭ3 $postfix" + os.extsep + "docx"))
        file_name = os.path.splitext(file_name_template.substitute(basename = output_basename, postfix = output_postfix))
        file_name = file_name[0].strip() + file_name[1]
        params = settings.get('output', {}).get('pe3-docx', {}).get('export', {})
        export_pe3_docx.export(pe3, os.path.join(output_directory, file_name), **params)

    #перечень элементов в pdf
    if make_pe3_pdf:
        print('')
        print("INFO >> Building pe3:")
        params = settings.get('output', {}).get('pe3-pdf', {}).get('build', {})
        pe3 = build_pe3.build([components, titleblock], **params)
        print('')
        print("INFO >> Exporting pe3 as PDF:")
        file_name_template = Template(settings.get('output', {}).get('pe3-pdf', {}).get('filename', "$basename ПЭ3 $postfix" + os.extsep + "pdf"))
        file_name = os.path.splitext(file_name_template.substitute(basename = output_basename, postfix = output_postfix))
        file_name = file_name[0].strip() + file_name[1]
        params = settings.get('output', {}).get('pe3-pdf', {}).get('export', {})
        export_pe3_pdf.export(pe3, os.path.join(output_directory, file_name), **params)

    #перечень элементов в csv
    if make_pe3_csv:
        print('')
        print("INFO >> Building pe3:")
        params = settings.get('output', {}).get('pe3-csv', {}).get('build', {})
        pe3 = build_pe3.build([components, None], **params)
        print('')
        print("INFO >> Exporting pe3 as CSV:")
        file_name_template = Template(settings.get('output', {}).get('pe3-csv', {}).get('filename', "$basename ПЭ3 $postfix" + os.extsep + "csv"))
        file_name = os.path.splitext(file_name_template.substitute(basename = output_basename, postfix = output_postfix))
        file_name = file_name[0].strip() + file_name[1]
        params = settings.get('output', {}).get('pe3-csv', {}).get('export', {})
        export_pe3_csv.export(pe3, os.path.join(output_directory, file_name), **params)

    #спецификация в csv
    if make_sp_csv:
        print('')
        print("INFO >> Building sp:")
        params = settings.get('output', {}).get('sp-csv', {}).get('build', {})
        sp = build_sp.build([components, titleblock], **params)
        print('')
        print("INFO >> Exporting sp as CSV:")
        file_name_template = Template(settings.get('output', {}).get('sp-csv', {}).get('filename', "$basename СП $postfix" + os.extsep + "csv"))
        file_name = os.path.splitext(file_name_template.substitute(basename = output_basename, postfix = output_postfix))
        file_name = file_name[0].strip() + file_name[1]
        params = settings.get('output', {}).get('sp-csv', {}).get('export', {})
        export_sp_csv.export(sp, os.path.join(output_directory, file_name), **params)

    print((' ' * 8).ljust(80, '='))


#импортирует анализатор данных
def _import_parser(parser):
    print("INFO >> Importing designer's parser", end ="... ")
    if parser is None: parser = default_parser
    if isinstance(parser, types.ModuleType):
        #на входе сразу модуль -> его и возвращаем
        print("ok, already imported.")
        return parser
    elif isinstance(parser, str):
        #на входе строка -> загружаем модуль по адресу в ней
        print(f"from file '{parser}'", end ="... ")
        path = os.path.join(_module_dirname, parser)
        if os.path.exists(path):
            name = os.path.splitext(os.path.basename(path))[0]
            import importlib.util
            spec = importlib.util.spec_from_file_location(name, path)
            parser = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(parser)
            print("ok.")
            return parser
        else:
            print("error! file doesn't exist.")
            raise FileExistsError
    else:
        print("error! invalid input.")
        raise ValueError

#импортирует данные основной надписи
def _import_titleblock(titleblock):
    print("INFO >> Importing titleblock data", end ="... ")
    if titleblock is None:
        print("nothing to import.")
        return None
    if isinstance(titleblock, dict):
        #на входе сразу словарь -> его и возвращаем
        print(f"ok, already in dictionary ({len(titleblock)} entries).")
        return titleblock
    elif isinstance(titleblock, str):
        #на входе строка -> загружаем модуль по адресу в ней
        print(f"from file '{titleblock}'", end ="... ")
        path = os.path.join(_module_dirname, titleblock)
        if os.path.exists(path):
            name = os.path.splitext(os.path.basename(path))[0]
            import importlib.util
            spec = importlib.util.spec_from_file_location(name, path)
            titleblock = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(titleblock)
            dictionary = titleblock.data
            print(f"done ({len(dictionary)} entries).")
            return dictionary
        else:
            print("error! file doesn't exist.")
            raise FileExistsError
    else:
        print("error! invalid input.")
        raise ValueError

#импортирует настройки
def _import_settings(settings):
    print("INFO >> Importing settings", end ="... ")
    if settings is None: settings = default_settings
    if isinstance(settings, dict):
        #на входе сразу словарь -> его и возвращаем
        print("ok, already imported.")
        return settings
    elif isinstance(settings, types.ModuleType):
        #на входе модуль -> возвращаем словарь из него
        print("extracting data", end ="... ")
        if isinstance(settings.data, dict):
            print("ok.")
            return settings.data
        else:
            print("error! data is not a dictionary.")
            raise ValueError
    elif isinstance(settings, str):
        #на входе строка -> загружаем модуль по адресу в ней
        print(f"from file '{settings}'", end ="... ")
        path = os.path.join(_module_dirname, settings)
        if os.path.exists(path):
            name = os.path.splitext(os.path.basename(path))[0]
            import importlib.util
            spec = importlib.util.spec_from_file_location(name, path)
            settings = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(settings)
            print("module loaded, extracting data", end ="... ")
            if isinstance(settings.data, dict):
                print("ok.")
                return settings.data
            else:
                print("error! data is not a dictionary.")
                raise ValueError
        else:
            print("error! file doesn't exist.")
            raise FileExistsError
    else:
        print("error! invalid input.")
        raise ValueError

#===================================================== END Specific functions =====================================================


#---------------------------------------------------------- Execution -------------------------------------------------------------

def main() -> None:
    #specify custom parameters to function call
    inputfiles = []                                                         #input files
    output_directory = None                                                 #output directory
    parser = None                                                           #модуль анализа данных [module|file_address]
    settings = None                                                         #настройки [dictionary|module|file_address]
    params = {#'output':                OutputID.ALL.value,                 #какие файлы делать: [OutputID.CL_XLSX.value, OutputID.PE3_DOCX.value, OutputID.PE3_PDF.value, OutputID.SP_CSV.value] или OutputID.ALL
                #'noquestions':           False                               #ничего не спрашивать при выполнении программы, при возникновении вопросов делать по-умолчанию
                #'output_name_enclosure': [' ', ' ']                          #заключение для типа документа в имени выходного файла
                #'output_name_prefix':    ''                                  #префикс имени выходного файла
                #'output_name_postfix':   ''                                  #суффикс имени выходного файла
    }

    #parse arguments
    parse_default = argparse.ArgumentParser(description='BoM converter v' + _module_version + ' (' + _module_date.strftime('%Y-%m-%d') + ') by Alexander Taluts')
    parse_default.add_argument('inputfiles',                          nargs='+', metavar='data-file',    help='input files to process')
    parse_default.add_argument('--adproject',          action='store_true',                              help='input files are Altium Designer project')
    parse_default.add_argument('--titleblock',         type=str,                 metavar='file',         help='dictionary with title block data')
    parse_default.add_argument('--output-dir',                                   metavar='path',         help='output directory')
    parse_default.add_argument('--parser',             type=str,                 metavar='file',         help='parser module to use')
    parse_default.add_argument('--settings',           type=str,                 metavar='file',         help='settings module to use')
    parse_default.add_argument('--output',             type=str,      nargs='+', action='extend',        help='which output to produce',        choices=[OutputID.CL_XLSX.value, OutputID.PE3_DOCX.value, OutputID.PE3_PDF.value, OutputID.PE3_CSV.value, OutputID.SP_CSV.value, OutputID.ALL.value, OutputID.NONE.value])
    parse_default.add_argument('--optimize',           type=str,      nargs='+', action='extend',        help='which optimization to perform',  choices=[OptimizationID.MFR_NAMES.value, OptimizationID.RES_TOL.value, OptimizationID.ALL.value, OptimizationID.NONE.value])
    parse_default.add_argument('--noquestions',        action='store_true',                              help='do not ask questions')
    parse_default.add_argument('--nohalt',             action='store_true',                              help='do not halt terminal')
    args = parse_default.parse_args()

    #take input data files and options from arguments
    inputfiles = args.inputfiles
    if args.output_dir is not None: output_directory = args.output_dir
    if args.parser is not None: parser = args.parser
    if args.settings is not None: params['settings'] = args.settings
    if args.output is not None: params['output'] = args.output
    if args.optimize is not None: params['optimize'] = args.optimize
    if args.nohalt is not None: 
        global _halt_on_exit
        _halt_on_exit = False
    params['noquestions'] = args.noquestions

    #process data
    print('')
    print('INFO >> BoM converter v' + _module_version + ' (' + _module_date.strftime('%Y-%m-%d') + ') by Alexander Taluts')
    print('')
    for file in inputfiles:
        if args.adproject is True or os.path.splitext(file)[1].lstrip(os.extsep) == 'PrjPcb':
            process_adproject(file, args.titleblock, output_directory, parser, settings, **params)
        else:
            process_bom(file, args.titleblock, output_directory, None, None, parser, settings, **params)
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
    wrap_stdout_utf8() #force output encoding to be utf-8

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