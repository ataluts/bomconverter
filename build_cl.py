import copy
from typedef_components import Components_typeDef                   #класс базы данных компонентов
from typedef_cl import CL_typeDef                                   #класс списка компонентов
import assemble                                                     #сборка ЕСКД значений
import dict_locale as lcl

#Создаёт список компонентов
def build(data, **kwargs):
    print('INFO >> cl building module running with parameters:')

    #локализация
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры
    title_book = kwargs.get('title_book', lcl.build_cl.TITLE_BOOK.value[locale_index])
    title_list_components = kwargs.get('title_list_components', lcl.build_cl.TITLE_COMPONENTS_LIST.value[locale_index])
    title_list_accessories = kwargs.get('title_list_accessories', lcl.build_cl.TITLE_ACCESSORIES_LIST.value[locale_index])
    title_list_substitutes = kwargs.get('title_list_substitutes', lcl.build_cl.TITLE_SUBSTITUTES_LIST.value[locale_index])
    sorting_method = kwargs.get('sorting_method', 'none')
    sorting_reverse = kwargs.get('sorting_reverse', False)
    content_accessories = kwargs.get('content_accessories', True)
    content_accessories_segregate = kwargs.get('content_accessories_segregate', False)
    content_substitutes = kwargs.get('content_substitutes', True)
    print(' ' * 12 + 'book title: "' +  title_book + '"')
    print(' ' * 12 + 'components list title: "' +  title_list_components + '"')
    print(' ' * 12 + 'substitutes list title: "' +  title_list_substitutes + '"')
    print(' ' * 12 + 'sorting method: ' +  sorting_method)
    print_txt = 'ascending' if not sorting_reverse else 'descending'
    print(' ' * 12 + 'sorting order: ' +  print_txt)
    print_txt = 'components'
    if content_accessories:
        print_txt += '+ accessories'
        if content_accessories_segregate: print_txt += ' (segregated)'
    if content_substitutes: print_txt += '+ substitutes'
    #print(' ' * 12 + 'content: ' +  print_txt)
    #print_txt = 'original' if not assemble_kind else 'assemble'
    #print(' ' * 12 + 'kind: ' +  print_txt)
    #print_txt = 'original' if not assemble_description else 'assemble'
    #print(' ' * 12 + 'description: ' +  print_txt)

    cl = CL_typeDef(title_book)

    print('INFO >> Processing components...')
    if len(data.entries) > 0:
        #создаём копию (полную) БД компонентов и сортируем её нужным образом
        data = copy.deepcopy(data)
        if   sorting_method == 'none':       pass
        elif sorting_method == 'designator': data.sort('designator', sorting_reverse)
        elif sorting_method == 'value':      data.sort('value', sorting_reverse)
        elif sorting_method == 'kind':       data.sort('kind', sorting_reverse)
        elif sorting_method == 'params':     data.sort('params', sorting_reverse)

        components = data.entries
        accessories = []

        #сопутствующие компоненты
        if content_accessories:
            if content_accessories_segregate:
                #выделяем в отдельный список
                for component in components:
                    if component.GENERIC_accessory_parent is not None:
                        accessories.append(component)
                        components.remove(component)
        else:
            #удаляем
            for component in components:
                if component.GENERIC_accessory_parent is not None:
                    components.remove(component)

        #формируем список компонентов
        if len(components) > 0:
            cl.components = CL_typeDef.Sublist(title_list_components)
            _build_sublist(cl.components, components, **kwargs)
        if len(accessories) > 0:
            cl.accessories = CL_typeDef.Sublist(title_list_accessories)
            _build_sublist(cl.accessories, accessories, **kwargs)

        print_txt = ' ' * 12 + 'component entries: '
        if cl.accessories is not None and len(cl.accessories.entries) > 0:
            print_txt += str(len(cl.components.entries) + len(cl.accessories.entries)) + ' (' + str(len(cl.components.entries)) + ' + ' + str(len(cl.accessories.entries)) + ')'
        else:
            print_txt += str(len(cl.components.entries))
        print(print_txt)

        #возвращаем компоненты удалённые из основного списка
        components.extend(accessories)

        #формируем список допустимых замен
        if content_substitutes:
            #создаём список компонентов у которых указаны замены сгруппированный по основным номиналу и производителю
            grouped_by_primary = []
            for component in components:
                if component.GENERIC_quantity > 0:
                    if component.GENERIC_substitute is not None:
                        #добавляем в список только те компоненты которые надо закупать и у которых есть замены
                        entryFound = False
                        for primary_group in grouped_by_primary:
                            for element in primary_group:
                                if (element.GENERIC_value == component.GENERIC_value) and (element.GENERIC_manufacturer == component.GENERIC_manufacturer):
                                    primary_group.append(component)
                                    entryFound = True
                                    break
                            if entryFound: break
                        else:
                            grouped_by_primary.append([component])
            
            if len(grouped_by_primary) > 0:
                #создаём список компонентов в котором предыдущий список разбит ещё и по вариантам замен внутри группы по номиналу
                grouped_by_entries = []
                for primary_group in grouped_by_primary:
                    grouped_by_substitutes = []
                    for component in primary_group:
                        for substitute_group in grouped_by_substitutes:
                            for i in range(len(substitute_group[0].GENERIC_substitute)):
                                if (substitute_group[0].GENERIC_substitute[i].value == component.GENERIC_substitute[i].value) and (substitute_group[0].GENERIC_substitute[i].manufacturer == component.GENERIC_substitute[i].manufacturer) and (substitute_group[0].GENERIC_substitute[i].note == component.GENERIC_substitute[i].note):
                                    pass
                                else:
                                    #замены отличаются -> переходим к сравнению следующей группы
                                    break
                            else:
                                #все замены совпали -> добавляем компонент в текущую группу
                                substitute_group.append(component)
                                break
                        else:
                            #группы с такими заменами не нашлось -> добавляем новую
                            grouped_by_substitutes.append([component])
                    grouped_by_entries.append(grouped_by_substitutes)

                #добавляем в предыдущий список группу компонентов без возможной замены
                for component in components:
                    if component.GENERIC_quantity > 0:
                        if component.GENERIC_substitute is None:
                            #добавляем в список только те компоненты которые надо закупать и у которых нет замены
                            for entry in grouped_by_entries:
                                if (entry[0][0].GENERIC_value == component.GENERIC_value) and (entry[0][0].GENERIC_manufacturer == component.GENERIC_manufacturer):
                                    #нашёлся компонент с совпадающим номиналом и производителем
                                    if entry[-1][0].GENERIC_substitute is None:
                                        #у компонента в последней группе нет замены => нужная группа уже существует -> добавляем компонент в неё
                                        entry[-1].append(component)
                                    else:
                                        #у компонента в последней группе есть замена => нужная группа не существует -> добавляем компонент новую группу
                                        entry.append([component])
                                    break #нашли нужную запись -> перестаём перебирать группы замен
                            
                #собираем список замен
                cl.substitutes = CL_typeDef.Sublist(title_list_substitutes)
                for primary_group in grouped_by_entries:
                    cl.substitutes.entries.append(cl.SubstituteEntry(primary_group[0][0].GENERIC_value, primary_group[0][0].GENERIC_manufacturer, 0, []))
                    for substitute_group in primary_group:
                        subgrp = cl.SubstituteEntry.SubstituteGroup([], 0, [])
                        for component in substitute_group:
                            subgrp.designator.append(component.GENERIC_designator)
                            subgrp.quantity += component.GENERIC_quantity
                        cl.substitutes.entries[-1].primary_quantity += subgrp.quantity
                        if (substitute_group[0].GENERIC_substitute is None) and (True):
                            #группа без замен
                            subgrp.substitute.append(cl.SubstituteEntry.SubstituteGroup.Substitute(lcl.build_cl.NO_SUBSITUTE.value[locale_index], None, None))
                            cl.substitutes.entries[-1].substitute_group.append(subgrp)
                        else:
                            #нормальная группа замен
                            for substitute in substitute_group[0].GENERIC_substitute:
                                subgrp.substitute.append(cl.SubstituteEntry.SubstituteGroup.Substitute(substitute.value, substitute.manufacturer, substitute.note))
                            cl.substitutes.entries[-1].substitute_group.append(subgrp)
                print(' ' * 12 + 'substitute entries: ' + str(len(cl.substitutes.entries)))
    else:
        print("0 components provided.")

    print('INFO >> cl building completed.') 

    return cl

#Создаёт подсписок компонентов
def _build_sublist(sublist, components, **kwargs):
    for component in components:
        if component.GENERIC_quantity > 0:
            if   component.flag == component.FlagType.ERROR:    flag = CL_typeDef.FlagType.ERROR
            elif component.flag == component.FlagType.WARNING:  flag = CL_typeDef.FlagType.WARNING
            elif component.flag == component.FlagType.OK:       flag = CL_typeDef.FlagType.OK
            else: flag = CL_typeDef.FlagType.NONE

            #проверяем поля
            if component.GENERIC_designator is None and component.GENERIC_accessory_parent is None:
                #если нет десигнатора и не аксесуар то это подозрительно
                if flag < CL_typeDef.FlagType.WARNING: flag = CL_typeDef.FlagType.WARNING
            if component.GENERIC_value is None:
                #если нет значения то это подозрительно
                if flag < CL_typeDef.FlagType.WARNING: flag = CL_typeDef.FlagType.WARNING

            kind = assemble.assemble_kind(component, **kwargs)
            description = assemble.assemble_parameters(component, **kwargs)
            for entry in sublist.entries:
                if component.GENERIC_value in entry.value:
                    entry.add(component.GENERIC_designator, kind, component.GENERIC_value, description, component.GENERIC_package, component.GENERIC_manufacturer, component.GENERIC_quantity, component.GENERIC_note, flag)
                    break
            else:
                sublist.entries.append(CL_typeDef.ComponentEntry(component.GENERIC_designator, kind, component.GENERIC_value, description, component.GENERIC_package, component.GENERIC_manufacturer, component.GENERIC_quantity, component.GENERIC_note,  flag))
