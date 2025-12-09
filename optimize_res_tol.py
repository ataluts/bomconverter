import os
from copy import deepcopy
import typedef_components as Components

script_dirName  = os.path.dirname(__file__)                                                          #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                                    #базовое имя модуля

# ----------------------------------------------------------- Generic functions -------------------------------------------------

#Check if 'advanced values' are equal
def _isequal(value1, value2):
    if isinstance(value1, Components.Quantity) and isinstance(value2, Components.Quantity):
        return value1.isequal(value2, False)
    elif isinstance(value1, (list, tuple)) and isinstance(value2, (list, tuple)):
        if len(value1) != len(value2): return False
        for i in range(len(value1)):
            if not _isequal(value1[i], value2[i]): return False
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
        if type(component) is Components.Component.Resistor:                        #только резисторы
            if component.GNRC_parametric is True:                                       #заданные параметрически (неявно)
                if component.RES_resistance is not None:                                    #у которых указано сопротивление
                    if component.RES_resistance.tolerance is not None:                          #у которых указан допуск
                        if component.RES_resistance.tolerance.isrelative():                         #в долях от значения
                            if component.RES_resistance.tolerance.issymmetric():                        #равная в обе стороны
                                if abs(component.RES_resistance.tolerance.lower_norm) == 0.05:              #5%
                                    res5.append(component)
                                elif abs(component.RES_resistance.tolerance.lower_norm) == 0.01:            #1%
                                    res1.append(component)
    print(f"done ({len(res5)} for 5%, {len(res1)} for 1%)")

    print('INFO >> Optimizing:')
    initial_res5_size = len(res5)
    i = 0
    while i < len(res1):
        modified = []
        j = 0
        while j < len(res5):
            #проверяем идентичность параметров резисторов
            resistance5 = deepcopy(res5[j].RES_resistance)
            resistance5.tolerance = res1[i].RES_resistance.tolerance
            if (res1[i].RES_resistance.isequal(resistance5, False) and                                          #значение сопротивления
               (res5[j].RES_type == res1[i].RES_type) and                                                       #тип
               (res5[j].RES_structure is None or res5[j].RES_structure == res1[i].RES_structure) and            #структура или у 5% не задан
               (res5[j].RES_TCR is None or _isequal(res5[j].RES_TCR, res1[i].RES_TCR)) and                      #ТКС или у 5% не задан
               (res5[j].RES_power is None or _isequal(res5[j].RES_power, res1[i].RES_power)) and                #мощность или у 5% не задана
               (res5[j].RES_voltage is None or _isequal(res5[j].RES_voltage, res1[i].RES_voltage)) and          #напряжение или у 5% не задано
               (res5[j].RES_turns == res1[i].RES_turns) and                                                     #количество оборотов (для переменных)
               (res5[j].GNRC_temperatureRange is None or _isequal(res5[j].GNRC_temperatureRange, res1[i].GNRC_temperatureRange)) and #диапазон рабочих температур или у 5% не задан
               (res5[j].GNRC_package == res1[i].GNRC_package) and                                               #корпус
               (res5[j].GNRC_mount == res1[i].GNRC_mount) and                                                   #тип монтажа
               (res5[j].GNRC_size == res1[i].GNRC_size) and                                                     #типоразмер
               (res5[j].GNRC_array == res1[i].GNRC_array) and                                                   #сборка
                _isequal(res5[j].GNRC_misc, res1[i].GNRC_misc)):                                                #оставшиеся нераспознанные параметры

                #копируем параметры компонента
                res5[j].GNRC_partnumber = deepcopy(res1[i].GNRC_partnumber)
                res5[j].GNRC_manufacturer = deepcopy(res1[i].GNRC_manufacturer)
                res5[j].GNRC_description = deepcopy(res1[i].GNRC_description)
                res5[j].GNRC_temperatureRange = deepcopy(res1[i].GNRC_temperatureRange)
                res5[j].RES_resistance = deepcopy(res1[i].RES_resistance)
                res5[j].RES_structure = deepcopy(res1[i].RES_structure)
                res5[j].RES_TCR = deepcopy(res1[i].RES_TCR)
                res5[j].RES_power = deepcopy(res1[i].RES_power)
                res5[j].RES_voltage = deepcopy(res1[i].RES_voltage)

                modified.append(str(res5[j].GNRC_designator))
                res5.pop(j)
            else:
                j += 1

        if len(modified) > 0:
            if   res1[i].RES_resistance.value.magnitude_norm <  1e0: res_str = '{0:.10f}'.format(res1[i].RES_resistance.value.magnitude_norm * 1e3).rstrip('0').rstrip('.') + 'm'
            elif res1[i].RES_resistance.value.magnitude_norm >= 1e3: res_str = '{0:.10f}'.format(res1[i].RES_resistance.value.magnitude_norm / 1e3).rstrip('0').rstrip('.') + 'k'
            elif res1[i].RES_resistance.value.magnitude_norm >= 1e6: res_str = '{0:.10f}'.format(res1[i].RES_resistance.value.magnitude_norm / 1e6).rstrip('0').rstrip('.') + 'M'
            else: res_str = '{0:.10f}'.format(res1[i].RES_resistance.value.magnitude_norm).rstrip('0').rstrip('.') + 'R'
            print(f"{' ' * 12}{res1[i].GNRC_designator} ({res_str}) -> {', '.join(modified)}")
        
        i += 1
    
    if initial_res5_size == len(res5): print(' ' * 12 + 'nothing to optimize.')
    print(f"INFO >> Resistors tolerances otimization completed ({initial_res5_size - len(res5)} resistors optimized).") 

    return True