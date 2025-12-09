from enum import Enum, IntEnum

class Locale(IntEnum):
    EN = 0      #English
    RU = 1      #Russian

    def translate(locale, value, sub:int = 0):
        result = value.value[locale.value]
        if isinstance(result, tuple):
            if sub >= len(result):
                return result[-1]
            else:
                return result[sub]
        return result

#Единицы измерения
class Unit():
    #множители
    class Multiplier(float, Enum):
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
        PERCENT  = 1e-2
        PERMILLE = 1e-3
        PPM      = 1e-6
        PPB      = 1e-9
        #возвращает префикс для множителя
        @property
        def prefix(multiplier:"Unit.Multiplier") -> "Unit.Prefix":
            return Unit.Prefix.__members__.get(multiplier.name)

    #приставки
    class Prefix(Enum):
        YOCTO = ('y',        'и' )
        ZEPTO = ('z',        'з' )
        ATTO  = ('a',        'а' )
        FEMTO = ('f',        'ф' )
        PICO  = ('p',        'п' )
        NANO  = ('n',        'н' )
        MICRO = (('µ', 'u'), 'мк')
        MILLI = ('m',        'м' )
        CENTI = ('c',        'с' )
        DECI  = ('d',        'д' )
        NONE  = ('',         ''  )
        DECA  = ('da',       'да')
        HECTO = ('h',        'г' )
        KILO  = ('k',        'к' )
        MEGA  = ('M',        'М' )
        GIGA  = ('G',        'Г' )
        TERA  = ('T',        'Т' )
        PETA  = ('P',        'П' )
        EXA   = ('E',        'Э' )
        ZETTA = ('Z',        'З' )
        YOTTA = ('Y',        'И' )
        #возвращает множитель для префикса
        @property
        def multiplier(prefix:"Unit.Prefix") -> "Unit.Multiplier":
            return Unit.Multiplier.__members__.get(prefix.name)

    #названия
    class Name(Enum):
        NONE        = ('', '')
        #Fraction / Доля
        PERCENT     = ('%', '%')
        PERMILLE    = ('‰', '‰')
        PPM         = ('ppm', 'ppm')
        PPB         = ('ppb', 'ppb')
        #Time / Время
        SECOND      = ('s', 'с')
        MINUTE      = ('min', 'мин')
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
        AMPERE_HOUR = ('Ah', 'Ач')
        #Optical / Оптические
        CANDELA     = ('cd', 'кд')
        LUMEN       = ('lm', 'лм')
        #Misc / Разное
        MOLE        = ('mol', 'моль')
        DEGREE      = (('°', 'deg.'), ('°', 'град.'))
        #Composite / Составные
        PPM_PER_CELCIUS_DEG = ('ppm/°C', 'ppm/°C')
        PPB_PER_CELCIUS_DEG = ('ppb/°C', 'ppb/°C')
        CELCIUS_DEG_PER_WATT = ('°C/W', '°C/Вт')
        WATT_PER_CELCIUS_DEG = ('W/°C', 'Вт/°C')
        AMPERE2_SECOND = (('A²s', 'A^2s', 'A?s'), ('А²с', 'А^2с', 'А?с')) #костыли для неюникода
        #Virtual / Виртуальные (для работы парсера)
        VIRTUAL_IND_QFACTOR = ('Q', 'Q')
        #возвращает множитель для парциальных единиц измерения
        @property
        def multiplier(prefix:"Unit.Name") -> "Unit.Multiplier":
            return Unit.Multiplier.__members__.get(prefix.name)
        
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
    DO_PLACE = ("", "")
    DO_NOT_PLACE = ("do not place", "не устанавливать")

class assemble_parameters(Enum):
    PACKAGE = ("package", "корпус")
    PACKAGE_SURFACE_CHIP = ("SMD", "чип")
    PACKAGE_SURFACE_MOLDED = ("SMD", "чип")
    PACKAGE_THROUGHHOLE = ("throughhole", "выводной")
    PACKAGE_THROUGHHOLE_AXIAL = ("axial", "акс.")
    PACKAGE_THROUGHHOLE_RADIAL = ("radial", "рад.")
    PACKAGE_HOLDER = ("in holder", "в держатель")
    PACKAGE_HOLDER_CYLINDRICAL = ("cyl.", "цил.")
    PACKAGE_HOLDER_BLADE = ("blade", "ножевой")
    ARRAY = ("array", "сборка")
    CAP_TYPE_CERAMIC = ("ceramic", "керам.")
    CAP_TYPE_TANTALUM = ("tantalum", "тант.")
    CAP_TYPE_FILM = ("film", "плён.")
    CAP_TYPE_ALUM_ELECTROLYTIC = ("alum.\xa0electrolytic", "алюм.\xa0эл-лит")
    CAP_TYPE_ALUM_POLYMER = ("alum.\xa0polymer", "алюм.\xa0полим.")
    CAP_TYPE_ALUM_HYBRID = ("alum.\xa0hybrid", "алюм.\xa0гибрид.")
    CAP_TYPE_SUPERCAPACITOR = ("supercap.", "ионистор")
    CAP_TYPE_NIOBIUM = ("niobium", "ниоб.")
    CAP_TYPE_MICA = ("mica", "слюд.")
    LOW_ESR = ("low\xa0ESR", "низк.\xa0имп.")
    LOW_CAPACITANCE = ("low\xa0cap.", "низк.\xa0ёмк.")
    SPD_TYPE_DIODE = ("TVS-diode", "супрессор")
    SPD_TYPE_VARISTOR = ("varistor", "варистор")
    SPD_UNIDIRECTIONAL = ("unidir.", "однонаправ.")
    SPD_BIDIRECTIONAL = ("bidir.", "двунаправ.")
    EMIF_TYPE_FERRITEBEAD = ("ferrite\xa0bead", "фер.\xa0бус.")
    EMIF_TYPE_COMMONMODECHOKE = ("CM\xa0choke", "синф.\xa0дроссель")
    CBRK_TYPE_FUSE = ("fuse", "плавкий")
    CBRK_TYPE_FUSE_PTCRESETTABLE = ("PTC", "самовосст.")
    CBRK_TYPE_FUSE_THERMAL = ("thermal", "терм.")
    CBRK_TYPE_BREAKER = ("circuit breaker", "авт.\xa0выкл.")
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
    JMP_TYPE_ELECTRICAL = ("", "")
    JMP_TYPE_THERMAL = ("thermal", "термо")
    BAT_TYPE_HOLDER = ("holder", "держатель")
    RES_TYPE_FIXED = ("", "")
    RES_TYPE_VARIABLE = ("variable", "перем.")
    RES_TYPE_THERMAL = ("thermal", "термо")
    RES_STRUCTURE_THICKFILM = ("thick film", "толстоплён.")
    RES_STRUCTURE_THINFILM = ("thin film", "тонкоплён.")
    RES_STRUCTURE_METALFILM = ("metal film", "мет-плён.")
    RES_STRUCTURE_METALOXIDE = ("metal oxide", "мет-окс.")
    RES_STRUCTURE_CARBONFILM = ("carbon", "углерод.")
    RES_STRUCTURE_WIREWOUND = ("wirewound", "провол.")
    RES_STRUCTURE_CERAMIC = ("ceramic", "керам.")
    DIODE_TYPE_GENERALPURPOSE = ("gen.\xa0purp.", "общ.\xa0прим.")
    DIODE_TYPE_SCHOTTKY = ("Schottky", "Шоттки")
    DIODE_TYPE_ZENER = ("zener", "стабилитрон")
    DIODE_TYPE_TUNNEL = ("tunnel", "туннельный")
    DIODE_TYPE_VARICAP = ("varicap", "варикап")

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

class assemble_pnp_layer(Enum):
    TOP = ("Top", "Верхний")
    BOTTOM = ("Bottom", "Нижний")
    MIDDLE = ("Middle", "Внутренний")

class assemble_pnp_mount(Enum):
    UNDEFINED = ("UNDEFINED", "незадан")
    SURFACE = ("SMD", "поверхностный")
    SEMI_SURFACE = ("SEMI-SMD", "полу-поверхностный")
    THROUGHHOLE = ("TH", "выводной")
    EDGE = ("EDGE", "краевой")
    CHASSIS = ("CHASSIS", "корпус")
    UNKNOWN = ("UNKNOWN", "неизветно")
    UNRECOGNIZED = ("UNRECOGNIZED", "неопознан")

class assemble_pnp_status(Enum):
    ENABLED = ("ON", "вкл")
    DISABLED = ("OFF", "выкл")

class build_cl(Enum):
    TITLE_BOOK = ("Component list", "Список компонентов")
    TITLE_COMPONENTS_LIST = ("Components", "Компоненты")
    TITLE_ACCESSORIES_LIST = ("Accessories", "Аксессуары")
    TITLE_SUBSTITUTES_LIST = ("Substitutes", "Допустимые замены")
    NO_SUBSITUTE = ("no substitute", "без замены")

class export_cl_xlsx(Enum):
    HEADER_DESIGNATOR = ("Designator", "Поз. обозначение")
    HEADER_COMPONENT_TYPE = ("Component type", "Тип элемента")
    HEADER_PARTNUMBER = ("Partnumber", "Артикул")
    HEADER_PARAMETRIC = ("⚙", "⚙")
    HEADER_PARAMETRIC_COMMENT = ("Counterpart with parameters from description is allowed", "Допустим аналог с параметрами из описания")
    HEADER_DESCRIPTION = ("Description", "Описание")
    HEADER_PACKAGE = ("Package", "Корпус")
    HEADER_MANUFACTURER = ("Manufacturer", "Производитель")
    HEADER_QUANTITY = ("Quantity", "Кол-во")
    HEADER_NOTE = ("Note", "Примечание")
    HEADER_ORIGINAL_PARTNUMBER = ("Orig. partnumber", "Изнач. артикул")
    HEADER_ORIGINAL_MANUFACTURER = ("Orig. manufacturer", "Изнач. производитель")
    HEADER_ORIGINAL_QUANTITY = ("Orig. quantity", "Изнач. кол-во")
    HEADER_SUBSTITUTE_QUANTITY = ("Subs. quantity", "Зам. кол-во")
    HEADER_SUBSTITUTE_PARTNUMBER = ("Subs. partnumber", "Зам. артикул")
    HEADER_SUBSTITUTE_MANUFACTURER = ("Subs. manufacturer", "Зам. производитель")
    HEADER_SUBSTITUTE_NOTE = ("Subs. note", "Зам. примечание")
    VALUE_PARAMETRIC_TRUE = ("●", "●")
    VALUE_PARAMETRIC_FALSE = ("◌", "◌")

class export_pe3_csv(Enum):
    HEADER_DESIGNATOR = ("Designator", "Поз. обозначение")
    HEADER_LABEL = ("Label", "Наименование")
    HEADER_QUANTITY = ("Quantity", "Кол.")
    HEADER_NOTE = ("Note", "Примечание")

class optimize_pnp_fp(Enum):
    DISABLE_REASON = ("OPTFP", "оптимизация")

class build_pnp(Enum):
    DISABLE_REASON_NOTBOM = ("NOBOM", "NOBOM")
    DISABLE_REASON_NOTFITTED = ("NOFIT", "NOFIT")
    DISABLE_REASON_MOUNT_SMD = ("MNT-SMD", "MNT-SMD")
    DISABLE_REASON_MOUNT_SEMISMD = ("MNT-SMSMD", "MNT-SMSMD")
    DISABLE_REASON_MOUNT_THROUGHHOLE = ("MNT-TH", "MNT-TH")
    DISABLE_REASON_MOUNT_EDGE = ("MNT-EDGE", "MNT-EDGE")
    DISABLE_REASON_MOUNT_CHASSIS = ("MNT-CHS", "MNT-CHS")
    DISABLE_REASON_MOUNT_UNKNOWN = ("MNT-UNK", "MNT-UNK")

class export_sp_csv(Enum):
    HEADER_LABEL = ("Label", "Наименование")
    HEADER_QUANTITY = ("Quantity", "Кол.")
    HEADER_DESIGNATOR = ("Designator", "Поз. обозначение")

class export_pnp_csv(Enum):
    HEADER_DESIGNATOR = ("Designator", "Поз. обозначение")
    HEADER_LAYER = ("Layer", "Слой")
    HEADER_LOCATION_X = ("Center-X", "Центр-X")
    HEADER_LOCATION_Y = ("Center-Y", "Центр-Y")
    HEADER_ROTATION = ("Rotation", "Поворот")
    HEADER_FOOTPRINT = ("Footprint", "Посадочное место")
    HEADER_MOUNT = ("Mount", "Монтаж")
    HEADER_STATE = ("State", "Состояние")
    HEADER_PARTNUMBER = ("Partnumber", "Артикул")
    HEADER_DESCRIPTION = ("Description", "Описание")
    HEADER_COMMENT = ("Comment", "Коментарий")

class export_pnp_txt(Enum):
    HEADER_DESIGNATOR = export_pnp_csv.HEADER_DESIGNATOR.value
    HEADER_LAYER = export_pnp_csv.HEADER_LAYER.value
    HEADER_LOCATION_X = export_pnp_csv.HEADER_LOCATION_X.value
    HEADER_LOCATION_Y = export_pnp_csv.HEADER_LOCATION_Y.value
    HEADER_ROTATION = export_pnp_csv.HEADER_ROTATION.value
    HEADER_FOOTPRINT = export_pnp_csv.HEADER_FOOTPRINT.value
    HEADER_MOUNT = export_pnp_csv.HEADER_MOUNT.value
    HEADER_STATE = export_pnp_csv.HEADER_STATE.value
    HEADER_PARTNUMBER = export_pnp_csv.HEADER_PARTNUMBER.value
    HEADER_DESCRIPTION = export_pnp_csv.HEADER_DESCRIPTION.value
    HEADER_COMMENT = export_pnp_csv.HEADER_COMMENT.value

class cldiscriminator(Enum):
    XLSX_SHEET_TITLE_MODIFIED = ("Modified", "Изменённые")
    XLSX_SHEET_TITLE_ADDED = ("Added", "Добавленные")
    XLSX_SHEET_TITLE_REMOVED = ("Removed", "Исключённые")

class bomdiscriminator(Enum):
    XLSX_SHEET_TITLE_MODIFIED = ("Modified", "Изменённые")
    XLSX_SHEET_TITLE_CHANGES = ("Changes", "Изменения")
    XLSX_SHEET_TITLE_ADDED = ("Added", "Добавленные")
    XLSX_SHEET_TITLE_REMOVED = ("Removed", "Исключённые")
    XLSX_FIELD_MODIFIED_COMMENT_PREFIX = ("Reference value:\n", "Исходное значение:\n")
