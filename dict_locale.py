from enum import Enum, IntEnum

class LocaleIndex(IntEnum):
    EN = 0      #English
    RU = 1      #Russian

class MetricPrefix(Enum):
    YOTTA = ('Y',  'И' )
    ZETTA = ('Z',  'З' )
    EXA   = ('E',  'Э' )
    PETA  = ('P',  'П' )
    TERA  = ('T',  'Т' )
    GIGA  = ('G',  'Г' )
    MEGA  = ('M',  'М' )
    KILO  = ('k',  'к' )
    HECTO = ('h',  'г' )
    DECA  = ('da', 'да')
    NONE  = ('',   ''  )
    DECI  = ('d',  'д' )
    CENTI = ('c',  'с' )
    MILLI = ('m',  'м' )
    MICRO = ('µ',  'мк')
    NANO  = ('n',  'н' )
    PICO  = ('p',  'п' )
    FEMTO = ('f',  'ф' )
    ATTO  = ('a',  'а' )
    ZEPTO = ('z',  'з' )
    YOCTO = ('y',  'и' )

class Units(Enum):
    #Fraction / Доля
    PERCENT     = ('%', '%')
    PERMILLE    = ('‰', '‰')
    PPM         = ('ppm', 'ppm')
    PPB         = ('ppb', 'ppb')
    #Time / Время
    SECOND      = ('s', 'с')
    MINUTE      = ('m', 'м')
    HOUR        = ('h', 'ч')
    HERTZ       = ('Hz', 'Гц')
    #Length / Длина
    METRE       = ('m', 'м')
    #Mass / Масса
    GRAMM       = ('g', 'г')
    KILOGRAMM   = ('kg', 'кг')
    TONNE       = ('mt', 'т')
    #Temperature / Температура
    KELVIN      = ('K', 'К')
    CELCIUS     = ('C', 'C')
    CELCIUS_DEG = ('°C', '°C')
    #Electric / Электрические
    VOLT        = ('V', 'В')
    AMPERE      = ('A', 'А')
    OHM         = ('Ohm', 'Ом')
    FARAD       = ('F', 'Ф')
    HENRY       = ('H', 'Гн')
    #Power / Мощность
    WATT        = ('W', 'Вт')
    #Energy / Энергия
    JOULE       = ('J', 'Дж')
    #Optical / Оптические
    CANDELA     = ('cd', 'кд')
    LUMEN       = ('lm', 'лм')
    #Misc / Разное
    MOLE        = ('mol', 'моль')
    DEGREE      = ('deg.', 'град.')

class Color(Enum):
    INFRARED    = ("infrared", "инфракрасный")
    ULTRAVIOLET = ("ultraviolet", "ультрафиолетовый")
    RED         = ("red", "красный")
    ORANGE      = ("orange", "оранжевый")
    AMBER       = ("amber", "янтарный")
    YELLOW      = ("yellow", "жёлтый")
    LIME        = ("lime", "салатовый")
    GREEN       = ("green", "зелёный")
    TURQUOISE   = ("turquoise", "бирюзовый")
    CYAN        = ("cyan", "голубой")
    BLUE        = ("blue", "синий")
    VIOLET      = ("violet", "фиолетовый")
    PURPLE      = ("purple", "пурпурный")
    PINK        = ("pink", "розовый")
    MULTI       = ("multicolor", "многоцветный")
    WHITE       = ("white", "белый")

class assemble_eskd(Enum):
    DO_NOT_PLACE = ("Do not place", "Не устанавливать")

class assemble_parameters(Enum):
    MOUNT_SURFACE = ("SMD", "чип")
    MOUNT_THROUGHHOLE = ("throughhole", "выводной")
    MOUNT_AXIAL = ("axial", "акс.")
    MOUNT_RADIAL = ("radial", "рад.")
    MOUNT_HOLDER = ("in holder", "в держатель")
    ARRAY = ("array", "сборка")
    CAP_TYPE_CERAMIC = ("ceramic", "керам.")
    CAP_TYPE_TANTALUM = ("tantalum", "тант.")
    CAP_TYPE_FILM = ("film", "плён.")
    CAP_TYPE_ALUM_ELECTROLYTIC = ("alum.\xa0electrolytic", "алюм.\xa0эл-лит")
    CAP_TYPE_ALUM_POLYMER = ("alum.\xa0polymer", "алюм.\xa0полим.")
    CAP_TYPE_SUPERCAPACITOR = ("supercap.", "ионистор")
    LOW_ESR = ("low\xa0ESR", "низк.\xa0имп.")
    LOW_CAPACITANCE = ("low\xa0cap.", "низк.\xa0ёмк.")
    SCHOTTKY = ("Schottky", "Шоттки")
    PACKAGE = ("package", "корпус")
    SPD_TYPE_DIODE = ("TVS-diode", "супрессор")
    SPD_TYPE_VARISTOR = ("varistor", "варистор")
    SPD_UNIDIRECTIONAL = ("unidir.", "однонаправ.")
    SPD_BIDIRECTIONAL = ("bidir.", "двунаправ.")
    FERRITE_BEAD = ("ferrite\xa0bead", "фер.\xa0бус.")
    COMMON_MODE_CHOKE = ("CM\xa0choke", "синф.\xa0дроссель")
    CBRK_TYPE_FUSE = ("fuse", "плавкий")
    CBRK_TYPE_FUSE_PTCRESETTABLE = ("PTC", "самовосст.")
    CBRK_TYPE_FUSE_THERMAL = ("thermal", "терм.")
    CBRK_TYPE_BREAKER = ("circuit breaker", "авт. выкл.")
    CBRK_TYPE_HOLDER = ("holder", "держатель")
    CBRK_SPEEDGRADE_FAST = ("fast", "быстрый")
    CBRK_SPEEDGRADE_MEDIUM = ("medium", "средний")
    CBRK_SPEEDGRADE_SLOW = ("slow", "медленный")
    VOLTAGE_AC = ("AC", "перем.")
    VOLTAGE_DC = ("DC", "пост.")
    OSC_STRUCTURE_QUARTZ = ("quartz", "кварц.")
    OSC_STRUCTURE_CERAMIC = ("ceramic", "керам.")
    OSC_OVERTONE = ("overtone", "гарм.")
    OSC_OVERTONE_FUNDAMENTAL = ("fund.", "фунд.")
    LED_TYPE_INDICATOR = ("indicator", "индикаторный")
    LED_TYPE_LIGHTING = ("lighting", "осветительный")
    LED_CRI = ("CRI", "CRI")
    JMP_TYPE_THERMAL = ("thermal", "термо")
    BAT_TYPE_HOLDER = ("holder", "держатель")

class assemble_kind(Enum):
    ASSEMBLY = ("assembly", "устройство")
    PHOTO_CELL = ("photocell", "фотоэлемент")
    PHOTO_DIODE = ("photodiode", "фотодиод")
    PHOTO_TRANSISTOR = ("phototransistor", "фототранзистор")
    PHOTO_RESISTOR = ("photoresistor", "фоторезистор")
    CAPACITOR = ("capacitor", "конденсатор")
    INTEGRATED_CIRCUIT = ("integrated circuit", "микросхема")
    FASTENER = ("fastener", "крепёж")
    HEATSINK = ("heatsink", "радиатор")
    CIRCUIT_BREAKER = ("circuit breaker", "автоматический выключатель")
    FUSE_PTC_RESETTABLE = ("PTC resettable", "предохранитель")
    FUSE_THERMAL = ("thermal fuse", "термопредохранитель")
    FUSE = ("fuse", "предохранитель")
    SURGE_PROTECTOR = ("surge protector", "ограничитель перенапряжения")
    TVS_DIODE = ("TVS diode", "супрессор")
    TVS_THYRISTOR = ("TVS thyristor", "супрессор")
    VARISTOR = ("varistor", "варистор")
    GAS_DISCHARGE_TUBE = ("gas discharge tube", "газоразрядник")
    BATTERY = ("battery", "батарея")
    DISPLAY = ("display", "дисплей")
    LED = ("LED", "светодиод")
    JUMPER = ("jumper", "перемычка")
    RELAY = ("relay", "реле")
    INDUCTOR = ("inductor", "индуктивность")
    CHOKE = ("choke", "дроссель")
    RESISTOR = ("resistor", "резистор")
    POTENTIOMETER = ("potentiometer", "потенциометр")
    SWITCH = ("switch", "переключатель")
    TRANSFORMER = ("transformer", "трансформатор")
    DIODE = ("diode", "диод")
    ZENER_DIODE = ("zener diode", "стабилитрон")
    VARICAP = ("varicap", "варикап")
    THYRISTOR = ("thyristor", "тиристор")
    TRIAC = ("TRIAC", "симистор")
    DYNISTOR = ("dynistor", "динистор")
    TRANSISTOR = ("transistor", "транзистор")
    OPTOISOLATOR = ("optoisolator", "Оптоизолятор")
    OPTOCOUPLER = ("optocoupler", "оптопара")
    PHOTOTRIAC = ("phototriac", "оптосимистор")
    CONNECTOR = ("connector", "соединитель")
    EMI_FILTER = ("EMI filter", "фильтр ЭМП")
    OSCILLATOR = ("oscillator", "осциллятор")
    CRYSTAL = ("crystal", "резонатор")
    RESONATOR = ("resonator", "резонатор")

class build_cl(Enum):
    TITLE_BOOK = ("Component list", "Список компонентов")
    TITLE_COMPONENTS_LIST = ("Components", "Список компонентов")
    TITLE_SUBSTITUTES_LIST = ("Substitutes", "Допустимые замены")
    NO_SUBSITUTE = ("no substitute", "без замены")

class export_cl_xlsx(Enum):
    HEADER_DESIGNATOR = ("Designator", "Поз. обозначение")
    HEADER_COMPONENT_TYPE = ("Component type", "Тип элемента")
    HEADER_VALUE = ("Value", "Номинал")
    HEADER_DESCRIPTION = ("Description", "Описание")
    HEADER_PACKAGE = ("Package", "Корпус")
    HEADER_MANUFACTURER = ("Manufacturer", "Производитель")
    HEADER_QUANTITY = ("Quantity", "Кол-во")
    HEADER_ORIGINAL_VALUE = ("Orig. value", "Изнач. номинал")
    HEADER_ORIGINAL_MANUFACTURER = ("Orig. manufacturer", "Изнач. производитель")
    HEADER_SUBSTITUTE_VALUE = ("Subs. value", "Зам. номинал")
    HEADER_SUBSTITUTE_MANUFACTURER = ("Subs. manufacturer", "Зам. производитель")
    HEADER_SUBSTITUTE_NOTE = ("Subs. note", "Зам. примечание")

