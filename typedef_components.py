import datetime
from enum import IntEnum
import re

#База данных с компонентами
class Components_typeDef():
    class ComponentTypes():
        #Общий класс компонента (с базовыми полями для всех классов)
        class Generic():
            def __init__(self):
                self.GENERIC_designator         = None          #десигнатор (полный)
                self.GENERIC_designator_channel = None          #десигнатор - канал
                self.GENERIC_designator_prefix  = None          #десигнатор - префикс
                self.GENERIC_designator_index   = None          #десигнатор - индекс
                self.GENERIC_kind               = None          #тип элемента
                self.GENERIC_value              = None          #номинал
                self.GENERIC_description        = None          #описание
                self.GENERIC_manufacturer       = None          #производитель
                self.GENERIC_quantity           = 0             #количество
                self.GENERIC_fitted             = True          #установка в изделие (да/нет)
                self.GENERIC_package            = None          #корпус
                self.GENERIC_explicit           = True          #явно заданный номинал (да/нет)
                self.GENERIC_mount              = None          #тип монтажа
                self.GENERIC_THtype             = None          #тип монтажа в отверстия
                self.GENERIC_size               = None          #типоразмер
                self.GENERIC_temperature_range  = None          #диапазон рабочих температур [<->, <+>], K
                self.GENERIC_assembly           = None          #сборка [<кол-во_блоков>, <кол-во_элем_в_блоке>, <AssemblyType>] (например [3, 2, SERIES] - 3 пары с последовательным включением)
                self.GENERIC_substitute         = None          #допустимая замена
                self.GENERIC_misc               = []            #оставшиеся нераспознанные параметры

                self.flag = self.__class__.FlagType.NONE        #флаг (ошибки, предупреждения и т.п.)
                self.types = Components_typeDef.ComponentTypes  #ссылка на класс с типами компонентов

            class AssemblyType(IntEnum):
                UNKNOWN         = 0     #неизвестный
                INDEPENDENT     = 1     #независимо
                COMMON_ANODE    = 2     #общий анод
                COMMON_CATHODE  = 3     #общий катод
                SERIES          = 4     #последовательно

            class FlagType(IntEnum):
                NONE    = 0     #не задан
                OK      = 1     #всё в порядке
                WARNING = 2     #предупреждение
                ERROR   = 3     #ошибка

            def __lt__(self, other):
                if self.GENERIC_designator_prefix < other.GENERIC_designator_prefix:
                    return True
                elif self.GENERIC_designator_prefix == other.GENERIC_designator_prefix:
                    return self.GENERIC_designator_index < other.GENERIC_designator_index
                else:
                    return False

            def __eq__(self, other):
                return self.GENERIC_value == other.GENERIC_value

            class Mounting():
                class Type(IntEnum):
                    UNKNOWN     = 0     #неизвестно
                    SURFACE     = 1     #поверхностный
                    THROUGHHOLE = 2     #выводной
                    CHASSIS     = 3     #на корпус
                    HOLDER      = 4     #в держатель

                class ThroughHole(IntEnum):
                    UNKNOWN     = 0
                    AXIAL       = 1
                    RADIAL      = 2

            class Substitute():
                def __init__(self, value = None, manufacturer = None, note = None):
                    self.value        = value           #номинал
                    self.manufacturer = manufacturer    #производитель
                    self.note         = note            #примечание

        #todo:
        #   добавить типы:
        #       TVS - сборка частично
        #       CircuitBreaker - парсинг частично сделан
        #       EMIFilter - парсинг частично сделан
        #       IC - всё
        #       Transistor - всё
        #   подумать над GENERIC флагом отображения описания задающимся в парсинге

        #Резистор
        class Resistor(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.RES_type        = None     #тип
                self.RES_resistance  = None     #сопротивление, Ом
                self.RES_tolerance   = None     #допуск сопротивления [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.RES_tempCoeff   = None     #ТКС [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.RES_power       = None     #максимальная мощность, Вт
                self.RES_voltage     = None     #максимальное напряжение, В
                #TKE

            class Type(IntEnum):
                UNKNOWN       = 0   #неизвестный
                THIN_FILM     = 1   #тонкоплёночный   
                THICK_FILM    = 2   #толстоплёночный
                METAL_FILM    = 3   #металлоплёночный
                CARBON_FILM   = 4   #углеродоплёночный
                WIREWOUND     = 5   #проволочный
                CERAMIC       = 6   #керамический

        #Перемычка
        class Jumper(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)

        #Конденсатор
        class Capacitor(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.CAP_type         = None    #тип
                self.CAP_capacitance  = None    #ёмкость, Ф
                self.CAP_tolerance    = None    #допуск ёмкости [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.CAP_voltage      = None    #максимальное напряжение, В
                self.CAP_dielectric   = None    #диэлектрик
                self.CAP_lowImpedance = False   #низкий импеданс (да/нет)

            class Type(IntEnum):
                UNKNOWN           = 0   #неизвестный
                CERAMIC           = 1   #керамический
                TANTALUM          = 2   #танталовый
                FILM              = 3   #плёночный
                ALUM_ELECTROLYTIC = 4   #алюминиевый электролитический
                ALUM_POLYMER      = 5   #алюминиевый полимерный
                SUPERCAPACITOR    = 6   #ионистор

        #Индуктивность
        class Inductor(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.IND_type        = None     #тип
                self.IND_inductance  = None     #индуктивность, Гн
                self.IND_tolerance   = None     #допуск индуктивности [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.IND_current     = None     #максимальный ток, А
                self.IND_lowCapacitance = False #низкая ёмкость (да/нет)

            class Type(IntEnum):
                UNKNOWN           = 0   #неизвестный
                INDUCTOR          = 1   #индуктивность
                CHOKE             = 2   #дроссель

        #Диод
        class Diode(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.DIODE_type                      = None   #тип
                self.DIODE_reverseVoltage            = None   #максимальное обратное напряжение, В
                self.DIODE_reverseVoltage_tolerance  = None   #допуск обратного напряжения [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.DIODE_forwardCurrent            = None   #максимальный прямой ток, А
                self.DIODE_power                     = None   #максимальная мощность, Вт
                self.DIODE_capacitance               = None   #ёмкость перехода, Ф
                self.DIODE_capacitance_tolerance     = None   #допуск ёмкости перехода [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.DIODE_capacitance_voltage       = None   #напряжение измерения ёмкости перехода, В
                self.DIODE_capacitance_frequency     = None   #частота измерения ёмкости перехода, В

            class Type(IntEnum):
                UNKNOWN         = 0     #неизвестный
                GENERAL_PURPOSE = 1     #общего применения
                SCHOTTKY        = 2     #Шоттки
                ZENER           = 3     #стабилитрон
                TUNNEL          = 4     #тунельный
                VARICAP         = 5     #варикап

        #Транзистор
        class Transistor(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.TRSTR_type         = None   #тип
                self.TRSTR_assembly     = False  #сборка (да/нет)
                self.TRSTR_CD_voltage   = None   #максимальное напряжение коллектор-эмиттер/сток-исток, В
                self.TRSTR_CD_current   = None   #максимальный ток коллектора/стока, А
                self.TRSTR_BG_voltage   = None   #максимальное напряжение база-эмиттер/затвор-исток, В

            class Type(IntEnum):
                UNKNOWN = 0     #неизвестный
                BJT     = 1     #биполярный
                JFET    = 2     #полевой с p-n переходом
                MOSFET  = 3     #полевой транзистор с МОП-структурой
                IGBT    = 4     #биполярный транзистор с изолированным затвором

        #Микросхема
        class IntegratedCircuit(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)

        #TVS
        class TVS(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.TVS_type                        = None   #тип
                self.TVS_standoff_voltage            = None   #максимальное рабочее напряжение, В
                self.TVS_breakdown_voltage           = None   #напряжение пробоя, В
                self.TVS_clamping_voltage            = None   #напряжение гашения выброса, В
                self.TVS_clamping_current            = None   #ток гашения выброса, А
                self.TVS_sparkover_voltage_dc        = None   #напряжение образования искры (постоянное), В
                self.TVS_sparkover_voltage_tolerance = None   #допуск напряжения образования искры [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.TVS_capacitance                 = None   #ёмкость, Ф
                self.TVS_bidirectional               = None   #двунаправленный тип (да/нет) - для диодов
                self.TVS_energy                      = None   #энергия, Дж
                self.TVS_power                       = None   #мощность, Вт
                self.TVS_testPulse                   = None   #тип тестового импульса

            class Type(IntEnum):
                UNKNOWN             = 0     #неизвестный
                DIODE               = 1     #диод
                THYRISTOR           = 2     #тиристор
                VARISTOR            = 3     #варистор
                GAS_DISCHARGE_TUBE  = 4     #газоразрядник
                IC                  = 5     #микросхема

            class TestPulse(IntEnum):
                UNKNOWN    = 0     #неизвестный
                US_8_20    = 1     #8/20мкс
                US_10_1000 = 2     #10/1000мкс

        #Предохранитель
        class CircuitBreaker(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.CBRK_type                  = None   #тип
                self.CBRK_speed_grade           = None   #классификация скорости срабатывания
                self.CBRK_speed                 = None   #значение скорости срабатывания
                self.CBRK_voltage               = None   #максимальное напряжение, В
                self.CBRK_voltage_ac            = None   #флаг переменного напряжения (да/нет)
                self.CBRK_current_rating        = None   #номинальный ток, А
                self.CBRK_current_maximum       = None   #максимальный допустимый ток, А (для самовосстанавливающихся)
                self.CBRK_current_interrupting  = None   #максимальный прерываемый ток, А
                self.CBRK_resistance            = None   #сопротивление, Ом
                self.CBRK_power                 = None   #максимальная мощность, Вт
                self.CBRK_meltingPoint          = None   #точка плавления, А²с (для плавких)

            class Type(IntEnum):
                UNKNOWN         = 0     #неизвестный
                FUSE            = 1     #плавкий
                PTC_RESETTABLE  = 2     #самовосстанавливающийся с положительным температурным коэффициентом
                THERMAL         = 3     #термо

            class SpeedGrade(IntEnum):
                UNKNOWN         = 0     #неизвестный
                FAST            = 1     #быстрый
                MEDIUM          = 2     #средний
                SLOW            = 3     #медленный

        #Фильтр ЭМП
        class EMIFilter(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.EMIF_type                  = None    #тип
                self.EMIF_impedance             = None    #импеданс, Ом
                self.EMIF_impedance_tolerance   = None    #допуск импеданса [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.EMIF_impedance_frequency   = None    #частота измерения значения импеданса, Гц
                self.EMIF_inductance            = None    #индуктивность, Ом
                self.EMIF_inductance_tolerance  = None    #допуск индуктивности [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.EMIF_capacitance           = None    #ёмкость, Ф
                self.EMIF_capacitance_tolerance = None    #допуск ёмкости [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.EMIF_resistance            = None    #активное сопротивление, Ом
                self.EMIF_resistance_tolerance  = None    #допуск активного сопротивления [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.EMIF_current               = None    #максимальный ток, А
                self.EMIF_voltage               = None    #максимальное напряжение, В

            class Type(IntEnum):
                UNKNOWN             = 0     #неизвестный
                FERRITE_BEAD        = 1     #ферритовая бусина
                COMMON_MODE_CHOKE   = 2     #синфазная катушка индуктивности
                ASSEMBLY            = 3     #готовое устройство

        #Резонатор
        class Oscillator(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.OSC_type               = None    #тип
                self.OSC_frequency          = None    #частота, Гц
                self.OSC_tolerance          = None    #допуск частоты [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.OSC_stability          = None    #стабильность частоты [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.OSC_loadCapacitance    = None    #ёмкость нагрузки, Ф
                self.OSC_ESR                = None    #эквивалентное последовательное сопротивление, Ом
                self.OSC_driveLevel         = None    #уровень возбуждения, Вт
                self.OSC_overtone           = None    #гармоника (=1 если фундаментальная)

            class Type(IntEnum):
                UNKNOWN  = 0     #неизвестный
                CRYSTAL  = 1     #кристалл
                CERAMIC  = 2     #кармический
                MEMS     = 3     #микроэлектромеханическая система

        #Светодиод
        class LED(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.LED_type                       = None    #тип
                self.LED_color                      = None    #цвет
                self.LED_color_temperature          = None    #цветовая температура, К
                self.LED_color_renderingIndex       = None    #индекс цветопередачи
                self.LED_wavelength_peak            = None    #пиковая длина волны, м
                self.LED_wavelength_dominant        = None    #основная длина волны, м
                self.LED_viewingAngle               = None    #угол обзора, град.
                self.LED_current_nominal            = None    #номинальный прямой ток, А
                self.LED_current_maximum            = None    #максимальный прямой ток, А
                self.LED_voltage_forward            = None    #прямое падение напряжения, В
                self.LED_luminous_flux              = None    #световой поток, лм
                self.LED_luminous_flux_current      = None    #ток измерения световго потока, А
                self.LED_luminous_intensity         = None    #сила света, кд
                self.LED_luminous_intensity_current = None    #ток измерения силы света, А

            class Type(IntEnum):
                UNKNOWN     = 0     #неизвестный
                INDICATION  = 1     #индикационный
                LIGHTING    = 2     #осветительный

            class Color(IntEnum):
                UNKNOWN     = 0     #неизвестный
                INFRARED    = 1     #инфракрасный
                ULTRAVIOLET = 2     #ультрафиолетовый
                RED         = 3     #красный
                ORANGE      = 4     #оранжевый
                AMBER       = 5     #янтарный
                YELLOW      = 6     #жёлтый
                LIME        = 7     #салатовый
                GREEN       = 8     #зелёный
                TURQUOISE   = 9     #бирюзовый
                CYAN        = 10    #голубой
                BLUE        = 11    #синий
                VIOLET      = 12    #фиолетовый
                PURPLE      = 13    #пурпурный
                PINK        = 14    #розовый
                WHITE       = 15    #белый
                MULTI       = 16    #многоцветный

    def __init__(self):
        self.entries = []

    def sort(self):
        self.entries = sorted(self.entries)