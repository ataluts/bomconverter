import os
import copy
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
        self.quantity   = int(quantity)
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

#сборка ЕСКД из параметров компонента
def assemble_eskd(component, **kwargs):
    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры содержимого полей
    content_value          = kwargs.get('content_value', True)
    content_value_explicit = kwargs.get('content_value_explicit', False)
    content_manufacturer   = kwargs.get('content_mfr', True)
    content_parameters     = kwargs.get('content_param', True)
    content_substitutes    = kwargs.get('content_subst', True)
    content_annot          = kwargs.get('content_annot', True)

    #параметры формата
    format_annot_enclosure = kwargs.get('format_annot_enclosure', ['', ''])
    format_value_enclosure = kwargs.get('format_value_enclosure', ['', ''])
    format_mfr_enclosure   = kwargs.get('format_mfr_enclosure',   [' ф.\xa0', ''])
    format_param_enclosure = kwargs.get('format_param_enclosure', ['', ''])
    format_subst_enclosure = kwargs.get('format_subst_enclosure', ['', ''])

    #инициализируем переменные
    result = eskdValue()

    #Базовые поля
    result.designator = assemble_designator(component.GENERIC_designator, **kwargs)
    result.quantity   = assemble_quantity(component, **kwargs)
    
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

    #Примечание
    if content_annot:
        result.annotation = assemble_annotation(component, **kwargs)
        if len(result.annotation) > 0: result.annotation = format_annot_enclosure[0] + result.annotation + format_annot_enclosure[1]

    return result

#сборка десигнатора
def assemble_designator(designator, **kwargs):
    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

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

#сборка количества
def assemble_quantity(component, **kwargs):
    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры формата
    format_fitted_quantity = kwargs.get('format_fitted_quantity', [-1, -1])

    if component.GENERIC_fitted:
        if format_fitted_quantity[0] < 0:
            return component.GENERIC_quantity
        else:
            return format_fitted_quantity[0]
    else:
        if format_fitted_quantity[1] < 0:
            return component.GENERIC_quantity
        else:
            return format_fitted_quantity[1]

#сборка типа компонента
def assemble_kind(component, **kwargs):
    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры сборки
    assemble_kind = kwargs.get('assemble_kind', True)

    #параметры формата
    format_capitalize = kwargs.get('format_kind_capitalize', False)

    result = ''
    if assemble_kind:
        #Сборка (Устройство)
        if isinstance(component, component.types.Assembly):
            result = lcl.assemble_kind.ASSEMBLY.value[locale_index]

        #Фотоэлемент
        elif isinstance(component, component.types.Photocell):
            result = lcl.assemble_kind.PHOTO_CELL.value[locale_index]
            if component.PHOTO_type == component.Type.DIODE: result = lcl.assemble_kind.PHOTO_DIODE.value[locale_index]
            elif component.PHOTO_type == component.Type.TRANSISTOR: result = lcl.assemble_kind.PHOTO_TRANSISTOR.value[locale_index]
            elif component.PHOTO_type == component.Type.RESISTOR: result = lcl.assemble_kind.PHOTO_RESISTOR.value[locale_index]

        #Конденсатор
        elif isinstance(component, component.types.Capacitor):
            result = lcl.assemble_kind.CAPACITOR.value[locale_index]

        #Микросхема
        elif isinstance(component, component.types.IntegratedCircuit):
            result = lcl.assemble_kind.INTEGRATED_CIRCUIT.value[locale_index]

        #Крепёж
        elif type(component) is component.types.Fastener:
            result = lcl.assemble_kind.FASTENER.value[locale_index]

        #Радиатор
        elif type(component) is component.types.Heatsink:
            result = lcl.assemble_kind.HEATSINK.value[locale_index]

        #Автоматический выключатель (Предохранитель)
        elif isinstance(component, component.types.CircuitBreaker):
            result = lcl.assemble_kind.CIRCUIT_BREAKER.value[locale_index]
            if component.CBRK_type == component.Type.FUSE: result = lcl.assemble_kind.FUSE.value[locale_index]
            elif component.CBRK_type == component.Type.FUSE_PTC_RESETTABLE: result = lcl.assemble_kind.FUSE_PTC_RESETTABLE.value[locale_index]
            elif component.CBRK_type == component.Type.FUSE_THERMAL: result = lcl.assemble_kind.FUSE_THERMAL.value[locale_index]

        #Ограничитель перенапряжения
        elif isinstance(component, component.types.SurgeProtector):
            result = lcl.assemble_kind.SURGE_PROTECTOR.value[locale_index]
            if component.SPD_type == component.Type.DIODE: result = lcl.assemble_kind.TVS_DIODE.value[locale_index]
            elif component.SPD_type == component.Type.THYRISTOR: result = lcl.assemble_kind.TVS_THYRISTOR.value[locale_index]
            elif component.SPD_type == component.Type.VARISTOR: result = lcl.assemble_kind.VARISTOR.value[locale_index]
            elif component.SPD_type == component.Type.GAS_DISCHARGE_TUBE: result = lcl.assemble_kind.GAS_DISCHARGE_TUBE.value[locale_index]
            elif component.SPD_type == component.Type.IC: result = lcl.assemble_kind.SURGE_PROTECTOR.value[locale_index]

        #Батарея
        elif isinstance(component, component.types.Battery):
            result = lcl.assemble_kind.BATTERY.value[locale_index]

        #Дисплей
        elif isinstance(component, component.types.Display):
            result = lcl.assemble_kind.DISPLAY.value[locale_index]

        #Светодиод
        elif isinstance(component, component.types.LED):
            result = lcl.assemble_kind.LED.value[locale_index]

        #Перемычка
        elif isinstance(component, component.types.Jumper):
            result = lcl.assemble_kind.JUMPER.value[locale_index]

        #Реле
        elif isinstance(component, component.types.Relay):
            result = lcl.assemble_kind.RELAY.value[locale_index]

        #Индуктивность
        elif isinstance(component, component.types.Inductor):
            result = lcl.assemble_kind.INDUCTOR.value[locale_index]
            if component.IND_type == component.Type.CHOKE: result = lcl.assemble_kind.CHOKE.value[locale_index]

        #Резистор
        elif isinstance(component, component.types.Resistor):
            result = lcl.assemble_kind.RESISTOR.value[locale_index]
            if component.RES_type == component.Type.VARIABLE: result = lcl.assemble_kind.POTENTIOMETER.value[locale_index]

        #Переключатель
        elif isinstance(component, component.types.Switch):
            result = lcl.assemble_kind.SWITCH.value[locale_index]

        #Трансформатор
        elif isinstance(component, component.types.Transformer):
            result = lcl.assemble_kind.TRANSFORMER.value[locale_index]

        #Диод
        elif isinstance(component, component.types.Diode):
            result = lcl.assemble_kind.DIODE.value[locale_index]
            if component.DIODE_type == component.Type.ZENER: result = lcl.assemble_kind.ZENER_DIODE.value[locale_index]
            elif component.DIODE_type == component.Type.VARICAP: result = lcl.assemble_kind.VARICAP.value[locale_index]

        #Тиристор
        elif isinstance(component, component.types.Thyristor):
            result = lcl.assemble_kind.THYRISTOR.value[locale_index]
            if component.THYR_type == component.Type.TRIAC: result = lcl.assemble_kind.TRIAC.value[locale_index]
            elif component.THYR_type == component.Type.DYNISTOR: result = lcl.assemble_kind.DYNISTOR.value[locale_index]

        #Транзистор
        elif isinstance(component, component.types.Transistor):
            result = lcl.assemble_kind.TRANSISTOR.value[locale_index]

        #Оптоизолятор
        elif isinstance(component, component.types.Optoisolator):
            result = lcl.assemble_kind.OPTOISOLATOR.value[locale_index]
            if component.OPTOISO_outputType == component.OutputType.TRANSISTOR: result = lcl.assemble_kind.OPTOCOUPLER.value[locale_index]
            elif component.OPTOISO_outputType == component.OutputType.DARLINGTON: result = lcl.assemble_kind.OPTOCOUPLER.value[locale_index]
            elif component.OPTOISO_outputType == component.OutputType.LINEAR: result = lcl.assemble_kind.OPTOCOUPLER.value[locale_index]
            elif component.OPTOISO_outputType == component.OutputType.TRIAC: result = lcl.assemble_kind.PHOTOTRIAC.value[locale_index]

        #Соединитель
        elif isinstance(component, component.types.Connector):
            result = lcl.assemble_kind.CONNECTOR.value[locale_index]

        #Фильтр ЭМП
        elif isinstance(component, component.types.EMIFilter):
            result = lcl.assemble_kind.EMI_FILTER.value[locale_index]

        #Осциллятор (Резонатор)
        elif isinstance(component, component.types.Oscillator):
            result = lcl.assemble_kind.OSCILLATOR.value[locale_index]
            if component.OSC_type == component.Type.RESONATOR:
                result = lcl.assemble_kind.RESONATOR.value[locale_index]
                if component.OSC_structure == component.Structure.QUARTZ:
                    result = lcl.assemble_kind.CRYSTAL.value[locale_index]

        else:
            result = component.GENERIC_kind
    else:
        result = component.GENERIC_kind

    if format_capitalize:
        if len(result) > 0: result = result[0].upper() + result[1:]

    return result

#сборка примечания
def assemble_annotation(component, **kwargs):
    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры содержимого
    content_annot_value = kwargs.get('content_annot_value', True)
    content_annot_fitted = kwargs.get('content_annot_fitted', True)

    #параметры формата
    format_annot_delimiter = kwargs.get('format_annot_delimiter', ';\n')
    format_fitted_label    = kwargs.get('format_fitted_label', [lcl.assemble_eskd.DO_PLACE.value[locale_index], lcl.assemble_eskd.DO_NOT_PLACE.value[locale_index]])

    result = ""
    if content_annot_value:
        if component.GENERIC_note is not None:
            result = component.GENERIC_note
    if content_annot_fitted:
        if component.GENERIC_fitted:
            result += format_annot_delimiter + format_fitted_label[0]
        else:
            result += format_annot_delimiter + format_fitted_label[1]
    result = string_strip_word(result, format_annot_delimiter)
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
    #локализация
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры сборки
    assemble_param = kwargs.get('assemble_param', True)

    #параметры содержимого
    content_basic = kwargs.get('content_param_basic', True)
    content_misc  = kwargs.get('content_param_misc', True)

    #параметры формата
    format_decimalPoint             = kwargs.get('format_param_decimalPoint', '.')
    format_rangeSymbol              = kwargs.get('format_param_rangeSymbol', '\u2026')
    format_param_delimiter          = kwargs.get('format_param_delimiter', ', ')
    format_unit_enclosure           = kwargs.get('format_param_unit_enclosure', ['', ''])
    format_multivalue_delimiter     = kwargs.get('format_param_multivalue_delimiter', '/')
    format_tolerance_enclosure      = kwargs.get('format_param_tolerance_enclosure', ['\xa0', ''])
    format_tolerance_signDelimiter  = kwargs.get('format_param_tolerance_signDelimiter', '')
    format_conditions_enclosure     = kwargs.get('format_param_conditions_enclosure', ['\xa0(', ')'])
    format_conditions_delimiter     = kwargs.get('format_param_conditions_delimiter', '; ')
    format_temperature_positiveSign = kwargs.get('format_param_temperature_positiveSign', True)

    result = ''
    if assemble_param:
        #базовые параметры
        if content_basic:
            #Сборка (Устройство)
            if type(component) is component.types.Assembly:
                pass

            #Фотоэлемент
            elif type(component) is component.types.Photocell:
                pass

            #Конденсатор
            elif type(component) is component.types.Capacitor:
                #тип
                if component.CAP_type == component.Type.CERAMIC:
                    result += lcl.assemble_parameters.CAP_TYPE_CERAMIC.value[locale_index]
                elif component.CAP_type == component.Type.TANTALUM:
                    result += lcl.assemble_parameters.CAP_TYPE_TANTALUM.value[locale_index]
                elif component.CAP_type == component.Type.FILM:
                    result += lcl.assemble_parameters.CAP_TYPE_FILM.value[locale_index]
                elif component.CAP_type == component.Type.ALUM_ELECTROLYTIC:
                    result += lcl.assemble_parameters.CAP_TYPE_ALUM_ELECTROLYTIC.value[locale_index]
                elif component.CAP_type == component.Type.ALUM_POLYMER:
                    result += lcl.assemble_parameters.CAP_TYPE_ALUM_POLYMER.value[locale_index]
                elif component.CAP_type == component.Type.SUPERCAPACITOR:
                    result += lcl.assemble_parameters.CAP_TYPE_SUPERCAPACITOR.value[locale_index]

                if len(result) > 0: result += format_param_delimiter

                #размер
                if component.GENERIC_mount == component.Mounting.Type.SURFACE:
                    result += lcl.assemble_parameters.MOUNT_SURFACE.value[locale_index]
                elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE:
                    if component.GENERIC_mount_th == component.Mounting.ThroughHole.AXIAL:
                        result += lcl.assemble_parameters.MOUNT_THROUGHHOLE_AXIAL.value[locale_index]
                    elif component.GENERIC_mount_th == component.Mounting.ThroughHole.RADIAL:
                        result += lcl.assemble_parameters.MOUNT_THROUGHHOLE_RADIAL.value[locale_index]
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
                    result += lcl.assemble_parameters.LOW_ESR.value[locale_index]
                    result += format_param_delimiter

            #Микросхема
            elif type(component) is component.types.IntegratedCircuit:
                pass

            #Крепёж
            elif type(component) is component.types.Fastener:
                pass

            #Радиатор
            elif type(component) is component.types.Heatsink:
                pass

            #Автоматический выключатель (Предохранитель)
            elif type(component) is component.types.CircuitBreaker:
                #тип
                if component.CBRK_type == component.Type.FUSE:
                    result += lcl.assemble_parameters.CBRK_TYPE_FUSE.value[locale_index]
                elif component.CBRK_type == component.Type.FUSE_PTC_RESETTABLE:
                    result += lcl.assemble_parameters.CBRK_TYPE_FUSE_PTCRESETTABLE.value[locale_index]
                elif component.CBRK_type == component.Type.FUSE_THERMAL:
                    result += lcl.assemble_parameters.CBRK_TYPE_FUSE_THERMAL.value[locale_index]
                elif component.CBRK_type == component.Type.BREAKER:
                    result += lcl.assemble_parameters.CBRK_TYPE_BREAKER.value[locale_index]
                elif component.CBRK_type == component.Type.HOLDER:
                    result += lcl.assemble_parameters.CBRK_TYPE_HOLDER.value[locale_index]
                if len(result) > 0: result += format_param_delimiter

                #тип монтажа + размер
                if component.GENERIC_mount == component.Mounting.Type.SURFACE: result += lcl.assemble_parameters.MOUNT_SURFACE.value[locale_index] + '\xa0'
                elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE:
                    if component.GENERIC_mount_th == component.Mounting.ThroughHole.AXIAL:
                        result += lcl.assemble_parameters.MOUNT_THROUGHHOLE_AXIAL.value[locale_index] + '\xa0'
                    elif component.GENERIC_mount_th == component.Mounting.ThroughHole.RADIAL:
                        result += lcl.assemble_parameters.MOUNT_THROUGHHOLE_RADIAL.value[locale_index] + '\xa0'
                elif component.GENERIC_mount == component.Mounting.Type.HOLDER:
                    if component.GENERIC_mount_holder == component.Mounting.Holder.CYLINDRICAL:
                        result += lcl.assemble_parameters.MOUNT_HOLDER_CYLINDRICAL.value[locale_index] + '\xa0'
                    elif component.GENERIC_mount_holder == component.Mounting.Holder.BLADE:
                        result += lcl.assemble_parameters.MOUNT_HOLDER_BLADE.value[locale_index] + '\xa0'
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
                    if component.CBRK_voltage_ac: result += '\xa0' + lcl.assemble_parameters.VOLTAGE_AC.value[locale_index]
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
                    if component.CBRK_speed_grade == component.SpeedGrade.FAST: result += lcl.assemble_parameters.CBRK_SPEEDGRADE_FAST.value[locale_index] + format_param_delimiter
                    elif component.CBRK_speed_grade == component.SpeedGrade.MEDIUM: result += lcl.assemble_parameters.CBRK_SPEEDGRADE_MEDIUM.value[locale_index] + format_param_delimiter
                    elif component.CBRK_speed_grade == component.SpeedGrade.SLOW: result += lcl.assemble_parameters.CBRK_SPEEDGRADE_SLOW.value[locale_index] + format_param_delimiter

            #Ограничитель перенапряжения
            elif type(component) is component.types.SurgeProtector:
                #тип
                if component.SPD_type == component.Type.DIODE:          #диод
                    result += lcl.assemble_parameters.SPD_TYPE_DIODE.value[locale_index]
                    result += format_param_delimiter

                    #двунаправленный тип
                    if component.SPD_bidirectional is not None:
                        if component.SPD_bidirectional:
                            result += lcl.assemble_parameters.SPD_BIDIRECTIONAL.value[locale_index]
                        else:
                            result += lcl.assemble_parameters.SPD_UNIDIRECTIONAL.value[locale_index]
                        result += format_param_delimiter

                    #максимальное рабочее напряжение
                    if component.SPD_standoff_voltage is not None:
                        ranges = ((1e0, MetricMultiplier.NONE), (10e3, MetricMultiplier.KILO))
                        result += _assemble_param_value(component.SPD_standoff_voltage, lcl.Units.VOLT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                        result += format_param_delimiter

                    #мощность + тип тестового импульса
                    if component.SPD_power is not None:
                        ranges = ((1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO))
                        result += _assemble_param_value(component.SPD_power, lcl.Units.WATT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                        if component.SPD_testPulse is not None:
                            result += format_conditions_enclosure[0]
                            if component.SPD_testPulse == component.TestPulse.US_8_20:
                                result += '8/20' + format_unit_enclosure[0] + lcl.MetricPrefix.MICRO.value[locale_index] + lcl.Units.SECOND.value[locale_index] + format_unit_enclosure[1]
                            elif component.SPD_testPulse == component.TestPulse.US_10_1000:
                                result += '10/1000' + format_unit_enclosure[0] + lcl.MetricPrefix.MICRO.value[locale_index] + lcl.Units.SECOND.value[locale_index] + format_unit_enclosure[1]
                            else:
                                result += '???'
                            result += format_conditions_enclosure[1]
                        result += format_param_delimiter

                    #корпус
                    if component.GENERIC_package is not None:
                        result += lcl.assemble_parameters.PACKAGE.value[locale_index] + '\xa0' + component.GENERIC_package 
                        result += format_param_delimiter

                elif component.SPD_type == component.Type.VARISTOR:     #варистор
                    result += lcl.assemble_parameters.SPD_TYPE_VARISTOR.value[locale_index]
                    result += format_param_delimiter

                    #тип + размер
                    if component.GENERIC_mount == component.Mounting.Type.SURFACE: result += lcl.assemble_parameters.MOUNT_SURFACE.value[locale_index]
                    elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE: result += lcl.assemble_parameters.MOUNT_THROUGHHOLE.value[locale_index]
                    result += '\xa0'
                    if component.GENERIC_size is not None: result += component.GENERIC_size
                    result = result.strip('\xa0')
                    result += format_param_delimiter
                    
                    #максимальное рабочее напряжение
                    if component.SPD_standoff_voltage is not None:
                        ranges = ((1e0, MetricMultiplier.NONE), (10e3, MetricMultiplier.KILO))
                        result += _assemble_param_value(component.SPD_standoff_voltage, lcl.Units.VOLT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                        result += format_param_delimiter
                    
                    #энергия + тип тестового импульса
                    if component.SPD_energy is not None:
                        ranges = ((1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO))
                        result += _assemble_param_value(component.SPD_energy, lcl.Units.JOULE, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                        if component.SPD_testPulse is not None:
                            result += format_conditions_enclosure[0]
                            if component.SPD_testPulse == component.TestPulse.US_8_20:
                                result += '8/20' + format_unit_enclosure[0] + lcl.MetricPrefix.MICRO.value[locale_index] + lcl.Units.SECOND.value[locale_index]  + format_unit_enclosure[1]
                            elif component.SPD_testPulse == component.TestPulse.US_10_1000:
                                result += '10/1000' + format_unit_enclosure[0] + lcl.MetricPrefix.MICRO.value[locale_index] + lcl.Units.SECOND.value[locale_index] + format_unit_enclosure[1]
                            else:
                                result += '???'
                            result += format_conditions_enclosure[1]
                        result += format_param_delimiter

            #Батарея
            elif type(component) is component.types.Battery:
                #тип
                if component.BAT_type == component.Type.HOLDER:
                    result += lcl.assemble_parameters.BAT_TYPE_HOLDER.value[locale_index]
                if len(result) > 0: result += format_param_delimiter

                #размер
                if component.GENERIC_size is not None:
                    result += component.GENERIC_size + format_param_delimiter

                #номинальное напряжение
                if component.BAT_voltage_rated is not None:
                    ranges = ((1e0, MetricMultiplier.NONE), )
                    result += _assemble_param_value(component.BAT_voltage_rated, lcl.Units.VOLT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                    result += format_param_delimiter

                #ёмкость @ нагрузка + температура
                if component.BAT_capacity is not None:
                    ranges = ((1e-6, MetricMultiplier.MICRO), (1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE))
                    result += _assemble_param_value(component.BAT_capacity, lcl.Units.AMPERE.value[locale_index] + lcl.Units.HOUR.value[locale_index], format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                    if (component.BAT_capacity_load_current is not None) or (component.BAT_capacity_load_resistance is not None) or (component.BAT_capacity_voltage is not None) or (component.BAT_capacity_temperature is not None):
                        result += format_conditions_enclosure[0]
                        
                        if component.BAT_capacity_load_current is not None:
                            ranges = ((1e-6, MetricMultiplier.MICRO), (1e-3, MetricMultiplier.MILLI), (1e0, MetricMultiplier.NONE))
                            result += _assemble_param_value(component.BAT_capacity_load_current, lcl.Units.AMPERE, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                            result += format_conditions_delimiter
                        
                        if component.BAT_capacity_load_resistance is not None:
                            ranges = ((1e0, MetricMultiplier.NONE), (1e3, MetricMultiplier.KILO), (1e6, MetricMultiplier.MEGA))
                            result += _assemble_param_value(component.BAT_capacity_load_resistance, lcl.Units.OHM, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                            result += format_conditions_delimiter
                        
                        if component.BAT_capacity_voltage is not None:
                            ranges = ((1e0, MetricMultiplier.NONE), )
                            result += _assemble_param_value(component.BAT_capacity_voltage, lcl.Units.VOLT, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, ranges)
                            result += format_conditions_delimiter
                        
                        if component.BAT_capacity_temperature is not None:
                            result += _assemble_param_temperature(component.BAT_capacity_temperature, lcl.Units.CELCIUS_DEG, format_decimalPoint, format_unit_enclosure, format_multivalue_delimiter, locale_index, format_temperature_positiveSign)
                            result += format_conditions_delimiter
                        
                        result = string_strip_word(result, format_conditions_delimiter)
                        result += format_conditions_enclosure[1]
                    result += format_param_delimiter

                #диапазон рабочих температур
                if component.GENERIC_temperature_range is not None:
                    result += _assemble_param_temperature_range(component.GENERIC_temperature_range, lcl.Units.CELCIUS_DEG, format_decimalPoint, format_unit_enclosure, format_rangeSymbol, locale_index, format_temperature_positiveSign)
                    result += format_param_delimiter

            #Дисплей
            elif type(component) is component.types.Display:
                pass

            #Светодиод
            elif type(component) is component.types.LED:
                #тип
                if component.LED_type == component.Type.INDICATION:
                    result += lcl.assemble_parameters.LED_TYPE_INDICATOR.value[locale_index]
                elif component.LED_type == component.Type.LIGHTING:
                    result += lcl.assemble_parameters.LED_TYPE_LIGHTING.value[locale_index]
                if len(result) > 0: result += format_param_delimiter

                #тип монтажа + размер
                if component.GENERIC_mount == component.Mounting.Type.SURFACE:
                    result += lcl.assemble_parameters.MOUNT_SURFACE.value[locale_index]
                    if component.GENERIC_size is not None: 
                        result +=  '\xa0' + component.GENERIC_size
                    result += format_param_delimiter
                elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE:
                    result += lcl.assemble_parameters.MOUNT_THROUGHHOLE.value[locale_index]
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
                    result += '\xa0' + _floatToString(component.LED_color_temperature, format_decimalPoint) + format_unit_enclosure[0] + lcl.Units.KELVIN.value[locale_index] + format_unit_enclosure[1]
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
                    result += lcl.assemble_parameters.LED_CRI.value[locale_index] + format_unit_enclosure[0] + _floatToString(component.LED_color_renderingIndex, format_decimalPoint) + format_unit_enclosure[1]
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
                    result += lcl.assemble_parameters.ARRAY.value[locale_index]
                    result += format_param_delimiter

            #Перемычка
            elif type(component) is component.types.Jumper:
                #тип
                if component.JMP_type is not None:
                    if component.JMP_type == component.Type.ELECTRICAL:
                        pass #result += '' + format_param_delimiter
                    elif component.JMP_type == component.Type.THERMAL:
                        result += lcl.assemble_parameters.JMP_TYPE_THERMAL.value[locale_index] + format_param_delimiter

                #тип монтажа + размер
                if component.GENERIC_mount == component.Mounting.Type.SURFACE: result += lcl.assemble_parameters.MOUNT_SURFACE.value[locale_index]
                elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE: result += lcl.assemble_parameters.MOUNT_THROUGHHOLE.value[locale_index]
                result += '\xa0'
                if component.GENERIC_size is not None: result += component.GENERIC_size
                result = result.strip('\xa0')
                result += format_param_delimiter

            #Реле
            elif type(component) is component.types.Relay:
                pass

            #Индуктивность
            elif type(component) is component.types.Inductor:
                #тип монтажа + размер
                if component.GENERIC_mount == component.Mounting.Type.SURFACE: result += lcl.assemble_parameters.MOUNT_SURFACE.value[locale_index]
                elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE: result += lcl.assemble_parameters.MOUNT_THROUGHHOLE.value[locale_index]
                result += '\xa0'
                if component.GENERIC_size is not None: result += component.GENERIC_size
                result = result.strip('\xa0')

                result += format_param_delimiter

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
                    result += lcl.assemble_parameters.LOW_CAPACITANCE.value[locale_index]
                    result += format_param_delimiter

            #Резистор
            elif type(component) is component.types.Resistor:
                #тип монтажа + размер
                if component.GENERIC_mount == component.Mounting.Type.SURFACE: result += lcl.assemble_parameters.MOUNT_SURFACE.value[locale_index]
                elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE: result += lcl.assemble_parameters.MOUNT_THROUGHHOLE.value[locale_index]
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

            #Переключатель
            elif type(component) is component.types.Switch:
                pass

            #Трансформатор
            elif type(component) is component.types.Transformer:
                pass

            #Диод
            elif type(component) is component.types.Diode:
                #тип
                if component.DIODE_type == component.Type.SCHOTTKY:
                    result += lcl.assemble_parameters.SCHOTTKY.value[locale_index]
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
                    result += lcl.assemble_parameters.PACKAGE.value[locale_index] + '\xa0' + component.GENERIC_package 
                    result += format_param_delimiter

            #Тиристор
            elif type(component) is component.types.Thyristor:
                pass

            #Транзистор
            elif type(component) is component.types.Transistor:
                pass

            #Оптоизолятор
            elif type(component) is component.types.Optoisolator:
                pass

            #Соединитель
            elif type(component) is component.types.Connector:
                pass

            #Фильтр ЭМП
            elif type(component) is component.types.EMIFilter:
                #тип
                if component.EMIF_type == component.Type.FERRITE_BEAD:
                    result += lcl.assemble_parameters.FERRITE_BEAD.value[locale_index]
                elif component.EMIF_type == component.Type.COMMON_MODE_CHOKE:
                    result += lcl.assemble_parameters.COMMON_MODE_CHOKE.value[locale_index]
                if len(result) > 0: result += format_param_delimiter

                #тип монтажа + размер
                if component.GENERIC_mount == component.Mounting.Type.SURFACE:
                    result += lcl.assemble_parameters.MOUNT_SURFACE.value[locale_index]
                    if component.GENERIC_size is not None: 
                        result +=  '\xa0' + component.GENERIC_size
                    result += format_param_delimiter
                elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE:
                    result += lcl.assemble_parameters.MOUNT_THROUGHHOLE.value[locale_index]
                    if component.GENERIC_size is not None: 
                        result +=  '\xa0' + component.GENERIC_size
                    result += format_param_delimiter

                #импеданс + допуск @ частота
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

            #Осциллятор (Резонатор)
            elif type(component) is component.types.Oscillator:
                #структура
                if component.OSC_structure == component.Structure.QUARTZ:
                    result += lcl.assemble_parameters.OSC_STRUCTURE_QUARTZ.value[locale_index]
                elif component.OSC_structure == component.Structure.CERAMIC:
                    result += lcl.assemble_parameters.OSC_STRUCTURE_CERAMIC.value[locale_index]
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
                        result += lcl.assemble_parameters.OSC_OVERTONE_FUNDAMENTAL.value[locale_index]
                    else:
                        result += str(component.OSC_overtone) + '\xa0' + lcl.assemble_parameters.OSC_OVERTONE.value[locale_index]
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
                    result += _assemble_param_temperature_range(component.GENERIC_temperature_range, lcl.Units.CELCIUS_DEG, format_decimalPoint, format_unit_enclosure, format_rangeSymbol, locale_index, format_temperature_positiveSign)
                    result += format_param_delimiter

            #Общий тип
            else:
                pass

        #дополнительные параметры
        if content_misc:
            for item in component.GENERIC_misc:
                result += format_param_delimiter
                result += item

        #удаляем лишние разделители
        result = string_strip_word(result, format_param_delimiter)
    else:
        #пересобирать не надо - возвращаем исходное описание
        if component.GENERIC_description is not None: result = component.GENERIC_description

    return result

#сборка списка замен
def assemble_substitutes(component, **kwargs):
    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры содержимого
    content_value = kwargs.get('content_subst_value', True)
    content_mfr   = kwargs.get('content_subst_mfr', True)
    content_note  = kwargs.get('content_subst_note', True)

    #параметры формата
    format_entry_enclosure = kwargs.get('format_subst_entry_enclosure', ['\nдоп.\xa0замена ', ''])
    format_value_enclosure = kwargs.get('format_subst_value_enclosure', ['', ''])
    format_mfr_enclosure   = kwargs.get('format_subst_mfr_enclosure', [' ф.\xa0', ''])
    format_note_enclosure  = kwargs.get('format_subst_note_enclosure', [' (', ')'])

    result = ''
    if component.GENERIC_substitute is not None:
        for substitute in component.GENERIC_substitute:
            result += format_entry_enclosure[0]
            if content_value and substitute.value is not None: result += format_value_enclosure[0] + substitute.value + format_value_enclosure[1]
            if content_mfr and substitute.manufacturer is not None: result += format_mfr_enclosure[0] + substitute.manufacturer + format_mfr_enclosure[1]
            if content_note and substitute.note is not None: result += format_note_enclosure[0] + substitute.note + format_note_enclosure[1]
            result += format_entry_enclosure[1]
    return result

#сборка параметра: значение
def _assemble_param_value(param, unit = None, decimalPoint = '.', unitEnclosure = ['', ''], multivalueDelimiter = '/', locale_index = 0, ranges = None):
    param = copy.copy(param)
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
        #определение множителя из единиц измерения
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

#сборка параметра: температура
def _assemble_param_temperature(param, unit = lcl.Units.KELVIN, decimalPoint = '.', unitEnclosure = ['', ''], multivalueDelimiter = '/', locale_index = 0, positiveSign = False):
    param = copy.copy(param)
    if isinstance(param, (int, float)): param = [param]         #если числовое значение, а не массив то делаем его массивом
    if not isinstance(param, (list, tuple)): return '<ERROR>'
    
    if unit == lcl.Units.KELVIN: offset = 0
    elif unit == lcl.Units.CELCIUS_DEG: offset = -273.15
    else: return '<ERROR>'

    for i in range(len(param)):
        param[i] += offset
        sign = ''
        if param[i] > 0 and positiveSign: sign = '+'
        param[i] = sign + _floatToString(param[i], decimalPoint)

    return multivalueDelimiter.join(param) + unitEnclosure[0] + unit.value[locale_index] + unitEnclosure[1]

#сборка параметра: диапазон рабочих температур
def _assemble_param_temperature_range(param, unit = lcl.Units.KELVIN, decimalPoint = '.', unitEnclosure = ['', ''], rangeSymbol = '\u2026', locale_index = 0, positiveSign = True):
    if not isinstance(param, (list, tuple)): return '<ERROR>'
    param = copy.copy(param)

    if unit == lcl.Units.KELVIN: offset = 0
    elif unit == lcl.Units.CELCIUS_DEG: offset = -273.15
    else: return '<ERROR>'

    for i in range(len(param)):
        param[i] += offset
        sign = ''
        if param[i] > 0 and positiveSign: sign = '+'
        param[i] = sign + _floatToString(param[i], decimalPoint)

    return rangeSymbol.join(param) + unitEnclosure[0] + unit.value[locale_index] + unitEnclosure[1]