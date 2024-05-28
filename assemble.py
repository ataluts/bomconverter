import os
import enum
import dict_locale as lcl
from typedef_components import Components_typeDef                   #класс базы данных компонентов

script_dirName  = os.path.dirname(__file__)                                                          #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                                    #базовое имя модуля

#Значения строки таблицы перечня
class eskdValue():
    def __init__(self, designator = '', label = '', quantity = 0, annotation = ''):
        self.designator = designator
        self.label      = label
        self.quantity   = quantity
        self.annotation = annotation

#Метрические множители
class MetricMultiplier(float, enum.Enum):
    YOCTO = 1e-24
    ZEPTO = 1e-21
    ATTO  = 1e-18
    FEMTO = 1e-15
    PICO  = 1e-12
    NANO  = 1e-9
    MICRO = 1e-6
    MILLI = 1e-3
    CENTI = 1e-2
    DECI  = 1e-1
    NONE  = 1e0
    DECA  = 1e1
    HECTO = 1e2
    KILO  = 1e3
    MEGA  = 1e6
    GIGA  = 1e9
    TERA  = 1e12
    PETA  = 1e15
    EXA   = 1e18
    ZETTA = 1e21
    YOTTA = 1e24

# ----------------------------------------------------------- Generic functions -------------------------------------------------

#Stips word from string
def string_strip_word(string, words, direction = 0, count = 0):
    if len(words) == 0: return string
    
    if isinstance(words, (str)): words = [words]
    if isinstance(words, (list, tuple)):
        #determine which end to strip from
        strip_start = False
        strip_end = False
        if direction == 0:
            strip_start = True
            strip_end = True
        elif direction == 1:
            strip_start = True
        elif direction == 2:
            strip_end = True

        if strip_start:
            for word in words:
                counter = 0
                while (counter < count) or (count == 0):
                    if string.startswith(word):
                        string = string[len(word):]
                        counter += 1
                    else:
                        break
        if strip_end:
            for word in words:
                counter = 0
                while (counter < count) or (count == 0):
                    if string.endswith(word):
                        string = string[0:-len(word)]
                        counter += 1
                    else:
                        break
    return string

#Convert float number to string
def _floatToString(value, decimalPoint = '.'):
    result = '{0:.10f}'.format(value)
    result = result.rstrip('0').rstrip('.')
    result = result.replace('.', decimalPoint)
    return result

#========================================================== END Generic functions =================================================

#Собирает значения полей компонента по ЕСКД из параметров компонента (сборка строк из параметров)
def assemble_eskd(data, **kwargs):
    #разворачиваем данные
    component = data

    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры содержимого полей
    content_value          = kwargs.get('content_value', True)
    content_value_explicit = kwargs.get('content_value_explicit', False)
    content_manufacturer   = kwargs.get('content_mfr', True)
    content_parameters     = kwargs.get('content_param', True)
    content_substitutes    = kwargs.get('content_subst', True)

    #параметры формата
    format_value_enclosure = kwargs.get('format_value_enclosure', ['', ''])
    format_mfr_enclosure   = kwargs.get('format_mfr_enclosure',   [' ф.\xa0', ''])
    format_param_enclosure = kwargs.get('format_param_enclosure', ['', ''])
    format_subst_enclosure = kwargs.get('format_subst_enclosure', ['', ''])

    #инициализируем переменные
    result = eskdValue()

    #Basic fields
    designator = component.GENERIC_designator
    if designator is None: designator = ''
    result.designator = designator
    result.quantity   = component.GENERIC_quantity
    if not component.GENERIC_fitted:
        result.annotation = lcl.Labels.DO_NOT_PLACE.value[locale_index]
        result.quantity   = 1     #фикс нулей в перечне когда элемент не устанавливается
    
    #Наименование
    #--- номинал
    if content_value:
        if content_value_explicit or component.GENERIC_explicit or (not content_parameters):
            value = assemble_value(component, **kwargs)
            if len(value) > 0:
                result.label += format_value_enclosure[0] + value + format_value_enclosure[1]
                #--- производитель (указываем только если есть номинал)
                if content_manufacturer is not False:
                    manufacturer = assemble_manufacturer(component, **kwargs)
                    if len(manufacturer) > 0: result.label += format_mfr_enclosure[0] + manufacturer + format_mfr_enclosure[1]

    #--- параметрическое описание
    if content_parameters:
        parameters = assemble_parameters(component, **kwargs)                  #собираем параметрическое описание
        if len(parameters) > 0:
            if len(result.label) == 0: result.label += parameters              #если до этого было пусто то пишем без ограждения
            else: result.label += format_param_enclosure[0] + parameters + format_param_enclosure[1]

    #--- допустимые замены
    if content_substitutes:
        substitutes = assemble_substitutes(component, **kwargs)
        if len(substitutes) > 0:
            result.label += format_subst_enclosure[0] + substitutes + format_subst_enclosure[1]

    return result

#сборка номинала
def assemble_value(component, **kwargs):
    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры содержимого
    content_value = kwargs.get('content_value_value', True)

    result = ''
    if component.GENERIC_value is not None:
        if content_value: result += component.GENERIC_value

    return result

#сборка производителя
def assemble_manufacturer(component, **kwargs):
    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры содержимого
    content_name = kwargs.get('content_mfr_value', True)

    result = ''
    if component.GENERIC_manufacturer is not None:
        if content_name: result += component.GENERIC_manufacturer
    
    return result

#сборка параметрической записи
def assemble_parameters(component, **kwargs):
    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры содержимого
    content_basic = kwargs.get('content_param_basic', True)
    content_misc  = kwargs.get('content_param_misc', True)

    #параметры формата
    format_decimalPoint            = kwargs.get('format_param_decimalPoint', '.')
    format_rangeSymbol             = kwargs.get('format_param_rangeSymbol', '\u2026')
    format_param_delimiter         = kwargs.get('format_param_delimiter', ', ')
    format_unit_enclosure          = kwargs.get('format_param_unit_enclosure', ['', ''])
    format_multivalue_delimiter    = kwargs.get('format_param_multivalue_delimiter', '/')
    format_tolerance_enclosure     = kwargs.get('format_param_tolerance_enclosure', ['\xa0', ''])
    format_tolerance_signDelimiter = kwargs.get('format_param_tolerance_signDelimiter', '')
    format_conditions_enclosure    = kwargs.get('format_param_conditions_enclosure', ['\xa0(', ')'])
    format_conditions_delimiter    = kwargs.get('format_param_conditions_delimiter', '; ')

    result = ''

    #базовые параметры
    if content_basic:
        #--- --- Резистор
        if type(component) is component.types.Resistor:
            #тип монтажа + размер
            if component.GENERIC_mount == component.Mounting.Type.SURFACE: result += lcl.Labels.MOUNT_SURFACE.value[locale_index]
            elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE: result += lcl.Labels.MOUNT_THROUGHHOLE.value[locale_index]
            result += '\xa0'
            if component.GENERIC_size is not None: result += component.GENERIC_size
            result = result.strip('\xa0')

            result += format_param_delimiter
            
            #мощность
            if component.RES_power is not None:
                ranges = ((1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO))
                result += _assemble_param_value(component.RES_power, lcl.Units.WATT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter
            
            #напряжение
            if component.RES_voltage is not None:
                ranges = ((1e0, MetricMultiplier.NONE), (10e3, MetricMultiplier.KILO))
                result += _assemble_param_value(component.RES_voltage, lcl.Units.VOLT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #сопротивление + допуск
            if component.RES_resistance is not None:
                ranges = ((1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO), (1e6, MetricMultiplier.MEGA), (1e9, MetricMultiplier.GIGA))
                result += _assemble_param_value(component.RES_resistance, lcl.Units.OHM, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                if component.RES_tolerance is not None:
                    result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.RES_tolerance, None, format_decimalPoint, format_unit_enclosure, format_tolerance_signDelimiter, format_rangeSymbol, locale_index) + format_tolerance_enclosure[1]
                result += format_param_delimiter

            #ТКС
            if component.RES_temperature_coefficient is not None:
                result += _assemble_param_tolerance(component.RES_temperature_coefficient, None, format_decimalPoint, format_unit_enclosure, format_tolerance_signDelimiter, format_rangeSymbol, locale_index)
                result += format_param_delimiter

        #--- --- Перемычка
        elif type(component) is component.types.Jumper:
            #тип + размер
            if component.GENERIC_mount == component.Mounting.Type.SURFACE: result += lcl.Labels.MOUNT_SURFACE.value[locale_index]
            elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE: result += lcl.Labels.MOUNT_THROUGHHOLE.value[locale_index]
            result += '\xa0'
            if component.GENERIC_size is not None: result += component.GENERIC_size
            result = result.strip('\xa0')
            result += format_param_delimiter
            
        #--- --- Конденсатор
        elif type(component) is component.types.Capacitor:
            #тип
            if component.CAP_type == component.Type.CERAMIC:
                result += lcl.Labels.CAP_TYPE_CERAMIC.value[locale_index]
            elif component.CAP_type == component.Type.TANTALUM:
                result += lcl.Labels.CAP_TYPE_TANTALUM.value[locale_index]
            elif component.CAP_type == component.Type.FILM:
                result += lcl.Labels.CAP_TYPE_FILM.value[locale_index]
            elif component.CAP_type == component.Type.ALUM_ELECTROLYTIC:
                result += lcl.Labels.CAP_TYPE_ALUM_ELECTROLYTIC.value[locale_index]
            elif component.CAP_type == component.Type.ALUM_POLYMER:
                result += lcl.Labels.CAP_TYPE_ALUM_POLYMER.value[locale_index]
            elif component.CAP_type == component.Type.SUPERCAPACITOR:
                result += lcl.Labels.CAP_TYPE_SUPERCAPACITOR.value[locale_index]

            if len(result) > 0: result += format_param_delimiter

            #размер
            if component.GENERIC_mount == component.Mounting.Type.SURFACE:
                result += lcl.Labels.MOUNT_SURFACE.value[locale_index]
            elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE:
                if component.GENERIC_THtype == component.Mounting.ThroughHole.AXIAL:
                    result += lcl.Labels.MOUNT_AXIAL.value[locale_index]
                elif component.GENERIC_THtype == component.Mounting.ThroughHole.RADIAL:
                    result += lcl.Labels.MOUNT_RADIAL.value[locale_index]
            result += "\xa0"
            if component.GENERIC_size is not None: result += component.GENERIC_size
            result = result.strip('\xa0')

            result += format_param_delimiter
            
            #диэлектрик
            if component.CAP_dielectric is not None:
                result += component.CAP_dielectric
                result += format_param_delimiter

            #напряжение
            if component.CAP_voltage is not None:
                ranges = ((1e0, MetricMultiplier.NONE), (10e3, MetricMultiplier.KILO))
                result += _assemble_param_value(component.CAP_voltage, lcl.Units.VOLT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #ёмкость + допуск
            if component.CAP_capacitance is not None:
                ranges = ((1e-12, MetricMultiplier.PICO), (10e-9, MetricMultiplier.MICRO), (0.1e0, MetricMultiplier.NONE))
                result += _assemble_param_value(component.CAP_capacitance, lcl.Units.FARAD, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                if component.CAP_tolerance is not None:
                    result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.CAP_tolerance, None, format_decimalPoint, format_unit_enclosure, format_tolerance_signDelimiter, format_rangeSymbol, locale_index) + format_tolerance_enclosure[1]
                result += format_param_delimiter

            #низкий импеданс
            if component.CAP_lowImpedance:
                result += lcl.Labels.LOW_ESR.value[locale_index]
                result += format_param_delimiter

        #--- --- Индуктивность
        elif type(component) is component.types.Inductor:
            #индуктивность + допуск
            if component.IND_inductance is not None:
                ranges = ((1e-9, MetricMultiplier.NANO), (1e-6, MetricMultiplier.MICRO), (1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE))
                result += _assemble_param_value(component.IND_inductance, lcl.Units.HENRY, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                if component.IND_tolerance is not None:
                    result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.IND_tolerance, None, format_decimalPoint, format_unit_enclosure, format_tolerance_signDelimiter, format_rangeSymbol, locale_index) + format_tolerance_enclosure[1]
                result += format_param_delimiter

            #ток
            if component.IND_current is not None:
                ranges = ((1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE))
                result += _assemble_param_value(component.IND_current, lcl.Units.AMPERE, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #низкая ёмкость
            if component.IND_lowCapacitance:
                result += lcl.Labels.LOW_CAPACITANCE.value[locale_index]
                result += format_param_delimiter

        #--- --- Диод
        elif type(component) is component.types.Diode:
            #тип
            if component.DIODE_type == component.Type.SCHOTTKY:
                result += lcl.Labels.SCHOTTKY.value[locale_index]
                result += format_param_delimiter

            #обратное напряжение
            if component.DIODE_reverseVoltage is not None:
                ranges = ((1e0, MetricMultiplier.NONE), (10e3, MetricMultiplier.KILO))
                result += _assemble_param_value(component.DIODE_reverseVoltage, lcl.Units.VOLT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                if component.DIODE_reverseVoltage_tolerance is not None:
                    result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.DIODE_reverseVoltage_tolerance, None, format_decimalPoint, format_unit_enclosure, format_tolerance_signDelimiter, format_rangeSymbol, locale_index) + format_tolerance_enclosure[1]
                result += format_param_delimiter

            #прямой ток
            if component.DIODE_forwardCurrent is not None:
                ranges = ((1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE))
                result += _assemble_param_value(component.DIODE_forwardCurrent, lcl.Units.AMPERE, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #максимальная мощность
            if component.DIODE_power is not None:
                ranges = ((1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO))
                result += _assemble_param_value(component.DIODE_power, lcl.Units.WATT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #ёмкость + допуск + условия
            if component.DIODE_capacitance is not None:
                ranges = ((1e-12, MetricMultiplier.PICO), )
                result += _assemble_param_value(component.DIODE_capacitance, lcl.Units.FARAD, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                #допуск
                if component.DIODE_capacitance_tolerance is not None:
                    result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.DIODE_capacitance_tolerance, None, format_decimalPoint, format_unit_enclosure, format_tolerance_signDelimiter, format_rangeSymbol, locale_index) + format_tolerance_enclosure[1]
                #условия
                if (component.DIODE_capacitance_voltage is not None) or (component.DIODE_capacitance_frequency is not None):
                    result += format_conditions_enclosure[0]
                    #напряжение
                    if component.DIODE_capacitance_voltage is not None:
                        ranges = ((1e0, MetricMultiplier.NONE), (10e3, MetricMultiplier.KILO))
                        result += _assemble_param_value(component.DIODE_capacitance_voltage, lcl.Units.VOLT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                        result += format_conditions_delimiter
                    #частота
                    if component.DIODE_capacitance_frequency is not None:
                        ranges = ((1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO), (1e6, MetricMultiplier.MEGA), (1e9, MetricMultiplier.GIGA))
                        result += _assemble_param_value(component.DIODE_capacitance_frequency, lcl.Units.HERTZ, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                        result += format_conditions_delimiter
                    result = string_strip_word(result, format_conditions_delimiter)
                    result += format_conditions_enclosure[1]
                result += format_param_delimiter

            #корпус
            if component.GENERIC_package is not None:
                result += lcl.Labels.PACKAGE.value[locale_index] + '\xa0' + component.GENERIC_package 
                result += format_param_delimiter

        #--- --- TVS
        elif type(component) is component.types.TVS:
            #тип
            if component.TVS_type == component.Type.DIODE:          #диод
                result += lcl.Labels.TVS_TYPE_DIODE.value[locale_index]
                result += format_param_delimiter

                #двунаправленный тип
                if component.TVS_bidirectional is not None:
                    if component.TVS_bidirectional:
                        result += lcl.Labels.TVS_BIDIRECTIONAL.value[locale_index]
                    else:
                        result += lcl.Labels.TVS_UNIDIRECTIONAL.value[locale_index]
                    result += format_param_delimiter

                #максимальное рабочее напряжение
                if component.TVS_standoff_voltage is not None:
                    ranges = ((1e0, MetricMultiplier.NONE), (10e3, MetricMultiplier.KILO))
                    result += _assemble_param_value(component.TVS_standoff_voltage, lcl.Units.VOLT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                    result += format_param_delimiter

                #мощность + тип тестового импульса
                if component.TVS_power is not None:
                    ranges = ((1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO))
                    result += _assemble_param_value(component.TVS_power, lcl.Units.WATT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                    if component.TVS_testPulse is not None:
                        result += format_conditions_enclosure[0]
                        if component.TVS_testPulse == component.TestPulse.US_8_20:
                            result += '8/20' + format_unit_enclosure[0] + lcl.MetricPrefix.MICRO.value[locale_index] + lcl.Units.SECOND.value[locale_index] + format_unit_enclosure[1]
                        elif component.TVS_testPulse == component.TestPulse.US_10_1000:
                            result += '10/1000' + format_unit_enclosure[0] + lcl.MetricPrefix.MICRO.value[locale_index] + lcl.Units.SECOND.value[locale_index] + format_unit_enclosure[1]
                        else:
                            result += '???'
                        result += format_conditions_enclosure[1]
                    result += format_param_delimiter

                #корпус
                if component.GENERIC_package is not None:
                    result += lcl.Labels.PACKAGE.value[locale_index] + '\xa0' + component.GENERIC_package 
                    result += format_param_delimiter

            elif component.TVS_type == component.Type.VARISTOR:     #варистор
                result += lcl.Labels.TVS_TYPE_VARISTOR.value[locale_index]
                result += format_param_delimiter

                #тип + размер
                if component.GENERIC_mount == component.Mounting.Type.SURFACE: result += lcl.Labels.MOUNT_SURFACE.value[locale_index]
                elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE: result += lcl.Labels.MOUNT_THROUGHHOLE.value[locale_index]
                result += '\xa0'
                if component.GENERIC_size is not None: result += component.GENERIC_size
                result = result.strip('\xa0')
                result += format_param_delimiter
                
                #максимальное рабочее напряжение
                if component.TVS_standoff_voltage is not None:
                    ranges = ((1e0, MetricMultiplier.NONE), (10e3, MetricMultiplier.KILO))
                    result += _assemble_param_value(component.TVS_standoff_voltage, lcl.Units.VOLT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                    result += format_param_delimiter
                
                #энергия + тип тестового импульса
                if component.TVS_energy is not None:
                    ranges = ((1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO))
                    result += _assemble_param_value(component.TVS_energy, lcl.Units.JOULE, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                    if component.TVS_testPulse is not None:
                        result += format_conditions_enclosure[0]
                        if component.TVS_testPulse == component.TestPulse.US_8_20:
                            result += '8/20' + format_unit_enclosure + lcl.MetricPrefix.MICRO.value[locale_index] + lcl.Units.SECOND.value[locale_index] 
                        elif component.TVS_testPulse == component.TestPulse.US_10_1000:
                            result += '10/1000' + format_unit_enclosure + lcl.MetricPrefix.MICRO.value[locale_index] + lcl.Units.SECOND.value[locale_index] 
                        else:
                            result += '???'
                        result += format_conditions_enclosure[1]
                    result += format_param_delimiter

        #--- --- Фильтр ЭМП
        elif type(component) is component.types.EMIFilter:
            #тип
            if component.EMIF_type == component.Type.FERRITE_BEAD:
                result += lcl.Labels.FERRITE_BEAD.value[locale_index]
            elif component.EMIF_type == component.Type.COMMON_MODE_CHOKE:
                result += lcl.Labels.COMMON_MODE_CHOKE.value[locale_index]
            if len(result) > 0: result += format_param_delimiter

            #тип монтажа + размер
            if component.GENERIC_mount == component.Mounting.Type.SURFACE:
                result += lcl.Labels.MOUNT_SURFACE.value[locale_index]
                if component.GENERIC_size is not None: 
                    result +=  '\xa0' + component.GENERIC_size
                result += format_param_delimiter
            elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE:
                result += lcl.Labels.MOUNT_THROUGHHOLE.value[locale_index]
                if component.GENERIC_size is not None: 
                    result +=  '\xa0' + component.GENERIC_size
                result += format_param_delimiter

            #импеданс + допуск + частота
            if component.EMIF_impedance is not None:
                ranges = ((1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO))
                result += _assemble_param_value(component.EMIF_impedance, lcl.Units.OHM, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                if component.EMIF_impedance_tolerance is not None:
                    result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.EMIF_impedance_tolerance, None, format_decimalPoint, format_unit_enclosure, format_tolerance_signDelimiter, format_rangeSymbol, locale_index) + format_tolerance_enclosure[1]
                if component.EMIF_impedance_frequency is not None:
                    result += format_conditions_enclosure[0]
                    ranges = ((1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO), (1e6, MetricMultiplier.MEGA), (1e9, MetricMultiplier.GIGA))
                    result += _assemble_param_value(component.EMIF_impedance_frequency, lcl.Units.HERTZ, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                    result += format_conditions_enclosure[1]
                result += format_param_delimiter

            #индуктивность + допуск
            if component.EMIF_inductance is not None:
                ranges = ((1e-9, MetricMultiplier.NANO), (1e-6, MetricMultiplier.MICRO), (1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE))
                result += _assemble_param_value(component.EMIF_inductance, lcl.Units.HENRY, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                if component.EMIF_inductance_tolerance is not None:
                    result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.EMIF_inductance_tolerance, None, format_decimalPoint, format_unit_enclosure, format_tolerance_signDelimiter, format_rangeSymbol, locale_index) + format_tolerance_enclosure[1]
                result += format_param_delimiter

            #ёмкость + допуск
            if component.EMIF_capacitance is not None:
                ranges = ((1e-12, MetricMultiplier.PICO), (1e-9, MetricMultiplier.NANO), (1e-6, MetricMultiplier.MICRO), (0.1e0, MetricMultiplier.NONE))
                result += _assemble_param_value(component.EMIF_capacitance, lcl.Units.FARAD, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                if component.EMIF_capacitance_tolerance is not None:
                    result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.EMIF_capacitance_tolerance, None, format_decimalPoint, format_unit_enclosure, format_tolerance_signDelimiter, format_rangeSymbol, locale_index) + format_tolerance_enclosure[1]
                result += format_param_delimiter

            #сопротивление + допуск
            if component.EMIF_resistance is not None:
                ranges = ((1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO))
                result += _assemble_param_value(component.EMIF_resistance, lcl.Units.OHM, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                if component.EMIF_resistance_tolerance is not None:
                    result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.EMIF_resistance_tolerance, None, format_decimalPoint, format_unit_enclosure, format_tolerance_signDelimiter, format_rangeSymbol, locale_index) + format_tolerance_enclosure[1]
                result += format_param_delimiter

            #номинальный ток
            if component.EMIF_current is not None:
                ranges = ((1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO))
                result += _assemble_param_value(component.EMIF_current, lcl.Units.AMPERE, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #максимальное напряжение
            if component.EMIF_voltage is not None:
                ranges = ((1e0, MetricMultiplier.NONE), (10e3, MetricMultiplier.KILO))
                result += _assemble_param_value(component.EMIF_voltage, lcl.Units.VOLT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

        #--- --- Предохранитель
        elif type(component) is component.types.CircuitBreaker:
            #тип
            if component.CBRK_type == component.Type.FUSE:
                result += lcl.Labels.CBRK_TYPE_FUSE.value[locale_index]
            elif component.CBRK_type == component.Type.PTC_RESETTABLE:
                result += lcl.Labels.CBRK_TYPE_PTCRESETTABLE.value[locale_index]
            elif component.CBRK_type == component.Type.THERMAL:
                result += lcl.Labels.CBRK_TYPE_THERMAL.value[locale_index]
            if len(result) > 0: result += format_param_delimiter

            #тип монтажа + размер
            if component.GENERIC_mount == component.Mounting.Type.SURFACE: result += lcl.Labels.MOUNT_SURFACE.value[locale_index] + '\xa0'
            elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE: result += lcl.Labels.MOUNT_THROUGHHOLE.value[locale_index] + '\xa0'
            elif component.GENERIC_mount == component.Mounting.Type.HOLDER: result += lcl.Labels.MOUNT_HOLDER.value[locale_index] + '\xa0'
            if component.GENERIC_size is not None: result += component.GENERIC_size
            result = result.strip('\xa0')
            result += format_param_delimiter

            #номинальный ток
            if component.CBRK_current_rating is not None:
                ranges = ((1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO))
                result += _assemble_param_value(component.CBRK_current_rating, lcl.Units.AMPERE, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #точка плавления
            if component.CBRK_meltingPoint is not None:
                ranges = ((1e0, MetricMultiplier.NONE), )
                result += _assemble_param_value(component.CBRK_meltingPoint, lcl.Units.AMPERE.value[locale_index]  + '²' + lcl.Units.SECOND.value[locale_index], format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #максимальное напряжение
            if component.CBRK_voltage is not None:
                ranges = ((1e0, MetricMultiplier.NONE), (10e3, MetricMultiplier.KILO))
                result += _assemble_param_value(component.CBRK_voltage, lcl.Units.VOLT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                if component.CBRK_voltage_ac: result += '\xa0' + lcl.Labels.VOLTAGE_AC.value[locale_index]
                result += format_param_delimiter

            #сопротивление
            if component.CBRK_resistance is not None:
                ranges = ((1e-6, MetricMultiplier.MICRO), (1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE))
                result += _assemble_param_value(component.CBRK_resistance, lcl.Units.OHM, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #максимальная мощность
            if component.CBRK_power is not None:
                ranges = ((1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO))
                result += _assemble_param_value(component.CBRK_power, lcl.Units.WATT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #классификация скорости срабатывания
            if component.CBRK_speed_grade is not None:
                if component.CBRK_speed_grade == component.SpeedGrade.FAST: result += lcl.Labels.CBRK_SPEEDGRADE_FAST.value[locale_index] + format_param_delimiter
                elif component.CBRK_speed_grade == component.SpeedGrade.MEDIUM: result += lcl.Labels.CBRK_SPEEDGRADE_MEDIUM.value[locale_index] + format_param_delimiter
                elif component.CBRK_speed_grade == component.SpeedGrade.SLOW: result += lcl.Labels.CBRK_SPEEDGRADE_SLOW.value[locale_index] + format_param_delimiter

        #--- --- Резонатор
        elif type(component) is component.types.Oscillator:
            #тип
            if component.OSC_type == component.Type.CRYSTAL:
                result += lcl.Labels.OSC_TYPE_CRYSTAL.value[locale_index]
            elif component.OSC_type == component.Type.CERAMIC:
                result += lcl.Labels.OSC_TYPE_CERAMICS.value[locale_index]
            elif component.OSC_type == component.Type.MEMS:
                result += lcl.Labels.OSC_TYPE_MEMS.value[locale_index]
            if len(result) > 0: result += format_param_delimiter

            #частота + допуск
            if component.OSC_frequency is not None:
                ranges = ((1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO), (1e6, MetricMultiplier.MEGA), (1e9, MetricMultiplier.GIGA))
                result += _assemble_param_value(component.OSC_frequency, lcl.Units.HERTZ, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                if component.OSC_tolerance is not None:
                    result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.OSC_tolerance, None, format_decimalPoint, format_unit_enclosure, format_tolerance_signDelimiter, format_rangeSymbol, locale_index) + format_tolerance_enclosure[1]
                result += format_param_delimiter

            #гармоника
            if component.OSC_overtone is not None:
                if component.OSC_overtone == 1:
                    result += lcl.Labels.OSC_OVERTONE_FUNDAMENTAL.value[locale_index]
                else:
                    result += str(component.OSC_overtone) + '\xa0' + lcl.Labels.OSC_OVERTONE.value[locale_index]
                result += format_param_delimiter

            #стабильность частоты
            if component.OSC_stability is not None:
                result += _assemble_param_tolerance(component.OSC_stability, None, format_decimalPoint, format_unit_enclosure, format_tolerance_signDelimiter, format_rangeSymbol, locale_index)
                result += format_param_delimiter

            #ёмкость нагрузки
            if component.OSC_loadCapacitance is not None:
                ranges = ((1e-12, MetricMultiplier.PICO), )
                result += _assemble_param_value(component.OSC_loadCapacitance, lcl.Units.FARAD, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #эквивалентное последовательное сопротивление
            if component.OSC_ESR is not None:
                ranges = ((1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO))
                result += _assemble_param_value(component.OSC_ESR, lcl.Units.OHM, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #уровень возбуждения
            if component.OSC_driveLevel is not None:
                ranges = ((1e-6, MetricMultiplier.MICRO), (1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE))
                result += _assemble_param_value(component.OSC_driveLevel, lcl.Units.WATT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #диапазон рабочих температур
            if component.GENERIC_temperature_range is not None:
                result += _assemble_param_temperature_range(component.GENERIC_temperature_range, lcl.Units.CELCIUS_DEG.value[locale_index] , format_decimalPoint, format_unit_enclosure, format_tolerance_signDelimiter, format_rangeSymbol)
                result += format_param_delimiter

        #--- --- Светодиод
        elif type(component) is component.types.LED:
            #тип
            if component.LED_type == component.Type.INDICATION:
                result += lcl.Labels.LED_TYPE_INDICATOR.value[locale_index]
            elif component.LED_type == component.Type.LIGHTING:
                result += lcl.Labels.LED_TYPE_LIGHTING.value[locale_index]
            if len(result) > 0: result += format_param_delimiter

            #тип монтажа + размер
            if component.GENERIC_mount == component.Mounting.Type.SURFACE:
                result += lcl.Labels.MOUNT_SURFACE.value[locale_index]
                if component.GENERIC_size is not None: 
                    result +=  '\xa0' + component.GENERIC_size
                result += format_param_delimiter
            elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE:
                result += lcl.Labels.MOUNT_THROUGHHOLE.value[locale_index]
                if component.GENERIC_size is not None: 
                    result +=  '\xa0' + component.GENERIC_size
                result += format_param_delimiter

            #цвет
            if component.LED_color is not None:
                if   component.LED_color == component.Color.INFRARED:    result += lcl.Color.INFRARED.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.ULTRAVIOLET: result += lcl.Color.ULTRAVIOLET.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.RED:         result += lcl.Color.RED.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.ORANGE:      result += lcl.Color.ORANGE.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.AMBER:       result += lcl.Color.AMBER.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.YELLOW:      result += lcl.Color.YELLOW.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.LIME:        result += lcl.Color.LIME.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.GREEN:       result += lcl.Color.GREEN.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.TURQUOISE:   result += lcl.Color.TURQUOISE.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.CYAN:        result += lcl.Color.CYAN.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.BLUE:        result += lcl.Color.BLUE.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.VIOLET:      result += lcl.Color.VIOLET.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.PURPLE:      result += lcl.Color.PURPLE.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.PINK:        result += lcl.Color.PINK.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.MULTI:       result += lcl.Color.MULTI.value[locale_index] + format_param_delimiter
                elif component.LED_color == component.Color.WHITE:       result += lcl.Color.WHITE.value[locale_index] + format_param_delimiter
                    
            #цветовая температура
            if component.LED_color_temperature is not None:
                result += '\xa0' + _floatToString(component.LED_color_temperature, format_decimalPoint) + format_unit_enclosure + lcl.Units.KELVIN.value[locale_index] 
                result += format_param_delimiter
                
            #длина волны
            if component.LED_wavelength_peak is not None:
                value = [component.LED_wavelength_peak]
                if component.LED_wavelength_dominant is not None: value.append(component.LED_wavelength_dominant)
                ranges = ((1e-9, MetricMultiplier.NANO), )
                result += _assemble_param_value(value, lcl.Units.METRE, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #индекс цветопередачи
            if component.LED_color_renderingIndex is not None:
                result += lcl.Labels.LED_CRI.value[locale_index] + format_unit_enclosure + _floatToString(component.LED_color_renderingIndex, format_decimalPoint)
                result += format_param_delimiter

            #сила света
            if component.LED_luminous_intensity is not None:
                ranges = ((1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE))
                result += _assemble_param_value(component.LED_luminous_intensity, lcl.Units.CANDELA, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                if component.LED_luminous_intensity_current is not None:
                    result += format_conditions_enclosure[0]
                    ranges = ((1e-6, MetricMultiplier.MICRO), (1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE))
                    result += _assemble_param_value(component.LED_luminous_intensity_current, lcl.Units.AMPERE, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                    result += format_conditions_enclosure[1]
                result += format_param_delimiter

            #световой поток
            if component.LED_luminous_flux is not None:
                ranges = ((1e0, MetricMultiplier.NONE), )
                result += _assemble_param_value(component.LED_luminous_flux, lcl.Units.LUMEN, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                if component.LED_luminous_flux_current is not None:
                    result += format_conditions_enclosure[0]
                    ranges = ((1e-6, MetricMultiplier.MICRO), (1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE))
                    result += _assemble_param_value(component.LED_luminous_flux_current, lcl.Units.AMPERE, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                    result += format_conditions_enclosure[1]
                result += format_param_delimiter

            #угол обзора
            if component.LED_viewingAngle is not None:
                ranges = ((1e0, MetricMultiplier.NONE), )
                result += _assemble_param_value(component.LED_viewingAngle, lcl.Units.DEGREE, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #прямой ток
            if component.LED_current_nominal is not None:
                value = [component.LED_current_nominal]
                if component.LED_current_maximum is not None: value.append(component.LED_current_maximum)
                ranges = ((1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE))
                result += _assemble_param_value(value, lcl.Units.AMPERE, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #прямое падение напряжения
            if component.LED_voltage_forward is not None:
                ranges = ((1e0, MetricMultiplier.NONE), )
                result += _assemble_param_value(component.LED_voltage_forward, lcl.Units.VOLT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                result += format_param_delimiter

            #сборка
            if component.GENERIC_array is not None:
                result += lcl.Labels.ARRAY.value[locale_index]
                result += format_param_delimiter

        #--- --- Общий тип
        else:
            pass

    #дополнительные параметры
    if content_misc:
        for item in component.GENERIC_misc:
            result += item
            result += format_param_delimiter

    #удаляем лишние разделители
    result = string_strip_word(result, format_param_delimiter)

    return result

#сборка списка замен
def assemble_substitutes(component, **kwargs):
    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры содержимого
    content_value        = kwargs.get('content_subst_value', True)
    content_manufacturer = kwargs.get('content_subst_manufacturer', True)
    content_note         = kwargs.get('content_subst_note', True)

    #параметры формата
    format_entry_enclosure        = kwargs.get('format_subst_entry_enclosure', ['\nдоп.\xa0замена ', ''])
    format_value_enclosure        = kwargs.get('format_subst_value_enclosure', ['', ''])
    format_manufacturer_enclosure = kwargs.get('format_subst_manufacturer_enclosure', [' ф.\xa0', ''])
    format_note_enclosure         = kwargs.get('format_subst_note_enclosure', [' (', ')'])

    result = ''
    if component.GENERIC_substitute is not None:
        for substitute in component.GENERIC_substitute:
            result += format_entry_enclosure[0]
            if content_value and substitute.value is not None: result += format_value_enclosure[0] + substitute.value + format_value_enclosure[1]
            if content_manufacturer and substitute.manufacturer is not None: result += format_manufacturer_enclosure[0] + substitute.manufacturer + format_manufacturer_enclosure[1]
            if content_note and substitute.note is not None: result += format_note_enclosure[0] + substitute.note + format_note_enclosure[1]
            result += format_entry_enclosure[1]
    return result

#сборка параметра: значение
def _assemble_param_value(param, unit = None, decimalPoint = '.', unitEnclosure = ['', ''], multivalueDelimiter = '/', locale_index = 0, ranges = None):
    if isinstance(param, (int, float)): param = [param]         #если числовое значение, а не массив то делаем его массивом
    if not isinstance(param, (list, tuple)): return '<ERROR>'

    #если единицы измерения не заданы то приставку добавлять некуда
    if unit is None:
        unit_str = ''
        prefix = ''
        multiplier = MetricMultiplier.NONE
    else:
        #определяем единицы измерения
        if isinstance(unit, lcl.Units):
            unit_str = unit.value[locale_index]
        else:
            unit_str = str(unit)

        #задаём диапазоны
        if ranges is None:
            #список диапазонов должен быть отсортирован по возрастанию
            ranges = ((0,     MetricMultiplier.NONE),
                      (1e-12, MetricMultiplier.PICO),
                      (1e-9,  MetricMultiplier.NANO),
                      (1e-6,  MetricMultiplier.MICRO),
                      (1e-3,  MetricMultiplier.MILLI),
                      (1e0,   MetricMultiplier.NONE),
                      (1e3,   MetricMultiplier.KILO),
                      (1e6,   MetricMultiplier.MEGA),
                      (1e9,   MetricMultiplier.GIGA))

        #определяем среднее значение исключая нули
        scope = 0; i = 0
        for p in param:
            if p != 0: scope += abs(p); i += 1
        if i > 0: scope = scope / i

        #определяем множитель
        if scope == 0:
            #обрабатываем частный случай когда значение равно 0
            multiplier = ranges[0][1]
        else:
            i = 1
            if ranges[0][0] == 0: i += 1
            while i < len(ranges):
                multiplier = ranges[i - 1][1]
                if scope < ranges[i][0]: break
                i += 1
            else:
                multiplier = ranges[-1][1]

        #получаем префикс
        for entry in lcl.MetricPrefix:
            if entry.name == multiplier.name: prefix = entry.value[locale_index]

    #получаем строковое значение
    for i in range(len(param)):
        param[i] = _floatToString(param[i] / multiplier.value, decimalPoint)

    return multivalueDelimiter.join(param) + unitEnclosure[0] + prefix + unit_str + unitEnclosure[1]

#сборка параметра: допуск
def _assemble_param_tolerance(param, unit = None, decimalPoint = '.', unitEnclosure = ['', ''], signToToleranceDelimiter = '', rangeSymbol = '\u2026', locale_index = 0):
    if param[2] is None:
        #допуск указан в долях от значения
        if unit is None:
            #определение единиц измерения автоматически исходя из значения параметра
            abs_max_value = max(abs(param[0]), abs(param[1]))
            abs_min_value = min(abs(param[0]), abs(param[1]))
            if   abs_max_value < 1e-6: unit = lcl.Units.PPB.value[locale_index]
            elif abs_max_value < 1e-3: unit = lcl.Units.PPM.value[locale_index]
            else:                      unit = lcl.Units.PERCENT.value[locale_index]
        #определение множителя из едениц измерения
        if   unit == lcl.Units.PERCENT.value[locale_index]:  multiplier = 100
        elif unit == lcl.Units.PERMILLE.value[locale_index]: multiplier = 1e3
        elif unit == lcl.Units.PPM.value[locale_index]:      multiplier = 1e6
        elif unit == lcl.Units.PPB.value[locale_index]:      multiplier = 1e9
        else: multiplier = 1
    else:
        #допуск указан в каких-то единицах измерения
        multiplier = 1
        unit = param[2]
        #нужно сделать перевод единиц измерения (например если они заданы латиницей)

    if -param[0] == param[1]:
        return "±" + signToToleranceDelimiter + _floatToString(param[1] * multiplier, decimalPoint) + unitEnclosure[0] + unit + unitEnclosure[1]
    else:
        return "+" + signToToleranceDelimiter + _floatToString(param[1] * multiplier, decimalPoint) + rangeSymbol + "-" + signToToleranceDelimiter + _floatToString(-param[0] * multiplier, decimalPoint) + unitEnclosure[0] + unit + unitEnclosure[1]

#сборка параметра: диапазон рабочих температур
def _assemble_param_temperature_range(param, unit = 'K', decimalPoint = '.', unitEnclosure = ['', ''], signToToleranceDelimiter = '', rangeSymbol = '\u2026'):
    lower_sign = ''
    upper_sign = ''
    lower_value = param[0]
    upper_value = param[1]
    
    if unit is None:
        unit = ''
        unitEnclosure = ['', '']
    elif (unit == '℃') or (unit == '°C'):
        offset = 273.15
        lower_value -= offset
        upper_value -= offset

        if lower_value < 0:
            lower_sign = '-'
            lower_value = -lower_value
        elif lower_value > 0:
            lower_sign = '+'
    
        if upper_value < 0:
            upper_sign = '-'
            upper_value = -upper_value
        elif upper_value > 0:
            upper_sign = '+'

    return lower_sign + signToToleranceDelimiter + _floatToString(lower_value, decimalPoint) + rangeSymbol + upper_sign + signToToleranceDelimiter + _floatToString(upper_value, decimalPoint) + unitEnclosure[0] + unit + unitEnclosure[1]
