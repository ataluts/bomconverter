import sys, argparse
import os
import copy
import datetime
from pathlib import Path

import dict_locale as lcl
from typedef_cl import CL_typeDef                               #класс списка компонентов
from import_cl_xlsx import importz as import_cl_xlsx            #импорт списка компонентов из Excel
from export_cl_xlsx import export as export_cl_xlsx             #экспорт списка компонентов в Excel
from bomconverter import _import_settings                       #функция загрузки настроек

_module_dirname = os.path.dirname(__file__)                     #адрес папки со скриптом
_module_date    = datetime.datetime(2025, 6, 17)
_halt_on_exit   = True
_debug          = False

# ----------------------------------------------------------- Generic functions -------------------------------------------------

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

#сравнивает списки компонентов из Excel и сохраняет результат в Excel
def cl_discriminate_xlsx(reference_path, subject_path, result_path, reference_settings = None, subject_settings = None, result_settings = None):
    #считываем настройки
    settings_reference = _import_settings(reference_settings)
    settings_subject = _import_settings(subject_settings)
    settings_result = _import_settings(result_settings)

    #обрабатываем настройки
    params_reference = copy.deepcopy(settings_reference.get('output', {}).get('cl-xlsx', {}).get('build', {}))
    params_reference.update(settings_reference.get('output', {}).get('cl-xlsx', {}).get('export', {}))
    params_subject = copy.deepcopy(settings_subject.get('output', {}).get('cl-xlsx', {}).get('build', {}))
    params_subject.update(settings_subject.get('output', {}).get('cl-xlsx', {}).get('export', {}))
    params_result = copy.deepcopy(settings_result.get('output', {}).get('cl-xlsx', {}).get('export', {}))
    params_result['content_accs_location'] = 'end'          #расположение аксессуаров только на листе с компонентами чтобы не было путаницы в листах

    #считываем списки компонентов
    print('')
    print('INFO >> Importing reference CL')
    cl_reference = import_cl_xlsx(reference_path, **params_reference)
    print('')
    print('INFO >> Importing subject CL')
    cl_subject = import_cl_xlsx(subject_path, **params_subject)
    
    print('')
    print("INFO >> Discriminating CLs", end ="... ")
    result = cl_discriminate(cl_reference, cl_subject, **params_result)
    print(f"done. (entries: {len(result[0].components.entries)} modified, {len(result[1].components.entries)} added, {len(result[1].components.entries)} removed)")

    print('')
    print("INFO >> Exporting cl as xlsx:")
    export_cl_xlsx(result, result_path, **params_result)

#Сравнивает списки компонентов, возвращает массив из 3 списков
def cl_discriminate(reference, subject, **kwargs):
    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    cl_reference = copy.deepcopy(reference)        #исходный список компонентов (в нём останется то что удалилось)
    cl_reference.components.title = lcl.cldiscriminator.TITLE_REMOVED_LIST.value[locale_index]
    cl_reference.substitutes = None
    cl_subject = copy.deepcopy(subject)            #сравниваемый список компонентов (в нём останется то что добавилось)
    cl_subject.components.title = lcl.cldiscriminator.TITLE_ADDED_LIST.value[locale_index]
    cl_subject.substitutes = None
    cl_changes = CL_typeDef()                      #список компонентов с изменениями (в нём появится то что изменилось по количеству)
    cl_changes.components = CL_typeDef.Sublist(lcl.cldiscriminator.TITLE_MODIFIED_LIST.value[locale_index])

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

    #переворачиваем список изменённых позиций так как перебирали их в обратном порядке
    cl_changes.components.entries.reverse()

    #возвращаем массив: [изменённые позиции, добавленные позиции, исключённые позиции]
    return [cl_changes, cl_subject, cl_reference]

#========================================================= END Specific functions =================================================

#---------------------------------------------------------- Execution -------------------------------------------------------------

def main() -> None:
    #parse arguments
    parse_default = argparse.ArgumentParser(description = f"CL discriminator v. {_module_date.strftime('%Y-%m-%d')} by Alexander Taluts")
    parse_default.add_argument('reference', type=Path, help='Reference CL')
    parse_default.add_argument('subject',   type=Path, help='Subject CL that is being compared against the reference')
    parse_default.add_argument('result',    type=Path, help='Comparison result')
    parse_default.add_argument('--settings-reference', type=Path, metavar='<file>', help='Settings used for reference CL')
    parse_default.add_argument('--settings-subject',   type=Path, metavar='<file>', help='Settings used for subject CL')
    parse_default.add_argument('--settings-result',    type=Path, metavar='<file>', help='Settings to use for result CL')
    parse_default.add_argument('--nohalt',             action='store_true',         help='Do not halt terminal')
    args = parse_default.parse_args()

    #take input data files and options from arguments
    if args.nohalt is not None: 
        global _halt_on_exit
        _halt_on_exit = False

    #process data
    print('')
    print(f"INFO >> CL discriminator v. {_module_date.strftime('%Y-%m-%d')} by Alexander Taluts")
    print('')
    cl_discriminate_xlsx(args.reference, args.subject, args.result, args.settings_reference, args.settings_subject, args.settings_result)
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