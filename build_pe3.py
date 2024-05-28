import os
import csv
from copy import deepcopy

from typedef_components import Components_typeDef                   #класс базы данных компонентов
from typedef_pe3 import PE3_typeDef                                 #класс перечня элементов
import assemble                                                     #сборка ЕСКД значений

script_dirName  = os.path.dirname(__file__)                                                          #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                                    #базовое имя модуля
elementGroupsDict_defaultAddress = os.path.join(script_dirName, script_baseName + os.extsep + 'csv') #адрес словаря с группами элементов по-умолчанию

#Значения строки таблицы перечня
class pe3Value():
    def __init__(self, designator = '', label = '', quantity = 0, annotation = ''):
        self.designator = designator
        self.label      = label
        self.quantity   = quantity
        self.annotation = annotation

#Группа элементов
class elementGroup():
    def __init__(self, prefix = '', nameForSingle = '', nameForMultiple = ''):
        self.prefix          = prefix
        self.nameForSingle   = nameForSingle
        self.nameForMultiple = nameForMultiple

#Создаёт перечень элементов
def build(data, **kwargs):
    print('INFO >> pe3 building module running.')

    #адрес словаря групп элементов
    elementGroupsDict_address = kwargs.pop('groupsDict', elementGroupsDict_defaultAddress)
    print(' ' * 12 + 'groups dictionary: ' +  os.path.basename(elementGroupsDict_address))

    #получаем словарь с группами элементов перечня из указанного файла
    print('INFO >> Reading groups dictionary', end ="... ", flush = True)
    elementGroups = []
    with open(elementGroupsDict_address, 'r', encoding='utf-8') as csvFile:
        dictreader = csv.DictReader(csvFile, delimiter=',', quotechar='"')
        for entry in dictreader:
            elementGroups.append(elementGroup(entry['Prefix'], entry['Single'], entry['Multiple']))
        csvFile.close()
    print('ok. (' + str(len(elementGroups)) + ' groups)')

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
            value = assemble.assemble_eskd(component, **kwargs) #собираем поля перечня из параметров компонента
            if len(pe3.entries) > 0:
                #список не пуст, сравниваем поля текущей записи с последней имеющейся в списке
                if pe3.entries[-1].prefix == component.GENERIC_designator_prefix and pe3.entries[-1].indexes[-1] == component.GENERIC_designator_index - 1 and pe3.entries[-1].label == value.label and pe3.entries[-1].annotation == value.annotation:
                    #нужные поля совпадают - добавляем этот компонент к предыдущей записи
                    pe3.entries[-1].add(value.designator, component.GENERIC_designator_index, [', ', '\u2013'], value.quantity)
                    continue
            #либо список пуст либо надо добавить новую запись
            pe3.entries.append(pe3.entry(value.designator, component.GENERIC_designator_prefix, component.GENERIC_designator_index, value.label, value.quantity, value.annotation))

        #создаём группы с записями
        for entry in pe3.entries:
            #определяем группу для текущей записи
            for group in elementGroups:
                if group.prefix == entry.prefix:
                    groupName = [group.nameForSingle, group.nameForMultiple]
                    break
            else:
                groupName = ['НЁХ', 'Разное']
                print("WARNING! >> Group for element with prefix '" + entry.prefix + "' not found in dictionary.")

            #добавляем запись в нужную группу или создаём новую
            for group in pe3.groups:
                if group.name == groupName:
                    #нашли подходящую группу для записи - добавляем запись в неё
                    group.add(entry)
                    break
            else:
                #либо список пуст либо совпадений нет - надо добавить новую группу
                pe3.groups.append(pe3.group(groupName, entry)) 

        #объединяем группы с одинаковыми названиями для множественного числа записей
        i = 0
        while i < len(pe3.groups):
            j = i + 1
            while j < len(pe3.groups):
                if pe3.groups[j].name[1] == pe3.groups[i].name[1]:
                    #имена групп для множественного числа совпадают - объединяем группы в одну
                    pe3.groups[i].entries.extend(pe3.groups[j].entries)
                    pe3.groups[i].name[0] = 'UNITED'
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
        print('done. (' + str(len(pe3.entries)) + ' entries in ' + str(len(pe3.groups)) + ' groups resulting to ' + str(len(pe3.rows)) + ' rows)')
    else:
        print("0 components provided.")
    
    print("INFO >> pe3 building completed.") 
    return pe3