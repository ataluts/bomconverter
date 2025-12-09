import os
from pathlib import Path
import lib_common                                   #библиотека с общими функциями

script_dirName  = Path(__file__).parent                                                                 #адрес папки со скриптом
script_baseName = Path(__file__).stem                                                                   #базовое имя модуля
dictionary_path = script_dirName / Path(script_baseName.replace('optimize', 'dict') + os.extsep + 'py') #адрес словаря

#Оптимизирует имена производителей
def optimize(data, **kwargs):
    print('INFO >> Manufacturer names optimizer module running.')

    #параметры
    dictionary = kwargs.get('dictionary', dictionary_path)
    case_sensitive = kwargs.get('caseSensitive', False)

    #получаем данные из словаря
    print("INFO >> Importing dictionary", end ="... ")
    dictionary = lib_common.import_dictionary(dictionary, True)

    #разворачиваем данные
    components = data

    print('INFO >> Translating names', end ="... ", flush = True)
    stats_replaced = 0
    for component in components.entries:
        if component.GNRC_manufacturer is not None:
            result = lib_common.dict_translate(component.GNRC_manufacturer, dictionary, case_sensitive, False, None)
            if result is None:
                #имя не найдено в словаре -> оставляем как есть
                pass
            else:
                #заменяем имя названием из словаря
                component.GNRC_manufacturer = result
                stats_replaced += 1
        if component.GNRC_substitute is not None:
            for substitute in component.GNRC_substitute:
                if substitute.manufacturer is not None:
                    result = lib_common.dict_translate(substitute.manufacturer, dictionary, case_sensitive, False, None)
                    if result is None:
                        #имя не найдено в словаре -> оставляем как есть
                        pass
                    else:
                        #заменяем имя названием из словаря
                        substitute.manufacturer = result
                        stats_replaced += 1
    print(f"done. ({stats_replaced} replaced)")

    print("INFO >> Manufacturers names optimization completed.") 
    return True