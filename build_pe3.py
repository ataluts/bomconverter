import os
import sys
from copy import deepcopy

from typedef_components import Components_typeDef                   #класс базы данных компонентов
from typedef_pe3 import PE3_typeDef                                 #класс перечня элементов
import assemble                                                     #сборка ЕСКД значений
import dict_locale as lcl

script_dirName  = os.path.dirname(__file__)                                                          #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                                    #базовое имя модуля
dictionary_address = os.path.join(script_dirName, script_baseName.replace('build', 'dict') + os.extsep + 'py')  #адрес файла со словарём

#Создаёт перечень элементов
def build(data, **kwargs):
    print("INFO >> pe3 building module running.")

    #локализация
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры
    content_accessories = kwargs.get('content_accessories', False)
    format_desig_delimiter = kwargs.get('format_desig_delimiter', [', ', '\u2013'])

    #словарь
    dict_groups = kwargs.get('dict_groups', dictionary_address)
    print(' ' * 12 + "dictionary: ", end ="", flush = True)
    if isinstance(dict_groups, str):
        #получили строку с адресом словаря
        print(f"from module ({os.path.basename(dict_groups)}), importing", end ="... ", flush = True)
        #импортируем словарь из модуля
        import importlib.util
        spec = importlib.util.spec_from_file_location("dict_pe3", dict_groups)
        dict_pe3 = importlib.util.module_from_spec(spec)
        sys.modules["dict_pe3"] = dict_pe3
        spec.loader.exec_module(dict_pe3)
        dict_groups = dict_pe3.data
        print(f"done ({len(dict_groups)} entries)")
    elif isinstance(dict_groups, dict):
        #получили словарь как аргумент
        print(f"from argument ({len(dict_groups)} entries)")
    else:
        #получили непонятно что
        print("invalid")
        raise ValueError

    #разворачиваем данные
    components  = data[0]
    titleBlock  = data[1]

    #создаём объект перечня
    pe3 = PE3_typeDef()

    #добавляем данные основной надписи внутрь перечня
    print('INFO >> Inserting title block.')
    pe3.titleBlock = deepcopy(titleBlock)
    
    print('INFO >> Processing components', end ="... ", flush = True)
    if len(components.entries) > 0:
        #создание записей перечня
        #группируем одинаковые последовательные позиции в одну запись
        for component in components.entries:
            if not content_accessories and component.GENERIC_accessory_parent is not None: continue     #пропускаем аксессуар если выбран соответствующий параметр
            value = assemble.assemble_eskd(component, **kwargs)                                         #собираем поля перечня из параметров компонента
            if component.GENERIC_accessory_parent is not None:                                          #если аксессуар то добавляем тип в наименование
                value.label = assemble.assemble_kind(component, **kwargs) + ' ' + value.label
            if len(pe3.entries) > 0:
                #список не пуст, сравниваем поля текущей записи с последней имеющейся в списке
                if pe3.entries[-1].prefix == component.GENERIC_designator_prefix and pe3.entries[-1].label == value.label and pe3.entries[-1].annotation == value.annotation:
                    previous_designator_index = component.GENERIC_designator_index - 1 if component.GENERIC_designator_index is not None else None
                    if pe3.entries[-1].indexes[-1] == previous_designator_index:
                        #нужные поля совпадают - добавляем этот компонент к предыдущей записи
                        pe3.entries[-1].add(value.designator, component.GENERIC_designator_index, format_desig_delimiter, value.quantity)
                        continue
            #либо список пуст либо надо добавить новую запись
            pe3.entries.append(pe3.entry(value.designator, component.GENERIC_designator_prefix, component.GENERIC_designator_index, value.label, value.quantity, value.annotation))

        #создаём группы с записями
        for entry in pe3.entries:
            if entry.prefix in dict_groups:
                group_name = dict_groups[entry.prefix]
            else:
                print(f"WARNING! >> Group for element with prefix '{entry.prefix}' not found in dictionary.")
                group_name = dict_groups.get(0, ('', ''))
            if isinstance(group_name[0], (tuple, list)):
                group_name = (group_name[0][locale_index], group_name[1][locale_index])     #если словарь с локализацией то выбираем нужную

            #добавляем запись в нужную группу или создаём новую
            for group in pe3.groups:
                if group.name == group_name:
                    #нашли подходящую группу для записи - добавляем запись в неё
                    group.add(entry)
                    break
            else:
                #либо список пуст либо совпадений нет - надо добавить новую группу
                pe3.groups.append(pe3.group(group_name, entry)) 

        #объединяем группы с одинаковыми названиями для множественного числа записей
        i = 0
        while i < len(pe3.groups):
            j = i + 1
            while j < len(pe3.groups):
                if pe3.groups[j].name[1] == pe3.groups[i].name[1]:
                    #имена групп для множественного числа совпадают - объединяем группы в одну
                    pe3.groups[i].entries.extend(pe3.groups[j].entries)
                    pe3.groups[i].name = ('UNITED', pe3.groups[i].name[1])
                    del pe3.groups[j]
                else:
                    j += 1
            i += 1

        #создаём строки таблицы перечня
        for group in pe3.groups:
            pe3.rows.append(pe3.row())
            if len(group.entries) == 1:
                pe3.rows.append(pe3.row(group.entries[0].designatorsRange,
                                        group.name[0] + ' ' + group.entries[0].label,
                                        group.entries[0].quantity,
                                        group.entries[0].annotation,
                                        pe3.row.FlagType.ITEM))
            else:
                pe3.rows.append(pe3.row('', group.name[1], '', '', pe3.row.FlagType.TITLE))
                for entry in group.entries:
                    pe3.rows.append(pe3.row(entry.designatorsRange,
                                            entry.label,
                                            entry.quantity,
                                            entry.annotation,
                                            pe3.row.FlagType.ITEM))
        pe3.rows.pop(0)
        print(f"done. ({len(pe3.entries)} entries in {len(pe3.groups)} groups resulting to {len(pe3.rows)} rows)")
    else:
        print("0 components provided.")
    
    print("INFO >> pe3 building completed.") 
    return pe3