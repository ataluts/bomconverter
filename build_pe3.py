import os
import sys
from copy import deepcopy
from itertools import groupby

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

    #основная надпись
    setting_data_titleblock = kwargs.get('data_titleblock', None)

    #локализация
    setting_locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры содержимого
    setting_content_table_group_header = kwargs.get('content_table_group_header', True)
    setting_content_accs = kwargs.get('content_accs', False)
    setting_content_accs_parent = kwargs.get('content_accs_parent', True)

    #параметры формата
    setting_format_table_group_indent = kwargs.get('format_table_group_indent', 1)
    setting_format_table_group_header_indent = kwargs.get('format_table_group_header_indent', 0)
    setting_format_table_entry_indent = kwargs.get('format_table_entry_indent', 0)
    setting_format_table_entry_composite_indent = kwargs.get('format_table_entry_composite_indent', 0)
    setting_format_table_entry_deviation_indent = kwargs.get('format_table_entry_deviation_indent', 0)
    setting_format_accs_parent_first = kwargs.get('format_accs_parent_first', True)
    setting_format_accs_parent_delimiter = kwargs.get('format_accs_parent_delimiter', '; ')
    setting_format_accs_parent_enclosure = kwargs.get('format_accs_parent_enclosure', ['', ''])
    setting_format_desig_delimiter = kwargs.get('format_desig_delimiter', [', ', '\u2013'])

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
    if isinstance(data, (tuple, list)):
        #в данных компоненты и основная надпись
        components  = data[0]
        titleblock  = data[1]
    elif isinstance(data, Components_typeDef):
        #в данных только компоненты
        components = data
        titleblock = None
    else:
        #в данных непонятно что
        raise ValueError("Invalid input data")

    #создаём объект перечня
    pe3 = PE3_typeDef()

    #добавляем данные основной надписи внутрь перечня
    print('INFO >> Processing title block.')
    if titleblock is None: titleblock = {}
    if not isinstance(titleblock, dict): raise ValueError("Invalid titleblock data.")
    pe3.titleblock = deepcopy(titleblock)
    if setting_data_titleblock is not None:
        if not isinstance(setting_data_titleblock, dict): raise ValueError("Invalid titleblock settings.")
        for key, value in setting_data_titleblock.items():
            if isinstance(value, (tuple, list)):
                #если тип значения 'tuple' или 'list' то собираем из него строку и добавляем её к уже имеющейся в полученных данных
                value = ''.join(value)
                if key in pe3.titleblock:
                    pe3.titleblock[key] += value
                    continue
            pe3.titleblock[key] = value
    
    print('INFO >> Processing components', end ="... ", flush = True)
    if len(components.entries) > 0:
        #создание записей перечня
        #консолидируем каналы в общий базовый компонент перечня
        for component in components.entries:
            #получаем значение
            value = assemble.assemble_eskd(component, **kwargs)
            quantity = value.quantity
            value = PE3_typeDef.Element.Value(value.label, value.annotation)
            if component.GENERIC_designator is None:
                #нет десигнатора (должно быть аксессуар) -> собираем компоненты с одинаковым значением в один элемент перечня
                if not setting_content_accs: continue                                                       #пропускаем если выбран соответствующий параметр
                designator = Components_typeDef.Designator('', None, '', 0, component.GENERIC_accessory_parent.GENERIC_designator) #делаем специальный десигнатор для таких элементов
                value.label = assemble.assemble_kind(component, **kwargs) + ' ' + value.label       #добавляем тип в наименование
                for element in pe3.elements:
                    if element.designator.name == designator.name:
                        if element.dominant.value.match(value):
                            element.add_channel(component.GENERIC_accessory_parent.GENERIC_designator, value, quantity)
                            break
                else:
                    pe3.elements.append(PE3_typeDef.Element(designator, value, quantity))
            else:
                #есть десигнатор -> консолидируем каналы в общий базовый элемент перечня
                for element in pe3.elements:
                    if element.designator.name == component.GENERIC_designator.name:
                        element.add_channel(component.GENERIC_designator.channel, value , quantity)
                        break
                else:
                    pe3.elements.append(PE3_typeDef.Element(component.GENERIC_designator, value, quantity))

        #добавляем десигнаторы родительских элементов в примечание аксессуаров
        if setting_content_accs_parent:
            for element in pe3.elements:
                if element.designator.prefix is None:
                    if len(element.dominant.channels) > 0:
                        parents = setting_format_accs_parent_enclosure[0]
                        for parent in element.dominant.channels:
                            #!!! TODO: написать группировку десигнаторов (с учётом каналов)
                            parents += assemble.assemble_designator(parent, **kwargs) + setting_format_desig_delimiter[0]
                        parents = parents[:-len(setting_format_desig_delimiter[0])] + setting_format_accs_parent_enclosure[1]
                        if len(element.dominant.value.annotation) > 0:
                            if setting_format_accs_parent_first:
                                element.dominant.value.annotation = parents + setting_format_accs_parent_delimiter + element.dominant.value.annotation
                            else:
                                element.dominant.value.annotation += setting_format_accs_parent_delimiter + parents
                        else:
                            element.dominant.value.annotation = parents

        #сортируем список консолидированных компонентов перечня (вариации сортируются по количеству каналов при их добавлении)
        pe3.elements.sort(key = lambda element: element._cmpkey(), reverse = False)

        #группируем одинаковые последовательные позиции в одну запись
        for element in pe3.elements:
            #получаем основное значение
            value = None
            if element.dominant is not None:
                value = PE3_typeDef.Entry.Value(element.designator.name, element.dominant.value.label, element.dominant.quantity, element.dominant.value.annotation)
            if len(pe3.entries) > 0:
                #список не пуст
                if value is not None and value.match(pe3.entries[-1].baseline):
                    #есть основное значение и оно совпадает с последней записью имеющейся в списке  
                    if pe3.entries[-1].prefix == element.designator.prefix and pe3.entries[-1].local_numbers[-1] == element.designator.number - 1:
                        #индексация продолжает предыдущую запись -> добавляем текущее значение в последнюю запись в списке
                        pe3.entries[-1].add_value(element.designator.number, value, setting_format_desig_delimiter)
                        pe3.entries[-1].add_deviations(_build_deviations(element, setting_format_desig_delimiter))
                        continue
            #либо список пуст либо текущая запись отличается от последней в списке
            pe3.entries.append(PE3_typeDef.Entry(element.designator.prefix, element.designator.number, value))
            pe3.entries[-1].add_deviations(_build_deviations(element, setting_format_desig_delimiter))

        #создаём группы с записями
        for entry in pe3.entries:
            if entry.prefix in dict_groups:
                group_name = dict_groups[entry.prefix]
            else:
                print(f"WARNING! >> Group for element with prefix '{entry.prefix}' not found in dictionary.")
                group_name = dict_groups.get(0, ('', ''))
            if isinstance(group_name[0], (tuple, list)):
                group_name = (group_name[0][setting_locale_index], group_name[1][setting_locale_index])     #если словарь с локализацией то выбираем нужную

            #добавляем запись в нужную группу или создаём новую
            for group in pe3.groups:
                if group.name == group_name:
                    #нашли подходящую группу для записи - добавляем запись в неё
                    group.add(entry)
                    break
            else:
                #либо список пуст либо совпадений нет - надо добавить новую группу
                pe3.groups.append(pe3.Group(group_name, entry)) 

        #объединяем группы с одинаковыми названиями для множественного числа записей
        if setting_content_table_group_header:
            i = 0
            while i < len(pe3.groups):
                j = i + 1
                while j < len(pe3.groups):
                    if pe3.groups[j].name[1] == pe3.groups[i].name[1]:
                        #имена групп для множественного числа совпадают - объединяем группы в одну
                        pe3.groups[i].entries.extend(pe3.groups[j].entries)
                        pe3.groups[i].name = ('<UNITED>', pe3.groups[i].name[1])
                        del pe3.groups[j]
                    else:
                        j += 1
                i += 1

        #создаём строки таблицы перечня
        for group in pe3.groups:
            #добавляем отступ между группами (пропускаем если это первая группа)
            if len(pe3.rows) > 0:
                for i in range(setting_format_table_group_indent):
                    pe3.rows.append(PE3_typeDef.Row())

            #определяем добавлять ли заголовок группы
            group_header = setting_content_table_group_header 
            if len(group.entries) == 1 and len(group.entries[0].deviations) == 0: group_header = False
            if group_header:
                #добавляем заголовок и отступ после него
                pe3.rows.append(PE3_typeDef.Row('', group.name[1], '', '', PE3_typeDef.Row.FlagType.TITLE))
                for i in range(setting_format_table_group_header_indent):
                    pe3.rows.append(PE3_typeDef.Row())

            #добавляем записи группы
            for index, entry in enumerate(group.entries):
                #добавляем отступ между записями (пропускаем если это первая запись в группе)
                if index > 0:
                    indent = setting_format_table_entry_indent
                    if len(entry.deviations) > 0: indent = max(indent, setting_format_table_entry_composite_indent)
                    for i in range(indent):
                        pe3.rows.append(PE3_typeDef.Row())
                #добавляем основную запись
                label_prefix = '' if group_header or len(group.name[0]) == 0 else group.name[0] + ' '
                if entry.baseline is not None:
                    pe3.rows.append(PE3_typeDef.Row(entry.baseline.designator,
                                                    label_prefix + entry.baseline.label,
                                                    str(entry.baseline.quantity),
                                                    entry.baseline.annotation,
                                                    PE3_typeDef.Row.FlagType.ITEM))
                #добавляем вариации
                for jndex, deviation in enumerate(entry.deviations):
                    #добавляем отступ между вариациями (пропускаем если это первый элемент в записи)
                    if jndex > 0 or entry.baseline is not None:
                        for i in range(setting_format_table_entry_deviation_indent):
                            pe3.rows.append(PE3_typeDef.Row())
                    pe3.rows.append(PE3_typeDef.Row(deviation.value.designator,
                                                    label_prefix + deviation.value.label,
                                                    str(deviation.value.quantity),
                                                    deviation.value.annotation,
                                                    PE3_typeDef.Row.FlagType.ITEM))
                #добавляем отступ после записи с вариациями если это не последняя запись в группе и следующая запись без вариаций
                if len(entry.deviations) > 0 and index < len(group.entries) - 1:
                    if len(group.entries[index + 1].deviations) == 0:
                        for i in range(setting_format_table_entry_composite_indent):
                            pe3.rows.append(PE3_typeDef.Row())

        print(f"done. ({len(pe3.entries)} entries in {len(pe3.groups)} groups resulting to {len(pe3.rows)} rows)")
    else:
        print("0 components provided.")
    
    print("INFO >> pe3 building completed.") 
    return pe3

#Создаёт перечень вариаций
def _build_deviations(element, format_desig_delimiter):
    deviations = []
    for variant in element.variants:
        for channel, quantity in zip(variant.channels, variant.quantities):
            #получаем значение
            value = PE3_typeDef.Entry.Value(element.designator.name + channel.full, variant.value.label, quantity, variant.value.annotation)
            if len(deviations) > 0:
                #список не пуст
                if value.match(deviations[-1].value):
                    #значение совпадает с последней записью имеющейся в списке  
                    if deviations[-1].channel_numbers[-1] == channel.number - 1:
                        #индексация продолжает предыдущую запись -> добавляем текущее значение в последнюю запись в списке
                        deviations[-1].add_value(channel.number, value, format_desig_delimiter)
                        continue
            #либо список пуст либо текущая запись отличается от последней в списке
            deviations.append(PE3_typeDef.Entry.Deviation(element.designator.number, channel.number, value))
    return deviations