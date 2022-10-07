import os
import copy
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

#Содержимое строки по ЕСКД
class eskdContent():
    def __init__(self,
                 value = True,
                 manufacturer = True,
                 description = True,
                 description_miscParams = True,
                 substitutes = True,
                 substitutes_value = True,
                 substitutes_manufacturer = True,
                 substitutes_note = True,
                 force_explicit = False):
        self.value                    = value                                 #номинал
        self.manufacturer             = manufacturer                          #производитель
        self.description              = description                           #описание
        self.description_miscParams   = description_miscParams                #дополнительные параметры в описании
        self.substitutes              = substitutes                           #допустимые замены
        self.substitutes_value        = substitutes_value                     #номинал в допустимых заменах
        self.substitutes_manufacturer = substitutes_manufacturer              #производитель в допустимых заменах
        self.substitutes_note         = substitutes_note                      #примечание в допустимых заменах
        self.force_explicit           = force_explicit                        #принудительное явное определение элементов

#Формат строки по ЕСКД
class eskdFormat():
    def __init__(self,
                 decimalPoint = '.',
                 descrParamsDelimiter = ', ',
                 valueToUnitDelimiter = '',
                 signToToleranceDelimiter = '',
                 multivalueDelimiter = '/',
                 conditionsValueDelimiter = '; ',
                 rangeSymbol = '\u2026',
                 toleranceEnclosure = ['\xa0', ''],
                 conditionsEnclosure = ['\xa0(', ')'],
                 valueEnclosure = ['', ''],
                 descrEnclosure = [' - ', ''],
                 mfrEnclosure = [' ф.\xa0', ''],
                 substSectionEnclosure = ['', ''],
                 substEntryEnclosure = ['\nдоп.\xa0замена ', ''],
                 substValueEnclosure = ['', ''],
                 substMfrEnclosure = [' ф.\xa0', ''],
                 substNoteEnclosure = [' (', ')']):
        self.decimalPoint             = decimalPoint                #разделитель целой и дробной части
        self.descrParamsDelimiter     = descrParamsDelimiter        #разделитель параметров в описании компонента
        self.valueToUnitDelimiter     = valueToUnitDelimiter        #разделитель значения и единиц измерения
        self.signToToleranceDelimiter = signToToleranceDelimiter    #разделитель знака и значения точности
        self.multivalueDelimiter      = multivalueDelimiter         #разделитель многозначного значения
        self.conditionsValueDelimiter = conditionsValueDelimiter    #разделитель значений условиях параметра
        self.rangeSymbol              = rangeSymbol                 #символ диапазона
        self.toleranceEnclosure       = toleranceEnclosure          #заключение допуска
        self.conditionsEnclosure      = conditionsEnclosure         #заключение условий параметра
        self.valueEnclosure           = valueEnclosure              #заключение номинала
        self.descrEnclosure           = descrEnclosure              #заключение описания
        self.mfrEnclosure             = mfrEnclosure                #заключение производителя
        self.substSectionEnclosure    = substSectionEnclosure       #заключение секции допустимых замен
        self.substEntryEnclosure      = substEntryEnclosure         #заключение каждого элемента в списке замен
        self.substValueEnclosure      = substValueEnclosure         #заключение номинала замены
        self.substMfrEnclosure        = substMfrEnclosure           #заключение производителя замены
        self.substNoteEnclosure       = substNoteEnclosure          #заключение примечания замены

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

#========================================================== END Generic functions =================================================

#Convert float number to string
def _floatToString(value, decimalPoint = '.'):
    result = '{0:.10f}'.format(value)
    result = result.rstrip('0').rstrip('.')
    result = result.replace('.', decimalPoint)
    return result

#Собирает значения полей компонента по ЕСКД из параметров компонента (сборка строк из параметров)
def assemble(data, **kwargs):
    #разворачиваем данные
    component = data

    #locale
    locale_index                     = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры содержимого полей
    content                          = copy.deepcopy(kwargs.get('content', eskdContent()))  #делаем копию чтобы не менять переданный объект
    content.value                    = kwargs.get('content_value', content.value)
    content.manufacturer             = kwargs.get('content_manufacturer', content.manufacturer)
    content.description              = kwargs.get('content_description', content.description)
    content.description_miscParams   = kwargs.get('content_description_miscParams', content.description_miscParams)
    content.substitutes              = kwargs.get('content_substitutes', content.substitutes)
    content.substitutes_value        = kwargs.get('content_substitutes_value', content.substitutes_value)
    content.substitutes_manufacturer = kwargs.get('content_substitutes_manufacturer', content.substitutes_manufacturer)
    content.substitutes_note         = kwargs.get('content_substitutes_note', content.substitutes_note)
    content.force_explicit           = kwargs.get('content_force_explicit', content.force_explicit)

    #параметры формата перечня
    fmt                              = copy.deepcopy(kwargs.get('format', eskdFormat()))    #делаем копию чтобы не менять переданный объект
    fmt.decimalPoint                 = kwargs.get('format_decimalPoint', fmt.decimalPoint)
    fmt.descrParamsDelimiter         = kwargs.get('format_descrParamsDelimiter', fmt.descrParamsDelimiter)
    fmt.valueToUnitDelimiter         = kwargs.get('format_valueToUnitDelimiter', fmt.valueToUnitDelimiter)
    fmt.signToToleranceDelimiter     = kwargs.get('format_signToToleranceDelimiter', fmt.signToToleranceDelimiter)
    fmt.multivalueDelimiter          = kwargs.get('format_multivalueDelimiter', fmt.multivalueDelimiter)
    fmt.conditionsValueDelimiter     = kwargs.get('format_conditionsValueDelimiter', fmt.conditionsValueDelimiter)
    fmt.rangeSymbol                  = kwargs.get('format_rangeSymbol', fmt.rangeSymbol)
    fmt.toleranceEnclosure           = kwargs.get('format_toleranceEnclosure', fmt.toleranceEnclosure)
    fmt.conditionsEnclosure          = kwargs.get('format_conditionsEnclosure', fmt.conditionsEnclosure)
    fmt.valueEnclosure               = kwargs.get('format_valueEnclosure', fmt.valueEnclosure)
    fmt.descrEnclosure               = kwargs.get('format_descrEnclosure', fmt.descrEnclosure)
    fmt.mfrEnclosure                 = kwargs.get('format_mfrEnclosure', fmt.mfrEnclosure)
    fmt.substSectionEnclosure        = kwargs.get('format_substSectionEnclosure', fmt.substSectionEnclosure)
    fmt.substEntryEnclosure          = kwargs.get('format_substEntryEnclosure', fmt.substEntryEnclosure)
    fmt.substValueEnclosure          = kwargs.get('format_substValueEnclosure', fmt.substValueEnclosure)
    fmt.substMfrEnclosure            = kwargs.get('format_substMfrEnclosure', fmt.substMfrEnclosure)
    fmt.substNoteEnclosure           = kwargs.get('format_substNoteEnclosure', fmt.substNoteEnclosure)

    #инициализируем переменные
    result = eskdValue()
    unit_prefix = ''

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
    if content.value and (component.GENERIC_value is not None):
        if component.GENERIC_explicit or (not content.description):
            result.label += fmt.valueEnclosure[0] + component.GENERIC_value + fmt.valueEnclosure[1]

    #--- производитель
    if content.manufacturer and (component.GENERIC_manufacturer is not None):
        if component.GENERIC_explicit:
            result.label += fmt.mfrEnclosure[0] + component.GENERIC_manufacturer + fmt.mfrEnclosure[1]

    #--- описание
    description = ''
    #--- --- Резистор
    if type(component) is component.types.Resistor:
        #тип монтажа + размер
        if component.GENERIC_mount == component.Mounting.Type.SURFACE: description += lcl.Labels.MOUNT_SURFACE.value[locale_index]
        elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE: description += lcl.Labels.MOUNT_THROUGHHOLE.value[locale_index]
        description += '\xa0'
        if component.GENERIC_size is not None: description += component.GENERIC_size
        description = description.strip('\xa0')

        description += fmt.descrParamsDelimiter
        
        #мощность
        if component.RES_power is not None:
            description += _floatToString(component.RES_power, fmt.decimalPoint) + fmt.valueToUnitDelimiter + lcl.Units.WATT.value[locale_index]
            description += fmt.descrParamsDelimiter
        
        #напряжение
        if component.RES_voltage is not None:
            description += _floatToString(component.RES_voltage, fmt.decimalPoint) + fmt.valueToUnitDelimiter + lcl.Units.VOLT.value[locale_index] 
            description += fmt.descrParamsDelimiter

        #сопротивление + допуск
        if component.RES_resistance is not None:
            if component.RES_resistance >= 1e6:
                multiplier = 1e-6
                unit_prefix = lcl.MetricPrefix.MEGA.value[locale_index]
            elif component.RES_resistance >= 1e3:
                multiplier = 1e-3
                unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.RES_resistance * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.OHM.value[locale_index]
            if component.RES_tolerance is not None:
                description += fmt.toleranceEnclosure[0] + _assemble_param_tolerance(component.RES_tolerance, None, fmt.decimalPoint, fmt.valueToUnitDelimiter, fmt.signToToleranceDelimiter, fmt.rangeSymbol, locale_index) + fmt.toleranceEnclosure[1]
            description += fmt.descrParamsDelimiter

        #ТКС
        if component.RES_tempCoeff is not None:
            description += _assemble_param_tolerance(component.RES_tempCoeff, None, fmt.decimalPoint, fmt.valueToUnitDelimiter, fmt.signToToleranceDelimiter, fmt.rangeSymbol, locale_index)
            description += fmt.descrParamsDelimiter

    #--- --- Перемычка
    elif type(component) is component.types.Jumper:
        #тип + размер
        if component.GENERIC_mount == component.Mounting.Type.SURFACE: description += lcl.Labels.MOUNT_SURFACE.value[locale_index]
        elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE: description += lcl.Labels.MOUNT_THROUGHHOLE.value[locale_index]
        description += '\xa0'
        if component.GENERIC_size is not None: description += component.GENERIC_size
        description = description.strip('\xa0')
        description += fmt.descrParamsDelimiter
        
    #--- --- Конденсатор
    elif type(component) is component.types.Capacitor:
        #тип
        if component.CAP_type == component.Type.CERAMIC:
            description += lcl.Labels.CAP_TYPE_CERAMIC.value[locale_index]
        elif component.CAP_type == component.Type.TANTALUM:
            description += lcl.Labels.CAP_TYPE_TANTALUM.value[locale_index]
        elif component.CAP_type == component.Type.FILM:
            description += lcl.Labels.CAP_TYPE_FILM.value[locale_index]
        elif component.CAP_type == component.Type.ALUM_ELECTROLYTIC:
            description += lcl.Labels.CAP_TYPE_ALUM_ELECTROLYTIC.value[locale_index]
        elif component.CAP_type == component.Type.ALUM_POLYMER:
            description += lcl.Labels.CAP_TYPE_ALUM_POLYMER.value[locale_index]
        elif component.CAP_type == component.Type.SUPERCAPACITOR:
            description += lcl.Labels.CAP_TYPE_SUPERCAPACITOR.value[locale_index]

        if len(description) > 0: description += fmt.descrParamsDelimiter

        #размер
        if component.GENERIC_mount == component.Mounting.Type.SURFACE:
            description += lcl.Labels.MOUNT_SURFACE.value[locale_index]
        elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE:
            if component.GENERIC_THtype == component.Mounting.ThroughHole.AXIAL:
                description += lcl.Labels.MOUNT_AXIAL.value[locale_index]
            elif component.GENERIC_THtype == component.Mounting.ThroughHole.RADIAL:
                description += lcl.Labels.MOUNT_RADIAL.value[locale_index]
        description += "\xa0"
        if component.GENERIC_size is not None: description += component.GENERIC_size
        description = description.strip('\xa0')

        description += fmt.descrParamsDelimiter
        
        #диэлектрик
        if component.CAP_dielectric is not None:
            description += component.CAP_dielectric
            description += fmt.descrParamsDelimiter

        #напряжение
        if component.CAP_voltage is not None:
            description += _floatToString(component.CAP_voltage, fmt.decimalPoint) + fmt.valueToUnitDelimiter + lcl.Units.VOLT.value[locale_index] 
            description += fmt.descrParamsDelimiter

        #ёмкость + допуск
        if component.CAP_capacitance is not None:
            if component.CAP_capacitance < 10e-9:
                multiplier = 1e12
                unit_prefix = lcl.MetricPrefix.PICO.value[locale_index]
            elif component.CAP_capacitance < 10e-3:
                multiplier = 1e6
                unit_prefix = lcl.MetricPrefix.MICRO.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.CAP_capacitance * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.FARAD.value[locale_index]  
            if component.CAP_tolerance is not None:
                description += fmt.toleranceEnclosure[0] + _assemble_param_tolerance(component.CAP_tolerance, None, fmt.decimalPoint, fmt.valueToUnitDelimiter, fmt.signToToleranceDelimiter, fmt.rangeSymbol, locale_index) + fmt.toleranceEnclosure[1]
            description += fmt.descrParamsDelimiter

        #низкий импеданс
        if component.CAP_lowImpedance:
            description += lcl.Labels.LOW_ESR.value[locale_index]
            description += fmt.descrParamsDelimiter

    #--- --- Индуктивность
    elif type(component) is component.types.Inductor:
        #индуктивность + допуск
        if component.IND_inductance is not None:
            if component.IND_inductance < 1e-6:
                multiplier = 1e9
                unit_prefix = lcl.MetricPrefix.NANO.value[locale_index]
            elif component.IND_inductance < 1e-3:
                multiplier = 1e6
                unit_prefix = lcl.MetricPrefix.MICRO.value[locale_index]
            elif component.IND_inductance < 1e-0:
                multiplier = 1e3
                unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.IND_inductance * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.HENRY.value[locale_index]  
            if component.IND_tolerance is not None:
                description += fmt.toleranceEnclosure[0] + _assemble_param_tolerance(component.IND_tolerance, None, fmt.decimalPoint, fmt.valueToUnitDelimiter, fmt.signToToleranceDelimiter, fmt.rangeSymbol, locale_index) + fmt.toleranceEnclosure[1]
            description += fmt.descrParamsDelimiter

        #ток
        if component.IND_current is not None:
            if component.IND_current < 1e-0:
                multiplier = 1e3
                unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.IND_current * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.AMPERE.value[locale_index] 
            description += fmt.descrParamsDelimiter

        #низкая ёмкость
        if component.IND_lowCapacitance:
            description += lcl.Labels.LOW_CAPACITANCE.value[locale_index]
            description += fmt.descrParamsDelimiter

    #--- --- Диод
    elif type(component) is component.types.Diode:
        #тип
        if component.DIODE_type == component.Type.SCHOTTKY:
            description += lcl.Labels.SCHOTTKY.value[locale_index]
            description += fmt.descrParamsDelimiter

        #обратное напряжение
        if component.DIODE_reverseVoltage is not None:
            if component.DIODE_reverseVoltage < 1e3:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            else:
                multiplier = 1e-3
                unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
            description += _floatToString(component.DIODE_reverseVoltage * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.VOLT.value[locale_index] 
            if component.DIODE_reverseVoltage_tolerance is not None:
                description += fmt.toleranceEnclosure[0] + _assemble_param_tolerance(component.DIODE_reverseVoltage_tolerance, None, fmt.decimalPoint, fmt.valueToUnitDelimiter, fmt.signToToleranceDelimiter, fmt.rangeSymbol, locale_index) + fmt.toleranceEnclosure[1]
            description += fmt.descrParamsDelimiter

        #прямой ток
        if component.DIODE_forwardCurrent is not None:
            if component.DIODE_forwardCurrent < 1e0:
                multiplier = 1e3
                unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.DIODE_forwardCurrent * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.AMPERE.value[locale_index] 
            description += fmt.descrParamsDelimiter

        #максимальная мощность
        if component.DIODE_power is not None:
            if component.DIODE_power < 1e0:
                multiplier = 1e3
                unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
            elif component.DIODE_power >= 1e3:
                multiplier = 1e-3
                unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.DIODE_power * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.WATT.value[locale_index] 
            description += fmt.descrParamsDelimiter

        #ёмкость + допуск + условия
        if component.DIODE_capacitance is not None:
            multiplier = 1e12
            unit_prefix = lcl.MetricPrefix.PICO.value[locale_index]
            description += _floatToString(component.DIODE_capacitance * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.FARAD.value[locale_index] 
            #допуск
            if component.DIODE_capacitance_tolerance is not None:
                description += fmt.toleranceEnclosure[0] + _assemble_param_tolerance(component.DIODE_capacitance_tolerance, None, fmt.decimalPoint, fmt.valueToUnitDelimiter, fmt.signToToleranceDelimiter, fmt.rangeSymbol, locale_index) + fmt.toleranceEnclosure[1]
            #условия
            if (component.DIODE_capacitance_voltage is not None) or (component.DIODE_capacitance_frequency is not None):
                description += fmt.conditionsEnclosure[0]
                #напряжение
                if component.DIODE_capacitance_voltage is not None:
                    if component.DIODE_capacitance_voltage >= 1e3:
                        multiplier = 1e-3
                        unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
                    else:
                        multiplier = 1e0
                        unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
                    description += _floatToString(component.DIODE_capacitance_voltage * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.VOLT.value[locale_index] 
                    description += fmt.conditionsValueDelimiter
                #частота
                if component.DIODE_capacitance_frequency is not None:
                    if component.DIODE_capacitance_frequency >= 1e9:
                        multiplier = 1e-9
                        unit_prefix = lcl.MetricPrefix.GIGA.value[locale_index]
                    elif component.DIODE_capacitance_frequency >= 1e6:
                        multiplier = 1e-6
                        unit_prefix = lcl.MetricPrefix.MEGA.value[locale_index]
                    elif component.DIODE_capacitance_frequency >= 1e3:
                        multiplier = 1e-3
                        unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
                    else:
                        multiplier = 1e0
                        unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
                    description += _floatToString(component.DIODE_capacitance_frequency * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.HERTZ.value[locale_index] 
                    description += fmt.conditionsValueDelimiter
                description = string_strip_word(description, fmt.conditionsValueDelimiter)
                description += fmt.conditionsEnclosure[1]
            description += fmt.descrParamsDelimiter

        #корпус
        if component.GENERIC_package is not None:
            description += lcl.Labels.PACKAGE.value[locale_index] + '\xa0' + component.GENERIC_package 
            description += fmt.descrParamsDelimiter

    #--- --- TVS
    elif type(component) is component.types.TVS:
        #тип
        if component.TVS_type == component.Type.DIODE:          #диод
            description += lcl.Labels.TVS_TYPE_DIODE.value[locale_index]
            description += fmt.descrParamsDelimiter

            #двунаправленный тип
            if component.TVS_bidirectional is not None:
                if component.TVS_bidirectional:
                    description += lcl.Labels.TVS_BIDIRECTIONAL.value[locale_index]
                else:
                    description += lcl.Labels.TVS_UNIDIRECTIONAL.value[locale_index]
                description += fmt.descrParamsDelimiter

            #максимальное рабочее напряжение
            if component.TVS_standoff_voltage is not None:
                description += _floatToString(component.TVS_standoff_voltage, fmt.decimalPoint)
                description += fmt.valueToUnitDelimiter + lcl.Units.VOLT.value[locale_index] 
                description += fmt.descrParamsDelimiter

            #мощность + тип тестового импульса
            if component.TVS_power is not None:
                if component.TVS_power >= 1e3:
                    multiplier = 1e-3
                    unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
                else:
                    multiplier = 1e0
                    unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
                description += _floatToString(component.TVS_power * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.WATT.value[locale_index] 
                if component.TVS_testPulse is not None:
                    description += fmt.conditionsEnclosure[0]
                    if component.TVS_testPulse == component.TestPulse.US_8_20:
                        description += '8/20' + fmt.valueToUnitDelimiter + lcl.MetricPrefix.MICRO.value[locale_index] + lcl.Units.SECOND.value[locale_index] 
                    elif component.TVS_testPulse == component.TestPulse.US_10_1000:
                        description += '10/1000' + fmt.valueToUnitDelimiter + lcl.MetricPrefix.MICRO.value[locale_index] + lcl.Units.SECOND.value[locale_index] 
                    else:
                        description += '???'
                    description += fmt.conditionsEnclosure[1]
                description += fmt.descrParamsDelimiter

            #корпус
            if component.GENERIC_package is not None:
                description += lcl.Labels.PACKAGE.value[locale_index] + '\xa0' + component.GENERIC_package 
                description += fmt.descrParamsDelimiter

        elif component.TVS_type == component.Type.VARISTOR:     #варистор
            description += lcl.Labels.TVS_TYPE_VARISTOR.value[locale_index]
            description += fmt.descrParamsDelimiter

            #тип + размер
            if component.GENERIC_mount == component.Mounting.Type.SURFACE: description += lcl.Labels.MOUNT_SURFACE.value[locale_index]
            elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE: description += lcl.Labels.MOUNT_THROUGHHOLE.value[locale_index]
            description += '\xa0'
            if component.GENERIC_size is not None: description += component.GENERIC_size
            description = description.strip('\xa0')
            description += fmt.descrParamsDelimiter
            
            #максимальное рабочее напряжение
            if component.TVS_standoff_voltage is not None:
                description += _floatToString(component.TVS_standoff_voltage, fmt.decimalPoint)
                description += fmt.valueToUnitDelimiter + lcl.Units.VOLT.value[locale_index] 
                description += fmt.descrParamsDelimiter
            
            #энергия + тип тестового импульса
            if component.TVS_energy is not None:
                if component.TVS_energy >= 1e3:
                    multiplier = 1e-3
                    unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
                elif component.TVS_energy >= 1e0:
                    multiplier = 1e0
                    unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
                else:
                    multiplier = 1e3
                    unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
                description += _floatToString(component.TVS_energy * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.JOULE.value[locale_index] 
                if component.TVS_testPulse is not None:
                    description += fmt.conditionsEnclosure[0]
                    if component.TVS_testPulse == component.TestPulse.US_8_20:
                        description += '8/20' + fmt.valueToUnitDelimiter + lcl.MetricPrefix.MICRO.value[locale_index] + lcl.Units.SECOND.value[locale_index] 
                    elif component.TVS_testPulse == component.TestPulse.US_10_1000:
                        description += '10/1000' + fmt.valueToUnitDelimiter + lcl.MetricPrefix.MICRO.value[locale_index] + lcl.Units.SECOND.value[locale_index] 
                    else:
                        description += '???'
                    description += fmt.conditionsEnclosure[1]
                description += fmt.descrParamsDelimiter

    #--- --- Фильтр ЭМП
    elif type(component) is component.types.EMIFilter:
        #тип
        if component.EMIF_type == component.Type.FERRITE_BEAD:
            description += lcl.Labels.FERRITE_BEAD.value[locale_index]
        elif component.EMIF_type == component.Type.COMMON_MODE_CHOKE:
            description += lcl.Labels.COMMON_MODE_CHOKE.value[locale_index]
        if len(description) > 0: description += fmt.descrParamsDelimiter

        #тип монтажа + размер
        if component.GENERIC_mount == component.Mounting.Type.SURFACE:
            description += lcl.Labels.MOUNT_SURFACE.value[locale_index]
            if component.GENERIC_size is not None: 
                description +=  '\xa0' + component.GENERIC_size
            description += fmt.descrParamsDelimiter
        elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE:
            description += lcl.Labels.MOUNT_THROUGHHOLE.value[locale_index]
            if component.GENERIC_size is not None: 
                description +=  '\xa0' + component.GENERIC_size
            description += fmt.descrParamsDelimiter

        #импеданс + допуск + частота
        if component.EMIF_impedance is not None:
            if component.EMIF_impedance >= 1e3:
                multiplier = 1e-3
                unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.EMIF_impedance * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.OHM.value[locale_index] 
            if component.EMIF_impedance_tolerance is not None:
                description += fmt.toleranceEnclosure[0] + _assemble_param_tolerance(component.EMIF_impedance_tolerance, None, fmt.decimalPoint, fmt.valueToUnitDelimiter, fmt.signToToleranceDelimiter, fmt.rangeSymbol, locale_index) + fmt.toleranceEnclosure[1]
            if component.EMIF_impedance_frequency is not None:
                description += fmt.conditionsEnclosure[0]
                if component.EMIF_impedance_frequency >= 1e9:
                    multiplier = 1e-9
                    unit_prefix = lcl.MetricPrefix.GIGA.value[locale_index]
                elif component.EMIF_impedance_frequency >= 1e6:
                    multiplier = 1e-6
                    unit_prefix = lcl.MetricPrefix.MEGA.value[locale_index]
                elif component.EMIF_impedance_frequency >= 1e3:
                    multiplier = 1e-3
                    unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
                else:
                    multiplier = 1e0
                    unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
                description += _floatToString(component.EMIF_impedance_frequency * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.HERTZ.value[locale_index] 
                description += fmt.conditionsEnclosure[1]
            description += fmt.descrParamsDelimiter

        #индуктивность + допуск
        if component.EMIF_inductance is not None:
            if component.EMIF_inductance < 1e-6:
                multiplier = 1e9
                unit_prefix = lcl.MetricPrefix.NANO.value[locale_index]
            elif component.EMIF_inductance < 1e-3:
                multiplier = 1e6
                unit_prefix = lcl.MetricPrefix.MICRO.value[locale_index]
            elif component.EMIF_inductance < 1e-0:
                multiplier = 1e3
                unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.EMIF_inductance * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.HENRY.value[locale_index] 
            if component.EMIF_inductance_tolerance is not None:
                description += fmt.toleranceEnclosure[0] + _assemble_param_tolerance(component.EMIF_inductance_tolerance, None, fmt.decimalPoint, fmt.valueToUnitDelimiter, fmt.signToToleranceDelimiter, fmt.rangeSymbol, locale_index) + fmt.toleranceEnclosure[1]
            description += fmt.descrParamsDelimiter

        #ёмкость + допуск
        if component.EMIF_capacitance is not None:
            if component.EMIF_capacitance < 1e-9:
                multiplier = 1e12
                unit_prefix = lcl.MetricPrefix.PICO.value[locale_index]
            elif component.EMIF_capacitance < 1e-6:
                multiplier = 1e9
                unit_prefix = lcl.MetricPrefix.NANO.value[locale_index]
            elif component.EMIF_capacitance < 1e-3:
                multiplier = 1e6
                unit_prefix = lcl.MetricPrefix.MICRO.value[locale_index]
            elif component.EMIF_capacitance < 1e-0:
                multiplier = 1e3
                unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.EMIF_capacitance * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.FARAD.value[locale_index] 
            if component.EMIF_capacitance_tolerance is not None:
                description += fmt.toleranceEnclosure[0] + _assemble_param_tolerance(component.EMIF_capacitance_tolerance, None, fmt.decimalPoint, fmt.valueToUnitDelimiter, fmt.signToToleranceDelimiter, fmt.rangeSymbol, locale_index) + fmt.toleranceEnclosure[1]
            description += fmt.descrParamsDelimiter

        #сопротивление + допуск
        if component.EMIF_resistance is not None:
            if component.EMIF_resistance < 1e0:
                multiplier = 1e3
                unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
            elif component.EMIF_resistance >= 1e3:
                multiplier = 1e-3
                unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.EMIF_resistance * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.OHM.value[locale_index] 
            if component.EMIF_resistance_tolerance is not None:
                description += fmt.toleranceEnclosure[0] + _assemble_param_tolerance(component.EMIF_resistance_tolerance, None, fmt.decimalPoint, fmt.valueToUnitDelimiter, fmt.signToToleranceDelimiter, fmt.rangeSymbol, locale_index) + fmt.toleranceEnclosure[1]
            description += fmt.descrParamsDelimiter

        #номинальный ток
        if component.EMIF_current is not None:
            if component.EMIF_current < 1e0:
                multiplier = 1e3
                unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
            elif component.EMIF_current >= 1e3:
                multiplier = 1e-3
                unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.EMIF_current * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.AMPERE.value[locale_index] 
            description += fmt.descrParamsDelimiter

        #максимальное напряжение
        if component.EMIF_voltage is not None:
            if component.EMIF_voltage >= 1e3:
                multiplier = 1e-3
                unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.EMIF_voltage * multiplier, fmt.decimalPoint) * fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.VOLT.value[locale_index] 
            description += fmt.descrParamsDelimiter

    #--- --- Предохранитель
    elif type(component) is component.types.CircuitBreaker:
        #тип
        if component.CBRK_type == component.Type.FUSE:
            description += lcl.Labels.CBRK_TYPE_FUSE.value[locale_index]
        elif component.CBRK_type == component.Type.PTC_RESETTABLE:
            description += lcl.Labels.CBRK_TYPE_PTCRESETTABLE.value[locale_index]
        elif component.CBRK_type == component.Type.THERMAL:
            description += lcl.Labels.CBRK_TYPE_THERMAL.value[locale_index]
        if len(description) > 0: description += fmt.descrParamsDelimiter

        #тип монтажа + размер
        if component.GENERIC_mount == component.Mounting.Type.SURFACE: description += lcl.Labels.MOUNT_SURFACE.value[locale_index] + '\xa0'
        elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE: description += lcl.Labels.MOUNT_THROUGHHOLE.value[locale_index] + '\xa0'
        elif component.GENERIC_mount == component.Mounting.Type.HOLDER: description += lcl.Labels.MOUNT_HOLDER.value[locale_index] + '\xa0'
        if component.GENERIC_size is not None: description += component.GENERIC_size
        description = description.strip('\xa0')
        description += fmt.descrParamsDelimiter

        #номинальный ток
        if component.CBRK_current_rating is not None:
            if component.CBRK_current_rating < 1e0:
                multiplier = 1e3
                unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
            elif component.CBRK_current_rating >= 1e3:
                multiplier = 1e-3
                unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.CBRK_current_rating * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.AMPERE.value[locale_index] 
            description += fmt.descrParamsDelimiter

        #точка плавления
        if component.CBRK_meltingPoint is not None:
            description += _floatToString(component.CBRK_meltingPoint, fmt.decimalPoint) + fmt.valueToUnitDelimiter + lcl.Units.AMPERE.value[locale_index]  + '²' + lcl.Units.SECOND.value[locale_index]  
            description += fmt.descrParamsDelimiter

        #максимальное напряжение
        if component.CBRK_voltage is not None:
            if component.CBRK_voltage >= 1e3:
                multiplier = 1e-3
                unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.CBRK_voltage * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.VOLT.value[locale_index] 
            if component.CBRK_voltage_ac: description += '\xa0' + lcl.Labels.VOLTAGE_AC.value[locale_index]
            description += fmt.descrParamsDelimiter

        #сопротивление
        if component.CBRK_resistance is not None:
            if component.CBRK_resistance < 1e-3:
                multiplier = 1e6
                unit_prefix = lcl.MetricPrefix.MICRO.value[locale_index]
            elif component.CBRK_current_rating < 1e0:
                multiplier = 1e3
                unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.CBRK_resistance * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.OHM.value[locale_index] 
            description += fmt.descrParamsDelimiter

        #максимальная мощность
        if component.CBRK_power is not None:
            if component.CBRK_power < 1e0:
                multiplier = 1e3
                unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
            elif component.CBRK_power >= 1e3:
                multiplier = 1e-3
                unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.CBRK_power * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.WATT.value[locale_index] 
            description += fmt.descrParamsDelimiter

        #классификация скорости срабатывания
        if component.CBRK_speed_grade is not None:
            if component.CBRK_speed_grade == component.SpeedGrade.FAST: description += lcl.Labels.CBRK_SPEEDGRADE_FAST.value[locale_index] + fmt.descrParamsDelimiter
            elif component.CBRK_speed_grade == component.SpeedGrade.MEDIUM: description += lcl.Labels.CBRK_SPEEDGRADE_MEDIUM.value[locale_index] + fmt.descrParamsDelimiter
            elif component.CBRK_speed_grade == component.SpeedGrade.SLOW: description += lcl.Labels.CBRK_SPEEDGRADE_SLOW.value[locale_index] + fmt.descrParamsDelimiter

    #--- --- Резонатор
    elif type(component) is component.types.Oscillator:
        #тип
        if component.OSC_type == component.Type.CRYSTAL:
            description += lcl.Labels.OSC_TYPE_CRYSTAL.value[locale_index]
        elif component.OSC_type == component.Type.CERAMIC:
            description += lcl.Labels.OSC_TYPE_CERAMICS.value[locale_index]
        elif component.OSC_type == component.Type.MEMS:
            description += lcl.Labels.OSC_TYPE_MEMS.value[locale_index]
        if len(description) > 0: description += fmt.descrParamsDelimiter

        #частота + допуск
        if component.OSC_frequency is not None:
            if component.OSC_frequency >= 1e6:
                multiplier = 1e-6
                unit_prefix = lcl.MetricPrefix.MEGA.value[locale_index]
            elif component.OSC_frequency >= 1e3:
                multiplier = 1e-3
                unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.OSC_frequency * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.HERTZ.value[locale_index] 
            if component.OSC_tolerance is not None:
                description += fmt.toleranceEnclosure[0] + _assemble_param_tolerance(component.OSC_tolerance, None, fmt.decimalPoint, fmt.valueToUnitDelimiter, fmt.signToToleranceDelimiter, fmt.rangeSymbol, locale_index) + fmt.toleranceEnclosure[1]
            description += fmt.descrParamsDelimiter

        #гармоника
        if component.OSC_overtone is not None:
            if component.OSC_overtone == 1:
                description += lcl.Labels.OSC_OVERTONE_FUNDAMENTAL.value[locale_index]
            else:
                description += str(component.OSC_overtone) + '\xa0' + lcl.Labels.OSC_OVERTONE.value[locale_index]
            description += fmt.descrParamsDelimiter

        #стабильность частоты
        if component.OSC_stability is not None:
            description += _assemble_param_tolerance(component.OSC_stability, None, fmt.decimalPoint, fmt.valueToUnitDelimiter, fmt.signToToleranceDelimiter, fmt.rangeSymbol, locale_index)
            description += fmt.descrParamsDelimiter

        #ёмкость нагрузки
        if component.OSC_loadCapacitance is not None:
            multiplier = 1e12
            unit_prefix = lcl.MetricPrefix.PICO.value[locale_index]
            description += _floatToString(component.OSC_loadCapacitance * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.FARAD.value[locale_index] 
            description += fmt.descrParamsDelimiter

        #эквивалентное последовательное сопротивление
        if component.OSC_ESR is not None:
            if component.OSC_ESR >= 1e3:
                multiplier = 1e-3
                unit_prefix = lcl.MetricPrefix.KILO.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.OSC_ESR * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.OHM.value[locale_index] 
            description += fmt.descrParamsDelimiter

        #уровень возбуждения
        if component.OSC_driveLevel is not None:
            if component.OSC_driveLevel < 1e-3:
                multiplier = 1e6
                unit_prefix = lcl.MetricPrefix.MICRO.value[locale_index]
            elif component.OSC_driveLevel < 1e0:
                multiplier = 1e3
                unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.OSC_driveLevel * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.WATT.value[locale_index] 
            description += fmt.descrParamsDelimiter

        #диапазон рабочих температур
        if component.GENERIC_temperature_range is not None:
            description += _assemble_param_temperature_range(component.GENERIC_temperature_range, lcl.Units.CELCIUS_DEG.value[locale_index] , fmt.decimalPoint, fmt.valueToUnitDelimiter, fmt.signToToleranceDelimiter, fmt.rangeSymbol)
            description += fmt.descrParamsDelimiter

    #--- --- Светодиод
    elif type(component) is component.types.LED:
        #тип
        if component.LED_type == component.Type.INDICATION:
            description += lcl.Labels.LED_TYPE_INDICATOR.value[locale_index]
        elif component.LED_type == component.Type.LIGHTING:
            description += lcl.Labels.LED_TYPE_LIGHTING.value[locale_index]
        if len(description) > 0: description += fmt.descrParamsDelimiter

        #тип монтажа + размер
        if component.GENERIC_mount == component.Mounting.Type.SURFACE:
            description += lcl.Labels.MOUNT_SURFACE.value[locale_index]
            if component.GENERIC_size is not None: 
                description +=  '\xa0' + component.GENERIC_size
            description += fmt.descrParamsDelimiter
        elif component.GENERIC_mount == component.Mounting.Type.THROUGHHOLE:
            description += lcl.Labels.MOUNT_THROUGHHOLE.value[locale_index]
            if component.GENERIC_size is not None: 
                description +=  '\xa0' + component.GENERIC_size
            description += fmt.descrParamsDelimiter

        #цвет
        if component.LED_color is not None:
            if   component.LED_color == component.Color.INFRARED:    description += lcl.Color.INFRARED.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.ULTRAVIOLET: description += lcl.Color.ULTRAVIOLET.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.RED:         description += lcl.Color.RED.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.ORANGE:      description += lcl.Color.ORANGE.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.AMBER:       description += lcl.Color.AMBER.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.YELLOW:      description += lcl.Color.YELLOW.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.LIME:        description += lcl.Color.LIME.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.GREEN:       description += lcl.Color.GREEN.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.TURQUOISE:   description += lcl.Color.TURQUOISE.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.CYAN:        description += lcl.Color.CYAN.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.BLUE:        description += lcl.Color.BLUE.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.VIOLET:      description += lcl.Color.VIOLET.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.PURPLE:      description += lcl.Color.PURPLE.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.PINK:        description += lcl.Color.PINK.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.MULTI:       description += lcl.Color.MULTI.value[locale_index] + fmt.descrParamsDelimiter
            elif component.LED_color == component.Color.WHITE:       description += lcl.Color.WHITE.value[locale_index] + fmt.descrParamsDelimiter
                
        #цветовая температура
        if component.LED_color_temperature is not None:
            description += '\xa0' + _floatToString(component.LED_color_temperature, fmt.decimalPoint) + fmt.valueToUnitDelimiter + lcl.Units.KELVIN.value[locale_index] 
            description += fmt.descrParamsDelimiter
            
        #длина волны
        if component.LED_wavelength_peak is not None:
            multiplier = 1e9
            unit_prefix = lcl.MetricPrefix.NANO.value[locale_index]
            description += _floatToString(component.LED_wavelength_peak * multiplier, fmt.decimalPoint)
            if component.LED_wavelength_dominant is not None:
                description += fmt.multivalueDelimiter + _floatToString(component.LED_wavelength_dominant * multiplier, fmt.decimalPoint)
            description += fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.METRE.value[locale_index] 
            description += fmt.descrParamsDelimiter

        #индекс цветопередачи
        if component.LED_color_renderingIndex is not None:
            description += lcl.Labels.LED_CRI.value[locale_index] + fmt.valueToUnitDelimiter + _floatToString(component.LED_color_renderingIndex, fmt.decimalPoint)
            description += fmt.descrParamsDelimiter

        #сила света
        if component.LED_luminous_intensity is not None:
            if component.LED_luminous_intensity < 1e0:
                multiplier = 1e3
                unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.LED_luminous_intensity * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.CANDELA.value[locale_index] 
            if component.LED_luminous_intensity_current is not None:
                description += fmt.conditionsEnclosure[0]
                if component.LED_luminous_intensity_current < 1e-3:
                    multiplier = 1e6
                    unit_prefix = lcl.MetricPrefix.MICRO.value[locale_index]
                elif component.LED_luminous_intensity_current < 1e0:
                    multiplier = 1e3
                    unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
                else:
                    multiplier = 1e0
                    unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
                description += _floatToString(component.LED_luminous_intensity_current * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.AMPERE.value[locale_index] 
                description += fmt.conditionsEnclosure[1]
            description += fmt.descrParamsDelimiter

        #световой поток
        if component.LED_luminous_flux is not None:
            description += _floatToString(component.LED_luminous_flux, fmt.decimalPoint) + fmt.valueToUnitDelimiter + lcl.Units.LUMEN.value[locale_index] 
            if component.LED_luminous_flux_current is not None:
                description += fmt.conditionsEnclosure[0]
                if component.LED_luminous_flux_current < 1e-3:
                    multiplier = 1e6
                    unit_prefix = lcl.MetricPrefix.MICRO.value[locale_index]
                elif component.LED_luminous_flux_current < 1e0:
                    multiplier = 1e3
                    unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
                else:
                    multiplier = 1e0
                    unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
                description += _floatToString(component.LED_luminous_flux_current * multiplier, fmt.decimalPoint) + fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.AMPERE.value[locale_index] 
                description += fmt.conditionsEnclosure[1]
            description += fmt.descrParamsDelimiter

        #угол обзора
        if component.LED_viewingAngle is not None:
            description += _floatToString(component.LED_viewingAngle, fmt.decimalPoint) + fmt.valueToUnitDelimiter + lcl.Units.DEGREE.value[locale_index]
            description += fmt.descrParamsDelimiter

        #прямой ток
        if component.LED_current_nominal is not None:
            if component.LED_current_nominal < 1e0:
                multiplier = 1e3
                unit_prefix = lcl.MetricPrefix.MILLI.value[locale_index]
            else:
                multiplier = 1e0
                unit_prefix = lcl.MetricPrefix.NONE.value[locale_index]
            description += _floatToString(component.LED_current_nominal * multiplier, fmt.decimalPoint)
            if component.LED_current_maximum is not None:
                description += fmt.multivalueDelimiter + _floatToString(component.LED_current_maximum * multiplier, fmt.decimalPoint)
            description += fmt.valueToUnitDelimiter + unit_prefix + lcl.Units.AMPERE.value[locale_index]
            description += fmt.descrParamsDelimiter

        #прямое падение напряжения
        if component.LED_voltage_forward is not None:
            description += _floatToString(component.LED_voltage_forward, fmt.decimalPoint) + fmt.valueToUnitDelimiter + lcl.Units.VOLT.value[locale_index]
            description += fmt.descrParamsDelimiter

        #сборка
        if component.GENERIC_assembly is not None:
            description += lcl.Labels.ASSEMBLY.value[locale_index]
            description += fmt.descrParamsDelimiter

    #--- --- Общий тип
    else:
        pass

    #--- дополнительные параметры
    if content.description_miscParams:
        for item in component.GENERIC_misc:
            description += item
            description += fmt.descrParamsDelimiter

    #--- удаляем лишние разделители
    description = string_strip_word(description, fmt.descrParamsDelimiter)

    #--- запись описания
    if content.description and len(description) > 0:
        if len(result.label) > 0:
            result.label += fmt.descrEnclosure[0] + description + fmt.descrEnclosure[1]
        else:
            result.label += description

    #--- допустимые замены
    if content.substitutes:
        if component.GENERIC_substitute is not None:
            result.label += fmt.substSectionEnclosure[0]
            for substitute in component.GENERIC_substitute:
                result.label += fmt.substEntryEnclosure[0]
                if content.substitutes_value and substitute.value is not None: result.label += fmt.substValueEnclosure[0] + substitute.value + fmt.substValueEnclosure[1]
                if content.substitutes_manufacturer and substitute.manufacturer is not None: result.label += fmt.substMfrEnclosure[0] + substitute.manufacturer + fmt.substMfrEnclosure[1]
                if content.substitutes_note and substitute.note is not None: result.label += fmt.substNoteEnclosure[0] + substitute.note + fmt.substNoteEnclosure[1]
                result.label += fmt.substEntryEnclosure[1]
                result.label += fmt.substSectionEnclosure[1]

    return result


#сборка параметра: допуск
def _assemble_param_tolerance(param, unit = None, decimalPoint = '.', valueToUnitDelimiter = '', signToToleranceDelimiter = '', rangeSymbol = '\u2026', locale_index = 0):
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
        return "±" + signToToleranceDelimiter + _floatToString(param[1] * multiplier, decimalPoint) + valueToUnitDelimiter + unit
    else:
        return "+" + signToToleranceDelimiter + _floatToString(param[1] * multiplier, decimalPoint) + rangeSymbol + "-" + signToToleranceDelimiter + _floatToString(-param[0] * multiplier, decimalPoint) + valueToUnitDelimiter + unit

#сборка параметра: диапазон рабочих температур
def _assemble_param_temperature_range(param, unit = 'K', decimalPoint = '.', valueToUnitDelimiter = '', signToToleranceDelimiter = '', rangeSymbol = '\u2026'):
    lower_sign = ''
    upper_sign = ''
    lower_value = param[0]
    upper_value = param[1]
    
    if unit is None:
        unit = ''
        valueToUnitDelimiter = ''
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

    return lower_sign + signToToleranceDelimiter + _floatToString(lower_value, decimalPoint) + rangeSymbol + upper_sign + signToToleranceDelimiter + _floatToString(upper_value, decimalPoint) + valueToUnitDelimiter + unit
