from dataclasses import dataclass, field
from copy import deepcopy
from enum import Enum, IntEnum, auto
import dict_locale as lcl
from typedef_designator import Designator

#Физическая величина
@dataclass
class Quantity():
    _magnitude  : list[float|int]                           #численное значение
    unit        : lcl.Unit.Name                             #единица змерения
    prefix      : lcl.Unit.Prefix   = lcl.Unit.Prefix.NONE  #приставка единицы измерения

    def __post_init__(self):
        self._shape_magnitude()

    #числовое значение
    @property
    def magnitude(self) -> float|int|list[float|int]:
        if self.ismulti():
            return self._magnitude
        else:
            return self._magnitude[0]

    @magnitude.setter
    def magnitude(self, new:list[float|int]):
        self._magnitude = new
        self._shape_magnitude()

    #нормализованное числовое значение
    @property
    def magnitude_norm(self):
        mult = self.prefix.multiplier
        if self.ismulti():
            return [v * mult for v in self._magnitude] 
        else:
            return self._magnitude[0] * mult

    def _shape_magnitude(self):
        if isinstance(self._magnitude, (list, tuple)):
            if all(isinstance(v, (int, float)) for v in self._magnitude):
                if isinstance(self._magnitude, tuple):
                    self._magnitude = list(self._magnitude)
            else:
                raise TypeError(f"magnitude have unsupported data type")
        elif isinstance(self._magnitude, (float, int)):
            self._magnitude = [self._magnitude]
        else:
            raise TypeError(f"magnitude have unsupported data type")

    def __eq__(self, other):
        return self.isequal(other, True)

    #сравнение объектов:
    #   strict=True  сравниваются значения атрибутов
    #   strict=False сравниваются абсолютные значения
    def isequal(self, other, strict:bool = False):
        if other is None: return False
        if not isinstance(other, type(self)): return NotImplemented
        if self.unit != other.unit: return False
        if len(self._magnitude) != len(other._magnitude): return False
        if strict:
            if self.prefix != other.prefix: return False
            for s, o in zip(self._magnitude, other._magnitude):
                if s != o: return False
        else:
            mult_s = self.prefix.multiplier
            mult_o = other.prefix.multiplier
            for s, o in zip(self._magnitude, other._magnitude):
                if s * mult_s != o * mult_o: return False
        return True
    
    #является ли значение множественным
    def ismulti(self):
        return len(self._magnitude) > 1

    #меняет префикс с пересчётом числовых значений
    def toprefix(self, prefix:lcl.Unit.Prefix, inplace:bool = False):
        mult_old = self.prefix.multiplier
        mult_new = prefix.multiplier
        if inplace: obj = self
        else:       obj = deepcopy(self)
        obj.prefix = prefix
        for i in range(len(obj._magnitude)):
            obj._magnitude[i] = obj._magnitude[i] * mult_old / mult_new
        return obj

    #нормализует значения (убирает префикс)
    def normilize(self, inplace:bool = False):
        return self.toprefix(lcl.Unit.Prefix.NONE, inplace)

#Диапазон значений величины
@dataclass
class QuantityRange(Quantity):
    def __post_init__(self):
        super().__post_init__()
        if len(self._magnitude) != 2:
            raise ValueError("Must contain exactly two magnitudes")

    @property
    def lower(self) -> float|int:
        return self._magnitude[0]

    @lower.setter
    def lower(self, new:float|int):
        self._magnitude[0] = new

    @property
    def lower_norm(self) -> float|int:
        return self.magnitude_norm[0]

    @property
    def upper(self) -> float|int:
        return self._magnitude[1]

    @upper.setter
    def upper(self, new:float|int):
        self._magnitude[1] = new

    @property
    def upper_norm(self) -> float|int:
        return self.magnitude_norm[1]

#Допуск величины
@dataclass
class Tolerance(QuantityRange):
    @property
    def lower_norm(self) -> float|int:
        mult = self.prefix.multiplier
        if self.isrelative():
            mult *= self.unit.multiplier
        return self._magnitude[0] * mult

    @property
    def upper_norm(self) -> float|int:
        mult = self.prefix.multiplier
        if self.isrelative():
            mult *= self.unit.multiplier
        return self._magnitude[1] * mult

    #допуск симметричный в обе стороны
    def issymmetric(self):
        return abs(self._magnitude[0]) == abs(self._magnitude[1])

    #относительный
    RELATIVE_UNITS = {lcl.Unit.Name.NONE, lcl.Unit.Name.PERCENT, lcl.Unit.Name.PERMILLE, lcl.Unit.Name.PPM, lcl.Unit.Name.PPB}
    def isrelative(self):
        return self.unit in Tolerance.RELATIVE_UNITS
    
    #абсолютный
    def isabsolute(self):
        return not self.isrelative()

    #нормализует значения (убирает префикс и парциальные единицы измерения)
    def normilize(self, inplace:bool = False):
        if inplace: obj = self
        else:       obj = deepcopy(self)
        obj.lower = obj.lower_norm
        obj.upper = obj.upper_norm
        obj.prefix = lcl.Unit.Prefix.NONE
        if self.isrelative():
            obj.unit = lcl.Unit.Name.NONE
        return obj

#Параметр компонента
@dataclass
class ParameterSpec():
    #типы условий
    class ConditionType(IntEnum):
        UNPARSED                    = -1
        VOLTAGE                     = auto()
        CURRENT                     = auto()
        RESISTANCE                  = auto()
        FREQUENCY                   = auto()
        TEMPERATURE                 = auto()
        TEMPERATURE_RISE            = auto()
        SURGE_WAVEFORM              = auto()
        SURGE_DURATION              = auto()
        PRIMARY_VALUE_DEVIATION     = auto()

    value       : Quantity                                      #номинальное значение
    tolerance   : Tolerance     = None                          #допуск
    conditions  : dict          = field(default_factory=dict)   #условия

    #сравнение объектов:
    #   strict=True  сравниваются значения атрибутов
    #   strict=False сравниваются абсолютные значения
    def isequal(self, other, strict:bool = False):
        if other is None: return False
        if not isinstance(other, type(self)): return NotImplemented
        
        if self.value is not None:
            if not self.value.isequal(other.value, strict): return False
        else:
            if other.value is not None: return False
        
        if self.tolerance is not None:
            if not self.tolerance.isequal(other.tolerance, strict): return False
        else:
            if other.tolerance is not None: return False

        if self.conditions is not None:
            if other.conditions is None: return False
            if isinstance(self.conditions, dict) and isinstance(other.conditions, dict):
                if len(self.conditions) != len(other.conditions): return False
                for k, v in self.conditions.items():
                    if k not in other.conditions: return False
                    if isinstance(v, Quantity):
                        if not v.isequal(other.conditions[k], strict): return False
                    else:
                        if v != other.conditions[k]: return False
            else:
                return self.conditions == other.conditions
        else:
            if other.conditions is not None: return False

        return True

    #нормализует значения (убирает префикс и парциальные единицы измерения)
    def normilize(self, inplace:bool = False):
        if inplace: obj = self
        else:       obj = deepcopy(self)
        obj.value.normilize(True)
        obj.tolerance.normilize(True)
        for v in self.conditions.values():
            if isinstance(v, Quantity):
                v.normilize(True)
        return obj

#Типы монтажа
class MountType(IntEnum):
    UNDEFINED    = -1       #не задан
    UNKNOWN      = 0        #неизвестно
    SURFACE      = auto()   #поверхностный
    SEMI_SURFACE = auto()   #поверхностный, но с выводами для механики
    THROUGHHOLE  = auto()   #выводной
    EDGE         = auto()   #в край (торец) платы
    CHASSIS      = auto()   #на корпус
    HOLDER       = auto()   #в держатель

#Варианты цвета
class ColorType(IntEnum):
    UNDEFINED   = -1        #не задан
    UNKNOWN     = 0         #неизвестный
    #длина волны применима
    INFRARED    = auto()    #инфракрасный
    ULTRAVIOLET = auto()    #ультрафиолетовый
    RED         = auto()    #красный
    ORANGE      = auto()    #оранжевый
    AMBER       = auto()    #янтарный
    YELLOW      = auto()    #жёлтый
    LIME        = auto()    #салатовый
    GREEN       = auto()    #зелёный
    TURQUOISE   = auto()    #бирюзовый
    CYAN        = auto()    #голубой
    BLUE        = auto()    #синий
    VIOLET      = auto()    #фиолетовый
    #длина волны не применима
    PURPLE      = auto()    #пурпурный
    PINK        = auto()    #розовый
    WHITE       = auto()    #белый
    MULTI       = auto()    #многоцветный

#Корпус
@dataclass
class Package():
    class Type():
        class Surface(IntEnum):         #тип корпуса поверхностного монтажа
            UNDEFINED   = -1                #не задан
            UNKNOWN     = 0                 #неизвестный
            NONSTANDARD = auto()            #нестандартный (дроссели, ...)
            CHIP        = auto()            #стандартный чип (0402, 0603, ...)
            MOLDED      = auto()            #формованный чип (A, B, C, ... у танталовых конденсаторов, SMA, SMB, SMC корпуса диодов и т.п.)
            VCHIP       = auto()            #цилиндрический чип (чип-электролитические конденсаторы)
            IC_LEAD     = auto()            #микросхема с выводами
            IC_NOLEAD   = auto()            #микросхема без выводов
            IC_BGA      = auto()            #микросхема с массивом шаров
            MODULE      = auto()            #модуль
            def __eq__(self, other):
                if type(self) is not type(other): return False
                return IntEnum.__eq__(self, other)
            __hash__ = IntEnum.__hash__   #restore hashing

        class ThroughHole(IntEnum):     #тип выводного корпуса
            UNDEFINED   = -1                #не задан
            UNKNOWN     = 0                 #неизвестный
            AXIAL       = auto()            #аксиальный (выводы по бокам)
            RADIAL      = auto()            #радиальный (выводы с одной стороны)
            IC          = auto()            #микросхема
            def __eq__(self, other):
                if type(self) is not type(other): return False
                return IntEnum.__eq__(self, other)
            __hash__ = IntEnum.__hash__   #restore hashing
            
        class Holder(IntEnum):          #тип корпуса в держатель
            UNDEFINED   = -1                #не задан
            UNKNOWN     = 0                 #неизвестный
            CYLINDRICAL = auto()            #цилиндрический
            BLADE       = auto()            #ножевой
            def __eq__(self, other):
                if type(self) is not type(other): return False
                return IntEnum.__eq__(self, other)
            __hash__ = IntEnum.__hash__   #restore hashing
            
    name:str = None
    type:Type = None

    def __str__(self):
        return self.name or ''

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        if self.name != other.name: return False
        if type(self.type) is not type(other.type): return False
        if self.type != other.type: return False
        return True

#Сборка
@dataclass
class Array():
    class Type(IntEnum):
        UNDEFINED       = -1        #не задан
        UNKNOWN         = 0         #неизвестный
        INDEPENDENT     = auto()    #независимо
        COMMON_ANODE    = auto()    #общий анод
        COMMON_CATHODE  = auto()    #общий катод
        SERIES          = auto()    #последовательно
        PARALLEL        = auto()    #параллельно
        MATRIX          = auto()    #матрица

    block_count         : int   = 0                 #количество блоков в сборке
    elements_per_block  : int   = 0                 #количество элементов в блоке
    type                : Type  = Type.UNDEFINED    #тип сборки

#Замена номинала
@dataclass
class Substitute():
    partnumber          : str   = None     #номинал
    manufacturer        : str   = None     #производитель
    note                : str   = None     #примечание

#Уникальный идентификатор
@dataclass
class UID():
    name:str = None
    path:str = None


class Component():
    #Типы флага
    class FlagType(IntEnum):
        NONE    = 0     #не задан
        OK      = 1     #всё в порядке
        WARNING = 2     #предупреждение
        ERROR   = 3     #ошибка

    #Общий тип компонента (с базовыми полями для всех типов)
    @dataclass
    class Generic():
        flag                    : "Component.FlagType"  = None                          #флаг (ошибки, предупреждения и т.п.)
        GNRC_designator         : Designator            = None                          #десигнатор
        GNRC_accessory_child    : list                  = None                          #ссылка/ссылки на дочерние компоненты (список)
        GNRC_accessory_parent   : object                = None                          #ссылка на родительский компонент
        GNRC_kind               : str                   = None                          #тип элемента
        GNRC_partnumber         : str                   = None                          #артикул
        GNRC_parametric         : bool                  = False                         #параметрически заданный компонент
        GNRC_description        : str                   = None                          #описание
        GNRC_manufacturer       : str                   = None                          #производитель
        GNRC_quantity           : int                   = 0                             #количество
        GNRC_fitted             : bool                  = True                          #установка в изделие
        GNRC_package            : Package               = None                          #корпус
        GNRC_mount              : MountType             = None                          #тип монтажа
        GNRC_size               : str                   = None                          #типоразмер
        GNRC_temperatureRange   : QuantityRange         = None                          #диапазон рабочих температур
        GNRC_array              : Array                 = None                          #сборка
        GNRC_substitute         : Substitute            = None                          #допустимые замены (список)
        GNRC_note               : str                   = None                          #примечание
        GNRC_uid                : UID                   = None                          #уникальный идентификатор
        GNRC_misc               : list                  = field(default_factory=list)   #оставшиеся нераспознанные параметры

        def __post_init__(self):
            self.flag = Component.FlagType.NONE
        
        #копирует базовые атрибуты из одного подкласса в другой 
        def _GNRC_copy(self, other):
            if isinstance(other, Component.Generic):
                for key, value in self.__dict__.items():
                    if key.startswith("GNRC_"):
                        setattr(other, key, value)
            else:
                raise ValueError("Invalid object class.")

        #ключ сортировки по десигнатору
        def _cmpkey_designator(self):
            key_desPrefix = self.GNRC_designator.prefix if self.GNRC_designator is not None else '\ufffd' #'' или '\ufffd' для сортировки в начало/конец если не указан
            key_desIndex = int(self.GNRC_designator.index) if self.GNRC_designator is not None else 0
            key_desChannel = str(self.GNRC_designator.channel).upper() if self.GNRC_designator is not None else  '' #'' или '\ufffd' для сортировки в начало/конец если не указан
            return (key_desPrefix, key_desIndex, key_desChannel)

        #ключ сортировки по номиналу
        def _cmpkey_partnumber(self):
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return key_partnumber

        #ключ сортировки по типу элемента (из парсера)
        def _cmpkey_kind(self):
            key_kind = str(self.GNRC_kind).upper() if self.GNRC_kind is not None else ''
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_partnumber)

        #ключ сортировки по параметрам (заглушка для базового класса)
        def _cmpkey_params(self):
            key_kind = str(self.GNRC_designator.prefix).upper() if self.GNRC_designator.prefix is not None else '\ufffd' #'' или '\ufffd' для сортировки в начало/конец если не указан
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_partnumber) #потенциально опасно так как есть вероятность сравнения второго ключа с несовместимым типом (из-за определения первого ключа по desPrefix, а типа компонента в парсере по kind)

    #Сборка (Устройство)
    @dataclass
    class Assembly(Generic):
        def _cmpkey_params(self):
            key_kind = 'A'
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_partnumber)

    #Фотоэлемент
    @dataclass
    class Photocell(Generic):
        class Type(IntEnum):
            UNDEFINED  = -1         #не задан
            UNKNOWN    = 0          #неизвестный
            DIODE      = auto()     #диод   
            TRANSISTOR = auto()     #транзистор
            RESISTOR   = auto()     #резистор

        PHOTO_type  : Type  = None                    #тип

        def _cmpkey_params(self):
            key_kind = 'BL'
            key_type = self.PHOTO_type.value if self.PHOTO_type is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_partnumber)

    #Конденсатор
    @dataclass
    class Capacitor(Generic):
        class Type(IntEnum):
            UNDEFINED         = -1          #не задан
            UNKNOWN           = 0           #неизвестный
            CERAMIC           = auto()      #керамический
            TANTALUM          = auto()      #танталовый
            FILM              = auto()      #плёночный
            ALUM_ELECTROLYTIC = auto()      #алюминиевый электролитический
            ALUM_POLYMER      = auto()      #алюминиевый полимерный
            ALUM_HYBRID       = auto()      #алюминиевый гибридный
            SUPERCAPACITOR    = auto()      #ионистор
            NIOBIUM           = auto()      #ниобиевый
            MICA              = auto()      #слюдяной

        CAP_type            : Type          = None              #тип
        CAP_capacitance     : ParameterSpec = None              #ёмкость
        CAP_voltage         : Quantity      = None              #максимальное напряжение
        CAP_dielectric      : str           = None              #диэлектрик
        CAP_lowESR          : bool          = False             #низкое эквивалентное сопротивление
        CAP_safetyRating    : str           = None              #класс безопасности

        def _cmpkey_params(self):
            key_kind = 'C'
            key_capacitance = 0
            key_tolerance   = (0, 0)
            if self.CAP_capacitance is not None:
                if self.CAP_capacitance.value is not None:
                    key_capacitance = self.CAP_capacitance.value.magnitude_norm
                if self.CAP_capacitance.tolerance is not None:
                    if self.CAP_capacitance.tolerance.isrelative(): key_tolerance_relative = 0
                    else: key_tolerance_relative = 1
                    key_tolerance = (key_tolerance_relative, self.CAP_capacitance.tolerance.upper_norm - self.CAP_capacitance.tolerance.lower_norm)
            key_voltage = self.CAP_voltage.magnitude_norm if self.CAP_voltage is not None else 0
            key_type = self.CAP_type.value if self.CAP_type is not None else 0
            key_dielectric = self.CAP_dielectric if self.CAP_dielectric is not None else '\ufffd'                       #'' или '\ufffd' для сортировки в начало/конец если не указан
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_capacitance, key_voltage, key_tolerance, key_dielectric, key_partnumber)

    #Микросхема
    @dataclass
    class IntegratedCircuit(Generic):
        def _cmpkey_params(self):
            key_kind = 'D'
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_partnumber)

    #Крепёж
    @dataclass
    class Fastener(Generic):
        def _cmpkey_params(self):
            key_kind = 'EF'
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_partnumber)

    #Радиатор
    @dataclass
    class Heatsink(Generic):
        def _cmpkey_params(self):
            key_kind = 'ER'
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_partnumber)

    #Автоматический выключатель (Предохранитель)
    @dataclass
    class CircuitBreaker(Generic):
        class Type(IntEnum):
            UNDEFINED           = -1        #не задан
            UNKNOWN             = 0         #неизвестный
            FUSE                = auto()    #плавкий
            FUSE_PTC_RESETTABLE = auto()    #самовосстанавливающийся с положительным температурным коэффициентом
            FUSE_THERMAL        = auto()    #термо
            BREAKER             = auto()    #расцепитель (автоматический выключатель)
            HOLDER              = auto()    #держатель

        class SpeedGrade(IntEnum):
            UNDEFINED           = -1        #не задан
            UNKNOWN             = 0         #неизвестный
            FAST                = auto()    #быстрый
            MEDIUM              = auto()    #средний
            SLOW                = auto()    #медленный

        CBRK_type                  : Type           = None              #тип
        CBRK_speed_grade           : SpeedGrade     = None              #классификация скорости срабатывания
        CBRK_speed                 : Quantity       = None              #значение скорости срабатывания
        CBRK_voltage               : Quantity       = None              #максимальное напряжение
        CBRK_voltage_ac            : bool           = None              #флаг переменного напряжения
        CBRK_current_rating        : Quantity       = None              #номинальный ток
        CBRK_current_maximum       : Quantity       = None              #максимальный допустимый ток (для самовосстанавливающихся)
        CBRK_current_interrupting  : Quantity       = None              #максимальный прерываемый ток
        CBRK_resistance            : Quantity       = None              #сопротивление
        CBRK_power                 : Quantity       = None              #максимальная мощность
        CBRK_meltingPoint          : Quantity       = None              #точка плавления (для плавких)

        def _cmpkey_params(self):
            key_kind = 'FP'
            key_type = self.CBRK_type.value if self.CBRK_type is not None else 0
            key_currentRating = self.CBRK_current_rating.magnitude_norm if self.CBRK_current_rating is not None else 0
            key_currentMaximum = self.CBRK_current_maximum.magnitude_norm if self.CBRK_current_maximum is not None else 0
            key_currentInterrupting = self.CBRK_current_interrupting.magnitude_norm if self.CBRK_current_interrupting is not None else 0
            key_voltage = self.CBRK_voltage.magnitude_norm if self.CBRK_voltage is not None else 0
            key_power = self.CBRK_power.magnitude_norm if self.CBRK_power is not None else 0
            key_meltingPoint = self.CBRK_meltingPoint.magnitude_norm if self.CBRK_meltingPoint is not None else 0
            key_resistance = self.CBRK_resistance.magnitude_norm if self.CBRK_resistance is not None else 0
            key_speedGrade = self.CBRK_speed_grade.value if self.CBRK_speed_grade is not None else 0
            key_speed = self.CBRK_speed.magnitude_norm if self.CBRK_speed is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_currentRating, key_currentMaximum, key_currentInterrupting, key_voltage, key_power, key_meltingPoint, key_resistance, key_speedGrade, key_speed, key_partnumber)

    #Ограничитель перенапряжения
    @dataclass
    class SurgeProtector(Generic):
        class Type(IntEnum):
            UNDEFINED           = -1        #не задан
            UNKNOWN             = 0         #неизвестный
            DIODE               = auto()    #диод
            THYRISTOR           = auto()    #тиристор
            VARISTOR            = auto()    #варистор
            GAS_DISCHARGE_TUBE  = auto()    #газоразрядник
            IC                  = auto()    #микросхема

        SPD_type                    : Type              = None              #тип
        SPD_voltage_standoff        : ParameterSpec     = None              #максимальное рабочее напряжение
        SPD_voltage_breakdown       : ParameterSpec     = None              #напряжение пробоя
        SPD_voltage_clamping        : ParameterSpec     = None              #напряжение гашения выброса
        SPD_voltage_sparkover_dc    : ParameterSpec     = None              #напряжение образования искры (постоянное)
        SPD_current_clamping        : ParameterSpec     = None              #ток гашения выброса
        SPD_capacitance             : ParameterSpec     = None              #ёмкость
        SPD_bidirectional           : bool              = None              #двунаправленный тип (для диодов)
        SPD_energy                  : ParameterSpec     = None              #энергия
        SPD_power                   : ParameterSpec     = None              #мощность

        def _cmpkey_params(self):
            key_kind = 'FV'
            key_type = self.SPD_type.value if self.SPD_type is not None else 0
            key_standoffVoltage = self.SPD_voltage_standoff.value.magnitude_norm if self.SPD_voltage_standoff is not None else 0
            key_breakdownVoltage = self.SPD_voltage_breakdown.value.magnitude_norm if self.SPD_voltage_breakdown is not None else 0
            key_sparkoverVoltageDC = self.SPD_voltage_sparkover_dc.value.magnitude_norm if self.SPD_voltage_sparkover_dc is not None else 0
            key_power = self.SPD_power.value.magnitude_norm if self.SPD_power is not None else 0
            key_energy = self.SPD_energy.value.magnitude_norm if self.SPD_energy is not None else 0
            key_capacitance = self.SPD_capacitance.value.magnitude_norm if self.SPD_capacitance is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_standoffVoltage, key_breakdownVoltage, key_sparkoverVoltageDC, key_capacitance, key_power, key_energy, key_capacitance, key_partnumber)
    
    #Батарея
    @dataclass
    class Battery(Generic):
        class Type(IntEnum):
            UNDEFINED   = -1        #не задан
            UNKNOWN     = 0         #неизвестный
            CELL        = auto()    #ячейка (элемент гальванический)
            BATTERY     = auto()    #батарея (несколько ячеек)
            HOLDER      = auto()    #держатель

        class Chemistry(Enum):
            #Цинково-марганцевые (солевые/алкалиновые)
            ZINC_MANGANESE_DIOXIDE = 'Zn-MnO2'          #обычные щелочные и солевые элементы
            #Литиевые первичные
            LITHIUM_MANGANESE_DIOXIDE = 'Li-MnO2'
            LITHIUM_THIONYL_CHLORIDE = 'Li-SOCl2'
            LITHIUM_IRON_DISULFIDE = 'Li-FeS2'          #распространённый для батарей AA/AAA
            LITHIUM_CARBON_MONOFLOURIDE = 'Li-CFx'      #Li-CFx, редкая специализированная батарея
            #Литиевые вторичные (аккумуляторы)
            LITHIUM_ION = 'Li-ion'
            LITHIUM_POLYMER = 'Li-Po'
            LITHIUM_IRON_PHOSPHATE = 'LiFePO4'
            #Никель-содержащие аккумуляторы
            NICKEL_CADMIUM = 'Ni-Cd'
            NICKEL_METAL_HYDRIDE = 'Ni-MH'
            #Свинцово-кислотные
            LEAD_ACID = 'Pb-acid'
            GEL = 'Pb-acid (gel)'
            AGM = 'Pb-acid (AGM)'
            #Другие
            ZINC_AIR = 'Zn-Air'
            MERCURY = 'Hg'                              #устаревшие, редко используются
            SILVER_OXIDE = 'Ag-O'                       #кнопочные элементы

        BAT_type                        : Type          = None              #тип
        BAT_capacity                    : ParameterSpec = None              #ёмкость
        BAT_voltage                     : Quantity      = None              #номинальное напряжение
        BAT_chemistry                   : Chemistry     = None              #химический тип
        BAT_rechargable                 : bool          = None              #возможность заряда

        def _cmpkey_params(self):
            key_kind = 'GB'
            key_type = self.BAT_type.value if self.BAT_type is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_partnumber)

    #Дисплей
    @dataclass
    class Display(Generic):
        class Type(IntEnum):
            UNDEFINED           = -1        #не задан
            UNKNOWN             = 0         #неизвестный
            NUMERIC_7SEG        = auto()    #числовой 7-сегментный
            ALPHANUMERIC_14SEG  = auto()    #буквенно-цифровой 14-сегментный
            ALPHANUMERIC_16SEG  = auto()    #буквенно-цифровой 16-сегментный
            BARGRAPH            = auto()    #шкальный
            DOTMATRIX           = auto()    #точечная матрица
            GRAPHIC             = auto()    #графический

        class Structure(IntEnum):
            UNKNOWN = 0         #неизвестный
            LED     = auto()    #светодиодный
            OLED    = auto()    #органически-светодиодный
            LCD     = auto()    #жидкокристаллический
            VFD     = auto()    #вакуумно-люминесцентный

        DISP_type           : Type          = None              #тип
        DISP_structure      : Structure     = None              #структура (конструктивные особенности)
        DISP_color          : ColorType     = None              #цвет
        DISP_viewingAngle   : Quantity      = None              #угол обзора, град.

        def _cmpkey_params(self):
            key_kind = 'HG'
            key_type = self.DISP_type.value if self.DISP_type is not None else 0
            key_structure = self.DISP_structure.value if self.DISP_structure is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_structure, key_partnumber)

    #Светодиод
    @dataclass
    class LED(Generic):
        class Type(IntEnum):
            UNDEFINED   = -1        #не задан
            UNKNOWN     = 0         #неизвестный
            INDICATION  = auto()    #индикационный
            LIGHTING    = auto()    #осветительный

        LED_type                        : Type          = None          #тип
        LED_color                       : ColorType     = None          #цвет
        LED_color_temperature           : Quantity      = None          #цветовая температура
        LED_color_renderingIndex        : Quantity      = None          #индекс цветопередачи
        LED_wavelength                  : Quantity      = None          #длина волны [основная, пиковая]
        LED_viewingAngle                : Quantity      = None          #угол обзора, град.
        LED_current                     : Quantity      = None          #прямой ток [номинальный, максимальный]
        LED_voltage_forward             : Quantity      = None          #прямое падение напряжения
        LED_luminous_flux               : ParameterSpec = None          #световой поток
        LED_luminous_intensity          : ParameterSpec = None          #сила света

        def _cmpkey_params(self):
            key_kind = 'HL'
            key_type = self.LED_type.value if self.LED_type is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_partnumber)

    #Перемычка
    @dataclass
    class Jumper(Generic):
        class Type(IntEnum):
            UNDEFINED   = -1        #не задан
            UNKNOWN     = 0         #неизвестный
            ELECTRICAL  = auto()    #электрический
            THERMAL     = auto()    #термический

        JMP_type                            : Type          = None              #тип
        JMP_electrical_current              : Quantity      = None              #электрический ток [рабочий/максимальный]
        JMP_electrical_capacitance          : Quantity      = None              #электрическая ёмкость
        JMP_electrical_voltage_isolation    : Quantity      = None              #максимальное напряжение электрической изоляции
        JMP_thermal_resistance              : Quantity      = None              #термическое сопротивление
        JMP_thermal_conductance             : Quantity      = None              #термическая проводимость

        def __init__(self, resistor:"Component.Resistor" = None):
            super().__init__()
            if resistor is not None:
                resistor._GNRC_copy(self)
                self.JMP_type = self.Type.ELECTRICAL

        def _cmpkey_params(self):
            key_kind = 'J'
            key_type = self.JMP_type.value if self.JMP_type is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_partnumber)

    #Реле
    @dataclass
    class Relay(Generic):
        def _cmpkey_params(self):
            key_kind = 'K'
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_partnumber)

    #Индуктивность
    @dataclass
    class Inductor(Generic):
        class Type(IntEnum):
            UNDEFINED   = -1        #не задан
            UNKNOWN     = 0         #неизвестный
            INDUCTOR    = auto()    #индуктивность
            CHOKE       = auto()    #дроссель

        IND_type                    : Type              = None              #тип
        IND_inductance              : ParameterSpec     = None              #индуктивность
        IND_current                 : ParameterSpec     = None              #максимальный ток [Irms, Isat]
        IND_resistance              : Quantity          = None              #сопротивление (по постоянному току)
        IND_qualityFactor           : ParameterSpec     = None              #добротность
        IND_selfResonance_frequency : Quantity          = None              #частота собственного резонанса
        IND_lowCap                  : bool              = False             #флаг низкой ёмкости

        def _cmpkey_params(self):
            key_kind = 'L'
            key_inductance = 0
            key_tolerance   = (0, 0)
            if self.IND_inductance is not None:
                if self.IND_inductance.value is not None:
                    key_inductance = self.IND_inductance.value.magnitude_norm
                if self.IND_inductance.tolerance is not None:
                    if self.IND_inductance.tolerance.isrelative(): key_tolerance_relative = 0
                    else: key_tolerance_relative = 1
                    key_tolerance = (key_tolerance_relative, self.IND_inductance.tolerance.upper_norm - self.IND_inductance.tolerance.lower_norm)
            key_type = self.IND_type.value if self.IND_type is not None else 0
            key_current = self.IND_current if self.IND_current is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_inductance, key_current, key_tolerance, key_partnumber)

    #Резистор
    @dataclass
    class Resistor(Generic):
        class Type(IntEnum):
            UNDEFINED   = -1        #не задан
            UNKNOWN     = 0         #неизвестный
            FIXED       = auto()    #постоянный
            VARIABLE    = auto()    #переменный
            THERMAL     = auto()    #термо

        class Structure(IntEnum):
            UNKNOWN     = 0         #неизвестный
            THICK_FILM  = auto()    #толстоплёночный
            THIN_FILM   = auto()    #тонкоплёночный
            METAL_FILM  = auto()    #металлоплёночный
            METAL_OXIDE = auto()    #металлооксидный
            CARBON_FILM = auto()    #углеродоплёночный
            WIREWOUND   = auto()    #проволочный
            CERAMIC     = auto()    #керамический

        RES_type            : Type          = None              #тип
        RES_structure       : Structure     = None              #структура (конструктивные особенности)
        RES_resistance      : ParameterSpec = None              #сопротивление
        RES_power           : Quantity      = None              #максимальная мощность
        RES_voltage         : Quantity      = None              #максимальное напряжение
        RES_turns           : int           = None              #количество оборотов (для переменных)
        RES_TCR             : Tolerance     = None              #температурный коэффициент сопротивления
        RES_temp_charac     : list          = None              #температурная характеристика (для терморезисторов) [<t0, K>, <t1, K>, <B>] !!!TODO непонятно что с этим делать

        def _cmpkey_params(self):
            key_kind = 'R'
            key_resistance = 0
            key_tolerance  = (0, 0)
            if self.RES_resistance is not None:
                if self.RES_resistance.value is not None:
                    key_resistance = self.RES_resistance.value.magnitude_norm
                if self.RES_resistance.tolerance is not None:
                    if self.RES_resistance.tolerance.isrelative(): key_tolerance_relative = 0
                    else: key_tolerance_relative = 1
                    key_tolerance = (key_tolerance_relative, self.RES_resistance.tolerance.upper_norm - self.RES_resistance.tolerance.lower_norm)
            key_power = self.RES_power.magnitude_norm if self.RES_power is not None else 0
            key_voltage = self.RES_voltage.magnitude_norm if self.RES_voltage is not None else 0
            key_TCR = (0, 0)
            if self.RES_TCR is not None:
                if self.RES_TCR.isrelative(): key_TCR_relative = 0
                else: key_TCR_relative = 1
                key_tolerance = (key_TCR_relative, self.RES_TCR.upper_norm - self.RES_TCR.lower_norm)
            key_type = self.RES_type.value if self.RES_type is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_resistance, key_power, key_voltage, key_tolerance, key_TCR, key_partnumber)

    #Переключатель
    @dataclass
    class Switch(Generic):
        class Type(IntEnum):
            UNDEFINED   = -1        #не задан
            UNKNOWN     = 0         #неизвестно
            TOGGLE      = auto()    #тумблер
            SLIDE       = auto()    #движковый
            PUSHBUTTON  = auto()    #кнопочный
            LIMIT       = auto()    #концевой ('микрик')
            ROTARY      = auto()    #галетный
            REED        = auto()    #геркон
            ROCKER      = auto()    #клавишный
            THUMBWHEEL  = auto()    #барабанный
            JOYSTICK    = auto()    #джойстик
            KEYLOCK     = auto()    #переключающийся ключом

        SW_type : Type = None           #тип

        def _cmpkey_params(self):
            key_kind = 'S'
            key_type = self.SW_type.value if self.SW_type is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_partnumber)

    #Трансформатор
    @dataclass
    class Transformer(Generic):
        def _cmpkey_params(self):
            key_kind = 'T'
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_partnumber)

    #Диод
    @dataclass
    class Diode(Generic):
        class Type(IntEnum):
            UNDEFINED       = -1        #не задан
            UNKNOWN         = 0         #неизвестный
            GENERAL_PURPOSE = auto()    #общего применения
            SCHOTTKY        = auto()    #Шоттки
            ZENER           = auto()    #стабилитрон
            TUNNEL          = auto()    #тунельный
            VARICAP         = auto()    #варикап

        DIODE_type                  : Type                      = None              #тип
        DIODE_voltage_reverse       : ParameterSpec             = None              #обратное напряжение 
        DIODE_current_reverse       : ParameterSpec             = None              #обратный ток
        DIODE_current_forward       : ParameterSpec             = None              #прямой ток
        DIODE_voltage_forward       : ParameterSpec             = None              #прямое напряжение 
        DIODE_power                 : ParameterSpec             = None              #мощность
        DIODE_capacitance           : ParameterSpec             = None              #ёмкость перехода
        DIODE_recovery_time         : ParameterSpec             = None              #время восстановления

        def _cmpkey_params(self):
            key_kind = 'VD'
            key_type = self.DIODE_type if self.DIODE_type is not None else 0
            key_reverseVoltage = 0
            key_reverseVoltageTolerance = (0, 0)
            if self.DIODE_voltage_reverse is not None:
                if self.DIODE_voltage_reverse.value is not None:
                    key_reverseVoltage = self.DIODE_voltage_reverse.value.magnitude_norm
                if self.DIODE_voltage_reverse.tolerance is not None:
                    if self.DIODE_voltage_reverse.tolerance.isrelative(): key_reverseVoltageTolerance_relative = 0
                    else: key_reverseVoltageTolerance_relative = 1
                    key_reverseVoltageTolerance = (key_reverseVoltageTolerance_relative, self.DIODE_voltage_reverse.tolerance.upper_norm - self.DIODE_voltage_reverse.tolerance.lower_norm)
            key_capacitance = 0
            key_capacitanceTolerance = (0, 0)
            if self.DIODE_capacitance is not None:
                if self.DIODE_capacitance.value is not None:
                    key_capacitance = self.DIODE_capacitance.value.magnitude_norm
                if self.DIODE_capacitance.tolerance is not None:
                    if self.DIODE_capacitance.tolerance.isrelative(): key_capacitanceTolerance_relative = 0
                    else: key_capacitanceTolerance_relative = 1
                    key_capacitanceTolerance = (key_capacitanceTolerance_relative, self.DIODE_capacitance.tolerance.upper_norm - self.DIODE_capacitance.tolerance.lower_norm)
            key_forwardCurrent = self.DIODE_current_forward.value.magnitude_norm if self.DIODE_current_forward is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_forwardCurrent, key_reverseVoltage, key_reverseVoltageTolerance, key_capacitance, key_capacitanceTolerance, key_partnumber)

    #Тиристор
    @dataclass
    class Thyristor(Generic):
        class Type(IntEnum):
            UNDEFINED   = -1        #не задан
            UNKNOWN     = 0         #неизвестный
            THYRISTOR   = auto()    #тиристор   
            TRIAC       = auto()    #симистор
            DYNISTOR    = auto()    #динистор

        THYR_type   : Type  = None              #тип

        def _cmpkey_params(self):
            key_kind = 'VS'
            key_type = self.THYR_type.value if self.THYR_type is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_partnumber)

    #Транзистор
    @dataclass
    class Transistor(Generic):
        class Type(IntEnum):
            UNDEFINED   = -1        #не задан
            UNKNOWN     = 0         #неизвестный
            BJT         = auto()    #биполярный
            JFET        = auto()    #полевой с p-n переходом
            MOSFET      = auto()    #полевой транзистор с МОП-структурой
            IGBT        = auto()    #биполярный транзистор с изолированным затвором

        TRSTR_type          : Type      = None              #тип
        TRSTR_CD_voltage    : Quantity  = None              #максимальное напряжение коллектор-эмиттер/сток-исток
        TRSTR_CD_current    : Quantity  = None              #максимальный ток коллектора/стока
        TRSTR_BG_voltage    : Quantity  = None              #максимальное напряжение база-эмиттер/затвор-исток

        def _cmpkey_params(self):
            key_kind = 'VT'
            key_type = self.TRSTR_type.value if self.TRSTR_type is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_partnumber)

    #Оптоизолятор
    @dataclass
    class Optoisolator(Generic):
        class OutputType(IntEnum):
            UNKNOWN     = 0         #неизвестный
            TRANSISTOR  = auto()    #транзистор
            DARLINGTON  = auto()    #составной транзистор
            DIODE       = auto()    #диод
            THYRISTOR   = auto()    #тиристор
            TRIAC       = auto()    #симистор
            LOGIC       = auto()    #логический
            LINEAR      = auto()    #линейный

        OPTOISO_outputType          : OutputType    = None   #тип выхода
        OPTOISO_channels            : int           = None   #количество каналов
        OPTOISO_isolation_voltage   : Quantity      = None   #напряжение изоляции
        OPTOISO_acinput             : bool          = None   #двуполярный вход
        OPTOISO_zeroCrossDetection  : bool          = None   #детектор перехода через ноль
        OPTOISO_CTR                 : Quantity      = None   #коэффициент передачи по току

        def _cmpkey_params(self):
            key_kind = 'VU'
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_partnumber)

    #Соединитель
    @dataclass
    class Connector(Generic):
        class Type(IntEnum):
            UNDEFINED   = -1    #не задан
            UNKNOWN     = 0     #неизвестный

        class Gender(IntEnum):
            UNKNOWN    = 0          #неизвестный
            PLUG       = auto()     #вилка
            RECEPTACLE = auto()     #розетка

        CON_type    : Type      = None              #тип
        CON_gender  : Gender    = None              #пол

        def _cmpkey_params(self):
            key_kind = 'X'
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_partnumber)

    #Фильтр ЭМП
    @dataclass
    class EMIFilter(Generic):
        class Type(IntEnum):
            UNDEFINED           = -1        #не задан
            UNKNOWN             = 0         #неизвестный
            FERRITE_BEAD        = auto()    #ферритовая бусина
            COMMON_MODE_CHOKE   = auto()    #синфазная катушка индуктивности
            ASSEMBLY            = auto()    #готовое устройство

        EMIF_type               : Type              = None              #тип
        EMIF_impedance          : ParameterSpec     = None              #импеданс
        EMIF_inductance         : ParameterSpec     = None              #индуктивность
        EMIF_capacitance        : ParameterSpec     = None              #ёмкость
        EMIF_resistance         : ParameterSpec     = None              #активное сопротивление
        EMIF_current            : Quantity          = None              #ток
        EMIF_voltage            : Quantity          = None              #напряжение

        def _cmpkey_params(self):
            key_kind = 'ZF'
            key_type = self.EMIF_type.value if self.EMIF_type is not None else 0
            key_impedance = self.EMIF_impedance.value.magnitude_norm if self.EMIF_impedance is not None else 0
            key_inductance = self.EMIF_inductance.value.magnitude_norm if self.EMIF_inductance is not None else 0
            key_resistance = self.EMIF_resistance.value.magnitude_norm if self.EMIF_resistance is not None else 0
            key_capacitance = self.EMIF_capacitance.value.magnitude_norm if self.EMIF_capacitance is not None else 0
            key_current = self.EMIF_current.magnitude_norm if self.EMIF_current is not None else 0
            key_voltage = self.EMIF_voltage.magnitude_norm if self.EMIF_voltage is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_impedance, key_inductance, key_resistance, key_capacitance, key_current, key_voltage, key_partnumber)

    #Осциллятор (Резонатор)
    @dataclass
    class Oscillator(Generic):
        class Type(IntEnum):
            UNDEFINED   = -1        #не задан
            UNKNOWN     = 0         #неизвестный
            OSCILLATOR  = auto()    #осциллятор (тактовый сигнал на выходе)
            RESONATOR   = auto()    #резонатор (фильтр частоты)
        
        class Structure(IntEnum):
            UNKNOWN     = 0         #неизвестный
            QUARTZ      = auto()    #кварцевый
            CERAMIC     = auto()    #керамический

        OSC_type            : Type              = None              #тип
        OSC_structure       : Structure         = None              #структура (конструктивные особенности)
        OSC_frequency       : ParameterSpec     = None              #частота
        OSC_stability       : Tolerance         = None              #стабильность частоты
        OSC_loadCapacitance : Quantity          = None              #ёмкость нагрузки
        OSC_ESR             : Quantity          = None              #эквивалентное последовательное сопротивление
        OSC_driveLevel      : Quantity          = None              #уровень возбуждения
        OSC_overtone        : int               = None              #номер гармоники (фундаментальная = 1)

        def _cmpkey_params(self):
            key_kind = 'ZG'
            key_type = self.OSC_type.value if self.OSC_type is not None else 0
            key_structure = self.OSC_structure if self.OSC_structure is not None else 0
            key_frequency = 0
            key_tolerance  = (0, 0)
            if self.OSC_frequency is not None:
                if self.OSC_frequency.value is not None:
                    key_frequency = self.OSC_frequency.value.magnitude_norm
                if self.OSC_frequency.tolerance is not None:
                    if self.OSC_frequency.tolerance.isrelative(): key_tolerance_relative = 0
                    else: key_tolerance_relative = 1
                    key_tolerance = (key_tolerance_relative, self.OSC_frequency.tolerance.upper_norm - self.OSC_frequency.tolerance.lower_norm)
            key_stability = (0, 0)
            if self.OSC_stability is not None:
                if self.OSC_stability.isrelative(): key_stability_relative = 0
                else: key_stability_relative = 1
                key_stability = (key_stability_relative, self.OSC_stability.upper_norm - self.OSC_stability.lower_norm)
            key_loadCapacitance = self.OSC_loadCapacitance.magnitude_norm if self.OSC_loadCapacitance is not None else 0
            key_ESR = self.OSC_ESR.magnitude_norm if self.OSC_ESR is not None else 0
            key_driveLevel = self.OSC_driveLevel.magnitude_norm if self.OSC_driveLevel is not None else 0
            key_partnumber = str(self.GNRC_partnumber).upper() if self.GNRC_partnumber is not None else ''
            return (key_kind, key_type, key_structure, key_frequency, key_tolerance, key_stability, key_loadCapacitance, key_ESR, key_driveLevel, key_partnumber)

#База данных с компонентами
@dataclass
class Database():
    #нарекания (в результате проверки)
    @dataclass
    class Complaints():
        warning     : int   = 0
        error       : int   = 0
        critical    : int   = 0

        def add(self, other):
            if not isinstance(other, self.__class__): raise ValueError("incompatiable types")
            self.warning  += other.warning
            self.error    += other.error
            self.critical += other.critical

        def reset(self):
            self.warning  = 0
            self.error    = 0
            self.critical = 0

        def none(self):
            if self.critical + self.error + self.warning == 0: return True
            return False
        
        def noerrors(self):
            if self.critical + self.error == 0: return True
            return False

    entries     : list[Component]   = field(default_factory=list)       #компоненты
    complaints  : Complaints        = field(default_factory=Complaints) #нарекания

    #вставляет запись
    def insert_entry(self, entry:Component, index:int = -1):
        if index > len(self.entries): index = len(self.entries)
        elif index < -len(self.entries): index = 0
        elif index < 0: index = len(self.entries) + index + 1
        self.entries.insert(index, entry)
        return entry

    #сортировка базы данных
    def sort(self, method:str = 'designator', reverse:bool = False):
        if method == 'designator':
            self.entries.sort(key = lambda entry: entry._cmpkey_designator(), reverse = reverse)
        elif method == 'partnumber':
            self.entries.sort(key = lambda entry: entry._cmpkey_partnumber(), reverse = reverse)
        elif method == 'kind':
            self.entries.sort(key = lambda entry: entry._cmpkey_kind(), reverse = reverse)
        elif method == 'params':
            self.entries.sort(key = lambda entry: entry._cmpkey_params(), reverse = reverse)
        else:
            raise NotImplementedError
    
    #проверка базы данных
    def check(self):
        print("INFO >> Checking data (system)", end ="... ")
        complaints = self.Complaints()

        #проверяем целостность десигнаторов
        for component in self.entries:
            if component.GNRC_designator is not None:
                #десигнатор есть, проверяем целостность
                if not component.GNRC_designator.check():
                    component.flag = Component.FlagType.ERROR
                    complaints.error += 1
                    print(f"\n{' ' * 12}error! {component.GNRC_designator} - inconsistent designator", end = '', flush = True)
            else:
                #десигнатора нет, проверяем что есть родительский компонент
                if component.GNRC_accessory_parent is None:
                    component.flag = Component.FlagType.ERROR
                    complaints.critical += 1
                    print(f"\n{' ' * 12}critical error! rogue component: {component.GNRC_partnumber}", end = '', flush = True)

        #проверяем уникальность десигнаторов
        for i in range(len(self.entries)):
            for j in range(i + 1, len(self.entries)):
                if self.entries[i].GNRC_designator is not None and self.entries[j].GNRC_designator is not None:
                    if self.entries[i].GNRC_designator.full == self.entries[j].GNRC_designator.full:
                        self.entries[i].flag = Component.FlagType.ERROR
                        self.entries[j].flag = Component.FlagType.ERROR
                        complaints.critical += 1
                        print(f"\n{' ' * 12}critical error! {self.entries[i].GNRC_designator} - duplicate designators", end = '', flush = True)

        if complaints.none(): 
            print("ok.")  
        else:
            print(f"\n{' ' * 12}completed: {complaints.critical} critical, {complaints.error} errors, {complaints.warning} warnings.")
        return complaints
