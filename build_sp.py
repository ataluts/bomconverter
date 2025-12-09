import os
from copy import deepcopy

from typedef_components import Database                             #класс базы данных компонентов
from typedef_sp import SP                                           #класс перечня элементов
import assemble                                                     #сборка ЕСКД значений

script_dirName  = os.path.dirname(__file__)                                                          #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                                    #базовое имя модуля

#Создаёт перечень элементов
def build(data, **kwargs):
    print('INFO >> sp building module running.')

    #основная надпись
    setting_data_titleblock = kwargs.get('data_titleblock', None)

    #параметры содержимого
    content_accs = kwargs.get('content_accs', True)
    content_accs_parent = kwargs.get('content_accs_parent', False)
    content_annot = kwargs.get('content_annot', False)

    #разворачиваем данные
    if isinstance(data, (tuple, list)):
        #в данных компоненты и основная надпись
        components  = data[0]
        titleblock  = data[1]
    elif isinstance(data, Database):
        #в данных только компоненты
        components = data
        titleblock = None
    else:
        #в данных непонятно что
        raise ValueError("Invalid input data")

    #создаём объект спецификации
    sp = SP()

    #добавляем данные основной надписи внутрь спецификации
    print('INFO >> Processing title block.')
    if titleblock is not None:
        if not isinstance(titleblock, dict): raise ValueError("Invalid titleblock data.")
        sp.titleblock = deepcopy(titleblock)
        if setting_data_titleblock is not None:
            if not isinstance(titleblock, dict): raise ValueError("Invalid titleblock settings.")
            for key, value in setting_data_titleblock.items():
                if isinstance(value, (tuple, list)):
                    #если тип значения 'tuple' или 'list' то собираем из него строку и добавляем её к уже имеющейся в полученных данных
                    value = ''.join(value)
                    if key in sp.titleblock:
                        sp.titleblock[key] += value
                        continue
                sp.titleblock[key] = value
    
    print('INFO >> Processing components', end ="... ", flush = True)
    if len(components.entries) > 0:
        #создание записей спецификации
        #группируем одинаковые позиции в одну запись
        for component in components.entries:
            if component.GNRC_designator is None:
            #нет десигнатора (должно быть аксессуар) -> собираем компоненты с одинаковым значением в один элемент перечня
                if not content_accs: continue                                   #пропускаем если выбран соответствующий параметр
                if content_accs_parent:
                    #указываем десигнатор родителя в качестве десигнатора
                    component = deepcopy(component)
                    component.GNRC_designator = component.GNRC_accessory_parent.GNRC_designator
            if component.GNRC_fitted:                                            #записываем только устанавливаемые компоненты
                value = assemble.assemble_eskd(component, **kwargs)                 #собираем поля перечня из параметров компонента
                if content_annot:
                    #добавляем примечание в наименование
                    value.label += value.annotation
                #сравниваем текущее значение с существующими записями
                for entry in sp.entries:
                    if value.label == entry.label:
                        #нашли совпадение, добавляем компонент в найденную запись
                        entry.add(value.designator, value.quantity)
                        break
                else:
                    #значение не найдено, добавляем новую запись
                    sp.entries.append(sp.entry(value.designator, value.label, value.quantity))

        print(f"done. ({len(sp.entries)} entries)")
    else:
        print("0 components provided.")
    
    print("INFO >> sp building completed.") 
    return sp