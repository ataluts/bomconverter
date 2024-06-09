from enum import Enum, IntEnum

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
                self.GENERIC_accessory_child    = None          #ссылка/ссылки на дочерние компоненты (список)
                self.GENERIC_accessory_parent   = None          #ссылка на родительский компонент
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
                self.GENERIC_array              = None          #сборка [<кол-во_блоков>, <кол-во_элем_в_блоке>, <ArrayType>] (например [3, 2, SERIES] - 3 пары с последовательным включением)
                self.GENERIC_substitute         = None          #допустимые замены (список)
                self.GENERIC_misc               = []            #оставшиеся нераспознанные параметры
                self.GENERIC_note               = None          #примечание

                self.flag = self.__class__.FlagType.NONE        #флаг (ошибки, предупреждения и т.п.)
                self.types = Components_typeDef.ComponentTypes  #ссылка на класс с типами компонентов

            class ArrayType(IntEnum):
                UNKNOWN         = 0     #неизвестный
                INDEPENDENT     = 1     #независимо
                COMMON_ANODE    = 2     #общий анод
                COMMON_CATHODE  = 3     #общий катод
                SERIES          = 4     #последовательно
                PARALLEL        = 5     #параллельно
                MATRIX          = 6     #матрица

            class FlagType(IntEnum):
                NONE    = 0     #не задан
                OK      = 1     #всё в порядке
                WARNING = 2     #предупреждение
                ERROR   = 3     #ошибка

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

            class Substitute():
                def __init__(self, value = None, manufacturer = None, note = None):
                    self.value        = value           #номинал
                    self.manufacturer = manufacturer    #производитель
                    self.note         = note            #примечание

            #ключ сортировки по десигнатору
            def _cmpkey_designator(self):
                key_desPrefix = self.GENERIC_designator_prefix if self.GENERIC_designator_prefix is not None else '\ufffd' #'' или '\ufffd' для сортировки в начало/конец если не указан
                key_desIndex = self.GENERIC_designator_index if self.GENERIC_designator_index is not None else 0
                key_desChannel = str(self.GENERIC_designator_index).upper() if self.GENERIC_designator_index is not None else  '' #'' или '\ufffd' для сортировки в начало/конец если не указан
                return (key_desPrefix, key_desIndex, key_desChannel)

            #ключ сортировки по номиналу
            def _cmpkey_value(self):
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return key_value

            #ключ сортировки по типу элемента (из парсера)
            def _cmpkey_kind(self):
                key_kind = str(self.GENERIC_kind).upper() if self.GENERIC_kind is not None else ''
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_value)

            #ключ сортировки по параметрам (заглушка для базового класса)
            def _cmpkey_params(self):
                key_kind = str(self.GENERIC_designator_prefix).upper() if self.GENERIC_designator_prefix is not None else '\ufffd' #'' или '\ufffd' для сортировки в начало/конец если не указан
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_value) #потенциально опасно так как есть вероятность сравнения второго ключа с несовместимым типом (из-за определения первого ключа по desPrefix, а типа компонента в парсере по kind)

        #Сборка (Устройство)
        class Assembly(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)

            def _cmpkey_params(self):
                key_kind = 'A'
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_value)

        #Фотоэлемент
        class Photocell(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.PHOTO_type = None     #тип

            class Type(IntEnum):
                UNKNOWN    = 0   #неизвестный
                DIODE      = 1   #диод   
                TRANSISTOR = 2   #транзистор
                RESISTOR   = 3   #резистор

            def _cmpkey_params(self):
                key_kind = 'BL'
                key_type = self.PHOTO_type if self.PHOTO_type is not None else 0
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_value)

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

            def _cmpkey_params(self):
                key_kind = 'C'
                key_capacitance = self.CAP_capacitance if self.CAP_capacitance is not None else 0
                key_voltage = self.CAP_voltage if self.CAP_voltage is not None else 0
                key_tolerance = (0, 0)
                if self.CAP_tolerance is not None:
                    if self.CAP_tolerance[2] is None: key_tolerance = (0, self.CAP_tolerance[1] - self.CAP_tolerance[0])    #в начале процентные
                    else: key_tolerance = (1, self.CAP_tolerance[1] - self.CAP_tolerance[0])                                #в конце абсолютные
                key_type = self.CAP_type if self.CAP_type is not None else 0
                key_dielectric = self.CAP_dielectric if self.CAP_dielectric is not None else '\ufffd'                       #'' или '\ufffd' для сортировки в начало/конец если не указан
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_capacitance, key_voltage, key_tolerance, key_dielectric, key_value)

        #Микросхема
        class IntegratedCircuit(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)

            def _cmpkey_params(self):
                key_kind = 'D'
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_value)

        #Крепёж
        class Fastener(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)

            def _cmpkey_params(self):
                key_kind = 'EF'
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_value)

        #Радиатор
        class Heatsink(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)

            def _cmpkey_params(self):
                key_kind = 'ER'
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_value)

        #Автоматический выключатель (Предохранитель)
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
                UNKNOWN             = 0     #неизвестный
                FUSE                = 1     #плавкий
                FUSE_PTC_RESETTABLE = 2     #самовосстанавливающийся с положительным температурным коэффициентом
                FUSE_THERMAL        = 3     #термо
                BREAKER             = 4     #расцепитель (автоматический выключатель)
                HOLDER              = 5     #держатель

            class SpeedGrade(IntEnum):
                UNKNOWN         = 0     #неизвестный
                FAST            = 1     #быстрый
                MEDIUM          = 2     #средний
                SLOW            = 3     #медленный

            def _cmpkey_params(self):
                key_kind = 'FP'
                key_type = self.CBRK_type if self.CBRK_type is not None else 0
                key_currentRating = self.CBRK_current_rating if self.CBRK_current_rating is not None else 0
                key_currentMaximum = self.CBRK_current_maximum if self.CBRK_current_maximum is not None else 0
                key_currentInterrupting = self.CBRK_current_interrupting if self.CBRK_current_interrupting is not None else 0
                key_voltage = self.CBRK_voltage if self.CBRK_voltage is not None else 0
                key_power = self.CBRK_power if self.CBRK_power is not None else 0
                key_meltingPoint = self.CBRK_meltingPoint if self.CBRK_meltingPoint is not None else 0
                key_resistance = self.CBRK_resistance if self.CBRK_resistance is not None else 0
                key_speedGrade = self.CBRK_speed_grade if self.CBRK_speed_grade is not None else 0
                key_speed = self.CBRK_speed if self.CBRK_speed is not None else 0
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_currentRating, key_currentMaximum, key_currentInterrupting, key_voltage, key_power, key_meltingPoint, key_resistance, key_speedGrade, key_speed, key_value)
  
        #Ограничитель перенапряжения
        class SurgeProtector(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.SPD_type                        = None   #тип
                self.SPD_standoff_voltage            = None   #максимальное рабочее напряжение, В
                self.SPD_breakdown_voltage           = None   #напряжение пробоя, В
                self.SPD_clamping_voltage            = None   #напряжение гашения выброса, В
                self.SPD_clamping_current            = None   #ток гашения выброса, А
                self.SPD_sparkover_voltage_dc        = None   #напряжение образования искры (постоянное), В
                self.SPD_sparkover_voltage_tolerance = None   #допуск напряжения образования искры [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.SPD_capacitance                 = None   #ёмкость, Ф
                self.SPD_bidirectional               = None   #двунаправленный тип (да/нет) - для диодов
                self.SPD_energy                      = None   #энергия, Дж
                self.SPD_power                       = None   #мощность, Вт
                self.SPD_testPulse                   = None   #тип тестового импульса

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

            def _cmpkey_params(self):
                key_kind = 'FV'
                key_type = self.SPD_type if self.SPD_type is not None else 0
                key_standoffVoltage = self.SPD_standoff_voltage if self.SPD_standoff_voltage is not None else 0
                key_breakdownVoltage = self.SPD_breakdown_voltage if self.SPD_breakdown_voltage is not None else 0
                key_sparkoverVoltageDC = self.SPD_sparkover_voltage_dc if self.SPD_sparkover_voltage_dc is not None else 0
                key_power = self.SPD_power if self.SPD_power is not None else 0
                key_energy = self.SPD_energy if self.SPD_energy is not None else 0
                key_capacitance = self.SPD_capacitance if self.SPD_capacitance is not None else 0
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_standoffVoltage, key_breakdownVoltage, key_sparkoverVoltageDC, key_capacitance, key_power, key_energy, key_capacitance, key_value)
         
        #Батарея
        class Battery(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.BAT_type                       = None   #тип
                self.BAT_rechargable                = None   #возможность заряда <True/False>
                self.BAT_capacity                   = None   #ёмкость, Ач
                self.BAT_capacity_load_current      = None   #ток нагрузки при измерении ёмкости, А
                self.BAT_capacity_load_resistance   = None   #сопротивление нагрузки при измерении ёмкости, Ом
                self.BAT_capacity_voltage           = None   #напряжение отсечки при измерении ёмкости, В
                self.BAT_capacity_temperature       = None   #температура при измерении ёмкости, К
                self.BAT_voltage_rated              = None   #номинальное напряжение, В
                self.BAT_chemistry                  = None   #химический тип

            class Type(IntEnum):
                UNKNOWN = 0     #неизвестный
                CELL    = 1     #ячейка (элемент гальванический)
                BATTERY = 2     #батарея (несколько ячеек)
                HOLDER  = 5     #держатель

            class Chemistry(Enum): #надо дополнять
                ZINC_MANGANESE_DIOXIDE = 'Zn-MnO2'
                LITHIUM_MANGANESE_DIOXIDE = 'Li-MnO2'
                LITHIUM_THIONYL_CHLORIDE = 'Li-SOCl2'
                NICKEL_CADMIUM = 'Ni-Cd'
                NICKEL_METAL_HYDRIDE = 'Ni-MH'

            def _cmpkey_params(self):
                key_kind = 'GB'
                key_type = self.BAT_type if self.BAT_type is not None else 0
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_value)

        #Дисплей
        class Display(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.DISP_type                      = None    #тип
                self.DISP_structure                 = None    #структура (конструктивные особенности)
                self.DISP_color                     = None    #цвет
                self.DISP_viewingAngle              = None    #угол обзора, град.

            class Type(IntEnum):
                UNKNOWN             = 0     #неизвестный
                NUMERIC_7SEG        = 1     #числовой 7-сегментный
                ALPHANUMERIC_14SEG  = 2     #буквенно-цифровой 14-сегментный
                ALPHANUMERIC_16SEG  = 3     #буквенно-цифровой 16-сегментный
                BARGRAPH            = 4     #шкальный
                DOTMATRIX           = 5     #точечная матрица
                GRAPHIC             = 6     #графический

            class Structure(IntEnum):
                UNKNOWN = 0   #неизвестный
                LED     = 1   #светодиодный
                OLED    = 2   #органически-светодиодный
                LCD     = 3   #жидкокристаллический
                VFD     = 4   #вакуумно-люминесцентный

            def _cmpkey_params(self):
                key_kind = 'HG'
                key_type = self.DISP_type if self.DISP_type is not None else 0
                key_structure = self.DISP_structure if self.DISP_structure is not None else 0
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_structure, key_value)

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
 
            def _cmpkey_params(self):
                key_kind = 'HL'
                key_type = self.LED_type if self.LED_type is not None else 0
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_value)

        #Перемычка
        class Jumper(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.JMP_type = None   #тип

            class Type(IntEnum):
                UNKNOWN    = 0     #неизвестный
                ELECTRICAL = 1     #электрический
                THERMAL    = 2     #термический

            def _cmpkey_params(self):
                key_kind = 'J'
                key_type = self.JMP_type if self.JMP_type is not None else 0
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_value)

        #Реле
        class Relay(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)

            def _cmpkey_params(self):
                key_kind = 'K'
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_value)

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

            def _cmpkey_params(self):
                key_kind = 'L'
                key_type = self.IND_type if self.IND_type is not None else 0
                key_inductance = self.IND_inductance if self.IND_inductance is not None else 0
                key_current = self.IND_current if self.IND_current is not None else 0
                key_tolerance = (0, 0)
                if self.IND_tolerance is not None:
                    if self.IND_tolerance[2] is None: key_tolerance = (0, self.IND_tolerance[1] - self.IND_tolerance[0])    #в начале процентные
                    else: key_tolerance = (1, self.IND_tolerance[1] - self.IND_tolerance[0])                                #в конце абсолютные
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_inductance, key_current, key_tolerance, key_value)

        #Резистор
        class Resistor(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.RES_type        = None     #тип
                self.RES_structure   = None     #структура (конструктивные особенности)
                self.RES_resistance  = None     #сопротивление, Ом
                self.RES_tolerance   = None     #допуск сопротивления [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.RES_power       = None     #максимальная мощность, Вт
                self.RES_voltage     = None     #максимальное напряжение, В
                self.RES_turns       = None     #количество оборотов (для переменных)
                self.RES_temperature_coefficient    = None #ТКС [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.RES_temperature_characteristic = None #температурная характеристика (для терморезисторов) [<t0, K>, <t1, K>, <B>]

            class Type(IntEnum):
                UNKNOWN       = 0   #неизвестный
                FIXED         = 1   #постоянный
                VARIABLE      = 2   #переменный
                THERMAL       = 3   #термо

            class Structure(IntEnum):
                UNKNOWN       = 0   #неизвестный
                THIN_FILM     = 1   #тонкоплёночный
                THICK_FILM    = 2   #толстоплёночный
                METAL_FILM    = 3   #металлоплёночный
                CARBON_FILM   = 4   #углеродоплёночный
                WIREWOUND     = 5   #проволочный
                CERAMIC       = 6   #керамический

            def _cmpkey_params(self):
                key_kind = 'R'
                key_resistance = self.RES_resistance if self.RES_resistance is not None else 0
                key_power = self.RES_power if self.RES_power is not None else 0
                key_voltage = self.RES_voltage if self.RES_voltage is not None else 0
                key_tolerance = (0, 0)
                if self.RES_tolerance is not None:
                    if self.RES_tolerance[2] is None: key_tolerance = (0, self.RES_tolerance[1] - self.RES_tolerance[0])    #в начале процентные
                    else: key_tolerance = (1, self.RES_tolerance[1] - self.RES_tolerance[0])                                #в конце абсолютные
                key_temperatureCoefficient = (0, 0)
                if self.RES_temperature_coefficient is not None:
                    if self.RES_temperature_coefficient[2] is None: key_temperatureCoefficient = (0, self.RES_temperature_coefficient[1] - self.RES_temperature_coefficient[0])  #в начале процентные
                    else: key_temperatureCoefficient = (1, self.RES_temperature_coefficient[1] - self.RES_temperature_coefficient[0])                                            #в конце абсолютные
                key_type = self.RES_type if self.RES_type is not None else 0
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_resistance, key_power, key_voltage, key_tolerance, key_temperatureCoefficient, key_value)

        #Переключатель
        class Switch(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.SW_type = None   #тип

            class Type(IntEnum):
                UNKNOWN     = 0     #неизвестно
                TOGGLE      = 1     #тумблер
                SLIDE       = 2     #движковый
                PUSHBUTTON  = 3     #кнопочный
                LIMIT       = 4     #концевой ('микрик')
                ROTARY      = 5     #галетный
                REED        = 6     #геркон
                ROCKER      = 7     #клавишный
                THUMBWHEEL  = 8     #барабанный
                JOYSTICK    = 9     #джойстик
                KEYLOCK     = 10    #переключающийся ключом

            def _cmpkey_params(self):
                key_kind = 'S'
                key_type = self.SW_type if self.SW_type is not None else 0
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_value)

        #Трансформатор
        class Transformer(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)

            def _cmpkey_params(self):
                key_kind = 'T'
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_value)

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

            def _cmpkey_params(self):
                key_kind = 'VD'
                key_type = self.DIODE_type if self.DIODE_type is not None else 0
                key_forwardCurrent = self.DIODE_forwardCurrent if self.DIODE_forwardCurrent is not None else 0
                key_reverseVoltage = self.DIODE_reverseVoltage if self.DIODE_reverseVoltage is not None else 0
                key_reverseVoltageTolerance = (0, 0)
                if self.DIODE_reverseVoltage_tolerance is not None:
                    if self.DIODE_reverseVoltage_tolerance[2] is None: key_reverseVoltageTolerance = (0, self.DIODE_reverseVoltage_tolerance[1] - self.DIODE_reverseVoltage_tolerance[0])   #в начале процентные
                    else: key_reverseVoltageTolerance = (1, self.DIODE_reverseVoltage_tolerance[1] - self.DIODE_reverseVoltage_tolerance[0])                                                #в конце абсолютные
                key_capacitance = self.DIODE_capacitance if self.DIODE_capacitance is not None else 0
                key_capacitanceTolerance = (0, 0)
                if self.DIODE_capacitance_tolerance is not None:
                    if self.DIODE_capacitance_tolerance[2] is None: key_capacitanceTolerance = (0, self.DIODE_capacitance_tolerance[1] - self.DIODE_capacitance_tolerance[0])   #в начале процентные
                    else: key_capacitanceTolerance = (1, self.DIODE_capacitance_tolerance[1] - self.DIODE_capacitance_tolerance[0])                                             #в конце абсолютные
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_forwardCurrent, key_reverseVoltage, key_reverseVoltageTolerance, key_capacitance, key_capacitanceTolerance, key_value)

        #Тиристор
        class Thyristor(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.THYR_type = None   #тип

            class Type(IntEnum):
                UNKNOWN   = 0   #неизвестный
                THYRISTOR = 1   #тиристор   
                TRIAC     = 2   #симистор
                DYNISTOR  = 3   #динистор

            def _cmpkey_params(self):
                key_kind = 'VS'
                key_type = self.THYR_type if self.THYR_type is not None else 0
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_value)

        #Транзистор
        class Transistor(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.TRSTR_type         = None   #тип
                self.TRSTR_CD_voltage   = None   #максимальное напряжение коллектор-эмиттер/сток-исток, В
                self.TRSTR_CD_current   = None   #максимальный ток коллектора/стока, А
                self.TRSTR_BG_voltage   = None   #максимальное напряжение база-эмиттер/затвор-исток, В

            class Type(IntEnum):
                UNKNOWN = 0     #неизвестный
                BJT     = 1     #биполярный
                JFET    = 2     #полевой с p-n переходом
                MOSFET  = 3     #полевой транзистор с МОП-структурой
                IGBT    = 4     #биполярный транзистор с изолированным затвором

            def _cmpkey_params(self):
                key_kind = 'VT'
                key_type = self.TRSTR_type if self.TRSTR_type is not None else 0
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_value)

        #Оптоизолятор
        class Optoisolator(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.OPTOISO_outputType             = None   #тип выхода
                self.OPTOISO_channels               = None   #количество каналов
                self.OPTOISO_isolation_voltage      = None   #напряжение изоляции
                self.OPTOISO_acinput                = None   #двуполярный вход <True/False>
                self.OPTOISO_zeroCrossDetection     = None   #детектор перехода через ноль <True/False>
                self.OPTOISO_CTR                    = None   #коэффициент передачи по току [<min>, <max>, <typ>]

            class OutputType(IntEnum):
                UNKNOWN    = 0     #неизвестный
                TRANSISTOR = 1     #транзистор
                DARLINGTON = 2     #составной транзистор
                DIODE      = 3     #диод
                THYRISTOR  = 4     #тиристор
                TRIAC      = 5     #симистор
                LOGIC      = 6     #логический
                LINEAR     = 7     #линейный

            def _cmpkey_params(self):
                key_kind = 'VU'
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_value)

        #Соединитель
        class Connector(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.CON_type   = None    #тип
                self.CON_gender = None    #пол (папа/мама)

            class Type(IntEnum):
                UNKNOWN     = 0     #неизвестный

            class Gender(IntEnum):
                UNKNOWN    = 0     #неизвестный
                PLUG       = 1     #вилка
                RECEPTACLE = 2     #розетка

            def _cmpkey_params(self):
                key_kind = 'X'
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_value)

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

            def _cmpkey_params(self):
                key_kind = 'ZF'
                key_type = self.EMIF_type if self.EMIF_type is not None else 0
                key_impedance = self.EMIF_impedance if self.EMIF_impedance is not None else 0
                key_inductance = self.EMIF_inductance if self.EMIF_inductance is not None else 0
                key_resistance = self.EMIF_resistance if self.EMIF_resistance is not None else 0
                key_capacitance = self.EMIF_capacitance if self.EMIF_capacitance is not None else 0
                key_current = self.EMIF_current if self.EMIF_current is not None else 0
                key_voltage = self.EMIF_voltage if self.EMIF_voltage is not None else 0
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_impedance, key_inductance, key_resistance, key_capacitance, key_current, key_voltage, key_value)

        #Осциллятор (Резонатор)
        class Oscillator(Generic):
            def __init__(self):
                self.__class__.__base__.__init__(self)
                self.OSC_type               = None    #тип
                self.OSC_structure          = None    #структура (конструктивные особенности)
                self.OSC_frequency          = None    #частота, Гц
                self.OSC_tolerance          = None    #допуск частоты [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.OSC_stability          = None    #стабильность частоты [<->, <+>, <unit>] (если unit==None то доли от значения)
                self.OSC_loadCapacitance    = None    #ёмкость нагрузки, Ф
                self.OSC_ESR                = None    #эквивалентное последовательное сопротивление, Ом
                self.OSC_driveLevel         = None    #уровень возбуждения, Вт
                self.OSC_overtone           = None    #гармоника (=1 если фундаментальная)

            class Type(IntEnum):
                UNKNOWN    = 0     #неизвестный
                OSCILLATOR = 1     #осциллятор (тактовый сигнал на выходе)
                RESONATOR  = 2     #резонатор (фильтр частоты)
            
            class Structure(IntEnum):
                UNKNOWN  = 0     #неизвестный
                QUARTZ   = 1     #кварцевый
                CERAMIC  = 2     #керамический

            def _cmpkey_params(self):
                key_kind = 'ZG'
                key_type = self.OSC_type if self.OSC_type is not None else 0
                key_structure = self.OSC_structure if self.OSC_structure is not None else 0
                key_frequency = self.OSC_frequency if self.OSC_frequency is not None else 0
                key_tolerance = (0, 0)
                if self.OSC_tolerance is not None:
                    if self.OSC_tolerance[2] is None: key_tolerance = (0, self.OSC_tolerance[1] - self.OSC_tolerance[0])    #в начале процентные
                    else: key_tolerance = (1, self.OSC_tolerance[1] - self.OSC_tolerance[0])                                #в конце абсолютные
                key_stability = (0, 0)
                if self.OSC_stability is not None:
                    if self.OSC_stability[2] is None: key_stability = (0, self.OSC_stability[1] - self.OSC_stability[0])    #в начале процентные
                    else: key_stability = (1, self.OSC_stability[1] - self.OSC_stability[0])                                #в конце абсолютные
                key_loadCapacitance = self.OSC_loadCapacitance if self.OSC_loadCapacitance is not None else 0
                key_ESR = self.OSC_ESR if self.OSC_ESR is not None else 0
                key_driveLevel = self.OSC_driveLevel if self.OSC_driveLevel is not None else 0
                key_value = str(self.GENERIC_value).upper() if self.GENERIC_value is not None else ''
                return (key_kind, key_type, key_structure, key_frequency, key_tolerance, key_stability, key_loadCapacitance, key_ESR, key_driveLevel, key_value)

    def __init__(self):
        self.entries = []

    #сортировка базы данных
    def sort(self, method = 'designator', reverse = False):
        if method == 'designator':
            self.entries.sort(key = lambda entry: entry._cmpkey_designator(), reverse = reverse)
        elif method == 'value':
            self.entries.sort(key = lambda entry: entry._cmpkey_value(), reverse = reverse)
        elif method == 'kind':
            self.entries.sort(key = lambda entry: entry._cmpkey_kind(), reverse = reverse)
        elif method == 'params':
            self.entries.sort(key = lambda entry: entry._cmpkey_params(), reverse = reverse)
        else:
            raise NotImplementedError