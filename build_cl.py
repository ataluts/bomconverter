import copy
from typedef_cl import ComponentList                                #класс списка компонентов
from typedef_components import Component
import assemble                                                     #сборка ЕСКД значений
import dict_locale as lcl

#Создаёт список компонентов
def build(data, **kwargs):
    print('INFO >> cl building module running with parameters:')

    #локализация
    locale = kwargs.get('locale', lcl.Locale.RU)

    #параметры
    title_book = locale.translate(lcl.build_cl.TITLE_BOOK)
    title_list_components = locale.translate(lcl.build_cl.TITLE_COMPONENTS_LIST)
    title_list_accessories = locale.translate(lcl.build_cl.TITLE_ACCESSORIES_LIST)
    title_list_substitutes = locale.translate(lcl.build_cl.TITLE_SUBSTITUTES_LIST)
    sorting_method = kwargs.get('sorting_method', 'none')
    sorting_reverse = kwargs.get('sorting_reverse', False)
    content_accs = kwargs.get('content_accs', True)
    content_accs_segregate = kwargs.get('content_accs_segregate', False)
    content_subst = kwargs.get('content_subst', True)
    print(' ' * 12 + 'book title: "' +  title_book + '"')
    print(' ' * 12 + 'components list title: "' +  title_list_components + '"')
    print(' ' * 12 + 'substitutes list title: "' +  title_list_substitutes + '"')
    print(' ' * 12 + 'sorting method: ' +  sorting_method)
    print_txt = 'ascending' if not sorting_reverse else 'descending'
    print(' ' * 12 + 'sorting order: ' +  print_txt)
    print_txt = 'components'
    if content_accs:
        print_txt += '+ accessories'
        if content_accs_segregate: print_txt += ' (segregated)'
    if content_subst: print_txt += '+ substitutes'
    #print(' ' * 12 + 'content: ' +  print_txt)
    #print_txt = 'original' if not assemble_kind else 'assemble'
    #print(' ' * 12 + 'kind: ' +  print_txt)
    #print_txt = 'original' if not assemble_description else 'assemble'
    #print(' ' * 12 + 'description: ' +  print_txt)

    cl = ComponentList(title_book)

    print('INFO >> Processing components...')
    if len(data.entries) > 0:
        #создаём копию (полную) БД компонентов и сортируем её нужным образом
        data = copy.deepcopy(data)
        if   sorting_method == 'none':       pass
        elif sorting_method == 'designator': data.sort('designator', sorting_reverse)
        elif sorting_method == 'value':      data.sort('value', sorting_reverse)
        elif sorting_method == 'kind':       data.sort('kind', sorting_reverse)
        elif sorting_method == 'params':     data.sort('params', sorting_reverse)

        #разделяем основные компоненты и аксессуары
        components  = []
        accessories = []
        for component in data.entries:
            if component.GNRC_accessory_parent is not None:
                if content_accs:
                    if content_accs_segregate:
                        accessories.append(component)
                    else:
                        components.append(component)
            else:
                components.append(component)

        #формируем список компонентов
        if len(components) > 0:
            cl.components = ComponentList.Sublist(title_list_components)
            _build_sublist(cl.components, components, **kwargs)
        if len(accessories) > 0:
            cl.accessories = ComponentList.Sublist(title_list_accessories)
            _build_sublist(cl.accessories, accessories, **kwargs)

        print_txt = ' ' * 12 + 'component entries: '
        if cl.accessories is not None and len(cl.accessories.entries) > 0:
            print_txt += f"{len(cl.components.entries) + len(cl.accessories.entries)} ({len(cl.components.entries)} + {len(cl.accessories.entries)})"
        else:
            print_txt += str(len(cl.components.entries))
        print(print_txt)

        #возвращаем компоненты удалённые из основного списка
        components.extend(accessories)

        #формируем список допустимых замен
        if content_subst:
            #создаём список компонентов у которых указаны замены сгруппированный по основным номиналу и производителю
            grouped_by_primary = []
            for component in components:
                if component.GNRC_quantity > 0:
                    if component.GNRC_substitute is not None:
                        #добавляем в список только те компоненты которые надо закупать и у которых есть замены
                        entryFound = False
                        for primary_group in grouped_by_primary:
                            for element in primary_group:
                                if (element.GNRC_partnumber == component.GNRC_partnumber) and (element.GNRC_manufacturer == component.GNRC_manufacturer):
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
                            for i in range(len(substitute_group[0].GNRC_substitute)):
                                if (substitute_group[0].GNRC_substitute[i].partnumber == component.GNRC_substitute[i].partnumber) and (substitute_group[0].GNRC_substitute[i].manufacturer == component.GNRC_substitute[i].manufacturer) and (substitute_group[0].GNRC_substitute[i].note == component.GNRC_substitute[i].note):
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
                    if component.GNRC_quantity > 0:
                        if component.GNRC_substitute is None:
                            #добавляем в список только те компоненты которые надо закупать и у которых нет замены
                            for entry in grouped_by_entries:
                                if (entry[0][0].GNRC_partnumber == component.GNRC_partnumber) and (entry[0][0].GNRC_manufacturer == component.GNRC_manufacturer):
                                    #нашёлся компонент с совпадающим номиналом и производителем
                                    if entry[-1][0].GNRC_substitute is None:
                                        #у компонента в последней группе нет замены => нужная группа уже существует -> добавляем компонент в неё
                                        entry[-1].append(component)
                                    else:
                                        #у компонента в последней группе есть замена => нужная группа не существует -> добавляем компонент новую группу
                                        entry.append([component])
                                    break #нашли нужную запись -> перестаём перебирать группы замен
                            
                #собираем список замен
                cl.substitutes = ComponentList.Sublist(title_list_substitutes)
                for primary_group in grouped_by_entries:
                    cl.substitutes.entries.append(ComponentList.SubstituteEntry(primary_group[0][0].GNRC_partnumber, primary_group[0][0].GNRC_manufacturer, 0, []))
                    for substitute_group in primary_group:
                        subgrp = ComponentList.SubstituteEntry.SubstituteGroup([], 0, [])
                        for component in substitute_group:
                            subgrp.designator.append(component.GNRC_designator.full)
                            subgrp.quantity += component.GNRC_quantity
                        cl.substitutes.entries[-1].primary_quantity += subgrp.quantity
                        if (substitute_group[0].GNRC_substitute is None) and (True):
                            #группа без замен
                            subgrp.substitute.append(ComponentList.SubstituteEntry.SubstituteGroup.Substitute(locale.translate(lcl.build_cl.NO_SUBSITUTE), None, None))
                            cl.substitutes.entries[-1].substitute_group.append(subgrp)
                        else:
                            #нормальная группа замен
                            for substitute in substitute_group[0].GNRC_substitute:
                                subgrp.substitute.append(ComponentList.SubstituteEntry.SubstituteGroup.Substitute(substitute.partnumber, substitute.manufacturer, substitute.note))
                            cl.substitutes.entries[-1].substitute_group.append(subgrp)
                print(' ' * 12 + 'substitute entries: ' + str(len(cl.substitutes.entries)))
    else:
        print("0 components provided.")

    print('INFO >> cl building completed.') 

    return cl

#Создаёт подсписок компонентов
def _build_sublist(sublist, components, **kwargs):
    for component in components:
        if component.GNRC_quantity > 0:
            if   component.flag == Component.FlagType.ERROR:    flag = ComponentList.FlagType.ERROR
            elif component.flag == Component.FlagType.WARNING:  flag = ComponentList.FlagType.WARNING
            elif component.flag == Component.FlagType.OK:       flag = ComponentList.FlagType.OK
            else: flag = ComponentList.FlagType.NONE

            #проверяем поля
            if component.GNRC_designator is None and component.GNRC_accessory_parent is None:
                #если нет десигнатора и не аксессуар то это подозрительно
                if flag < ComponentList.FlagType.WARNING: flag = ComponentList.FlagType.WARNING
            if component.GNRC_partnumber is None:
                #если нет артикула то это подозрительно
                if flag < ComponentList.FlagType.WARNING: flag = ComponentList.FlagType.WARNING

            kind = assemble.assemble_kind(component, **kwargs)
            description = assemble.assemble_parameters(component, **kwargs)
            designator = assemble.assemble_designator(component.GNRC_designator, **kwargs)
            package = component.GNRC_package.name if component.GNRC_package is not None else None
            for entry in sublist.entries:
                if (component.GNRC_partnumber in entry.partnumber) and (component.GNRC_parametric == entry.parametric):
                    entry.add(designator, kind, component.GNRC_partnumber, component.GNRC_parametric, description, package, component.GNRC_manufacturer, component.GNRC_quantity, component.GNRC_note, flag)
                    break
            else:
                sublist.entries.append(ComponentList.ComponentEntry(designator, kind, component.GNRC_partnumber, component.GNRC_parametric, description, package, component.GNRC_manufacturer, component.GNRC_quantity, component.GNRC_note,  flag))
