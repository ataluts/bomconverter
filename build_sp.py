import os
from copy import deepcopy

from typedef_components import Components_typeDef                   #класс базы данных компонентов
from typedef_sp import SP_typeDef                                   #класс перечня элементов
import assemble                                                     #сборка ЕСКД значений

script_dirName  = os.path.dirname(__file__)                                                          #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                                    #базовое имя модуля

#Создаёт перечень элементов
def build(data, **kwargs):
    print('INFO >> sp building module running.')

    #разворачиваем данные
    components  = data[0]
    titleBlock  = data[1]

    #создаём объект спецификации
    sp = SP_typeDef()

    #добавляем данные основной надписи внутрь перечня
    print('INFO >> Inserting title block.')
    sp.titleBlock = deepcopy(titleBlock)
    
    print('INFO >> Processing components', end ="... ", flush = True)
    if len(components.entries) > 0:
        #создание записей спецификации
        #группируем одинаковые позиции в одну запись
        for component in components.entries:
            if component.GENERIC_fitted:                                    #записываем только устанавливаемые компоненты
                value = assemble.assemble_eskd(component, **kwargs)         #собираем поля перечня из параметров компонента
                #сравниваем текущее значение с существующими записями
                for spEntry in sp.entries:
                    if value.label == spEntry.label:
                        #нашли совпадение, добавляем компонент в найденную запись
                        spEntry.add(value.designator, value.quantity)
                        break
                else:
                    #значение не найдено, добавляем новую запись
                    sp.entries.append(sp.entry(value.designator, value.label, value.quantity, value.annotation))

        print('done. (' + str(len(sp.entries)) + ' entries)')
    else:
        print("0 components provided.")
    
    print("INFO >> sp building completed.") 
    return sp