import sys, argparse
import os
import copy
import datetime
from pathlib import Path

import lib_common                                               #библиотека с общими функциями
import dict_locale as lcl
from typedef_cl import CL_typeDef                               #класс списка компонентов
from import_cl_xlsx import importz as import_cl_xlsx            #импорт списка компонентов из Excel
from export_cl_xlsx import export as export_cl_xlsx             #экспорт списка компонентов в Excel

_module_dirname = os.path.dirname(__file__)                     #адрес папки со скриптом
_module_date    = datetime.datetime(2025, 10, 14)
_halt_on_exit   = True
_debug          = False

# ----------------------------------------------------------- Generic functions -------------------------------------------------

#Сравнивает списки (игнорируя последовательность элементов)
def lists_equal(list1, list2):
    if list1 is None and list2 is None: return True
    if list1 is not None and list2 is None: return False
    if list1 is None and list2 is not None: return False
    if len(list1) != len(list2): return False
    if len(list1) == 0: return True

    list1_sorted = copy.deepcopy(list1)
    list2_sorted = copy.deepcopy(list2)

    list1_sorted.sort()
    list2_sorted.sort()

    if list1_sorted == list2_sorted: return True
    return False

#========================================================== END Generic functions =================================================

# ----------------------------------------------------------- Specific functions --------------------------------------------------

#Сравнивает списки компонентов, возвращает массив из 3 списков
def discriminate(reference, subject, **kwargs):
    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    cl_reference = copy.deepcopy(reference)        #исходный список компонентов (в нём останется то что удалилось)
    cl_reference.components.title = lcl.cldiscriminator.XLSX_SHEET_TITLE_REMOVED.value[locale_index]
    if cl_reference.accessories is None: cl_reference.accessories = CL_typeDef.Sublist()
    cl_reference.accessories.title = lcl.cldiscriminator.XLSX_SHEET_TITLE_REMOVED.value[locale_index]
    cl_reference.substitutes = None
    cl_subject = copy.deepcopy(subject)            #сравниваемый список компонентов (в нём останется то что добавилось)
    cl_subject.components.title = lcl.cldiscriminator.XLSX_SHEET_TITLE_ADDED.value[locale_index]
    if cl_subject.accessories is None: cl_subject.accessories = CL_typeDef.Sublist()
    cl_subject.accessories.title = lcl.cldiscriminator.XLSX_SHEET_TITLE_ADDED.value[locale_index]
    cl_subject.substitutes = None
    cl_changes = CL_typeDef()                      #список компонентов с изменениями (в нём появится то что изменилось по количеству)
    cl_changes.components = CL_typeDef.Sublist(lcl.cldiscriminator.XLSX_SHEET_TITLE_MODIFIED.value[locale_index])
    cl_changes.accessories = CL_typeDef.Sublist(lcl.cldiscriminator.XLSX_SHEET_TITLE_MODIFIED.value[locale_index])

    #список основных компонентов
    #перебираем записи сравниваемого списка
    for i in range(len(cl_subject.components.entries) - 1, -1, -1):
        #перебираем записи исходного списка
        for j in range(len(cl_reference.components.entries) - 1, -1, -1):
            #сравниваем номиналы
            if lists_equal(cl_reference.components.entries[j].value, cl_subject.components.entries[i].value):
                #сравниваем количество
                if cl_reference.components.entries[j].quantity != cl_subject.components.entries[i].quantity:
                    #количество не равно, находим разницу и записываем в новый список с изменениями
                    cl_changes.components.entries.append(copy.deepcopy(cl_subject.components.entries[i]))
                    cl_changes.components.entries[-1].quantity = cl_subject.components.entries[i].quantity - cl_reference.components.entries[j].quantity
                #удаляем записи в списках
                cl_reference.components.entries.pop(j)
                cl_subject.components.entries.pop(i)
                break

    #список сопутствующих компонентов
    #перебираем записи сравниваемого списка
    for i in range(len(cl_subject.accessories.entries) - 1, -1, -1):
        #перебираем записи исходного списка
        for j in range(len(cl_reference.accessories.entries) - 1, -1, -1):
            #сравниваем номиналы
            if lists_equal(cl_reference.accessories.entries[j].value, cl_subject.accessories.entries[i].value):
                #сравниваем количество
                if cl_reference.accessories.entries[j].quantity != cl_subject.accessories.entries[i].quantity:
                    #количество не равно, находим разницу и записываем в новый список с изменениями
                    cl_changes.accessories.entries.append(copy.deepcopy(cl_subject.accessories.entries[i]))
                    cl_changes.accessories.entries[-1].quantity = cl_subject.accessories.entries[i].quantity - cl_reference.accessories.entries[j].quantity
                #удаляем записи в списках
                cl_reference.accessories.entries.pop(j)
                cl_subject.accessories.entries.pop(i)
                break

    #переворачиваем список изменённых позиций так как перебирали их в обратном порядке
    cl_changes.components.entries.reverse()
    cl_changes.accessories.entries.reverse()

    #удаляем пустые списки
    result = [cl_changes, cl_subject, cl_reference]     #[изменённые позиции, добавленные позиции, исключённые позиции]
    for cl in result:
        if len(cl.components.entries) == 0: cl.components = None
        if len(cl.accessories.entries) == 0: cl.accessories = None

    #возвращаем массив: 
    return result

#сравнивает списки компонентов из Excel и сохраняет результат в Excel
def discriminate_file(reference_path, subject_path, result_path, reference_settings = None, subject_settings = None, result_settings = None):
    #считываем настройки
    settings_reference = lib_common.import_settings(reference_settings)
    if 'cldiscriminator' in settings_reference: settings_reference = settings_reference['cldiscriminator']
    settings_subject = lib_common.import_settings(subject_settings)
    if 'cldiscriminator' in settings_subject: settings_subject = settings_subject['cldiscriminator']
    settings_result = lib_common.import_settings(result_settings)
    if 'cldiscriminator' in settings_result: settings_result = settings_result['cldiscriminator']

    #обрабатываем настройки
    params_reference_input = copy.deepcopy(settings_reference.get('input', {}).get('xlsx', {}))
    params_subject_input = copy.deepcopy(settings_reference.get('input', {}).get('xlsx', {}))
    params_result_discriminate = copy.deepcopy(settings_result.get('discriminate', {}))
    params_result_output = copy.deepcopy(settings_result.get('output', {}).get('xlsx', {}))
    #расположение аксессуаров только на листе с компонентами чтобы не было путаницы в листах
    if params_result_output.get('content_accs_location') == 'sheet':
        params_result_output['content_accs_location'] = 'end'          

    #считываем списки компонентов
    print('')
    print('INFO >> Importing reference CL')
    cl_reference = import_cl_xlsx(reference_path, **params_reference_input)
    print('')
    print('INFO >> Importing subject CL')
    cl_subject = import_cl_xlsx(subject_path, **params_subject_input)
    
    print('')
    print("INFO >> Discriminating CLs", end ="... ")
    result = discriminate(cl_reference, cl_subject, **params_result_discriminate)
    counter = [0] * (len(result) + 1)
    for i, cl in enumerate(result):
        counter[i] += len(cl.components.entries) if cl.components is not None else 0
        counter[i] += len(cl.accessories.entries) if cl.accessories is not None else 0
        counter[-1] += counter[i]
    print(f"done. (entries: {counter[0]} modified, {counter[1]} added, {counter[2]} removed)")

    print('')
    if counter[-1] > 0:
        print("INFO >> Exporting cl as xlsx:")
        export_cl_xlsx(result, result_path, **params_result_output)
    else:
        print("INFO >> Lists are identical, nothing to export.")
        if os.path.exists(result_path):
            print("INFO >> Removing existing result file.")
            os.remove(result_path)

#========================================================= END Specific functions =================================================

#---------------------------------------------------------- Execution -------------------------------------------------------------

def main() -> None:
    #parse arguments
    argparser = argparse.ArgumentParser(description = f"CL discriminator v. {_module_date.strftime('%Y-%m-%d')} by Alexander Taluts")
    argparser.add_argument('reference', type=Path, help='Reference CL')
    argparser.add_argument('subject',   type=Path, help='Subject CL that is being compared against the reference')
    argparser.add_argument('result',    type=Path, help='Comparison result')
    argparser.add_argument('--settings-reference', type=Path, metavar='<file>', help='Settings to use for reference CL import')
    argparser.add_argument('--settings-subject',   type=Path, metavar='<file>', help='Settings to use for subject CL import')
    argparser.add_argument('--settings-result',    type=Path, metavar='<file>', help='Settings to use for result CL export')
    argparser.add_argument('--nohalt',             action='store_true',         help='Do not halt terminal')
    args = argparser.parse_args()

    #take input data files and options from arguments
    if args.nohalt is not None: 
        global _halt_on_exit
        _halt_on_exit = False

    #process data
    print('')
    print(f"INFO >> CL discriminator v. {_module_date.strftime('%Y-%m-%d')} by Alexander Taluts")
    print('')
    discriminate_file(args.reference, args.subject, args.result, args.settings_reference, args.settings_subject, args.settings_result)
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

#prevent launch when importing
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