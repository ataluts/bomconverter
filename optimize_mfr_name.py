import os
import sys
from typedef_components import Components_typeDef                   #класс базы данных компонентов

script_dirName  = os.path.dirname(__file__)                                                          #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                                    #базовое имя модуля
dictionary_address = os.path.join(script_dirName, script_baseName.replace('optimize', 'dict') + os.extsep + 'py')  #адрес словаря с именами производителей

#Оптимизирует имена производителей
def optimize(data, **kwargs):
    print('INFO >> Manufacturer names optimizer module running.')

    #словарь
    dict_names = kwargs.get('dict_names', dictionary_address)
    print(' ' * 12 + "dictionary: ", end ="", flush = True)
    if isinstance(dict_names, str):
        #получили строку с адресом словаря
        print(f"from module ({os.path.basename(dict_names)}), importing", end ="... ", flush = True)
        #импортируем словарь из модуля
        import importlib.util
        spec = importlib.util.spec_from_file_location("dict_mfr_name", dict_names)
        dict_mfr_name = importlib.util.module_from_spec(spec)
        sys.modules["dict_mfr_name"] = dict_mfr_name
        spec.loader.exec_module(dict_mfr_name)
        dict_names = dict_mfr_name.data
        print(f"done ({len(dict_names)} entries)")
    elif isinstance(dict_names, dict):
        #получили словарь как аргумент
        print(f"from argument ({len(dict_names)} entries)")
    else:
        #получили непонятно что
        print("invalid")
        raise ValueError

    #разворачиваем данные
    components = data

    print('INFO >> Translating names', end ="... ", flush = True)
    for component in components.entries:
        if component.GENERIC_manufacturer is not None:
            entryFound = False
            for entry in dict_names:
                for word in dict_names[entry]:
                    if word.casefold() == component.GENERIC_manufacturer.casefold():
                        component.GENERIC_manufacturer = entry
                        entryFound = True
                        break
                if entryFound: break
        if component.GENERIC_substitute is not None:
            for substitute in component.GENERIC_substitute:
                if substitute.manufacturer is not None:
                    entryFound = False
                    for entry in dict_names:
                        for word in dict_names[entry]:
                            if word.casefold() == substitute.manufacturer.casefold():
                                substitute.manufacturer = entry
                                entryFound = True
                                break
                        if entryFound: break
    print('done.')

    print("INFO >> Manufacturers names optimization completed.") 
    return True