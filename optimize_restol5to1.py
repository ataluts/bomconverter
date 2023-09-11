import os
import copy
from typedef_components import Components_typeDef                   #класс базы данных компонентов

script_dirName  = os.path.dirname(__file__)                                                          #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                                    #базовое имя модуля

# ----------------------------------------------------------- Generic functions -------------------------------------------------

#Check if 'advanced values' are equal
def listedvalue_equal(value1, value2):
    if isinstance(value1, list) and isinstance(value2, list):
        if len(value1) != len(value2): return False
        for i in range(len(value1)):
            if not listedvalue_equal(value1[i], value2[i]): return False
        return True
    else:
        return value1 == value2

#========================================================== END Generic functions =================================================


#Оптимизирует номиналы резисторов по точности
def optimize(data, **kwargs):
    print('INFO >> Resistors tolerance optimizer module running.')

    #разворачиваем данные
    components = data

    #составляем список резисторов допустимых к оптимизации
    print('INFO >> Building suitable resistors lists', end ="... ", flush = True)
    res5 = []
    res1 = []
    for component in components.entries:
        if isinstance(component, component.types.Resistor):                         #только резисторы
            if component.GENERIC_explicit is False:                                     #заданные параметрически (неявно)
                if component.RES_tolerance is not None:                                     #у которых указана точность
                    if component.RES_tolerance[2] is None:                                      #в долях от значения
                        if abs(component.RES_tolerance[0]) == abs(component.RES_tolerance[1]):      #равная в обе стороны
                            if abs(component.RES_tolerance[0]) == 0.05:                                 #5%
                                res5.append(component)
                            elif abs(component.RES_tolerance[0]) == 0.01:                               #1%
                                res1.append(component)
    print('done (' + str(len(res5)) + ' for 5%, ' + str(len(res1)) + ' for 1%)')

    print('INFO >> Optimizing:')
    initial_res5_size = len(res5)
    i = 0
    while i < len(res1):
        modified = []
        j = 0
        while j < len(res5):
            #проверяем идентичность параметров резисторов
            if ((res5[j].RES_resistance == res1[i].RES_resistance) and                                      #значение сопротивления
                ((res5[j].RES_type == res1[i].RES_type) or (res5[j].RES_type is None)) and                  #тип или у 5% не задан
                ((res5[j].RES_tempCoeff == res1[i].RES_tempCoeff) or (res5[j].RES_tempCoeff is None)) and   #ТКС или у 5% не задан
                ((res5[j].RES_power == res1[i].RES_power) or (res5[j].RES_power is None)) and               #мощность или у 5% не задана
                ((res5[j].RES_voltage == res1[i].RES_voltage) or (res5[j].RES_voltage is None)) and         #напряжение или у 5% не задано
                (res5[j].GENERIC_package == res1[i].GENERIC_package) and                                    #корпус
                (res5[j].GENERIC_mount == res1[i].GENERIC_mount) and                                        #тип монтажа
                (res5[j].GENERIC_THtype == res1[i].GENERIC_THtype) and                                      #тип монтажа в отверстия
                (res5[j].GENERIC_size == res1[i].GENERIC_size) and                                          #типоразмер
                (listedvalue_equal(res5[j].GENERIC_temperature_range, res1[i].GENERIC_temperature_range) or (res5[j].GENERIC_temperature_range is None)) and  #диапазон рабочих температур или у 5% не задан
                listedvalue_equal(res5[j].GENERIC_assembly, res1[i].GENERIC_assembly) and                   #сборка
                listedvalue_equal(res5[j].GENERIC_misc, res1[i].GENERIC_misc)):                             #оставшиеся нераспознанные параметры

                #копируем параметры компонента
                res5[j].GENERIC_value = copy.deepcopy(res1[i].GENERIC_value)
                res5[j].GENERIC_manufacturer = copy.deepcopy(res1[i].GENERIC_manufacturer)
                res5[j].GENERIC_description = copy.deepcopy(res1[i].GENERIC_description)
                res5[j].RES_tolerance = copy.deepcopy(res1[i].RES_tolerance)
                res5[j].RES_type = copy.deepcopy(res1[i].RES_type)
                res5[j].RES_tempCoeff = copy.deepcopy(res1[i].RES_tempCoeff)
                res5[j].RES_power = copy.deepcopy(res1[i].RES_power)
                res5[j].RES_voltage = copy.deepcopy(res1[i].RES_voltage)
                res5[j].GENERIC_temperature_range = copy.deepcopy(res1[i].GENERIC_temperature_range)

                modified.append(res5[j].GENERIC_designator)
                res5.pop(j)
            else:
                j += 1

        if len(modified) > 0:
            if   res1[i].RES_resistance <  1e0: res_str = '{0:.10f}'.format(res1[i].RES_resistance * 1e3).rstrip('0').rstrip('.') + 'm'
            elif res1[i].RES_resistance >= 1e3: res_str = '{0:.10f}'.format(res1[i].RES_resistance / 1e3).rstrip('0').rstrip('.') + 'k'
            elif res1[i].RES_resistance >= 1e6: res_str = '{0:.10f}'.format(res1[i].RES_resistance / 1e6).rstrip('0').rstrip('.') + 'M'
            else: res_str = '{0:.10f}'.format(res1[i].RES_resistance).rstrip('0').rstrip('.') + 'R'
            print(' ' * 12 + res1[i].GENERIC_designator + ' (' + res_str + ') -> ' + ', '.join(modified))
        
        i += 1
    
    if initial_res5_size == len(res5): print(' ' * 12 + 'nothing to optimize.')
    print("INFO >> Resistors tolerances otimization completed (" + str(initial_res5_size - len(res5)) + ' resistors optimized).') 

    return True