import os
from copy import deepcopy
import enum
import dict_locale as lcl
from typedef_designator import Designator                                                           #класс десигнатора
import typedef_components as Components                                                            #класс базы данных компонентов
import typedef_pnp as PickPlace

script_dirName  = os.path.dirname(__file__)                                                          #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                                    #базовое имя модуля

#Значения строки таблицы перечня
class eskdValue():
    def __init__(self, designator = '', label = '', quantity = 0, annotation = ''):
        self.designator = designator
        self.label      = label
        self.quantity   = int(quantity)
        self.annotation = annotation

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
def _floatToString(value:float, decimalPoint:str = '.', positiveSign:bool = False) -> str:
    result = '{0:.10f}'.format(value)
    result = result.rstrip('0').rstrip('.')
    result = result.replace('.', decimalPoint)
    if positiveSign and value > 0:
        result = "+" + result
    return result

#========================================================== END Generic functions =================================================

#сборка ЕСКД из параметров компонента
def assemble_eskd(component:Components.Component.Generic, **kwargs):
    #locale
    locale = kwargs.get('locale', lcl.Locale.RU)

    #параметры содержимого полей
    content_partnumber     = kwargs.get('content_partnumber', True)
    content_partnumber_explicit = kwargs.get('content_partnumber_explicit', False)
    content_manufacturer   = kwargs.get('content_mfr', True)
    content_parameters     = kwargs.get('content_param', True)
    content_substitutes    = kwargs.get('content_subst', True)
    content_annot          = kwargs.get('content_annot', True)

    #параметры формата
    format_annot_enclosure      = kwargs.get('format_annot_enclosure', ['', ''])
    format_partnumber_enclosure = kwargs.get('format_partnumber_enclosure', ['', ''])
    format_mfr_enclosure        = kwargs.get('format_mfr_enclosure',   [' ф.\xa0', ''])
    format_param_enclosure      = kwargs.get('format_param_enclosure', ['', ''])
    format_subst_enclosure      = kwargs.get('format_subst_enclosure', ['', ''])

    #инициализируем переменные
    result = eskdValue()

    #Базовые поля
    result.designator = assemble_designator(component.GNRC_designator, **kwargs)
    result.quantity   = assemble_quantity(component, **kwargs)
    
    #Наименование
    #--- артикул
    if content_partnumber:
        if content_partnumber_explicit or (not component.GNRC_parametric) or (not content_parameters):
            value = assemble_partnumber(component, **kwargs)
            if len(value) > 0:
                result.label += format_partnumber_enclosure[0] + value + format_partnumber_enclosure[1]
                #--- производитель (указываем только если есть номинал)
                if content_manufacturer is not False:
                    manufacturer = assemble_manufacturer(component, **kwargs)
                    if len(manufacturer) > 0: result.label += format_mfr_enclosure[0] + manufacturer + format_mfr_enclosure[1]

    #--- параметрическое описание
    if content_parameters:
        parameters = assemble_parameters(component, **kwargs)              #собираем параметрическое описание
        if len(parameters) > 0:
            if len(result.label) == 0: result.label += parameters              #если до этого было пусто то пишем без ограждения
            else: result.label += format_param_enclosure[0] + parameters + format_param_enclosure[1]

    #--- допустимые замены
    if content_substitutes:
        substitutes = assemble_substitutes(component, **kwargs)
        if len(substitutes) > 0:
            result.label += format_subst_enclosure[0] + substitutes + format_subst_enclosure[1]

    #Примечание
    if content_annot:
        result.annotation = assemble_annotation(component, **kwargs)
        if len(result.annotation) > 0: result.annotation = format_annot_enclosure[0] + result.annotation + format_annot_enclosure[1]

    return result

#сборка десигнатора
def assemble_designator(designator:Designator, **kwargs):
    #locale
    locale = kwargs.get('locale', lcl.Locale.RU)

    #параметры сборки
    assemble_desig = kwargs.get('assemble_designator', False)

    result = ''
    if designator is not None:
        if assemble_desig:
            result += designator.prefix + designator.index
            if designator.channel is not None:
                result += designator.channel.enclosure[0] + designator.channel.prefix + designator.channel.index + designator.channel.enclosure[1]
        else:
            result += designator.full
    return result

#сборка количества
def assemble_quantity(component, **kwargs):
    #locale
    locale = kwargs.get('locale', lcl.Locale.RU)

    #параметры формата
    format_fitted_quantity = kwargs.get('format_fitted_quantity', [-1, -1])

    if component.GNRC_fitted:
        if format_fitted_quantity[0] < 0:
            return component.GNRC_quantity
        else:
            return format_fitted_quantity[0]
    else:
        if format_fitted_quantity[1] < 0:
            return component.GNRC_quantity
        else:
            return format_fitted_quantity[1]

#сборка типа компонента
def assemble_kind(component, **kwargs):
    #locale
    locale= kwargs.get('locale', lcl.Locale.RU)

    #параметры сборки
    assemble_kind = kwargs.get('assemble_kind', True)

    #параметры формата
    format_capitalize = kwargs.get('format_kind_capitalize', False)

    result = ''
    if assemble_kind:
        #Сборка (Устройство)
        if isinstance(component, Components.Component.Assembly):
            result = locale.translate(lcl.assemble_kind.ASSEMBLY)

        #Фотоэлемент
        elif isinstance(component, Components.Component.Photocell):
            result = locale.translate(lcl.assemble_kind.PHOTO_CELL)
            if component.PHOTO_type == component.Type.DIODE:        result = locale.translate(lcl.assemble_kind.PHOTO_DIODE)
            elif component.PHOTO_type == component.Type.TRANSISTOR: result = locale.translate(lcl.assemble_kind.PHOTO_TRANSISTOR)
            elif component.PHOTO_type == component.Type.RESISTOR:   result = locale.translate(lcl.assemble_kind.PHOTO_RESISTOR)

        #Конденсатор
        elif isinstance(component, Components.Component.Capacitor):
            result = locale.translate(lcl.assemble_kind.CAPACITOR)

        #Микросхема
        elif isinstance(component, Components.Component.IntegratedCircuit):
            result = locale.translate(lcl.assemble_kind.INTEGRATED_CIRCUIT)

        #Крепёж
        elif type(component) is Components.Component.Fastener:
            result = locale.translate(lcl.assemble_kind.FASTENER)

        #Радиатор
        elif type(component) is Components.Component.Heatsink:
            result = locale.translate(lcl.assemble_kind.HEATSINK)

        #Автоматический выключатель (Предохранитель)
        elif isinstance(component, Components.Component.CircuitBreaker):
            result = locale.translate(lcl.assemble_kind.CIRCUIT_BREAKER)
            if   component.CBRK_type == Components.Component.CircuitBreaker.Type.FUSE:                result = locale.translate(lcl.assemble_kind.FUSE)
            elif component.CBRK_type == Components.Component.CircuitBreaker.Type.FUSE_PTC_RESETTABLE: result = locale.translate(lcl.assemble_kind.FUSE_PTC_RESETTABLE)
            elif component.CBRK_type == Components.Component.CircuitBreaker.Type.FUSE_THERMAL:        result = locale.translate(lcl.assemble_kind.FUSE_THERMAL)

        #Ограничитель перенапряжения
        elif isinstance(component, Components.Component.SurgeProtector):
            result = locale.translate(lcl.assemble_kind.SURGE_PROTECTOR)
            if   component.SPD_type == Components.Component.SurgeProtector.Type.DIODE:              result = locale.translate(lcl.assemble_kind.TVS_DIODE)
            elif component.SPD_type == Components.Component.SurgeProtector.Type.THYRISTOR:          result = locale.translate(lcl.assemble_kind.TVS_THYRISTOR)
            elif component.SPD_type == Components.Component.SurgeProtector.Type.VARISTOR:           result = locale.translate(lcl.assemble_kind.VARISTOR)
            elif component.SPD_type == Components.Component.SurgeProtector.Type.GAS_DISCHARGE_TUBE: result = locale.translate(lcl.assemble_kind.GAS_DISCHARGE_TUBE)
            elif component.SPD_type == Components.Component.SurgeProtector.Type.IC:                 result = locale.translate(lcl.assemble_kind.SURGE_PROTECTOR)

        #Батарея
        elif isinstance(component, Components.Component.Battery):
            result = locale.translate(lcl.assemble_kind.BATTERY)

        #Дисплей
        elif isinstance(component, Components.Component.Display):
            result = locale.translate(lcl.assemble_kind.DISPLAY)

        #Светодиод
        elif isinstance(component, Components.Component.LED):
            result = locale.translate(lcl.assemble_kind.LED)

        #Перемычка
        elif isinstance(component, Components.Component.Jumper):
            result = locale.translate(lcl.assemble_kind.JUMPER)

        #Реле
        elif isinstance(component, Components.Component.Relay):
            result = locale.translate(lcl.assemble_kind.RELAY)

        #Индуктивность
        elif isinstance(component, Components.Component.Inductor):
            result = locale.translate(lcl.assemble_kind.INDUCTOR)
            if component.IND_type == Components.Component.Inductor.Type.CHOKE: result = locale.translate(lcl.assemble_kind.CHOKE)

        #Резистор
        elif isinstance(component, Components.Component.Resistor):
            result = locale.translate(lcl.assemble_kind.RESISTOR)
            if component.RES_type == Components.Component.Resistor.Type.VARIABLE: result = locale.translate(lcl.assemble_kind.POTENTIOMETER)

        #Переключатель
        elif isinstance(component, Components.Component.Switch):
            result = locale.translate(lcl.assemble_kind.SWITCH)

        #Трансформатор
        elif isinstance(component, Components.Component.Transformer):
            result = locale.translate(lcl.assemble_kind.TRANSFORMER)

        #Диод
        elif isinstance(component, Components.Component.Diode):
            result = locale.translate(lcl.assemble_kind.DIODE)
            if   component.DIODE_type == Components.Component.Diode.Type.ZENER:   result = locale.translate(lcl.assemble_kind.ZENER_DIODE)
            elif component.DIODE_type == Components.Component.Diode.Type.VARICAP: result = locale.translate(lcl.assemble_kind.VARICAP)

        #Тиристор
        elif isinstance(component, Components.Component.Thyristor):
            result = locale.translate(lcl.assemble_kind.THYRISTOR)
            if   component.THYR_type == Components.Component.Thyristor.Type.TRIAC:    result = locale.translate(lcl.assemble_kind.TRIAC)
            elif component.THYR_type == Components.Component.Thyristor.Type.DYNISTOR: result = locale.translate(lcl.assemble_kind.DYNISTOR)

        #Транзистор
        elif isinstance(component, Components.Component.Transistor):
            result = locale.translate(lcl.assemble_kind.TRANSISTOR)

        #Оптоизолятор
        elif isinstance(component, Components.Component.Optoisolator):
            result = locale.translate(lcl.assemble_kind.OPTOISOLATOR)
            if   component.OPTOISO_outputType == Components.Component.Optoisolator.OutputType.TRANSISTOR: result = locale.translate(lcl.assemble_kind.OPTOCOUPLER)
            elif component.OPTOISO_outputType == Components.Component.Optoisolator.OutputType.DARLINGTON: result = locale.translate(lcl.assemble_kind.OPTOCOUPLER)
            elif component.OPTOISO_outputType == Components.Component.Optoisolator.OutputType.LINEAR:     result = locale.translate(lcl.assemble_kind.OPTOCOUPLER)
            elif component.OPTOISO_outputType == Components.Component.Optoisolator.OutputType.TRIAC:      result = locale.translate(lcl.assemble_kind.PHOTOTRIAC)

        #Соединитель
        elif isinstance(component, Components.Component.Connector):
            result = locale.translate(lcl.assemble_kind.CONNECTOR)

        #Фильтр ЭМП
        elif isinstance(component, Components.Component.EMIFilter):
            result = locale.translate(lcl.assemble_kind.EMI_FILTER)

        #Осциллятор (Резонатор)
        elif isinstance(component, Components.Component.Oscillator):
            result = locale.translate(lcl.assemble_kind.OSCILLATOR)
            if component.OSC_type == component.Type.RESONATOR:
                result = locale.translate(lcl.assemble_kind.RESONATOR)
                if component.OSC_structure == component.Structure.QUARTZ:
                    result = locale.translate(lcl.assemble_kind.CRYSTAL)

        else:
            result = component.GNRC_kind
    else:
        result = component.GNRC_kind

    if format_capitalize:
        if len(result) > 0: result = result[0].upper() + result[1:]

    return result

#сборка примечания
def assemble_annotation(component, **kwargs):
    #locale
    locale = kwargs.get('locale', lcl.Locale.RU)

    #параметры содержимого
    content_annot_value = kwargs.get('content_annot_value', True)
    content_annot_fitted = kwargs.get('content_annot_fitted', True)

    #параметры формата
    format_annot_delimiter = kwargs.get('format_annot_delimiter', ';\n')
    format_fitted_label    = kwargs.get('format_fitted_label', [locale.translate(lcl.assemble_eskd.DO_PLACE), locale.translate(lcl.assemble_eskd.DO_NOT_PLACE)])

    result = ""
    if content_annot_value:
        if component.GNRC_note is not None:
            result = component.GNRC_note
    if content_annot_fitted:
        if component.GNRC_fitted:
            result += format_annot_delimiter + format_fitted_label[0]
        else:
            result += format_annot_delimiter + format_fitted_label[1]
    result = string_strip_word(result, format_annot_delimiter)
    return result

#сборка артикула
def assemble_partnumber(component, **kwargs):
    #locale
    locale = kwargs.get('locale', lcl.Locale.RU)

    #параметры содержимого
    content_value = kwargs.get('content_partnumber_value', True)

    result = ''
    if component.GNRC_partnumber is not None:
        if content_value: result += component.GNRC_partnumber

    return result

#сборка производителя
def assemble_manufacturer(component, **kwargs):
    #locale
    locale = kwargs.get('locale', lcl.Locale.RU)

    #параметры содержимого
    content_name = kwargs.get('content_mfr_value', True)

    result = ''
    if component.GNRC_manufacturer is not None:
        if content_name: result += component.GNRC_manufacturer
    
    return result

#сборка параметрической записи
def assemble_parameters(component, **kwargs):
    #локализация
    locale = kwargs.get('locale', lcl.Locale.RU)

    #параметры сборки
    assemble_param = kwargs.get('assemble_param', True)

    #параметры содержимого
    content_basic = kwargs.get('content_param_basic', True)
    content_misc  = kwargs.get('content_param_misc', True)

    #параметры формата
    format_delimiter                        = kwargs.get('format_param_delimiter', ', ')
    format_decimalPoint                     = kwargs.get('format_param_decimalPoint', '.')
    format_temperature_positiveSign         = kwargs.get('format_param_temperature_positiveSign', True)
    format_value_enclosure                  = kwargs.get('format_param_value_enclosure', ('', ''))
    format_value_multi_delimiter            = kwargs.get('format_param_value_multi_delimiter', '/')
    format_value_range_delimiter            = kwargs.get('format_param_value_range_delimiter', '\u2026')
    format_unit_enclosure                   = kwargs.get('format_param_unit_enclosure', ('', ''))
    format_tolerance_enclosure              = kwargs.get('format_param_tolerance_enclosure', ('\xa0', ''))
    format_tolerance_sym_sign               = kwargs.get('format_param_tolerance_sym_sign', '±')
    format_tolerance_sym_value_enclosure    = kwargs.get('format_param_tolerance_sym_value_enclosure', ('', ''))
    format_tolerance_asym_value_upperFirst  = kwargs.get('format_param_tolerance_asym_value_upperFirst', False)
    format_tolerance_asym_value_delimiter   = kwargs.get('format_param_tolerance_asym_value_delimiter', '\u2026')
    format_tolerance_asym_value_enclosure   = kwargs.get('format_param_tolerance_asym_value_enclosure', ('', ''))
    format_conditions_delimiter             = kwargs.get('format_param_conditions_delimiter', '; ')
    format_conditions_enclosure             = kwargs.get('format_param_conditions_enclosure', ('\xa0(', ')'))
    format_package_delimiter                = kwargs.get('format_param_package_delimiter', '\xa0')

    result = ''

    if assemble_param:
        #базовые параметры
        if content_basic:
            #Сборка (Устройство)
            if type(component) is Components.Component.Assembly:
                pass

            #Фотоэлемент
            elif type(component) is Components.Component.Photocell:
                pass

            #Конденсатор
            elif type(component) is Components.Component.Capacitor:
                #тип
                param_str = ''
                if component.CAP_type == Components.Component.Capacitor.Type.CERAMIC:
                    param_str = locale.translate(lcl.assemble_parameters.CAP_TYPE_CERAMIC)
                elif component.CAP_type == Components.Component.Capacitor.Type.TANTALUM:
                    param_str = locale.translate(lcl.assemble_parameters.CAP_TYPE_TANTALUM)
                elif component.CAP_type == Components.Component.Capacitor.Type.FILM:
                    param_str = locale.translate(lcl.assemble_parameters.CAP_TYPE_FILM)
                elif component.CAP_type == Components.Component.Capacitor.Type.ALUM_ELECTROLYTIC:
                    param_str = locale.translate(lcl.assemble_parameters.CAP_TYPE_ALUM_ELECTROLYTIC)
                elif component.CAP_type == Components.Component.Capacitor.Type.ALUM_POLYMER:
                    param_str = locale.translate(lcl.assemble_parameters.CAP_TYPE_ALUM_POLYMER)
                elif component.CAP_type == Components.Component.Capacitor.Type.ALUM_HYBRID:
                    param_str = locale.translate(lcl.assemble_parameters.CAP_TYPE_ALUM_HYBRID)
                elif component.CAP_type == Components.Component.Capacitor.Type.SUPERCAPACITOR:
                    param_str = locale.translate(lcl.assemble_parameters.CAP_TYPE_SUPERCAPACITOR)
                elif component.CAP_type == Components.Component.Capacitor.Type.NIOBIUM:
                    param_str = locale.translate(lcl.assemble_parameters.CAP_TYPE_NIOBIUM)
                elif component.CAP_type == Components.Component.Capacitor.Type.MICA:
                    param_str = locale.translate(lcl.assemble_parameters.CAP_TYPE_MICA)
                if param_str: result += param_str + format_delimiter

                #корпус
                if component.GNRC_package is not None:
                    result += _assemble_param_package(component.GNRC_package, locale, format_package_delimiter)
                    result += format_delimiter
                
                #диэлектрик
                if component.CAP_dielectric is not None:
                    result += component.CAP_dielectric
                    result += format_delimiter

                #напряжение
                if component.CAP_voltage is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), (10e3, lcl.Unit.Prefix.KILO))
                    result += _assemble_param_quantity(component.CAP_voltage, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #ёмкость + допуск
                if component.CAP_capacitance is not None and component.CAP_capacitance.value is not None:
                    ranges = ((1e-12, lcl.Unit.Prefix.PICO), (10e-9, lcl.Unit.Prefix.MICRO), (0.1e0, lcl.Unit.Prefix.NONE))
                    value = deepcopy(component.CAP_capacitance.value)
                    result += _assemble_param_quantity(value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.CAP_capacitance.tolerance is not None:
                        ranges = ()
                        result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.CAP_capacitance.tolerance, False, ranges, value.prefix, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure) + format_tolerance_enclosure[1]
                    result += format_delimiter

                #низкое эквивалентное сопротивление
                if component.CAP_lowESR:
                    result += locale.translate(lcl.assemble_parameters.LOW_ESR)
                    result += format_delimiter

            #Микросхема
            elif type(component) is Components.Component.IntegratedCircuit:
                pass

            #Крепёж
            elif type(component) is Components.Component.Fastener:
                pass

            #Радиатор
            elif type(component) is Components.Component.Heatsink:
                pass

            #Автоматический выключатель (Предохранитель)
            elif type(component) is Components.Component.CircuitBreaker:
                #тип
                param_str = ''
                if component.CBRK_type == Components.Component.CircuitBreaker.Type.FUSE:
                    param_str = locale.translate(lcl.assemble_parameters.CBRK_TYPE_FUSE)
                elif component.CBRK_type == Components.Component.CircuitBreaker.Type.FUSE_PTC_RESETTABLE:
                    param_str = locale.translate(lcl.assemble_parameters.CBRK_TYPE_FUSE_PTCRESETTABLE)
                elif component.CBRK_type == Components.Component.CircuitBreaker.Type.FUSE_THERMAL:
                    param_str = locale.translate(lcl.assemble_parameters.CBRK_TYPE_FUSE_THERMAL)
                elif component.CBRK_type == Components.Component.CircuitBreaker.Type.BREAKER:
                    param_str = locale.translate(lcl.assemble_parameters.CBRK_TYPE_BREAKER)
                elif component.CBRK_type == Components.Component.CircuitBreaker.Type.HOLDER:
                    param_str = locale.translate(lcl.assemble_parameters.CBRK_TYPE_HOLDER)
                if param_str: result += param_str + format_delimiter

                #корпус
                if component.GNRC_package is not None:
                    result += _assemble_param_package(component.GNRC_package, locale, format_package_delimiter)
                    result += format_delimiter

                #номинальный ток
                if component.CBRK_current_rating is not None:
                    ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO))
                    result += _assemble_param_quantity(component.CBRK_current_rating, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #точка плавления
                if component.CBRK_meltingPoint is not None:
                    ranges = ((0, lcl.Unit.Prefix.NONE), )
                    result += _assemble_param_quantity(component.CBRK_meltingPoint, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #максимальное напряжение
                if component.CBRK_voltage is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), (10e3, lcl.Unit.Prefix.KILO))
                    result += _assemble_param_quantity(component.CBRK_voltage, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.CBRK_voltage_ac: result += '\xa0' + locale.translate(lcl.assemble_parameters.VOLTAGE_AC)
                    result += format_delimiter

                #сопротивление
                if component.CBRK_resistance is not None:
                    ranges = ((1e-6, lcl.Unit.Prefix.MICRO), (1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                    result += _assemble_param_quantity(component.CBRK_resistance, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #максимальная мощность
                if component.CBRK_power is not None:
                    ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO))
                    result += _assemble_param_quantity(component.CBRK_power, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #классификация скорости срабатывания
                if component.CBRK_speed_grade is not None:
                    if   component.CBRK_speed_grade == Components.Component.CircuitBreaker.SpeedGrade.FAST:   result += locale.translate(lcl.assemble_parameters.CBRK_SPEEDGRADE_FAST)   + format_delimiter
                    elif component.CBRK_speed_grade == Components.Component.CircuitBreaker.SpeedGrade.MEDIUM: result += locale.translate(lcl.assemble_parameters.CBRK_SPEEDGRADE_MEDIUM) + format_delimiter
                    elif component.CBRK_speed_grade == Components.Component.CircuitBreaker.SpeedGrade.SLOW:   result += locale.translate(lcl.assemble_parameters.CBRK_SPEEDGRADE_SLOW)   + format_delimiter

            #Ограничитель перенапряжения
            elif type(component) is Components.Component.SurgeProtector:
                #тип
                if component.SPD_type == Components.Component.SurgeProtector.Type.DIODE:    #диод
                    result += locale.translate(lcl.assemble_parameters.SPD_TYPE_DIODE)
                    result += format_delimiter

                    #направленность
                    if component.SPD_bidirectional is not None:
                        if component.SPD_bidirectional: result += locale.translate(lcl.assemble_parameters.SPD_BIDIRECTIONAL)
                        else:                           result += locale.translate(lcl.assemble_parameters.SPD_UNIDIRECTIONAL)
                        result += format_delimiter

                    #максимальное рабочее напряжение
                    if component.SPD_voltage_standoff is not None and component.SPD_voltage_standoff.value is not None:
                        ranges = ((1e0, lcl.Unit.Prefix.NONE), (10e3, lcl.Unit.Prefix.KILO))
                        result += _assemble_param_quantity(component.SPD_voltage_standoff.value, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                        result += format_delimiter

                    #мощность + тип тестового импульса
                    if component.SPD_power is not None and component.SPD_power.value is not None:
                        ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO))
                        result += _assemble_param_quantity(component.SPD_power.value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                        if component.SPD_power.conditions:
                            conditions_str = ""
                            if Components.ParameterSpec.ConditionType.SURGE_WAVEFORM in component.SPD_power.conditions:
                                ranges = ()
                                conditions_str += _assemble_param_quantity(component.SPD_power.conditions[Components.ParameterSpec.ConditionType.SURGE_WAVEFORM], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                                conditions_str += format_conditions_delimiter
                            if Components.ParameterSpec.ConditionType.SURGE_DURATION in component.SPD_power.conditions:
                                ranges = ()
                                conditions_str += _assemble_param_quantity(component.SPD_power.conditions[Components.ParameterSpec.ConditionType.SURGE_DURATION], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                                conditions_str += format_conditions_delimiter
                            conditions_str = string_strip_word(conditions_str, format_conditions_delimiter)
                            if conditions_str: result += format_conditions_enclosure[0] + conditions_str + format_conditions_enclosure[1]
                        result += format_delimiter

                    #корпус
                    if component.GNRC_package is not None:
                        result += locale.translate(lcl.assemble_parameters.PACKAGE) + '\xa0' + component.GNRC_package.name
                        result += format_delimiter

                elif component.SPD_type == Components.Component.SurgeProtector.Type.VARISTOR:     #варистор
                    result += locale.translate(lcl.assemble_parameters.SPD_TYPE_VARISTOR)
                    result += format_delimiter

                    #корпус
                    if component.GNRC_package is not None:
                        result += _assemble_param_package(component.GNRC_package, locale, format_package_delimiter)
                        result += format_delimiter
                    
                    #максимальное рабочее напряжение
                    if component.SPD_voltage_standoff is not None and component.SPD_voltage_standoff.value is not None:
                        ranges = ((1e0, lcl.Unit.Prefix.NONE), (10e3, lcl.Unit.Prefix.KILO))
                        result += _assemble_param_quantity(component.SPD_voltage_standoff.value, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                        result += format_delimiter
                    
                    #энергия + тип тестового импульса
                    if component.SPD_energy is not None and component.SPD_energy.value is not None:
                        ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO))
                        result += _assemble_param_quantity(component.SPD_energy.value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                        if component.SPD_energy.conditions:
                            conditions_str = ""
                            if Components.ParameterSpec.ConditionType.SURGE_WAVEFORM in component.SPD_energy.conditions:
                                ranges = ()
                                conditions_str += _assemble_param_quantity(component.SPD_energy.conditions[Components.ParameterSpec.ConditionType.SURGE_WAVEFORM], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                                conditions_str += format_conditions_delimiter
                            if Components.ParameterSpec.ConditionType.SURGE_DURATION in component.SPD_energy.conditions:
                                ranges = ()
                                conditions_str += _assemble_param_quantity(component.SPD_energy.conditions[Components.ParameterSpec.ConditionType.SURGE_DURATION], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                                conditions_str += format_conditions_delimiter
                            conditions_str = string_strip_word(conditions_str, format_conditions_delimiter)
                            if conditions_str: result += format_conditions_enclosure[0] + conditions_str + format_conditions_enclosure[1]
                        result += format_delimiter

            #Батарея
            elif type(component) is Components.Component.Battery:
                #тип
                param_str = ''
                if component.BAT_type == component.Type.HOLDER:
                    param_str = locale.translate(lcl.assemble_parameters.BAT_TYPE_HOLDER)
                if param_str: result += param_str + format_delimiter

                #размер
                if component.GNRC_size is not None:
                    result += component.GNRC_size + format_delimiter

                #номинальное напряжение
                if component.BAT_voltage is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), )
                    result += _assemble_param_quantity(component.BAT_voltage, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #ёмкость + допуск @ нагрузка + температура
                if component.BAT_capacity is not None and component.BAT_capacity.value is not None:
                    ranges = ((1e-6, lcl.Unit.Prefix.MICRO), (1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                    value = deepcopy(component.BAT_capacity.value)
                    result += _assemble_param_quantity(value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.BAT_capacity.tolerance is not None:
                        ranges = ()
                        result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.BAT_capacity.tolerance, False, ranges, value.prefix, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure) + format_tolerance_enclosure[1]
                    if component.BAT_capacity.conditions:
                        conditions_str = ""
                        if Components.ParameterSpec.ConditionType.CURRENT in component.BAT_capacity.conditions:
                            ranges = ((1e-6, lcl.Unit.Prefix.MICRO), (1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                            conditions_str += _assemble_param_quantity(component.BAT_capacity.conditions[Components.ParameterSpec.ConditionType.CURRENT], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        if Components.ParameterSpec.ConditionType.RESISTANCE in component.BAT_capacity.conditions:
                            ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO), (1e6, lcl.Unit.Prefix.MEGA))
                            conditions_str += _assemble_param_quantity(component.BAT_capacity.conditions[Components.ParameterSpec.ConditionType.RESISTANCE], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        if Components.ParameterSpec.ConditionType.VOLTAGE in component.BAT_capacity.conditions:
                            ranges = ((1e0, lcl.Unit.Prefix.NONE), )
                            conditions_str += _assemble_param_quantity(component.BAT_capacity.conditions[Components.ParameterSpec.ConditionType.VOLTAGE], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        if Components.ParameterSpec.ConditionType.TEMPERATURE in component.BAT_capacity.conditions:
                            ranges = ((1e0, lcl.Unit.Prefix.NONE), )
                            conditions_str += _assemble_param_quantity(component.BAT_capacity.conditions[Components.ParameterSpec.ConditionType.TEMPERATURE], False, ranges, locale, format_decimalPoint, format_temperature_positiveSign, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        conditions_str = string_strip_word(conditions_str, format_conditions_delimiter)
                        if conditions_str: result += format_conditions_enclosure[0] + conditions_str + format_conditions_enclosure[1]
                    result += format_delimiter

            #Дисплей
            elif type(component) is Components.Component.Display:
                pass

            #Светодиод
            elif type(component) is Components.Component.LED:
                #тип
                param_str = ''
                if component.LED_type == Components.Component.LED.Type.INDICATION:
                    param_str = locale.translate(lcl.assemble_parameters.LED_TYPE_INDICATOR)
                elif component.LED_type == Components.Component.LED.Type.LIGHTING:
                    param_str = locale.translate(lcl.assemble_parameters.LED_TYPE_LIGHTING)
                if param_str: result += param_str + format_delimiter

                #корпус
                if component.GNRC_package is not None:
                    result += _assemble_param_package(component.GNRC_package, locale, format_package_delimiter)
                    result += format_delimiter

                #цвет
                if component.LED_color is not None:
                    if   component.LED_color == Components.ColorType.INFRARED:    param_str = locale.translate(lcl.Color.INFRARED)
                    elif component.LED_color == Components.ColorType.ULTRAVIOLET: param_str = locale.translate(lcl.Color.ULTRAVIOLET)
                    elif component.LED_color == Components.ColorType.RED:         param_str = locale.translate(lcl.Color.RED)
                    elif component.LED_color == Components.ColorType.ORANGE:      param_str = locale.translate(lcl.Color.ORANGE)
                    elif component.LED_color == Components.ColorType.AMBER:       param_str = locale.translate(lcl.Color.AMBER)
                    elif component.LED_color == Components.ColorType.YELLOW:      param_str = locale.translate(lcl.Color.YELLOW)
                    elif component.LED_color == Components.ColorType.LIME:        param_str = locale.translate(lcl.Color.LIME)
                    elif component.LED_color == Components.ColorType.GREEN:       param_str = locale.translate(lcl.Color.GREEN)
                    elif component.LED_color == Components.ColorType.TURQUOISE:   param_str = locale.translate(lcl.Color.TURQUOISE)
                    elif component.LED_color == Components.ColorType.CYAN:        param_str = locale.translate(lcl.Color.CYAN)
                    elif component.LED_color == Components.ColorType.BLUE:        param_str = locale.translate(lcl.Color.BLUE)
                    elif component.LED_color == Components.ColorType.VIOLET:      param_str = locale.translate(lcl.Color.VIOLET)
                    elif component.LED_color == Components.ColorType.PURPLE:      param_str = locale.translate(lcl.Color.PURPLE)
                    elif component.LED_color == Components.ColorType.PINK:        param_str = locale.translate(lcl.Color.PINK)
                    elif component.LED_color == Components.ColorType.MULTI:       param_str = locale.translate(lcl.Color.MULTI)
                    elif component.LED_color == Components.ColorType.WHITE:       param_str = locale.translate(lcl.Color.WHITE)
                    if param_str: result += param_str + format_delimiter
                        
                #цветовая температура
                if component.LED_color_temperature is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), )
                    result += _assemble_param_quantity(component.LED_color_temperature, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter
                    
                #длина волны
                if component.LED_wavelength is not None:
                    ranges = ((1e-9, lcl.Unit.Prefix.NANO), )
                    result += _assemble_param_quantity(component.LED_wavelength, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #индекс цветопередачи
                if component.LED_color_renderingIndex is not None:
                    result += locale.translate(lcl.assemble_parameters.LED_CRI) + '\xa0' + _assemble_param_quantity(component.LED_color_renderingIndex, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #сила света
                if component.LED_luminous_intensity is not None and component.LED_luminous_intensity.value is not None:
                    ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                    value = deepcopy(component.LED_luminous_intensity.value)
                    result += _assemble_param_quantity(value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.LED_luminous_intensity.tolerance is not None:
                        ranges = ()
                        result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.LED_luminous_intensity.tolerance, False, ranges, value.prefix, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure) + format_tolerance_enclosure[1]
                    if component.LED_luminous_intensity.conditions:
                        conditions_str = ""
                        if Components.ParameterSpec.ConditionType.CURRENT in component.LED_luminous_intensity.conditions:
                            ranges = ((1e-6, lcl.Unit.Prefix.MICRO), (1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                            conditions_str += _assemble_param_quantity(component.LED_luminous_intensity.conditions[Components.ParameterSpec.ConditionType.CURRENT], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        conditions_str = string_strip_word(conditions_str, format_conditions_delimiter)
                        if conditions_str: result += format_conditions_enclosure[0] + conditions_str + format_conditions_enclosure[1]
                    result += format_delimiter


                #световой поток
                if component.LED_luminous_flux is not None and component.LED_luminous_flux.value is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), )
                    value = deepcopy(component.LED_luminous_flux.value)
                    result += _assemble_param_quantity(value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.LED_luminous_flux.tolerance is not None:
                        ranges = ()
                        result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.LED_luminous_flux.tolerance, False, ranges, value.prefix, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure) + format_tolerance_enclosure[1]
                    if component.LED_luminous_flux.conditions:
                        conditions_str = ""
                        if Components.ParameterSpec.ConditionType.CURRENT in component.LED_luminous_flux.conditions:
                            ranges = ((1e-6, lcl.Unit.Prefix.MICRO), (1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                            conditions_str += _assemble_param_quantity(component.LED_luminous_flux.conditions[Components.ParameterSpec.ConditionType.CURRENT], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        conditions_str = string_strip_word(conditions_str, format_conditions_delimiter)
                        if conditions_str: result += format_conditions_enclosure[0] + conditions_str + format_conditions_enclosure[1]
                    result += format_delimiter

                #угол обзора
                if component.LED_viewingAngle is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), )
                    result += _assemble_param_quantity(component.LED_viewingAngle, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #прямой ток
                if component.LED_current is not None:
                    ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                    result += _assemble_param_quantity(component.LED_current, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #прямое падение напряжения
                if component.LED_voltage_forward is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), )
                    result += _assemble_param_quantity(component.LED_voltage_forward, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

            #Перемычка
            elif type(component) is Components.Component.Jumper:
                #тип
                param_str = ""
                if component.JMP_type is not None:
                    if component.JMP_type == component.Type.ELECTRICAL:
                        param_str += locale.translate(lcl.assemble_parameters.JMP_TYPE_ELECTRICAL)
                    elif component.JMP_type == component.Type.THERMAL:
                        param_str += locale.translate(lcl.assemble_parameters.JMP_TYPE_THERMAL)
                if param_str: result += param_str + format_delimiter

                #корпус
                if component.GNRC_package is not None:
                    result += _assemble_param_package(component.GNRC_package, locale, format_package_delimiter)
                    result += format_delimiter

            #Реле
            elif type(component) is Components.Component.Relay:
                pass

            #Индуктивность
            elif type(component) is Components.Component.Inductor:
                #корпус
                if component.GNRC_package is not None:
                    result += _assemble_param_package(component.GNRC_package, locale, format_package_delimiter)
                    result += format_delimiter

                #индуктивность
                if component.IND_inductance is not None and component.IND_inductance.value is not None:
                    ranges = ((1e-9, lcl.Unit.Prefix.NANO), (1e-6, lcl.Unit.Prefix.MICRO), (1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                    value = deepcopy(component.IND_inductance.value)
                    result += _assemble_param_quantity(value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.IND_inductance.tolerance is not None:
                        ranges = ()
                        result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.IND_inductance.tolerance, False, ranges, value.prefix, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure) + format_tolerance_enclosure[1]
                    if component.IND_inductance.conditions:
                        conditions_str = ""
                        if Components.ParameterSpec.ConditionType.FREQUENCY in component.IND_inductance.conditions:
                            ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO), (1e6, lcl.Unit.Prefix.MEGA))
                            conditions_str += _assemble_param_quantity(component.IND_inductance.conditions[Components.ParameterSpec.ConditionType.FREQUENCY], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        if Components.ParameterSpec.ConditionType.VOLTAGE in component.IND_inductance.conditions:
                            ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                            conditions_str += _assemble_param_quantity(component.IND_inductance.conditions[Components.ParameterSpec.ConditionType.VOLTAGE], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        conditions_str = string_strip_word(conditions_str, format_conditions_delimiter)
                        if conditions_str: result += format_conditions_enclosure[0] + conditions_str + format_conditions_enclosure[1]
                    result += format_delimiter

                #ток
                if component.IND_current is not None and component.IND_current.value is not None:
                    ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                    result += _assemble_param_quantity(component.IND_current.value, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.IND_current.conditions:
                        conditions_str = ""
                        if Components.ParameterSpec.ConditionType.TEMPERATURE_RISE in component.IND_current.conditions:
                            ranges = ((1e0, lcl.Unit.Prefix.NONE), )
                            conditions_str += _assemble_param_quantity(component.IND_current.conditions[Components.ParameterSpec.ConditionType.TEMPERATURE_RISE], False, ranges, locale, format_decimalPoint, format_temperature_positiveSign, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                        if Components.ParameterSpec.ConditionType.PRIMARY_VALUE_DEVIATION in component.IND_current.conditions:
                            if conditions_str: conditions_str += format_value_multi_delimiter
                            ranges = ()
                            conditions_str += _assemble_param_quantity(component.IND_inductance.conditions[Components.ParameterSpec.ConditionType.PRIMARY_VALUE_DEVIATION], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                        if conditions_str: result += format_conditions_enclosure[0] + conditions_str + format_conditions_enclosure[1]
                    result += format_delimiter

                #сопротивление (по постоянному току)
                if component.IND_resistance is not None:
                    ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                    result += _assemble_param_quantity(component.IND_resistance, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #низкая ёмкость
                if component.IND_lowCap:
                    result += locale.translate(lcl.assemble_parameters.LOW_CAPACITANCE)
                    result += format_delimiter

            #Резистор
            elif type(component) is Components.Component.Resistor:
                #тип
                param_str = ''
                if component.RES_type == Components.Component.Resistor.Type.FIXED:
                    param_str = locale.translate(lcl.assemble_parameters.RES_TYPE_FIXED)
                elif component.RES_type == Components.Component.Resistor.Type.VARIABLE:
                    param_str = locale.translate(lcl.assemble_parameters.RES_TYPE_VARIABLE)
                elif component.RES_type == Components.Component.Resistor.Type.THERMAL:
                    param_str = locale.translate(lcl.assemble_parameters.RES_TYPE_THERMAL)
                if param_str: result += param_str + format_delimiter

                #структура
                param_str = ''
                if component.RES_structure == Components.Component.Resistor.Structure.THICK_FILM:
                    param_str = locale.translate(lcl.assemble_parameters.RES_STRUCTURE_THICKFILM)
                elif component.RES_structure == Components.Component.Resistor.Structure.THIN_FILM:
                    param_str = locale.translate(lcl.assemble_parameters.RES_STRUCTURE_THINFILM)
                elif component.RES_structure == Components.Component.Resistor.Structure.METAL_FILM:
                    param_str = locale.translate(lcl.assemble_parameters.RES_STRUCTURE_METALFILM)
                elif component.RES_structure == Components.Component.Resistor.Structure.METAL_OXIDE:
                    param_str = locale.translate(lcl.assemble_parameters.RES_STRUCTURE_METALOXIDE)
                elif component.RES_structure == Components.Component.Resistor.Structure.CARBON_FILM:
                    param_str = locale.translate(lcl.assemble_parameters.RES_STRUCTURE_CARBONFILM)
                elif component.RES_structure == Components.Component.Resistor.Structure.WIREWOUND:
                    param_str = locale.translate(lcl.assemble_parameters.RES_STRUCTURE_WIREWOUND)
                elif component.RES_structure == Components.Component.Resistor.Structure.CERAMIC:
                    param_str = locale.translate(lcl.assemble_parameters.RES_STRUCTURE_CERAMIC)
                if param_str: result += param_str + format_delimiter

                #корпус
                if component.GNRC_package is not None:
                    result += _assemble_param_package(component.GNRC_package, locale, format_package_delimiter)
                    result += format_delimiter

                #мощность
                if component.RES_power is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO))
                    result += _assemble_param_quantity(component.RES_power, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #напряжение
                if component.RES_voltage is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), (10e3, lcl.Unit.Prefix.KILO))
                    result += _assemble_param_quantity(component.RES_voltage, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #сопротивление + допуск
                if component.RES_resistance is not None and component.RES_resistance.value is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO), (1e6, lcl.Unit.Prefix.MEGA), (1e9, lcl.Unit.Prefix.GIGA))
                    value = deepcopy(component.RES_resistance.value)
                    result += _assemble_param_quantity(value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.RES_resistance.tolerance is not None:
                        ranges = ()
                        result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.RES_resistance.tolerance, False, ranges, value.prefix, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure) + format_tolerance_enclosure[1]
                    result += format_delimiter

                #температурный коэффициент сопротивления
                if component.RES_TCR is not None:
                    ranges = ()
                    result += _assemble_param_tolerance(component.RES_TCR, False, ranges, lcl.Unit.Prefix.NONE, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

            #Переключатель
            elif type(component) is Components.Component.Switch:
                pass

            #Трансформатор
            elif type(component) is Components.Component.Transformer:
                pass

            #Диод
            elif type(component) is Components.Component.Diode:
                #тип
                param_str = ''
                if component.DIODE_type == Components.Component.Diode.Type.GENERAL_PURPOSE:
                    param_str = locale.translate(lcl.assemble_parameters.DIODE_TYPE_GENERALPURPOSE)
                elif component.DIODE_type == Components.Component.Diode.Type.SCHOTTKY:
                    param_str = locale.translate(lcl.assemble_parameters.DIODE_TYPE_SCHOTTKY)
                elif component.DIODE_type == Components.Component.Diode.Type.ZENER:
                    param_str = locale.translate(lcl.assemble_parameters.DIODE_TYPE_ZENER)
                elif component.DIODE_type == Components.Component.Diode.Type.TUNNEL:
                    param_str = locale.translate(lcl.assemble_parameters.DIODE_TYPE_TUNNEL)
                elif component.DIODE_type == Components.Component.Diode.Type.VARICAP:
                    param_str = locale.translate(lcl.assemble_parameters.DIODE_TYPE_VARICAP)
                if param_str: result += param_str + format_delimiter

                #обратное напряжение
                if component.DIODE_voltage_reverse is not None and component.DIODE_voltage_reverse.value is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), (10e3, lcl.Unit.Prefix.KILO))
                    value = deepcopy(component.DIODE_voltage_reverse.value)
                    result += _assemble_param_quantity(value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.DIODE_voltage_reverse.tolerance is not None:
                        ranges = ()
                        result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.DIODE_voltage_reverse.tolerance, False, ranges, value.prefix, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure) + format_tolerance_enclosure[1]
                    result += format_delimiter

                #прямой ток
                if component.DIODE_current_forward is not None and component.DIODE_current_forward.value is not None:
                    ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                    result += _assemble_param_quantity(component.DIODE_current_forward.value, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.DIODE_current_forward.conditions:
                        conditions_str = ""
                        if Components.ParameterSpec.ConditionType.TEMPERATURE in component.DIODE_current_forward.conditions:
                            ranges = ((1e0, lcl.Unit.Prefix.NONE), )
                            conditions_str += _assemble_param_quantity(component.DIODE_current_forward.conditions[Components.ParameterSpec.ConditionType.TEMPERATURE], False, ranges, locale, format_decimalPoint, format_temperature_positiveSign, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                        if conditions_str: result += format_conditions_enclosure[0] + conditions_str + format_conditions_enclosure[1]
                    result += format_delimiter

                #мощность
                if component.DIODE_power is not None and component.DIODE_power.value is not None:
                    ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO))
                    result += _assemble_param_quantity(component.DIODE_power.value, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.DIODE_power.conditions:
                        conditions_str = ""
                        if Components.ParameterSpec.ConditionType.TEMPERATURE in component.DIODE_power.conditions:
                            ranges = ((1e0, lcl.Unit.Prefix.NONE), )
                            conditions_str += _assemble_param_quantity(component.DIODE_power.conditions[Components.ParameterSpec.ConditionType.TEMPERATURE], False, ranges, locale, format_decimalPoint, format_temperature_positiveSign, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                        if conditions_str: result += format_conditions_enclosure[0] + conditions_str + format_conditions_enclosure[1]
                    result += format_delimiter


                #ёмкость
                if component.DIODE_capacitance is not None and component.DIODE_capacitance.value is not None:
                    ranges = ((1e-12, lcl.Unit.Prefix.PICO), )
                    value = deepcopy(component.DIODE_capacitance.value)
                    result += _assemble_param_quantity(value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.DIODE_capacitance.tolerance is not None:
                        ranges = ()
                        result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.DIODE_capacitance.tolerance, False, ranges, value.prefix, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure) + format_tolerance_enclosure[1]
                    if component.DIODE_capacitance.conditions:
                        conditions_str = ""
                        if Components.ParameterSpec.ConditionType.VOLTAGE in component.DIODE_capacitance.conditions:
                            ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                            conditions_str += _assemble_param_quantity(component.DIODE_capacitance.conditions[Components.ParameterSpec.ConditionType.VOLTAGE], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        if Components.ParameterSpec.ConditionType.FREQUENCY in component.DIODE_capacitance.conditions:
                            ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO), (1e6, lcl.Unit.Prefix.MEGA))
                            conditions_str += _assemble_param_quantity(component.DIODE_capacitance.conditions[Components.ParameterSpec.ConditionType.FREQUENCY], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        conditions_str = string_strip_word(conditions_str, format_conditions_delimiter)
                        if conditions_str: result += format_conditions_enclosure[0] + conditions_str + format_conditions_enclosure[1]
                    result += format_delimiter

                #время восстановления
                if component.DIODE_recovery_time is not None and component.DIODE_recovery_time.value is not None:
                    ranges = ((1e-12, lcl.Unit.Prefix.PICO), (1e-9, lcl.Unit.Prefix.NANO), (1e-6, lcl.Unit.Prefix.MICRO), (1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                    result += _assemble_param_quantity(component.DIODE_recovery_time.value, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #корпус
                if component.GNRC_package is not None:
                    result += locale.translate(lcl.assemble_parameters.PACKAGE) + '\xa0' + component.GNRC_package.name
                    result += format_delimiter

            #Тиристор
            elif type(component) is Components.Component.Thyristor:
                pass

            #Транзистор
            elif type(component) is Components.Component.Transistor:
                pass

            #Оптоизолятор
            elif type(component) is Components.Component.Optoisolator:
                pass

            #Соединитель
            elif type(component) is Components.Component.Connector:
                pass

            #Фильтр ЭМП
            elif type(component) is Components.Component.EMIFilter:
                #тип
                param_str = ""
                if component.EMIF_type == Components.Component.EMIFilter.Type.FERRITE_BEAD:
                    param_str += locale.translate(lcl.assemble_parameters.EMIF_TYPE_FERRITEBEAD)
                elif component.EMIF_type == Components.Component.EMIFilter.Type.COMMON_MODE_CHOKE:
                    param_str += locale.translate(lcl.assemble_parameters.EMIF_TYPE_COMMONMODECHOKE)
                if param_str: result += param_str + format_delimiter

                #корпус
                if component.GNRC_package is not None:
                    result += _assemble_param_package(component.GNRC_package, locale, format_package_delimiter)
                    result += format_delimiter

                #импеданс
                if component.EMIF_impedance is not None and component.EMIF_impedance.value is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO))
                    value = deepcopy(component.EMIF_impedance.value)
                    result += _assemble_param_quantity(value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.EMIF_impedance.tolerance is not None:
                        ranges = ()
                        result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.EMIF_impedance.tolerance, False, ranges, value.prefix, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure) + format_tolerance_enclosure[1]
                    if component.EMIF_impedance.conditions:
                        conditions_str = ""
                        if Components.ParameterSpec.ConditionType.FREQUENCY in component.EMIF_impedance.conditions:
                            ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO), (1e6, lcl.Unit.Prefix.MEGA), (1e9, lcl.Unit.Prefix.GIGA))
                            conditions_str += _assemble_param_quantity(component.EMIF_impedance.conditions[Components.ParameterSpec.ConditionType.FREQUENCY], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        conditions_str = string_strip_word(conditions_str, format_conditions_delimiter)
                        if conditions_str: result += format_conditions_enclosure[0] + conditions_str + format_conditions_enclosure[1]
                    result += format_delimiter

                #индуктивность
                if component.EMIF_inductance is not None and component.EMIF_inductance.value is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO))
                    value = deepcopy(component.EMIF_inductance.value)
                    result += _assemble_param_quantity(value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.EMIF_inductance.tolerance is not None:
                        ranges = ()
                        result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.EMIF_inductance.tolerance, False, ranges, value.prefix, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure) + format_tolerance_enclosure[1]
                    if component.EMIF_inductance.conditions:
                        conditions_str = ""
                        if Components.ParameterSpec.ConditionType.FREQUENCY in component.EMIF_inductance.conditions:
                            ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO), (1e6, lcl.Unit.Prefix.MEGA), (1e9, lcl.Unit.Prefix.GIGA))
                            conditions_str += _assemble_param_quantity(component.EMIF_inductance.conditions[Components.ParameterSpec.ConditionType.FREQUENCY], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        if Components.ParameterSpec.ConditionType.VOLTAGE in component.EMIF_inductance.conditions:
                            ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO))
                            conditions_str += _assemble_param_quantity(component.EMIF_inductance.conditions[Components.ParameterSpec.ConditionType.VOLTAGE], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        if Components.ParameterSpec.ConditionType.CURRENT in component.EMIF_inductance.conditions:
                            ranges = ((1e-6, lcl.Unit.Prefix.MICRO), (1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                            conditions_str += _assemble_param_quantity(component.EMIF_inductance.conditions[Components.ParameterSpec.ConditionType.CURRENT], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        conditions_str = string_strip_word(conditions_str, format_conditions_delimiter)
                        if conditions_str: result += format_conditions_enclosure[0] + conditions_str + format_conditions_enclosure[1]
                    result += format_delimiter

                #ёмкость
                if component.EMIF_capacitance is not None and component.EMIF_capacitance.value is not None:
                    ranges = ((1e-12, lcl.Unit.Prefix.PICO), (1e-9, lcl.Unit.Prefix.NANO), (1e-6, lcl.Unit.Prefix.MICRO), (0.1e0, lcl.Unit.Prefix.NONE))
                    value = deepcopy(component.EMIF_capacitance.value)
                    result += _assemble_param_quantity(value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.EMIF_capacitance.tolerance is not None:
                        ranges = ()
                        result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.EMIF_capacitance.tolerance, False, ranges, value.prefix, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure) + format_tolerance_enclosure[1]
                    if component.EMIF_capacitance.conditions:
                        conditions_str = ""
                        if Components.ParameterSpec.ConditionType.FREQUENCY in component.EMIF_capacitance.conditions:
                            ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO), (1e6, lcl.Unit.Prefix.MEGA), (1e9, lcl.Unit.Prefix.GIGA))
                            conditions_str += _assemble_param_quantity(component.EMIF_capacitance.conditions[Components.ParameterSpec.ConditionType.FREQUENCY], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        if Components.ParameterSpec.ConditionType.VOLTAGE in component.EMIF_capacitance.conditions:
                            ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO))
                            conditions_str += _assemble_param_quantity(component.EMIF_capacitance.conditions[Components.ParameterSpec.ConditionType.VOLTAGE], False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                            conditions_str += format_conditions_delimiter
                        conditions_str = string_strip_word(conditions_str, format_conditions_delimiter)
                        if conditions_str: result += format_conditions_enclosure[0] + conditions_str + format_conditions_enclosure[1]
                    result += format_delimiter

                #сопротивление
                if component.EMIF_resistance is not None and component.EMIF_resistance.value is not None:
                    ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO))
                    value = deepcopy(component.EMIF_resistance.value)
                    result += _assemble_param_quantity(value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.EMIF_resistance.tolerance is not None:
                        ranges = ()
                        result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.EMIF_resistance.tolerance, False, ranges, value.prefix, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure) + format_tolerance_enclosure[1]
                    result += format_delimiter

                #ток
                if component.EMIF_current is not None:
                    ranges = ((1e-6, lcl.Unit.Prefix.MICRO), (1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO))
                    result += _assemble_param_quantity(component.EMIF_current, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #напряжение
                if component.EMIF_voltage is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), (10e3, lcl.Unit.Prefix.KILO))
                    result += _assemble_param_quantity(component.EMIF_voltage, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

            #Осциллятор (Резонатор)
            elif type(component) is Components.Component.Oscillator:
                #структура
                param_str = ""
                if component.OSC_structure == Components.Component.Oscillator.Structure.QUARTZ:
                    param_str += locale.translate(lcl.assemble_parameters.OSC_STRUCTURE_QUARTZ)
                elif component.OSC_structure == Components.Component.Oscillator.Structure.CERAMIC:
                    param_str += locale.translate(lcl.assemble_parameters.OSC_STRUCTURE_CERAMIC)
                if param_str: result += param_str + format_delimiter

                #частота + допуск
                if component.OSC_frequency is not None and component.OSC_frequency.value is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO), (1e6, lcl.Unit.Prefix.MEGA), (1e9, lcl.Unit.Prefix.GIGA))
                    value = deepcopy(component.OSC_frequency.value)
                    result += _assemble_param_quantity(value, True, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    if component.OSC_frequency.tolerance is not None:
                        ranges = ()
                        result += format_tolerance_enclosure[0] + _assemble_param_tolerance(component.OSC_frequency.tolerance, False, ranges, value.prefix, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure) + format_tolerance_enclosure[1]
                    result += format_delimiter

                #гармоника
                if component.OSC_overtone is not None:
                    if component.OSC_overtone == 1:
                        result += locale.translate(lcl.assemble_parameters.OSC_OVERTONE_FUNDAMENTAL)
                    else:
                        result += str(component.OSC_overtone) + '\xa0' + locale.translate(lcl.assemble_parameters.OSC_OVERTONE)
                    result += format_delimiter

                #стабильность частоты
                if component.OSC_stability is not None:
                    ranges = ()
                    result += _assemble_param_tolerance(component.OSC_stability, False, ranges, lcl.Unit.Prefix.NONE, locale, format_decimalPoint, format_tolerance_sym_sign, format_tolerance_sym_value_enclosure, format_tolerance_asym_value_upperFirst, format_tolerance_asym_value_delimiter, format_tolerance_asym_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #ёмкость нагрузки
                if component.OSC_loadCapacitance is not None:
                    ranges = ((1e-12, lcl.Unit.Prefix.PICO), )
                    result += _assemble_param_quantity(component.OSC_loadCapacitance, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #эквивалентное последовательное сопротивление
                if component.OSC_ESR is not None:
                    ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO))
                    result += _assemble_param_quantity(component.OSC_ESR, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

                #уровень возбуждения
                if component.OSC_driveLevel is not None:
                    ranges = ((1e-6, lcl.Unit.Prefix.MICRO), (1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                    result += _assemble_param_quantity(component.OSC_driveLevel, False, ranges, locale, format_decimalPoint, False, format_value_multi_delimiter, format_value_enclosure, format_unit_enclosure)
                    result += format_delimiter

            #Общий тип
            else:
                pass
            
            #собираем параметры общие для всех типов
            #сборка
            if component.GNRC_array is not None:
                #TODO доделать форматирование
                result += _assemble_param_array(component.GNRC_array, locale, '', '')
                result += format_delimiter

            #диапазон рабочих температур
            if component.GNRC_temperatureRange is not None:
                ranges = ((0, lcl.Unit.Prefix.NONE), )
                result += _assemble_param_quantity(component.GNRC_temperatureRange, False, ranges, locale, format_decimalPoint, format_temperature_positiveSign, format_value_range_delimiter, format_value_enclosure, format_unit_enclosure)
                result += format_delimiter

        #дополнительные параметры
        if content_misc:
            for item in component.GNRC_misc:
                result += item
                result += format_delimiter

        #удаляем лишние разделители
        result = string_strip_word(result, format_delimiter)
    else:
        #пересобирать не надо - возвращаем исходное описание
        if component.GNRC_description is not None: result = component.GNRC_description

    return result

#сборка списка замен
def assemble_substitutes(component, **kwargs):
    #locale
    locale = kwargs.get('locale', lcl.Locale.RU)

    #параметры содержимого
    content_partnumber  = kwargs.get('content_subst_partnumber', True)
    content_mfr         = kwargs.get('content_subst_mfr', True)
    content_note        = kwargs.get('content_subst_note', True)

    #параметры формата
    format_entry_enclosure = kwargs.get('format_subst_entry_enclosure', ['\nдоп.\xa0замена ', ''])
    format_partnumber_enclosure = kwargs.get('format_subst_partnumber_enclosure', ['', ''])
    format_mfr_enclosure   = kwargs.get('format_subst_mfr_enclosure', [' ф.\xa0', ''])
    format_note_enclosure  = kwargs.get('format_subst_note_enclosure', [' (', ')'])

    result = ''
    if component.GNRC_substitute is not None:
        for substitute in component.GNRC_substitute:
            result += format_entry_enclosure[0]
            if content_partnumber and substitute.partnumber is not None: result += format_partnumber_enclosure[0] + substitute.partnumber + format_partnumber_enclosure[1]
            if content_mfr and substitute.manufacturer is not None: result += format_mfr_enclosure[0] + substitute.manufacturer + format_mfr_enclosure[1]
            if content_note and substitute.note is not None: result += format_note_enclosure[0] + substitute.note + format_note_enclosure[1]
            result += format_entry_enclosure[1]
    return result

#сборка параметра: величина
def _assemble_param_quantity(quantity:Components.Quantity,
                             modify_value:bool = False,
                             ranges:tuple[tuple[float|int, lcl.Unit.Prefix]] = None,
                             locale:lcl.Locale|tuple[lcl.Locale, int] = lcl.Locale.EN,
                             decimal_point:str = '.',
                             sign_positive:bool = False,
                             value_delimiter:str = '/',
                             value_enclosure:tuple[str, str] = ('', ''),
                             unit_enclosure:tuple[str, str] = ('', '')
                             ) -> str:
    #смотрим есть ли вариация локали
    if isinstance(locale, (tuple, list)):
        locale_sub = locale[1]
        locale = locale[0]
    else:
        locale_sub = 0
    
    if quantity.unit == lcl.Unit.Name.NONE:
        #если единицы измерения не заданы то приставку добавлять некуда -> нормализуем значение
        quantity = quantity.normilize(modify_value)
    elif ranges is None:
        #оставляем префикс как есть
        pass
    else:
        #определяем префикс по значению диапазона
        if ranges == ():
            #диапазоны не заданы -> используем диапазоны по-умолчанию
            ranges = ((0,     lcl.Unit.Prefix.NONE),
                      (1e-24, lcl.Unit.Prefix.YOCTO),
                      (1e-21, lcl.Unit.Prefix.ZEPTO),
                      (1e-18, lcl.Unit.Prefix.ATTO),
                      (1e-15, lcl.Unit.Prefix.FEMTO),
                      (1e-12, lcl.Unit.Prefix.PICO),
                      (1e-9,  lcl.Unit.Prefix.NANO),
                      (1e-6,  lcl.Unit.Prefix.MICRO),
                      (1e-3,  lcl.Unit.Prefix.MILLI),
                      (1e0,   lcl.Unit.Prefix.NONE),
                      (1e3,   lcl.Unit.Prefix.KILO),
                      (1e6,   lcl.Unit.Prefix.MEGA),
                      (1e9,   lcl.Unit.Prefix.GIGA),
                      (1e12,  lcl.Unit.Prefix.TERA),
                      (1e15,  lcl.Unit.Prefix.PETA),
                      (1e18,  lcl.Unit.Prefix.EXA),
                      (1e21,  lcl.Unit.Prefix.ZETTA),
                      (1e24,  lcl.Unit.Prefix.YOTTA))

        #определяем среднее значение исключая нули
        scope = 0; i = 0
        for m in quantity._magnitude:
            if m != 0:
                scope += abs(m)
                i += 1
        if i > 0:
            scope = (scope / i) * quantity.prefix.multiplier

        #определяем множитель
        if scope == 0:
            #обрабатываем частный случай когда значение равно 0
            prefix = ranges[0][1]
        else:
            i = 1
            if ranges[0][0] == 0: i += 1
            while i < len(ranges):
                if scope < ranges[i][0]:
                    prefix = ranges[i - 1][1]
                    break
                i += 1
            else:
                prefix = ranges[-1][1]

        #если префикс не совпадает с существующим то конвертируем
        if quantity.prefix != prefix:
            quantity = quantity.toprefix(prefix, modify_value)

    #получаем строковое значение
    value_str = []
    for item in quantity._magnitude:
        value_str.append(_floatToString(item, decimal_point, sign_positive))

    #получаем блок с единицами измерения
    if quantity.unit == lcl.Unit.Name.NONE: unit_str = ''
    else:                                   unit_str = unit_enclosure[0] + locale.translate(quantity.prefix, locale_sub) + locale.translate(quantity.unit, locale_sub) + unit_enclosure[1]

    return value_enclosure[0] + value_delimiter.join(value_str) + value_enclosure[1] + unit_str

#сборка параметра: допуск
def _assemble_param_tolerance(tolerance:Components.Tolerance,
                              modify_value:bool = False,
                              rel_ranges:tuple[tuple[float|int, lcl.Unit.Name]] = None,
                              abs_prefix:lcl.Unit.Prefix = None,
                              locale:lcl.Locale|tuple[lcl.Locale, int] = lcl.Locale.EN,
                              decimal_point:str = '.',
                              sym_sign = '±',
                              sym_value_enclosure:tuple[str, str] = ('', ''),
                              asym_value_upperfirst:bool = False,
                              asym_value_delimiter:str = '\u2026',
                              asym_value_enclosure:tuple[str, str] = ('', ''),
                              unit_enclosure:tuple[str, str] = ('', '')
                              ) -> str:
    #смотрим есть ли вариация локали
    if isinstance(locale, (tuple, list)):
        locale_sub = locale[1]
        locale = locale[0]
    else:
        locale_sub = 0
    
    if tolerance.isrelative():
        #допуск в относительных единицах измерения
        if rel_ranges is None:
            #оставляем единицы измерения как есть
            pass
        else:
            if rel_ranges == ():
                #диапазоны не заданы -> используем диапазоны по-умолчанию
                rel_ranges = ((0,     lcl.Unit.Name.PERCENT),
                              (1e-9,  lcl.Unit.Name.PPB),
                              (1e-6,  lcl.Unit.Name.PPM),
                              (1e-3,  lcl.Unit.Name.PERCENT))
            #определяем среднее значение исключая нули
            scope = 0
            i = 0
            if tolerance.lower_norm != 0:
                scope += abs(tolerance.lower_norm)
                i += 1
            if tolerance.upper_norm != 0:
                scope += abs(tolerance.upper_norm)
                i += 1
            if i > 0: scope = scope / i

            #определяем единицу измерения
            if scope == 0:
                #обрабатываем частный случай когда значение равно 0
                unit = rel_ranges[0][1]
            else:
                i = 1
                if rel_ranges[0][0] == 0: i += 1
                while i < len(rel_ranges):
                    if scope < rel_ranges[i][0]:
                        unit = rel_ranges[i - 1][1]
                        break
                    i += 1
                else:
                    unit = rel_ranges[-1][1]

            #если единицы измерения не совпадает с существующим то конвертируем
            if tolerance.unit != unit:
                if not modify_value:
                    tolerance = deepcopy(tolerance)
                tolerance.lower = tolerance.lower_norm / unit.multiplier
                tolerance.upper = tolerance.upper_norm / unit.multiplier
                tolerance.prefix = lcl.Unit.Name.NONE
                tolerance.unit = unit
    else:
        #допуск в абсолютных единицах измерения
        if abs_prefix is not None:
            tolerance = tolerance.toprefix(abs_prefix, modify_value)

    #получаем блок с единицами измерения
    if tolerance.unit == lcl.Unit.Name.NONE: unit_str = ''
    else:                                    unit_str = unit_enclosure[0] + locale.translate(tolerance.prefix, locale_sub) + locale.translate(tolerance.unit, locale_sub) + unit_enclosure[1]

    if tolerance.issymmetric():
        #допуск симметричный
        return sym_sign + sym_value_enclosure[0] + _floatToString(abs(tolerance.lower), decimal_point, False) + sym_value_enclosure[1] + unit_str
    else:
        #допуск не симметричный
        if asym_value_upperfirst:
            first = _floatToString(tolerance.upper, decimal_point, True)
            last = _floatToString(tolerance.lower, decimal_point, True)
        else:
            first = _floatToString(tolerance.lower, decimal_point, True)
            last = _floatToString(tolerance.upper, decimal_point, True)
        return asym_value_enclosure[0] + first + asym_value_delimiter + last + asym_value_enclosure[1] + unit_str

#сборка параметра: корпус
def _assemble_param_package(package:Components.Package, locale:lcl.Locale = lcl.Locale.EN, delimiter:str = '\xa0') -> str:
    result = ''
    if isinstance(package.type, Components.Package.Type.Surface):
        #поверхностный монтаж
        if package.type == Components.Package.Type.Surface.CHIP:
            result += locale.translate(lcl.assemble_parameters.PACKAGE_SURFACE_CHIP)
        elif package.type == Components.Package.Type.Surface.MOLDED:
            result += locale.translate(lcl.assemble_parameters.PACKAGE_SURFACE_MOLDED)
    elif isinstance(package.type, Components.Package.Type.ThroughHole):
        #выводной монтаж
        result += locale.translate(lcl.assemble_parameters.PACKAGE_THROUGHHOLE)
        if package.type == Components.Package.Type.ThroughHole.AXIAL:
            result += delimiter + locale.translate(lcl.assemble_parameters.PACKAGE_THROUGHHOLE_AXIAL)
        elif package.type == Components.Package.Type.ThroughHole.RADIAL:
            result += delimiter + locale.translate(lcl.assemble_parameters.PACKAGE_THROUGHHOLE_RADIAL)
    elif isinstance(package.type, Components.Package.Type.Holder):
        #монтаж в держатель
        result += locale.translate(lcl.assemble_parameters.PACKAGE_HOLDER)
        if package.type == Components.Package.Type.Holder.CYLINDRICAL:
            result += delimiter + locale.translate(lcl.assemble_parameters.PACKAGE_HOLDER_CYLINDRICAL)
        elif package.type == Components.Package.Type.Holder.BLADE:
            result += delimiter + locale.translate(lcl.assemble_parameters.PACKAGE_HOLDER_BLADE)
    if package.name is not None: result += delimiter + package.name
    return result.strip(delimiter)

#сборка параметра: сборка
#TODO: сделать нормально полную реализацию
def _assemble_param_array(array:Components.Array, locale:lcl.Locale = lcl.Locale.EN, value_delimiter:str = '×', value_enclosure:tuple[str, str] = ('\xa0', '')) -> str:
    result = ''
    result += locale.translate(lcl.assemble_parameters.ARRAY)
    return result

#сборка универсального артикула
def assemble_generic_partnumber(component:Components.Component.Generic, **kwargs) -> str:
    '''
    <код>-<корпус>-<параметры>...

    код:
        0 - флаг параметрического номинала
            $               - (задаётся в настройках)
        1 - тип компонента
            C - Capacitor   - конденсатор
            R - Resistor    - резистор
            J - Jumper      - перемычка
            L - inductor    - индуктивность
        2 - конструктивные особенности
            Конденсаторы
                C - Ceramic         - керамический
                F - Film            - плёночный
                T - Tantalum        - танталовый
                E - Electrolytic    - алюминиевый электролитический
                P - Polymer         - алюминиевый полимерный
                H - Hybrid          - алюминиевый гибридный
                N - Niobium         - ниобиевый
                M - Mica            - слюдяной
                S - Supercap        - суперконденсатор
            Резисторы
                T - Thick film      - толстоплёночный (самый ширпотреб)
                F - thin Film       - тонкоплёночный
                M - Metal film      - металлоплёночный
                C - Carbon          - углеродный
                O - metal Oxide     - металлооксидный
                W - Wirewound       - проволочный
            Перемычки
                E - Electrical      - электрический
                T - Thermal         - тепловой
            Индуктивности   TODO: сделать нормальный классификатор
                P - Power           - силовой дроссель для цепей питания
                S - Signal          - сигнальная индуктивность
        3 - тип корпуса/монтажа
            S - Surface     - поверхностный монтаж (общий)
            C - Chip        - стандартный чип
            M - Molded      - формованный чип (как у чип-танталов)
            V - V-chip      - цилиндрический чип (как у чип-электролитов)
            T - Throughhole - выводной для монтажа в отверстия (общий)
            A - throughhole Axial  - выводной аксиальный
            R - throughhole Radial - выводной радиальный

    корпус:
        код корпуса - для стандартных чип корпусов - 0201|0402|0603|...|A|B|C|D|E|X
        размер корпуса в миллиметрах - для нестандартных корпусов - 8x10|5x6.3|...
    '''

    def package_code(package:Components.Package, fallback:str) -> str:
        if package is not None:
            if isinstance(package.type, Components.Package.Type.Surface):
                if package.type == Components.Package.Type.Surface.CHIP:
                    return 'C'
                elif package.type == Components.Package.Type.Surface.MOLDED:
                    return 'M'
                elif package.type == Components.Package.Type.Surface.VCHIP:
                    return 'V'
                else:
                    return 'S'
            elif isinstance(package.type, Components.Package.Type.ThroughHole):
                if   package.type == Components.Package.Type.ThroughHole.AXIAL:
                    return 'A'
                elif package.type == Components.Package.Type.ThroughHole.RADIAL:
                    return 'R'
                else:
                    return 'T'
        return fallback
    def package_name(package:Components.Package, fallback:str) -> str:
        if package is not None and package.name:
            return package.name
        return fallback

    #locale
    locale = kwargs.get('locale', lcl.Locale.EN)
    format_param_error                              = kwargs.get('format_param_error', '!')
    format_param_unknown                            = kwargs.get('format_param_unknown', '?')
    format_param_enclosure                          = kwargs.get('format_param_enclosure', ('$', ''))
    format_param_delimiter                          = kwargs.get('format_param_delimiter', '-')
    format_param_decimalPoint                       = kwargs.get('format_param_decimalPoint', '.')
    format_param_temperature_positiveSign           = kwargs.get('format_param_temperature_positiveSign', True)
    format_param_value_enclosure                    = kwargs.get('format_param_value_enclosure', ('', ''))
    format_param_value_multi_delimiter              = kwargs.get('format_param_value_multi_delimiter', '/')
    format_param_value_range_delimiter              = kwargs.get('format_param_value_range_delimiter', '_')
    format_param_unit_enclosure                     = kwargs.get('format_param_unit_enclosure', ('', ''))
    format_param_tolerance_enclosure                = kwargs.get('format_param_tolerance_enclosure', ('', ''))
    format_param_tolerance_sym_sign                 = kwargs.get('format_param_tolerance_sym_sign', '±')
    format_param_tolerance_sym_value_enclosure      = kwargs.get('format_param_tolerance_sym_value_enclosure', ('', ''))
    format_param_tolerance_asym_value_upperFirst    = kwargs.get('format_param_tolerance_asym_value_upperFirst', False)
    format_param_tolerance_asym_value_delimiter     = kwargs.get('format_param_tolerance_asym_value_delimiter', '/')
    format_param_tolerance_asym_value_enclosure     = kwargs.get('format_param_tolerance_asym_value_enclosure', ('(', ')'))

    result = ''

    if type(component) is Components.Component.Capacitor:
        result += format_param_enclosure[0]
        #код типа компонента
        result += 'C'
        #код типа конструктива
        if component.CAP_type is not None:
            if   component.CAP_type == Components.Component.Capacitor.Type.CERAMIC:           result += 'C'
            elif component.CAP_type == Components.Component.Capacitor.Type.FILM:              result += 'F'
            elif component.CAP_type == Components.Component.Capacitor.Type.TANTALUM:          result += 'T'
            elif component.CAP_type == Components.Component.Capacitor.Type.ALUM_ELECTROLYTIC: result += 'E'
            elif component.CAP_type == Components.Component.Capacitor.Type.ALUM_POLYMER:      result += 'P'
            elif component.CAP_type == Components.Component.Capacitor.Type.ALUM_HYBRID:       result += 'H'
            elif component.CAP_type == Components.Component.Capacitor.Type.SUPERCAPACITOR:    result += 'S'
            elif component.CAP_type == Components.Component.Capacitor.Type.NIOBIUM:           result += 'N'
            elif component.CAP_type == Components.Component.Capacitor.Type.MICA:              result += 'M'
            else:                                                                           result += format_param_unknown
        else:
            result += format_param_unknown
        #код типа корпуса
        result += package_code(component.GNRC_package, format_param_unknown)
        result += format_param_delimiter

        #название корпуса
        result += package_name(component.GNRC_package, format_param_unknown)
        result += format_param_delimiter

        #диэлектрик
        if component.CAP_dielectric is not None:
            result += component.CAP_dielectric
            result += format_param_delimiter
        
        #напряжение
        if component.CAP_voltage is not None:
            ranges = ((1e0, lcl.Unit.Prefix.NONE), )
            result += _assemble_param_quantity(component.CAP_voltage, False, ranges, locale, format_param_decimalPoint, False, format_param_value_multi_delimiter, format_param_value_enclosure, format_param_unit_enclosure)
        else:
            result += format_param_error + locale.translate(lcl.Unit.Name.VOLT)
        result += format_param_delimiter

        #ёмкость + допуск
        if component.CAP_capacitance is not None and component.CAP_capacitance.value is not None:
            ranges = ((1e-12, lcl.Unit.Prefix.PICO), (10e-9, lcl.Unit.Prefix.MICRO), (0.1e0, lcl.Unit.Prefix.NONE))
            value = deepcopy(component.CAP_capacitance.value)
            result += _assemble_param_quantity(value, True, ranges, locale, format_param_decimalPoint, False, format_param_value_multi_delimiter, format_param_value_enclosure, format_param_unit_enclosure)
            if component.CAP_capacitance.tolerance is not None:
                ranges = ()
                result += format_param_tolerance_enclosure[0] + _assemble_param_tolerance(component.CAP_capacitance.tolerance, False, ranges, value.prefix, locale, format_param_decimalPoint, format_param_tolerance_sym_sign, format_param_tolerance_sym_value_enclosure, format_param_tolerance_asym_value_upperFirst, format_param_tolerance_asym_value_delimiter, format_param_tolerance_asym_value_enclosure, format_param_unit_enclosure) + format_param_tolerance_enclosure[1]
            else:
                result += format_param_error + locale.translate(lcl.Unit.Name.PERCENT)
        else:
            result += format_param_error + locale.translate(lcl.Unit.Name.FARAD)
        result += format_param_delimiter

        #низкий импеданс
        if component.CAP_lowESR:
            result += "LESR"
            result += format_param_delimiter

        result = string_strip_word(result, format_param_delimiter)
        result += format_param_enclosure[1]

    elif type(component) is Components.Component.Jumper:
        result += format_param_enclosure[0]
        #код типа компонента
        result += 'J'
        #код типа конструктива
        if   component.JMP_type == Components.Component.Jumper.Type.ELECTRICAL: result += 'E'
        elif component.JMP_type == Components.Component.Jumper.Type.THERMAL:    result += 'T'
        else:                                                                 result += format_param_unknown
        #код типа корпуса
        result += package_code(component.GNRC_package, format_param_unknown)
        result += format_param_delimiter
        
        #название корпуса
        result += package_name(component.GNRC_package, format_param_unknown)
        result += format_param_delimiter

        #параметры
        if component.JMP_type == Components.Component.Jumper.Type.ELECTRICAL:
            #ток
            if component.JMP_electrical_current is not None:
                #если указан ток, но он типовой для данного корпуса то мы его не указываем
                current = True
                if component.GNRC_package is not None:
                    if component.GNRC_package.type == Components.Package.Type.Surface.CHIP:
                        if component.GNRC_package.name == '0075' and component.JMP_electrical_current == 0.5 or \
                            component.GNRC_package.name == '0100' and component.JMP_electrical_current == 0.5 or \
                            component.GNRC_package.name == '0201' and component.JMP_electrical_current == 0.5 or \
                            component.GNRC_package.name == '0402' and component.JMP_electrical_current == 1.0 or \
                            component.GNRC_package.name == '0603' and component.JMP_electrical_current == 1.0 or \
                            component.GNRC_package.name == '0805' and component.JMP_electrical_current == 2.0 or \
                            component.GNRC_package.name == '1206' and component.JMP_electrical_current == 2.0 or \
                            component.GNRC_package.name == '1210' and component.JMP_electrical_current == 2.0 or \
                            component.GNRC_package.name == '1218' and component.JMP_electrical_current == 6.0 or \
                            component.GNRC_package.name == '2010' and component.JMP_electrical_current == 2.0 or \
                            component.GNRC_package.name == '2512' and component.JMP_electrical_current == 2.0:
                            current = False
                if current:
                    ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
                    result += _assemble_param_quantity(component.JMP_electrical_current, False, ranges, locale, format_param_decimalPoint, False, format_param_value_multi_delimiter, format_param_value_enclosure, format_param_unit_enclosure)
                    result += format_param_delimiter

        elif component.JMP_type == Components.Component.Jumper.Type.THERMAL:
            pass

        result = string_strip_word(result, format_param_delimiter)
        result += format_param_enclosure[1]

    elif type(component) is Components.Component.Inductor:
        result += format_param_enclosure[0]
        #код типа компонента
        result += 'L'
        #код типа конструктива
        if component.IND_type is not None:
            if   component.IND_type == Components.Component.Inductor.Type.CHOKE:    result += 'P'
            elif component.IND_type == Components.Component.Inductor.Type.INDUCTOR: result += 'S'
            else:                                                                   result += format_param_unknown
        else:
            result += format_param_unknown
        #код типа корпуса
        result += package_code(component.GNRC_package, format_param_unknown)
        result += format_param_delimiter

        #название корпуса
        result += package_name(component.GNRC_package, format_param_unknown)
        result += format_param_delimiter

        #индуктивность + допуск
        if component.IND_inductance is not None and component.IND_inductance.value is not None:
            ranges = ((1e-9, lcl.Unit.Prefix.NANO), (1e-6, lcl.Unit.Prefix.MICRO), (1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
            value = deepcopy(component.IND_inductance.value)
            result += _assemble_param_quantity(value, True, ranges, locale, format_param_decimalPoint, False, format_param_value_multi_delimiter, format_param_value_enclosure, format_param_unit_enclosure)
            if component.IND_inductance.tolerance is not None:
                ranges = ()
                result += format_param_tolerance_enclosure[0] + _assemble_param_tolerance(component.IND_inductance.tolerance, False, ranges, value.prefix, locale, format_param_decimalPoint, format_param_tolerance_sym_sign, format_param_tolerance_sym_value_enclosure, format_param_tolerance_asym_value_upperFirst, format_param_tolerance_asym_value_delimiter, format_param_tolerance_asym_value_enclosure, format_param_unit_enclosure) + format_param_tolerance_enclosure[1]
            else:
                result += format_param_error + locale.translate(lcl.Unit.Name.PERCENT)
        else:
            result += format_param_error + locale.translate(lcl.Unit.Name.HENRY)
        result += format_param_delimiter

        #ток
        if component.IND_current is not None and component.IND_current.value is not None:
            ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
            result += _assemble_param_quantity(component.IND_current.value, False, ranges, locale, format_param_decimalPoint, False, format_param_value_multi_delimiter, format_param_value_enclosure, format_param_unit_enclosure)
        else:
            result += format_param_error + locale.translate(lcl.Unit.Name.AMPERE)
        result += format_param_delimiter

        #сопротивление (по постоянному току)
        if component.IND_resistance is not None:
            ranges = ((1e-3, lcl.Unit.Prefix.MILLI), (1e0, lcl.Unit.Prefix.NONE))
            result += _assemble_param_quantity(component.IND_resistance, False, ranges, locale, format_param_decimalPoint, False, format_param_value_multi_delimiter, format_param_value_enclosure, format_param_unit_enclosure)
            result += format_param_delimiter

        #низкая ёмкость
        if component.IND_lowCap:
            result += "LCAP"
            result += format_param_delimiter

        result = string_strip_word(result, format_param_delimiter)
        result += format_param_enclosure[1]

    elif type(component) is Components.Component.Resistor and component.RES_type == Components.Component.Resistor.Type.FIXED:
        if component.RES_resistance is not None and component.RES_resistance.value.magnitude == 0:
            #резистор с нулевым сопротивлением -> электрическая перемычка
            return assemble_pnp_partnumber(Components.Component.Jumper(component), **kwargs)

        result += format_param_enclosure[0]
        #код типа компонента
        result += 'R'
        #код типа конструктива
        if   (component.RES_structure is None and (component.GNRC_package is not None and component.GNRC_package.type == Components.Package.Type.Surface.CHIP)) or \
                component.RES_structure == Components.Component.Resistor.Structure.THICK_FILM:  result += 'T' #если тип не указан и чип корпус то берём толстоплёночный
        elif component.RES_structure == Components.Component.Resistor.Structure.THIN_FILM:   result += 'F'
        elif component.RES_structure == Components.Component.Resistor.Structure.METAL_FILM:  result += 'M'
        elif component.RES_structure == Components.Component.Resistor.Structure.CARBON_FILM: result += 'C'
        elif component.RES_structure == Components.Component.Resistor.Structure.METAL_OXIDE: result += 'O'
        elif component.RES_structure == Components.Component.Resistor.Structure.WIREWOUND:   result += 'W'
        else:                                                                                result += format_param_unknown
        #код типа корпуса
        result += package_code(component.GNRC_package, format_param_unknown)
        result += format_param_delimiter
        
        #название корпуса
        result += package_name(component.GNRC_package, format_param_unknown)
        result += format_param_delimiter

        #мощность
        if component.RES_power is not None:
            #если указана мощность, но она типовая для данного корпуса то мы её не указываем
            power = True
            if component.GNRC_package is not None:
                if component.GNRC_package.type == Components.Package.Type.Surface.CHIP:
                    if component.GNRC_package.name == '0075' and component.RES_power == 0.02    or \
                        component.GNRC_package.name == '0100' and component.RES_power == 0.03125 or \
                        component.GNRC_package.name == '0201' and component.RES_power == 0.05    or \
                        component.GNRC_package.name == '0402' and component.RES_power == 0.0625  or \
                        component.GNRC_package.name == '0603' and component.RES_power == 0.1     or \
                        component.GNRC_package.name == '0805' and component.RES_power == 0.125   or \
                        component.GNRC_package.name == '1206' and component.RES_power == 0.25    or \
                        component.GNRC_package.name == '1210' and component.RES_power == 0.5     or \
                        component.GNRC_package.name == '1218' and component.RES_power == 1.0     or \
                        component.GNRC_package.name == '2010' and component.RES_power == 0.75    or \
                        component.GNRC_package.name == '2512' and component.RES_power == 1.0:
                        power = False
            if power:
                ranges = ((1e0, lcl.Unit.Prefix.NONE), )
                result += _assemble_param_quantity(component.RES_power, False, ranges, locale, format_param_decimalPoint, False, format_param_value_multi_delimiter, format_param_value_enclosure, format_param_unit_enclosure)
                result += format_param_delimiter
        
        #напряжение
        if component.RES_voltage is not None:
            #если указано напряжение, но оно типовое для данного корпуса то мы его не указываем
            voltage = True
            if component.GNRC_package is not None:
                if component.GNRC_package.type == Components.Package.Type.Surface.CHIP:
                    if component.GNRC_package.name == '0075' and component.RES_power == 10  or \
                        component.GNRC_package.name == '0100' and component.RES_power == 15  or \
                        component.GNRC_package.name == '0201' and component.RES_power == 25  or \
                        component.GNRC_package.name == '0402' and component.RES_power == 50  or \
                        component.GNRC_package.name == '0603' and component.RES_power == 75  or \
                        component.GNRC_package.name == '0805' and component.RES_power == 150 or \
                        component.GNRC_package.name == '1206' and component.RES_power == 200 or \
                        component.GNRC_package.name == '1210' and component.RES_power == 200 or \
                        component.GNRC_package.name == '1218' and component.RES_power == 200 or \
                        component.GNRC_package.name == '2010' and component.RES_power == 200 or \
                        component.GNRC_package.name == '2512' and component.RES_power == 200:
                        voltage = False
            if voltage:
                ranges = ((1e0, lcl.Unit.Prefix.NONE), )
                result += _assemble_param_quantity(component.RES_voltage, False, ranges, locale, format_param_decimalPoint, False, format_param_value_multi_delimiter, format_param_value_enclosure, format_param_unit_enclosure)
                result += format_param_delimiter

        #сопротивление + допуск
        if component.RES_resistance is not None and component.RES_resistance.value is not None:
            ranges = ((1e0, lcl.Unit.Prefix.NONE), (1e3, lcl.Unit.Prefix.KILO), (1e6, lcl.Unit.Prefix.MEGA), (1e9, lcl.Unit.Prefix.GIGA))
            value = deepcopy(component.RES_resistance.value)
            result += _assemble_param_quantity(value, True, ranges, locale, format_param_decimalPoint, False, format_param_value_multi_delimiter, format_param_value_enclosure, format_param_unit_enclosure)
            if component.RES_resistance.tolerance is not None:
                ranges = ()
                result += format_param_tolerance_enclosure[0] + _assemble_param_tolerance(component.RES_resistance.tolerance, False, ranges, value.prefix, locale, format_param_decimalPoint, format_param_tolerance_sym_sign, format_param_tolerance_sym_value_enclosure, format_param_tolerance_asym_value_upperFirst, format_param_tolerance_asym_value_delimiter, format_param_tolerance_asym_value_enclosure, format_param_unit_enclosure) + format_param_tolerance_enclosure[1]
            else:
                result += format_param_error + locale.translate(lcl.Unit.Name.PERCENT)
        else:
            result += format_param_error + locale.translate(lcl.Unit.Name.OHM)
        result += format_param_delimiter

        #ТКС
        if component.RES_TCR is not None:
            ranges = ()
            result += format_param_tolerance_enclosure[0] + _assemble_param_tolerance(component.RES_TCR, False, ranges, lcl.Unit.Prefix.NONE, locale, format_param_decimalPoint, format_param_tolerance_sym_sign, format_param_tolerance_sym_value_enclosure, format_param_tolerance_asym_value_upperFirst, format_param_tolerance_asym_value_delimiter, format_param_tolerance_asym_value_enclosure, format_param_unit_enclosure) + format_param_tolerance_enclosure[1]
            result += format_param_delimiter

        result = string_strip_word(result, format_param_delimiter)
        result += format_param_enclosure[1]
    else:
        #параметрической сборки для данного типа компонента нет -> копируем артикул с флагом ошибки
        result += format_param_enclosure[0]
        if component.GNRC_partnumber is not None:
            result += format_param_error + str(component.GNRC_partnumber)
        result += format_param_enclosure[1]
    return result

# ------------------------------------------------------------- Pick and Place --------------------------------------------------
#сборка десигнатора
def assemble_pnp_designator(designator:Designator, **kwargs) -> str:
    #locale
    locale = kwargs.get('locale', lcl.Locale.EN)

    #параметры сборки
    assemble_desig = kwargs.get('assemble_desig', False)

    result = ''
    if designator is not None:
        if assemble_desig:
            result += designator.prefix + designator.index
            if designator.channel is not None:
                result += designator.channel.enclosure[0] + designator.channel.prefix + designator.channel.index + designator.channel.enclosure[1]
        else:
            result += designator.full
    return result

#сборка слоя
def assemble_pnp_layer(layer:PickPlace.PCBlayer, **kwargs) -> str:
    #locale
    locale = kwargs.get('locale', lcl.Locale.EN)

    result = ''
    if layer is not None:
        if   layer == PickPlace.PCBlayer.TOP: result += locale.translate(lcl.assemble_pnp_layer.TOP)
        elif layer == PickPlace.PCBlayer.BOTTOM: result += locale.translate(lcl.assemble_pnp_layer.BOTTOM)
        elif layer == PickPlace.PCBlayer.MIDDLE_1 <= layer.value() <= layer == PickPlace.PCBlayer.MIDDLE_30:
            result += locale.translate(lcl.assemble_pnp_layer.MIDDLE) + str((layer.value() - PickPlace.PCBlayer.MIDDLE_1) + 1)
    return result

#сборка типа монтажа
def assemble_pnp_mount(mount:PickPlace.MountType, **kwargs) -> str:
    #locale
    locale= kwargs.get('locale', lcl.Locale.EN)

    result = ''
    if mount is not None:
        if   mount == PickPlace.MountType.UNDEFINED: result += locale.translate(lcl.assemble_pnp_mount.UNDEFINED)
        elif mount == PickPlace.MountType.SURFACE: result += locale.translate(lcl.assemble_pnp_mount.SURFACE)
        elif mount == PickPlace.MountType.SEMI_SURFACE: result += locale.translate(lcl.assemble_pnp_mount.SEMI_SURFACE)
        elif mount == PickPlace.MountType.THROUGHHOLE: result += locale.translate(lcl.assemble_pnp_mount.THROUGHHOLE)
        elif mount == PickPlace.MountType.EDGE: result += locale.translate(lcl.assemble_pnp_mount.EDGE)
        elif mount == PickPlace.MountType.CHASSIS: result += locale.translate(lcl.assemble_pnp_mount.CHASSIS)
        elif mount == PickPlace.MountType.UNKNOWN: result += locale.translate(lcl.assemble_pnp_mount.UNKNOWN)
        else: result += locale.translate(lcl.assemble_pnp_mount.UNRECOGNIZED)
    return result

#сборка состояния
def assemble_pnp_state(state:PickPlace.PnP.Entry.State, **kwargs) -> str:
    #locale
    locale = kwargs.get('locale', lcl.Locale.EN)

    format_reason_enclosure = kwargs.get('format_reason_enclosure', (':', ''))

    result = ''
    if state.enabled is not None:
        if state.enabled:
            result += locale.translate(lcl.assemble_pnp_status.ENABLED)
        else:
            result += locale.translate(lcl.assemble_pnp_status.DISABLED)
        if state.reason is not None:
            result += format_reason_enclosure[0] + state.reason + format_reason_enclosure[1]
    return result

#сборка артикула
def assemble_pnp_partnumber(component:Components.Component.Generic, **kwargs) -> str:
    assemble_partnumber_parametric = kwargs.get('assemble_partnumber_parametric', True)
    assemble_partnumber_explicit   = kwargs.get('assemble_partnumber_explicit', False)
    format_partnumber_parametric_enclosure = kwargs.get('format_partnumber_parametric_enclosure', (' [', ']'))

    if component.GNRC_parametric and assemble_partnumber_parametric:
        #артикул параметрический и его надо собрать
        return assemble_generic_partnumber(component, **kwargs)
    elif assemble_partnumber_parametric and assemble_partnumber_explicit:
        #артикул явный, но надо добавить параметрический аналог
        parametric = assemble_generic_partnumber(component, **kwargs)
        if component.GNRC_partnumber:
            #имеется явный артикул
            if component.GNRC_partnumber in parametric:
                #явный артикул является частью параметрического -> соответствующего сборщика нет -> возвращаем один явный артикул
                return component.GNRC_partnumber
            else:
                #параметрический артикул собрался -> возвращаем оба варианта
                return component.GNRC_partnumber + format_partnumber_parametric_enclosure[0] + parametric + format_partnumber_parametric_enclosure[1]
        elif parametric:
            #явного артикула нет, но собрался параметрический -> возврадаем один параметрический
            return parametric
        else:
            #вообще ничего нет -> возвращаем пустую строку
            return ''
    else:
        #артикул не параметрический и ничего добавлять не надо
        if component.GNRC_partnumber is not None:
            return component.GNRC_partnumber
        else:
            return ''
        
#сборка описания
def assemble_pnp_description(component:Components.Component.Generic, **kwargs) -> str:
    #locale
    locale = kwargs.get('locale', lcl.Locale.RU)

    assemble_param = kwargs.get('assemble_param', False)
    content_description_kind = kwargs.get('content_description_kind', True)
    format_description_param_enclosure = kwargs.get('format_description_param_enclosure', (': ', ''))

    result = ''
    if content_description_kind:
        result += assemble_kind(component, **kwargs)

    if assemble_param:
        description = assemble_parameters(component, **kwargs)
    else:
        description = component.GNRC_description or ""

    if description:
        result += format_description_param_enclosure[0] + description + format_description_param_enclosure[1]

    return result

#сборка комментария
def assemble_pnp_comment(component, **kwargs) -> str:
    #locale
    locale = kwargs.get('locale', lcl.Locale.EN)

    result = ''
    if component.GNRC_note is not None:
        result += component.GNRC_note
    return result