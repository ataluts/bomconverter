import os
import datetime
from typedef_bom import BoM_typeDef                                                             #класс BoM
from typedef_components import Components_typeDef                                               #класс базы данных компонентов
from typedef_titleBlock import TitleBlock_typeDef                                               #класс основной надписи

script_dirName  = os.path.dirname(__file__)                                                     #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                               #базовое имя модуля
script_date     = datetime.datetime(2024, 6, 8)

designer_name = "Alexander Taluts"                                                              #имя разработчика

# ----------------------------------------------------------- Generic functions -------------------------------------------------

#Find tuple items in string (true if any present)
def string_find_any(string, stringTuple, start = 0, end = -1, caseSensitive = False):
    if end < 0: end = len(string)
    if caseSensitive:
        for item in stringTuple:
            if string.find(item, start, end) >= 0: return True
    else:
        string = string.casefold()
        for item in stringTuple:
            if string.find(item.casefold(), start, end) >= 0: return True
    return False

#Find tuple items in string (true if all present)
def string_find_all(string, stringTuple, start = 0, end = -1, caseSensitive = False):
    if end < 0: end = len(string)
    if caseSensitive:
        for item in stringTuple:
            if string.find(item, start, end) < 0: return False
    else:
        string = string.casefold()
        for item in stringTuple:
            if string.find(item.casefold(), start, end) < 0: return False
    return True

#Compare string from strings in a tuple (true if any is equal)
def string_equal(string, stringTuple, caseSensitive = False):
    if string is not None:
        if caseSensitive:
            for item in stringTuple:
                if string == item: return True
        else:
            for item in stringTuple:
                if string.casefold() == item.casefold(): return True
    return False

#Check if string starts with tuple items
def string_startswith(string, prefixTuple, start = 0, end = -1, caseSensitive = False):
    if string is not None:
        if end < 0: end = len(string)
        if caseSensitive:
            for item in prefixTuple:
                if string.startswith(item, start, end): return True
        else:
            string = string.casefold()
            for item in prefixTuple:
                if string.startswith(item.casefold(), start, end): return True
    return False

#Check if string ends with tuple items
def string_endswith(string, prefixTuple, start = 0, end = -1, caseSensitive = False):
    if string is not None:
        if end < 0: end = len(string)
        if caseSensitive:
            for item in prefixTuple:
                if string.endswith(item, start, end): return True
        else:
            string = string.casefold()
            for item in prefixTuple:
                if string.endswith(item.casefold(), start, end): return True
    return False

#Extract enclosed substrings from the string (return source string without substings in element 0 and substrings in subsequent elements)
def string_extract_enclosed(string, enclosure = ['(', ')'], start = 0, end = -1, max_extract = -1, case_sensitive = True):
    if len(enclosure[0]) + len(enclosure[1]) < 2: return [string]
    if end < 0: end = len(string)
    if max_extract < 0: max_extract = len(string)

    if case_sensitive:
        string_cf = string
        enclosure_cf = enclosure
    else:
        string_cf = string.casefold()
        enclosure_cf[0] = enclosure[0].casefold()
        enclosure_cf[1] = enclosure[1].casefold()
    
    result = ['']
    string_start = 0
    enclosure_start = start
    while len(result) < max_extract + 1:
        enclosure_start = string_cf.find(enclosure_cf[0], enclosure_start, end)
        enclosure_end   = string_cf.find(enclosure_cf[1], enclosure_start, end)
        if enclosure_start >= 0 and enclosure_end >= 0 and enclosure_end > enclosure_start:
            result[0] += string[string_start:enclosure_start]
            result.append(string[enclosure_start + 1:enclosure_end])
            string_start = enclosure_end + 1
            enclosure_start = enclosure_end
        else:
            break
    result[0] += string[string_start:]

    return result

#========================================================== END Generic functions =================================================


# ----------------------------------------------------------- Designer functions --------------------------------------------------

#Заполнение данных проекта
def parse_project(data, **kwargs):
    print(' ' * 12 + 'designer: ' +  designer_name + ' (' + script_baseName + ')')
    
    print("INFO >> Defining BoM files", end ="... ", flush = True)
    #определяем BoM-файлы и имена конфигураций
    bomFilePrefix = 'bom'   #в моём случае берём файлы с расширением csv начинающиеся на BoM, а всё что между этим - название конфигурации
    bomFileExt    = 'csv'
    for generatedFile in data.generatedFiles:
        if os.path.splitext(generatedFile)[1].casefold() == os.extsep + bomFileExt.casefold():
            if os.path.basename(generatedFile)[0:3].casefold() == bomFilePrefix.casefold():
                data.BoMs.append(generatedFile)
                data.BoMVariantNames.append((os.path.basename(generatedFile)[len(bomFilePrefix):-len(os.extsep + bomFileExt)]).strip())
    if len(data.BoMs) > 0:
        print('done (' + str(len(data.BoMs)) + ' files)')
    else:
        print("no BoMs found.")

    print("INFO >> Parsing project parameters", end ="... ", flush = True)
    #определяем откуда брать основную надпись
    schematic = data.SchDocs[0]             #в моём случае это самый первый схемный файл проекта
    schematic.read(casefold_keys = True)    #читаем его сворачивая регистр имён параметров

    #с какой-то версии Altium после 17 имена полей стали в CamelCase вместо UPPERCASE
    keys = {'RECORD':'RECORD', 'OWNERPARTID':'OWNERPARTID', 'NAME':'NAME', 'TEXT':'TEXT'}
    #поэтому сворачиваем регистр для сравнения имён полей
    for key in keys:
        keys[key] = keys[key].casefold()

    #читаем нужные поля основной надписи из соответствующих полей схемного файла
    for line in schematic.lines:
        #анализируем словарь параметров
        if keys['RECORD'] in line and keys['OWNERPARTID'] in line and keys['NAME'] in line and keys['TEXT'] in line:
            if line[keys['RECORD']] == '41' and line[keys['OWNERPARTID']] == '-1':
                if   line[keys['NAME']] == 'TitleBlock_01a_DocumentName': data.titleBlock.tb01a_DocumentName += line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_01a_DocumentName_line1': data.titleBlock.tb01a_DocumentName = line[keys['TEXT']] + data.titleBlock.tb01a_DocumentName
                elif line[keys['NAME']] == 'TitleBlock_01a_DocumentName_line2': data.titleBlock.tb01a_DocumentName = data.titleBlock.tb01a_DocumentName + ' ' + line[keys['TEXT']]
                #elif line[keys['NAME']] == 'TitleBlock_01b_DocumentType': data.titleBlock.tb01b_DocumentType += line[keys['TEXT']]
                #elif line[keys['NAME']] == 'TitleBlock_01b_DocumentType_line1': data.titleBlock.tb01b_DocumentType = line[keys['TEXT']] + data.titleBlock.tb01b_DocumentType
                #elif line[keys['NAME']] == 'TitleBlock_01b_DocumentType_line2': data.titleBlock.tb01b_DocumentType =data.titleBlock.tb01b_DocumentType + ' ' + line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_02_DocumentDesignator': data.titleBlock.tb02_DocumentDesignator = line[keys['TEXT']].rsplit(' ', 1)[0]
                elif line[keys['NAME']] == 'TitleBlock_04_Letter_left': data.titleBlock.tb04_Letter_left = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_04_Letter_middle': data.titleBlock.tb04_Letter_middle = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_04_Letter_right': data.titleBlock.tb04_Letter_right = line[keys['TEXT']]
                #elif line[keys['NAME']] == 'TitleBlock_07_SheetNumber': data.titleBlock.tb07_SheetIndex = line[keys['TEXT']]
                #elif line[keys['NAME']] == 'TitleBlock_08_SheetTotal': data.titleBlock.tb08_SheetsTotal = line[keys['TEXT']]        
                elif line[keys['NAME']] == 'TitleBlock_09_Organization': data.titleBlock.tb09_Organization = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_10d_ActivityType_Extra': data.titleBlock.tb10d_ActivityType_Extra = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_11a_Name_Designer': data.titleBlock.tb11a_Name_Designer = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_11b_Name_Checker': data.titleBlock.tb11b_Name_Checker = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_11c_Name_TechnicalSupervisor': data.titleBlock.tb11c_Name_TechnicalSupervisor = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_11d_Name_Extra': data.titleBlock.tb11d_Name_Extra = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_11e_Name_NormativeSupervisor': data.titleBlock.tb11e_Name_NormativeSupervisor = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_11f_Name_Approver': data.titleBlock.tb11f_Name_Approver = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_13a_SignatureDate_Designer': data.titleBlock.tb13a_SignatureDate_Designer = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_13b_SignatureDate_Checker': data.titleBlock.tb13b_SignatureDate_Checker = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_13c_SignatureDate_TechnicalSupervisor': data.titleBlock.tb13c_SignatureDate_TechnicalSupervisor = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_13d_SignatureDate_Extra': data.titleBlock.tb13d_SignatureDate_Extra = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_13e_SignatureDate_NormativeSupervisor': data.titleBlock.tb13e_SignatureDate_NormativeSupervisor = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_13f_SignatureDate_Approver': data.titleBlock.tb13f_SignatureDate_Approver = line[keys['TEXT']]
                #elif line[keys['NAME']] == 'TitleBlock_19_OriginalInventoryNumber': data.titleBlock.tb19_OriginalInventoryNumber = line[keys['TEXT']]
                #elif line[keys['NAME']] == 'TitleBlock_21_ReplacedOriginalInventoryNumber': data.titleBlock.tb21_ReplacedOriginalInventoryNumber = line[keys['TEXT']]
                #elif line[keys['NAME']] == 'TitleBlock_22_DuplicateInventoryNumber': data.titleBlock.tb22_DuplicateInventoryNumber = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_24_BaseDocumentDesignator': data.titleBlock.tb24_BaseDocumentDesignator = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_25_FirstReferenceDocumentDesignator': data.titleBlock.tb25_FirstReferenceDocumentDesignator = line[keys['TEXT']]
    
    #заполняем свойства проекта
    data.designator = data.titleBlock.tb02_DocumentDesignator
    if data.designator.endswith('Э3'): data.designator = data.designator[:-2]
    data.designator = data.designator.strip()
    data.name = data.titleBlock.tb01a_DocumentName
    data.author = data.titleBlock.tb11a_Name_Designer
    print("done.")

#Создание базы данных компонентов из BoM
def parse_components(components, BoM, **kwargs):
    print(' ' * 12 + 'designer: ' +  designer_name + ' (' + script_baseName + ')')

    stats = [0, 0]      #статистика [errors, warnings]

    print("INFO >> Parsing BoM data", end ="... ", flush = True)
    for i in range(len(BoM.entries)):
        component = _parse_component(BoM.entries[i], None, stats)
        if isinstance(component, Components_typeDef.ComponentTypes.Generic):
            components.entries.append(component)
            if component.GENERIC_accessory_child is not None:
                for child in component.GENERIC_accessory_child:
                    components.entries.append(child)
        else:
            stats[0] += 1
            print('\n' + ' ' * 12 + "error: parsing bom entry #" +  str(i) + " failed")
    
    if stats[0] + stats[1] == 0: 
        print('done (' + str(len(components.entries)) + ' components created)')
    else:
        print('\n' + ' ' * 12 + 'completed with ' + str(stats[0]) + ' errors and ' +  str(stats[1]) + ' warnings.')

    designer_check(components)

#разбор компонента
def _parse_component(bom_entry, parent = None, stats = [0, 0], **kwargs):
    decimalPoint = '.'

    #определяем тип элемента
    kind = bom_entry['BOM_type']
    if   string_equal(kind, ("Assembly", "Сборка", "Устройство"), False):
        component = Components_typeDef.ComponentTypes.Assembly()
    elif string_equal(kind, ("Photocell", "Фотоэлемент", "Photodiode", "Фотодиод", "Phototransistor", "Фототранзистор", "Photoresistor", "Фоторезистор"), False):
        component = Components_typeDef.ComponentTypes.Photocell()
    elif string_equal(kind, ("Capacitor", "Конденсатор"), False):
        component = Components_typeDef.ComponentTypes.Capacitor()
    elif string_equal(kind, ("Integrated Circuit", "Микросхема"), False):
        component = Components_typeDef.ComponentTypes.IntegratedCircuit()
    elif string_equal(kind, ("Fastener", "Крепёж"), False):
        component = Components_typeDef.ComponentTypes.Fastener()
    elif string_equal(kind, ("Heatsink", "Радиатор"), False):
        component = Components_typeDef.ComponentTypes.Heatsink()
    elif string_equal(kind, ("Circuit Breaker", "Автоматический выключатель", "Fuse", "Предохранитель"), False):
        component = Components_typeDef.ComponentTypes.CircuitBreaker()
    elif string_equal(kind, ("Surge protector", "Ограничитель перенапряжения", "TVS", "Супрессор", "GDT", "Разрядник", "Varistor", "Варистор"), False):
        component = Components_typeDef.ComponentTypes.SurgeProtector()
    elif string_equal(kind, ("Cell", "Элемент гальванический", "Battery", "Батарея", "Battery holder", "Держатель батареи"), False):
        component = Components_typeDef.ComponentTypes.Battery()
    elif string_equal(kind, ("Display", "Дисплей"), False):
        component = Components_typeDef.ComponentTypes.Display()
    elif string_equal(kind, ("LED", "Светодиод"), False):
        component = Components_typeDef.ComponentTypes.LED()
    elif string_equal(kind, ("Jumper", "Перемычка"), False):
        component = Components_typeDef.ComponentTypes.Jumper()
    elif string_equal(kind, ("Relay", "Реле"), False):
        component = Components_typeDef.ComponentTypes.Relay()
    elif string_equal(kind, ("Inductor", "Индуктивность", "Choke", "Дроссель"), False):
        component = Components_typeDef.ComponentTypes.Inductor()
    elif string_equal(kind, ("Resistor", "Резистор", "Thermistor", "Термистор", "Posistor", "Позистор", "Potentiometer", "Потенциометр", "Rheostat", "Реостат"), False):
        component = Components_typeDef.ComponentTypes.Resistor()
    elif string_equal(kind, ("Switch", "Переключатель", "Выключатель", "Button", "Кнопка"), False):
        component = Components_typeDef.ComponentTypes.Switch()
    elif string_equal(kind, ("Transformer", "Трансформатор"), False):
        component = Components_typeDef.ComponentTypes.Transformer()
    elif string_equal(kind, ("Diode", "Диод", "Zener", "Стабилитрон", "Varicap", "Варикап"), False):
        component = Components_typeDef.ComponentTypes.Diode()
    elif string_equal(kind, ("Thyristor", "Тиристор", "TRIAC", "Symistor", "Симистор", "DIAC", "Dynistor", "Динистор"), False):
        component = Components_typeDef.ComponentTypes.Thyristor()
    elif string_equal(kind, ("Transistor", "Транзистор"), False):
        component = Components_typeDef.ComponentTypes.Transistor()
    elif string_equal(kind, ("Optoisolator", "Оптоизолятор", "Optocoupler", "Оптопара", "Phototriac", "Оптосимистор"), False):
        component = Components_typeDef.ComponentTypes.Optoisolator()
    elif string_equal(kind, ("Connector", "Соединитель", "Разъём"), False):
        component = Components_typeDef.ComponentTypes.Connector()
    elif string_equal(kind, ("EMI filter", "Фильтр ЭМП"), False):
        component = Components_typeDef.ComponentTypes.EMIFilter()
    elif string_equal(kind, ("Crystal", "Resonator", "Резонатор", "Oscillator", "Осциллятор"), False):
        component = Components_typeDef.ComponentTypes.Oscillator()
    else:
        component = Components_typeDef.ComponentTypes.Generic()
    component.GENERIC_kind = kind

    #Fill-in generic attributes
    component.GENERIC_accessory_parent  = parent                            #ссылка на родительский компонент
    
    #--- десигнатор
    if 'Designator' in bom_entry:
        if len(bom_entry['Designator'].strip(' ')) > 0:
            component.GENERIC_designator = bom_entry['Designator']
            if len(component.GENERIC_designator) > 0:
                tmp = component.GENERIC_designator.rsplit('.', 1)
                if len(tmp) > 1:
                    component.GENERIC_designator_channel = tmp[0]
                    tmp = tmp[1]
                else:
                    component.GENERIC_designator_channel = ''
                    tmp = tmp[0]
                component.GENERIC_designator_prefix = ''
                for char in tmp:
                    if not char.isdigit():
                        component.GENERIC_designator_prefix += char
                    else:
                        break
                component.GENERIC_designator_index = int(''.join([s for s in tmp if s.isdigit()]))
    
    #--- номинал
    if 'BOM_value' in bom_entry:
        if len(bom_entry['BOM_value'].strip(' ')) > 0:
            component.GENERIC_value = bom_entry['BOM_value']

    #--- количество
    if 'Quantity' in bom_entry:
        if len(bom_entry['Quantity'].strip(' ')) > 0:
            component.GENERIC_quantity = int(bom_entry['Quantity'])

    #--- производитель
    if 'BOM_manufacturer' in bom_entry:
        if len(bom_entry['BOM_manufacturer'].strip(' ')) > 0:
            component.GENERIC_manufacturer = bom_entry['BOM_manufacturer']
    
    #--- установка на плату
    if 'Fitted' in bom_entry:
        if bom_entry['Fitted'] == 'Not Fitted':
            component.GENERIC_fitted = False
    
    #--- допустимые замены
    if 'BOM_substitute' in bom_entry:
        substitutes = bom_entry['BOM_substitute']
        if len(substitutes) > 0:                                            #проверяем пустое ли поле
            component.GENERIC_substitute = []                                   #создаём пустой список замен чтобы добавлять в него элементы
            substitutes = substitutes.split(';')
            for entry in substitutes:
                tmp = entry.split('*', 1)
                sub_note = None
                if len(tmp) > 1: sub_note = tmp[1].strip(' ')
                tmp = tmp[0].split('@', 1)
                sub_value = tmp[0].strip(' ')
                sub_manufacturer = None
                if len(tmp) > 1: sub_manufacturer = tmp[1].strip(' ')
                component.GENERIC_substitute.append(component.Substitute(sub_value, sub_manufacturer, sub_note))

    #--- явное определение
    if 'BOM_explicit' in bom_entry:
        #есть данные в BoM
        if   string_equal(bom_entry['BOM_explicit'], ('true', 'истина', '1'), False): component.GENERIC_explicit = True
        elif string_equal(bom_entry['BOM_explicit'], ('false', 'ложь', '0'), False): component.GENERIC_explicit = False
        else: component.GENERIC_explicit = True     #значение по-умолчанию если не смогли распознать значение поля
    else:
        #нет данных в BoM
        #legacy: у резисторов и конденсаторов если не указан производитель то задание неявное
        component.GENERIC_explicit = True
        if isinstance(component, (component.types.Resistor, component.types.Capacitor, component.types.Jumper)):
            if component.GENERIC_manufacturer is None: component.GENERIC_explicit = False

    #--- footprint - переводим в package с помощью словаря
    if 'Footprint' in bom_entry:
        for entry in __dict_package:
            for word in __dict_package[entry]:
                if word == bom_entry['Footprint']:
                    component.GENERIC_package = entry
                    break
            if component.GENERIC_package is not None: break

    #--- примечание
    if 'BOM_note' in bom_entry:
        if len(bom_entry['BOM_note'].strip(' ')) > 0:
            component.GENERIC_note = bom_entry['BOM_note']

    #--- описание
    if 'BOM_description' in bom_entry:
        if len(bom_entry['BOM_description'].strip(' ')) > 0:
            component.GENERIC_description = bom_entry['BOM_description']

    #Разбираем параметры из описания
    if component.GENERIC_description is None: descriptionParams = ['']
    else: descriptionParams = [s.strip() for s in component.GENERIC_description.split(',')]

    #Сборка (Устройство)
    if type(component) is component.types.Assembly:
        pass

    #Фотоэлемент
    elif type(component) is component.types.Photocell:
        pass

    #Конденсатор
    elif type(component) is component.types.Capacitor:
        #legacy: затычка для старого формата где у чипов нет ',' после типа конденсатора (впоследствии надо убрать)
        tmp = descriptionParams[0].replace('керам. ', 'керам., ')
        tmp = tmp.replace('тантал. ', 'тантал., ')
        tmp = tmp.split(', ')
        if len(tmp) > 1:
            descriptionParams[0] = tmp[0]
            descriptionParams.insert(1, tmp[1])

        #legacy: затычка для старого формата где ёмкость и допуск в разных параметрах
        for j in range(len(descriptionParams)):
            if descriptionParams[j].endswith('Ф') and j < len(descriptionParams) - 1:
                if descriptionParams[j + 1].endswith('%'):
                    descriptionParams[j] += ' ±' + descriptionParams.pop(j + 1).replace('±', '')
                break

        #Parsing params
        for j in range(len(descriptionParams)):
            #тип конденсатора
            if component.CAP_type is None:
                if string_equal(descriptionParams[j], ('керамический', 'керам.'), False):
                    component.CAP_type = component.Type.CERAMIC
                elif string_equal(descriptionParams[j], ('танталовый', 'тантал.'), False):
                    component.CAP_type = component.Type.TANTALUM
                elif string_equal(descriptionParams[j], ('плёночный', 'плён.'), False):
                    component.CAP_type = component.Type.FILM
                elif string_equal(descriptionParams[j], ('ионистор', 'суперконд.'), False):
                    component.CAP_type = component.Type.SUPERCAPACITOR
                elif string_find_any(descriptionParams[j], ('алюминиевый', 'алюм.'), False):
                    if string_find_any(descriptionParams[j], ('электролитический', 'эл-лит'), False):
                        component.CAP_type = component.Type.ALUM_ELECTROLYTIC
                    elif string_find_any(descriptionParams[j], ('полимерный', 'полим.'), False):
                        component.CAP_type = component.Type.ALUM_POLYMER
                    else:
                        component.CAP_type = component.Type.UNKNOWN
                #завершаем обработку если нашли нужный параметр
                if component.CAP_type is not None:   
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            #тип монтажа и типоразмер
            if component.GENERIC_mount is None:
                if _parse_param_mountandsize(descriptionParams[j], component):
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            #тип диэлектрика (температурный коэффициент)
            if component.CAP_dielectric is None:
                #керамические
                if component.CAP_type == component.Type.CERAMIC:
                    if string_equal(descriptionParams[j], ('COG', 'C0H', 'C0J', 'C0K', 'CCG', 'CGJ', 'M5U', 'NP0', 'P90', 'U2J', 'U2K', 'UNJ', 'X0U', 'X5R', 'X5S', 'X6S', 'X6T','X7R', 'X7S', 'X7T', 'X7U', 'X8G', 'X8L', 'X8M', 'X8R', 'X9M', 'Y5E', 'Y5P', 'Y5R', 'Y5U', 'Y5V', 'Z5U', 'Z7S', 'ZLM'), True):
                        component.CAP_dielectric = descriptionParams[j]
                #плёночные
                elif component.CAP_type == component.Type.FILM:
                    if string_equal(descriptionParams[j], ('PC', 'PEN', 'PET', 'PPS', 'PP', 'PS'), True):
                        component.CAP_dielectric = descriptionParams[j]
                #завершаем обработку если нашли нужный параметр
                if component.CAP_dielectric is not None:   
                    descriptionParams[j] = '' #clear parsed parameter
                    continue
            
            parsing_result = _parse_param_valueWithTolerance(descriptionParams[j], decimalPoint)
            if parsing_result is not None:
                #ёмкость
                if component.CAP_capacitance is None:
                    if string_equal(parsing_result[0][1], ('F', 'Ф'), True):
                        component.CAP_capacitance = parsing_result[0][0]
                        #допуск
                        if parsing_result[1] is not None:
                            component.CAP_tolerance = parsing_result[1]
                        else:
                            component.flag = component.FlagType.ERROR
                            stats[0] += 1
                            print('\n' + ' ' * 12 + 'error! ' + component.GENERIC_designator + ' - tolerance absent or can not be parsed', end = '', flush = True)
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #напряжение
                if component.CAP_voltage is None:
                    if string_equal(parsing_result[0][1], ('V', 'В'), True):
                        component.CAP_voltage = parsing_result[0][0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

            #низкий импеданс
            if string_equal(descriptionParams[j], ("low ESR", "низк. имп."), False):
                component.CAP_lowImpedance = True
                descriptionParams[j] = '' #clear parsed parameter
                continue

            #сборка
            parsing_result = _parse_param_array(descriptionParams[j])
            if parsing_result is not None:
                component.GENERIC_array = parsing_result
                descriptionParams[j] = '' #clear parsed parameter
                continue

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
        #Parsing params
        for j in range(len(descriptionParams)):
            #тип предохранителя
            if component.CBRK_type is None:
                if string_equal(descriptionParams[j], ('fuse', 'плавкий'), False):
                    component.CBRK_type = component.Type.FUSE
                elif string_equal(descriptionParams[j], ('PTC resettable', 'самовосстанавливающийся', 'самовосст.'), False):
                    component.CBRK_type = component.Type.FUSE_PTC_RESETTABLE
                elif string_equal(descriptionParams[j], ('thermal', 'термо'), False):
                    component.CBRK_type = component.Type.FUSE_THERMAL
                elif string_equal(descriptionParams[j], ('circuit breaker', 'авт. выкл.'), False):
                    component.CBRK_type = component.Type.BREAKER
                elif string_equal(descriptionParams[j], ('holder', 'держатель'), False):
                    component.CBRK_type = component.Type.HOLDER
                #завершаем обработку если нашли нужный параметр
                if component.CBRK_type is not None:   
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            #тип монтажа и типоразмер
            if component.GENERIC_mount is None:
                if _parse_param_mountandsize(descriptionParams[j], component):
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            parsing_result = _parse_param_valueWithTolerance(descriptionParams[j], decimalPoint)
            if parsing_result is not None:
                #номинальный ток
                if component.CBRK_current_rating is None:
                    if string_equal(parsing_result[0][1], ('A', 'А')):
                        component.CBRK_current_rating = parsing_result[0][0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #напряжение
                if component.CBRK_voltage is None:
                    if string_equal(parsing_result[0][1], ('V', 'В'), True):
                        component.CBRK_voltage = parsing_result[0][0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #точка плавления
                if component.CBRK_meltingPoint is None:
                    if string_equal(parsing_result[0][1], ('A²s', 'А²с', 'A?s', 'А?с'), True): #костыли для неюникода
                        component.CBRK_meltingPoint = parsing_result[0][0]
                        #фикс неюникода
                        component.GENERIC_description = component.GENERIC_description.replace('A?s', 'A²s')
                        component.GENERIC_description = component.GENERIC_description.replace('А?с', 'А²с')
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

            #классификация скорости срабатывания
            if component.CBRK_speed_grade is None:
                if string_equal(descriptionParams[j], ('fast', 'быстрый', 'быстр.'), False):
                    component.CBRK_speed_grade = component.SpeedGrade.FAST
                elif string_equal(descriptionParams[j], ('medium', 'средний', 'средн.'), False):
                    component.CBRK_speed_grade = component.SpeedGrade.MEDIUM
                elif string_equal(descriptionParams[j], ('slow', 'медленный', 'медл.'), False):
                    component.CBRK_speed_grade = component.SpeedGrade.SLOW
                #завершаем обработку если нашли нужный параметр
                if component.CBRK_speed_grade is not None:   
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

    #Ограничитель перенапряжения
    elif type(component) is component.types.SurgeProtector:
        #Определяем тип по разновидности компонента
        if string_equal(component.GENERIC_kind, ("TVS", "Супрессор"), False):
            component.SPD_type = component.Type.DIODE
        elif string_equal(component.GENERIC_kind, ("Varistor", "Варистор"), False):
            component.SPD_type = component.Type.VARISTOR
        elif string_equal(component.GENERIC_kind, ("GDT", "Разрядник"), False):
            component.SPD_type = component.Type.GAS_DISCHARGE_TUBE

        #Parsing params
        for j in range(len(descriptionParams)):
            #тип монтажа и типоразмер
            if component.GENERIC_mount is None:
                if _parse_param_mountandsize(descriptionParams[j], component):
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            #ток гашения выброса
            if component.SPD_clamping_current is None:
                parsing_result = _parse_param_valueWithToleranceAtConditions(descriptionParams[j], decimalPoint)
                if parsing_result is not None:
                    if string_equal(parsing_result[0][1], ('A', 'А'), True):
                        component.SPD_clamping_current = parsing_result[0][0]
                        if component.SPD_testPulse is None and parsing_result[2] is not None:
                            conditions = parsing_result[2][0].replace(' ', '')
                            if string_equal(conditions, ('8/20us', '8/20мкс'), False):
                                component.SPD_testPulse = component.TestPulse.US_8_20
                            elif  string_equal(conditions, ('10/1000us', '10/1000мкс'), False):
                                component.SPD_testPulse = component.TestPulse.US_10_1000
                            else:
                                component.SPD_testPulse = component.TestPulse.UNKNOWN
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

            #диод
            if component.SPD_type == component.Type.DIODE:
                #направленность
                if component.SPD_bidirectional is None:
                    if string_equal(descriptionParams[j], ('однонаправленный', 'однонаправ.'), False):
                        component.SPD_bidirectional = False
                    elif string_equal(descriptionParams[j], ('двунаправленный', 'двунаправ.'), False):
                        component.SPD_bidirectional = True
                    #завершаем обработку если нашли нужный параметр
                    if component.SPD_bidirectional is not None:   
                        descriptionParams[j] = '' #clear parsed parameter
                        continue

                parsing_result = _parse_param_valueWithToleranceAtConditions(descriptionParams[j], decimalPoint)
                if parsing_result is not None:
                    #максимальное рабочее напряжение
                    if component.SPD_standoff_voltage is None:
                        if string_equal(parsing_result[0][1], ('V', 'В'), True):
                            component.SPD_standoff_voltage = parsing_result[0][0]
                            #clear parsed parameter and go to next param
                            descriptionParams[j] = ''
                            continue

                    #мощность
                    if component.SPD_power is None:
                        if string_equal(parsing_result[0][1], ('W', 'Вт'), True):
                            component.SPD_power = parsing_result[0][0]
                            if component.SPD_testPulse is None and parsing_result[2] is not None:
                                conditions = parsing_result[2][0].replace(' ', '')
                                if string_equal(conditions, ('8/20us', '8/20мкс'), False):
                                    component.SPD_testPulse = component.TestPulse.US_8_20
                                elif  string_equal(conditions, ('10/1000us', '10/1000мкс'), False):
                                    component.SPD_testPulse = component.TestPulse.US_10_1000
                                else:
                                    component.SPD_testPulse = component.TestPulse.UNKNOWN
                            #clear parsed parameter and go to next param
                            descriptionParams[j] = ''
                            continue


            #варистор
            elif component.SPD_type == component.Type.VARISTOR:
                parsing_result = _parse_param_valueWithToleranceAtConditions(descriptionParams[j], decimalPoint)
                if parsing_result is not None:
                    #максимальное рабочее напряжение
                    if component.SPD_standoff_voltage is None:
                        if string_equal(parsing_result[0][1], ('V', 'В'), True):
                            component.SPD_standoff_voltage = parsing_result[0][0]
                            #clear parsed parameter and go to next param
                            descriptionParams[j] = ''
                            continue

                    #энергия
                    if component.SPD_energy is None:
                        if string_equal(parsing_result[0][1], ('J', 'Дж'), True):
                            component.SPD_energy = parsing_result[0][0]
                            #clear parsed parameter and go to next param
                            descriptionParams[j] = ''
                            continue

            #газоразрядник
            elif component.SPD_type == component.Type.GAS_DISCHARGE_TUBE:
                pass

            #сборка
            parsing_result = _parse_param_array(descriptionParams[j])
            if parsing_result is not None:
                component.GENERIC_array = parsing_result
                descriptionParams[j] = '' #clear parsed parameter
                continue

    #Батарея
    elif type(component) is component.types.Battery:
        #Определяем тип по разновидности компонента
        if string_equal(component.GENERIC_kind, ("Battery holder", "Держатель батареи"), False):
            component.BAT_type = component.Type.HOLDER
        elif string_equal(component.GENERIC_kind, ("Cell", "Элемент гальванический"), False):
            component.BAT_type = component.Type.CELL
        elif string_equal(component.GENERIC_kind, ("Battery", "Батарея"), False):
            component.BAT_type = component.Type.BATTERY
    
        #Parsing params
        for j in range(len(descriptionParams)):
            #тип (ищем признак держателя в описании)
            if component.BAT_type != component.Type.HOLDER:
                if string_equal(descriptionParams[j], ('holder', 'держатель'), False):
                    component.BAT_type = component.Type.HOLDER
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            #диапазон рабочих температур
            if component.GENERIC_temperature_range is None:
                parsing_result = _parse_param_temperatureRange(descriptionParams[j], decimalPoint)
                if parsing_result is not None:
                    component.GENERIC_temperature_range = parsing_result
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            parsing_result = _parse_param_valueWithToleranceAtConditions(descriptionParams[j], decimalPoint)
            if parsing_result is not None:
                #номинальное напряжение
                if component.BAT_voltage_rated is None:
                    if string_equal(parsing_result[0][1], ('V', 'В'), True):
                        component.BAT_voltage_rated = parsing_result[0][0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #ёмкость
                if component.BAT_capacity is None:
                    if string_equal(parsing_result[0][1], ('Ah', 'Ач'), True):
                        component.BAT_capacity = parsing_result[0][0]
                        #допуск
                        #if parsing_result[1] is not None:
                        #    component.BAT_capacity_tolerance = parsing_result[1]
                        #условия измерения
                        if parsing_result[2] is not None:
                            for k in range(len(parsing_result[2])):
                                condition = _parse_param_value(parsing_result[2][k], decimalPoint)
                                if condition is not None:
                                    #ток нагрузки
                                    if string_equal(condition[1], ('A', 'А'), True):
                                        component.BAT_capacity_load_current = condition[0]
                                        parsing_result[2][k] = ''
                                        continue
                                    #сопротивление нагрузки
                                    if string_equal(condition[1], ('Ohm', 'Ом'), True):
                                        component.BAT_capacity_load_resistance = condition[0]
                                        parsing_result[2][k] = ''
                                        continue
                                    #напряжение отсечки
                                    if string_equal(condition[1], ('V', 'В'), True):
                                        component.BAT_capacity_voltage = condition[0]
                                        parsing_result[2][k] = ''
                                        continue
                                    #температура
                                    if string_equal(condition[1], ('°C', '℃', 'K', 'К'), True):
                                        component.BAT_capacity_temperature = _parse_param_temperature(condition, decimalPoint)
                                        parsing_result[2][k] = ''
                                        continue
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

    #Дисплей
    elif type(component) is component.types.Display:
        #Parsing params
        for j in range(len(descriptionParams)):
            #тип
            if component.DISP_type is None:
                if string_equal(descriptionParams[j], ('7-seg', '7-сегм.', '7 segment'), False):
                    component.DISP_type = component.Type.NUMERIC_7SEG
                elif string_equal(descriptionParams[j], ('14-seg', '14-сегм.', '14 segment'), False): 
                    component.DISP_type = component.Type.ALPHANUMERIC_14SEG
                elif string_equal(descriptionParams[j], ('16-seg', '16-сегм.', '16 segment'), False): 
                    component.DISP_type = component.Type.ALPHANUMERIC_16SEG
                elif string_equal(descriptionParams[j], ('bar graph', 'шкальный'), False): 
                    component.DISP_type = component.Type.BARGRAPH
                elif string_equal(descriptionParams[j], ('dot matrix', 'матричный'), False): 
                    component.DISP_type = component.Type.DOTMATRIX
                elif string_equal(descriptionParams[j], ('graphic', 'графический'), False): 
                    component.DISP_type = component.Type.GRAPHIC
                #завершаем обработку если нашли нужный параметр
                if component.DISP_type is not None:   
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            #структура
            if component.DISP_structure is None:
                if string_equal(descriptionParams[0], ('LED', 'светодиодный'), False):
                    component.DISP_structure = component.Structure.LED
                elif string_equal(descriptionParams[0], ('OLED', 'орг. светодиодный'), False):
                    component.DISP_structure = component.Structure.OLED
                elif string_equal(descriptionParams[0], ('LCD', 'жидкокрист.'), False):
                    component.DISP_structure = component.Structure.LCD
                elif string_equal(descriptionParams[0], ('VFD', 'вак. люм.'), False):
                    component.DISP_structure = component.Structure.VFD
                #завершаем обработку если нашли нужный параметр
                if component.DISP_structure is not None:   
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            #цвет
            if component.DISP_color is None:
                parsing_result = _parse_param_color(descriptionParams[j])
                if parsing_result is not None:
                    component.DISP_color = parsing_result
                    #clear parsed parameter and go to next param
                    descriptionParams[j] = ''
                    continue

            #сборка
            parsing_result = _parse_param_array(descriptionParams[j])
            if parsing_result is not None:
                component.GENERIC_array = parsing_result
                descriptionParams[j] = '' #clear parsed parameter
                continue

    #Светодиод
    elif type(component) is component.types.LED:
        #Parsing params
        for j in range(len(descriptionParams)):
            #тип монтажа и типоразмер
            if component.GENERIC_mount is None:
                if _parse_param_mountandsize(descriptionParams[j], component):
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            #цвет
            if component.LED_color is None:
                parsing_result = _parse_param_color(descriptionParams[j])
                if parsing_result is not None:
                    component.LED_color = parsing_result
                    #clear parsed parameter and go to next param
                    descriptionParams[j] = ''
                    continue

            #индекс цветопередачи
            if component.LED_color_renderingIndex is None:
                if descriptionParams[j].startswith('CRI'):
                    parsing_result = _parse_param_value(descriptionParams[j][3:], decimalPoint)
                    if parsing_result is not None:
                        component.LED_color_renderingIndex = parsing_result[0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

            parsing_result = _parse_param_valueWithToleranceAtConditions(descriptionParams[j], decimalPoint)
            if parsing_result is not None:
                #длина волны
                if (component.LED_color is None) or (component.LED_color <= component.Color.VIOLET):
                    if (component.LED_wavelength_peak is None) and (component.LED_wavelength_dominant is None):
                        if string_equal(parsing_result[0][1], ('m', 'м'), True):
                            if isinstance(parsing_result[0][0], list):
                                component.LED_wavelength_peak = parsing_result[0][0][0]
                                component.LED_wavelength_dominant = parsing_result[0][0][1]
                            else:
                                component.LED_wavelength_peak = parsing_result[0][0]
                            #clear parsed parameter and go to next param
                            descriptionParams[j] = ''
                            continue

                #цветовая температура
                if component.LED_color == component.Color.WHITE:
                    if component.LED_color_temperature is None:
                        if string_equal(parsing_result[0][1], ('K', 'К'), True):
                            component.LED_color_temperature = parsing_result[0][0]
                            #clear parsed parameter and go to next param
                            descriptionParams[j] = ''
                            continue
                    
                #сила света
                if component.LED_luminous_intensity is None:
                    if string_equal(parsing_result[0][1], ('cd', 'кд'), True):
                        component.LED_luminous_intensity = parsing_result[0][0]
                        if parsing_result[2] is not None:
                            conditions = _parse_param_value(parsing_result[2][0], decimalPoint)
                            if conditions is not None:
                                if string_equal(conditions[1], ('A', 'А'), True):
                                    component.LED_luminous_intensity_current = conditions[0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #световой поток
                if component.LED_luminous_flux is None:
                    if string_equal(parsing_result[0][1], ('lm', 'лм'), True):
                        component.LED_luminous_flux = parsing_result[0][0]
                        if parsing_result[2] is not None:
                            conditions = _parse_param_value(parsing_result[2][0], decimalPoint)
                            if conditions is not None:
                                if string_equal(conditions[1], ('A', 'А'), True):
                                    component.LED_luminous_flux_current = conditions[0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #угол обзора
                if component.LED_viewingAngle is None:
                    if string_equal(parsing_result[0][1], ('°', 'degrees', 'град.'), True):
                        component.LED_viewingAngle = parsing_result[0][0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #прямой ток
                if (component.LED_current_nominal is None) and (component.LED_current_maximum is None):
                    if string_equal(parsing_result[0][1], ('A', 'А'), True):
                        if isinstance(parsing_result[0][0], list):
                            component.LED_current_nominal = parsing_result[0][0][0]
                            component.LED_current_maximum = parsing_result[0][0][1]
                        else:
                            component.LED_current_nominal = parsing_result[0][0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #прямое падение напряжения
                if component.LED_voltage_forward is None:
                    if string_equal(parsing_result[0][1], ('V', 'В'), True):
                        component.LED_voltage_forward = parsing_result[0][0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

            #сборка
            parsing_result = _parse_param_array(descriptionParams[j])
            if parsing_result is not None:
                component.GENERIC_array = parsing_result
                descriptionParams[j] = '' #clear parsed parameter
                continue

    #Перемычка
    elif type(component) is component.types.Jumper:
        #Parsing params
        for j in range(len(descriptionParams)):
            #тип
            if component.JMP_type is None:
                if string_equal(descriptionParams[j], ('thermal', 'термо'), False):
                    component.JMP_type = component.Type.THERMAL
                    descriptionParams[j] = '' #clear parsed parameter
                    continue
                else: 
                    component.JMP_type = component.Type.ELECTRICAL

            #тип монтажа и типоразмер
            if component.GENERIC_mount is None:
                if _parse_param_mountandsize(descriptionParams[j], component):
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

    #Реле
    elif type(component) is component.types.Relay:
        pass

    #Индуктивность
    elif type(component) is component.types.Inductor:
        #Определяем тип
        if string_equal(component.GENERIC_kind, ("Inductor", "Индуктивность"), False):
            component.IND_type = component.Type.INDUCTOR
        elif string_equal(component.GENERIC_kind, ("Choke", "Дроссель"), False):
            component.IND_type = component.Type.CHOKE

        #legacy: затычка для старого формата где ёмкость и допуск в разных параметрах
        for j in range(len(descriptionParams)):
            if descriptionParams[j].endswith('Гн') and j < len(descriptionParams) - 1:
                if descriptionParams[j + 1].endswith('%'):
                    descriptionParams[j] += ' ±' + descriptionParams.pop(j + 1).replace('±', '')
                break

        #Parsing params
        for j in range(len(descriptionParams)):
            #тип монтажа и типоразмер
            if component.GENERIC_mount is None:
                if _parse_param_mountandsize(descriptionParams[j], component):
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            parsing_result = _parse_param_valueWithTolerance(descriptionParams[j], decimalPoint)
            if parsing_result is not None:
                #индуктивность
                if component.IND_inductance is None:
                    if string_equal(parsing_result[0][1], ('H', 'Гн'), True):
                        component.IND_inductance = parsing_result[0][0]
                        #допуск
                        if parsing_result[1] is not None:
                            component.IND_tolerance = parsing_result[1]
                        else:
                            component.flag = component.FlagType.ERROR
                            stats[0] += 1
                            print('\n' + ' ' * 12 + 'error! ' + component.GENERIC_designator + ' - tolerance absent or can not be parsed', end = '', flush = True)
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #ток
                if component.IND_current is None:
                    if string_equal(parsing_result[0][1], ('A', 'А'), True):
                        component.IND_current = parsing_result[0][0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

    #Резистор
    elif type(component) is component.types.Resistor:
        #legacy: затычка для старого формата где сопротивление и допуск в разных параметрах
        for j in range(len(descriptionParams)):
            if descriptionParams[j].endswith('Ом') and j < len(descriptionParams) - 1:
                if descriptionParams[j + 1].endswith('%'):
                    descriptionParams[j] += ' ±' + descriptionParams.pop(j + 1).replace('±', '')
                break
        
        #тип
        if string_equal(component.GENERIC_kind, ("Resistor", "Резистор"), False):
            component.RES_type = component.Type.FIXED
        elif string_equal(component.GENERIC_kind, ("Potentiometer", "Потенциометр", "Rheostat", "Реостат"), False):
            component.RES_type = component.Type.VARIABLE
        elif string_equal(component.GENERIC_kind, ("Thermistor", "Термистор", "Posistor", "Позистор"), False):
            component.RES_type = component.Type.THERMAL

        #Parsing params
        for j in range(len(descriptionParams)):
            #структура
            if component.RES_structure is None:
                if string_equal(descriptionParams[0], ('тонкоплёночный', 'тонкоплён.'), False):
                    component.RES_structure = component.Structure.THIN_FILM
                elif string_equal(descriptionParams[0], ('толстоплёночный', 'толстоплён.'), False):
                    component.RES_structure = component.Structure.THICK_FILM
                elif string_equal(descriptionParams[0], ('металло-плёночный', 'мет-плён.'), False):
                    component.RES_structure = component.Structure.METAL_FILM
                elif string_equal(descriptionParams[0], ('углеродистый', 'углерод.'), False):
                    component.RES_structure = component.Structure.CARBON_FILM
                elif string_equal(descriptionParams[0], ('проволочный', 'провол.'), False):
                    component.RES_structure = component.Structure.WIREWOUND
                elif string_equal(descriptionParams[0], ('керамический', 'керам.'), False):
                    component.RES_structure = component.Structure.CERAMIC
                #завершаем обработку если нашли нужный параметр
                if component.RES_structure is not None:   
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            #тип монтажа и типоразмер
            if component.GENERIC_mount is None:
                if _parse_param_mountandsize(descriptionParams[j], component):
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            parsing_result = _parse_param_valueWithTolerance(descriptionParams[j], decimalPoint)
            if parsing_result is not None:
                #сопротивление
                if component.RES_resistance is None:
                    if string_equal(parsing_result[0][1], ('Ohm', 'Ом'), True):
                        component.RES_resistance = parsing_result[0][0]
                        #допуск
                        if parsing_result[1] is not None:
                            component.RES_tolerance = parsing_result[1]
                        elif component.RES_resistance == 0:
                            pass #если сопротивление равно нулю (т.е. перемычка) то допуск добавлять не надо и это не ошибка
                        else:
                            component.flag = component.FlagType.ERROR
                            stats[0] += 1
                            print('\n' + ' ' * 12 + 'error! ' + component.GENERIC_designator + ' - tolerance absent or can not be parsed', end = '', flush = True)
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #ТКС
                if component.RES_temperature_coefficient is None:
                    if parsing_result[1] is not None:
                        if string_equal(parsing_result[1][2], ('ppm/°C', ), True):
                            component.RES_temperature_coefficient = parsing_result[1]
                            #clear parsed parameter and go to next param
                            descriptionParams[j] = ''
                            continue

                #напряжение
                if component.RES_voltage is None:
                    if string_equal(parsing_result[0][1], ('V', 'В'), True):
                        component.RES_voltage = parsing_result[0][0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #мощность
                if component.RES_power is None:
                    if string_equal(parsing_result[0][1], ('W', 'Вт'), True):
                        component.RES_power = parsing_result[0][0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

            #сборка
            parsing_result = _parse_param_array(descriptionParams[j])
            if parsing_result is not None:
                component.GENERIC_array = parsing_result
                descriptionParams[j] = '' #clear parsed parameter
                continue

        #добавляем мощность к чип-резисторам (если не указана)
        #if component.GENERIC_mount == component.Mounting.Type.SURFACE and component.RES_power is None:
        #    if   component.GENERIC_size == '0075': component.RES_power = 0.02
        #    elif component.GENERIC_size == '0100': component.RES_power = 0.03125
        #    elif component.GENERIC_size == '0201': component.RES_power = 0.05
        #    elif component.GENERIC_size == '0402': component.RES_power = 0.0625
        #    elif component.GENERIC_size == '0603': component.RES_power = 0.1
        #    elif component.GENERIC_size == '0805': component.RES_power = 0.125
        #    elif component.GENERIC_size == '1206': component.RES_power = 0.25
        #    elif component.GENERIC_size == '1210': component.RES_power = 0.5
        #    elif component.GENERIC_size == '1218': component.RES_power = 1.0
        #    elif component.GENERIC_size == '2010': component.RES_power = 0.75
        #    elif component.GENERIC_size == '2512': component.RES_power = 1.0

    #Переключатель
    elif type(component) is component.types.Switch:
        pass

    #Трансформатор
    elif type(component) is component.types.Transformer:
        #Parsing params
        for j in range(len(descriptionParams)):
            #сборка
            parsing_result = _parse_param_array(descriptionParams[j])
            if parsing_result is not None:
                component.GENERIC_array = parsing_result
                descriptionParams[j] = '' #clear parsed parameter
                continue

    #Диод
    elif type(component) is component.types.Diode:
        #Определяем тип по разновидности компонента
        if string_equal(component.GENERIC_kind, ("Zener", "Стабилитрон"), False):
            component.DIODE_type = component.Type.ZENER
        elif string_equal(component.GENERIC_kind, ("Varicap", "Варикап"), False):
            component.DIODE_type = component.Type.VARICAP
    
        #Parsing params
        for j in range(len(descriptionParams)):
            #тип диода
            if component.DIODE_type is None:
                if string_equal(descriptionParams[j], ("general purpose", "общего применения", "общ. прим."), False):
                    component.DIODE_type = component.Type.GENERAL_PURPOSE
                elif string_equal(descriptionParams[j], ("Шоттки", "Schottky"), False):
                    component.DIODE_type = component.Type.SCHOTTKY
                elif string_equal(descriptionParams[j], ("tunnel", "туннельный", ), False):
                    component.DIODE_type = component.Type.TUNNEL
                #завершаем обработку если нашли нужный параметр
                if component.DIODE_type is not None:   
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            parsing_result = _parse_param_valueWithToleranceAtConditions(descriptionParams[j], decimalPoint)
            if parsing_result is not None:
                #прямой ток
                if component.DIODE_forwardCurrent is None:
                    if string_equal(parsing_result[0][1], ('A', 'А'), True):
                        component.DIODE_forwardCurrent = parsing_result[0][0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #обратное напряжение
                if component.DIODE_reverseVoltage is None:
                    if string_equal(parsing_result[0][1], ('V', 'В'), True):
                        component.DIODE_reverseVoltage = parsing_result[0][0]
                        #допуск
                        if parsing_result[1] is not None:
                            component.DIODE_reverseVoltage_tolerance = parsing_result[1]
                        else:
                            if component.DIODE_type is component.Type.ZENER:
                                component.flag = component.FlagType.ERROR
                                stats[0] += 1
                                print('\n' + ' ' * 12 + 'error! ' + component.GENERIC_designator + ' - tolerance absent or can not be parsed', end = '', flush = True)
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #максимальная мощность
                if component.DIODE_power is None:
                    if string_equal(parsing_result[0][1], ('W', 'Вт'), True):
                        component.DIODE_power = parsing_result[0][0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #ёмкость перехода
                if component.DIODE_capacitance is None:
                    if string_equal(parsing_result[0][1], ('F', 'Ф'), True):
                        component.DIODE_capacitance = parsing_result[0][0]
                        #допуск
                        if parsing_result[1] is not None:
                            component.EMIF_capacitance_tolerance = parsing_result[1]
                        #условия измерения
                        if parsing_result[2] is not None:
                            for k in range(len(parsing_result[2])):
                                condition = _parse_param_value(parsing_result[2][k], decimalPoint)
                                if condition is not None:
                                    #напряжение
                                    if string_equal(condition[1], ('V', 'В'), True):
                                        component.DIODE_capacitance_voltage = condition[0]
                                        parsing_result[2][k] = ''
                                        continue
                                    #частота
                                    if string_equal(condition[1], ('Hz', 'Гц'), True):
                                        component.DIODE_capacitance_frequency = condition[0]
                                        parsing_result[2][k] = ''
                                        continue
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

            #сборка
            parsing_result = _parse_param_array(descriptionParams[j])
            if parsing_result is not None:
                component.GENERIC_array = parsing_result
                descriptionParams[j] = '' #clear parsed parameter
                continue

    #Тиристор
    elif type(component) is component.types.Thyristor:
        pass

    #Транзистор
    elif type(component) is component.types.Transistor:
        #Parsing params
        for j in range(len(descriptionParams)):
            #сборка
            parsing_result = _parse_param_array(descriptionParams[j])
            if parsing_result is not None:
                component.GENERIC_array = parsing_result
                descriptionParams[j] = '' #clear parsed parameter
                continue

    #Оптоизолятор
    elif type(component) is component.types.Optoisolator:
        #Определяем тип по разновидности компонента
        if string_equal(component.GENERIC_kind, ("Optocoupler", "Оптопара"), False):
            component.OPTOISO_outputType = component.OutputType.TRANSISTOR
        elif string_equal(component.GENERIC_kind, ("Phototriac", "Оптосимистор"), False):
            component.OPTOISO_outputType = component.OutputType.TRIAC

    #Соединитель
    elif type(component) is component.types.Connector:
        #Parsing params
        for j in range(len(descriptionParams)):
            #пол
            if component.CON_gender is None:
                if string_equal(descriptionParams[j], ('plug', 'вилка', 'male', 'папа'), False):
                    component.CON_gender = component.Gender.PLUG
                elif string_equal(descriptionParams[j], ('receptacle', 'socket', 'розетка', 'female', 'мама'), False):
                    component.CON_gender = component.Gender.RECEPTACLE
                #завершаем обработку если нашли нужный параметр
                if component.CON_gender is not None:   
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

    #Фильтр ЭМП
    elif type(component) is component.types.EMIFilter:
        #Parsing params
        for j in range(len(descriptionParams)):
            #тип фильтра
            if component.EMIF_type is None:
                if string_equal(descriptionParams[0], ('ферритовая бусина', 'фер. бус.'), False):
                    component.EMIF_type = component.Type.FERRITE_BEAD
                elif string_equal(descriptionParams[0], ('синфазный дроссель', 'синф. дроссель', 'синф. др.'), False):
                    component.EMIF_type = component.Type.COMMON_MODE_CHOKE
                #завершаем обработку если нашли нужный параметр
                if component.EMIF_type is not None:   
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            #тип монтажа и типоразмер
            if component.GENERIC_mount is None:
                if _parse_param_mountandsize(descriptionParams[j], component):
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            parsing_result = _parse_param_valueWithToleranceAtConditions(descriptionParams[j], decimalPoint)
            if parsing_result is not None:
                #импеданс
                if component.EMIF_impedance is None:
                    if parsing_result[2] is not None:
                        conditions = _parse_param_value(parsing_result[2][0], decimalPoint)
                        if conditions is not None:
                            if string_equal(conditions[1], ('Hz', 'Гц'), True):
                                if string_equal(parsing_result[0][1], ('Ohm', 'Ом'), True):
                                    component.EMIF_impedance = parsing_result[0][0]
                                    component.EMIF_impedance_frequency = conditions[0]
                                    #допуск
                                    if parsing_result[1] is not None:
                                        component.EMIF_impedance_tolerance = parsing_result[1]
                                    else:
                                        component.flag = component.FlagType.ERROR
                                        stats[0] += 1
                                        print('\n' + ' ' * 12 + 'error! ' + component.GENERIC_designator + ' - tolerance absent or can not be parsed', end = '', flush = True)
                                    #clear parsed parameter and go to next param
                                    descriptionParams[j] = ''
                                    continue

                #индуктивность
                if component.EMIF_inductance is None:
                    if string_equal(parsing_result[0][1], ('H', 'Гн'), True):
                        component.EMIF_inductance = parsing_result[0][0]
                        #допуск
                        if parsing_result[1] is not None:
                            component.EMIF_inductance_tolerance = parsing_result[1]
                        else:
                            component.flag = component.FlagType.ERROR
                            stats[0] += 1
                            print('\n' + ' ' * 12 + 'error! ' + component.GENERIC_designator + ' - tolerance absent or can not be parsed', end = '', flush = True)
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #ток
                if component.EMIF_current is None:
                    if string_equal(parsing_result[0][1], ('A', 'А'), True):
                        component.EMIF_current = parsing_result[0][0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #напряжение
                if component.EMIF_voltage is None:
                    if string_equal(parsing_result[0][1], ('V', 'В'), True):
                        component.EMIF_voltage = parsing_result[0][0]
                        #clear parsed parameter and go to next param
                        descriptionParams[j] = ''
                        continue

                #активное сопротивление
                if component.EMIF_resistance is None:
                    if string_equal(parsing_result[2][0], ("DC", )):
                        if string_equal(parsing_result[0][1], ('Ohm', 'Ом'), True):
                            component.EMIF_resistance = parsing_result[0][0]
                            #clear parsed parameter and go to next param
                            descriptionParams[j] = ''
                            continue
            
    #Осциллятор (Резонатор)
    elif type(component) is component.types.Oscillator:
        #Определяем тип по разновидности компонента
        if string_equal(component.GENERIC_kind, ("Oscillator", "Осциллятор"), False):
            component.OSC_type = component.Type.OSCILLATOR
        elif string_equal(component.GENERIC_kind, ("Resonator", "Резонатор", ), False):
            component.OSC_type = component.Type.RESONATOR
        
        #Parsing params
        for j in range(len(descriptionParams)):
            #тип резонатора
            if component.OSC_structure is None:
                if string_equal(descriptionParams[j], ('кварцевый', 'кварц.'), False):
                    component.OSC_structure = component.Structure.QUARTZ
                elif string_equal(descriptionParams[j], ('керамический', 'керам.'), False):
                    component.OSC_structure = component.Structure.CERAMIC
                #завершаем обработку если нашли нужный параметр
                if component.OSC_structure is not None:   
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            #тип монтажа и типоразмер (поидее не надо, но пусть будет)
            if component.GENERIC_mount is None:
                if _parse_param_mountandsize(descriptionParams[j], component):
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            #диапазон рабочих температур
            if component.GENERIC_temperature_range is None:
                parsing_result = _parse_param_temperatureRange(descriptionParams[j], decimalPoint)
                if parsing_result is not None:
                    component.GENERIC_temperature_range = parsing_result
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

            parsing_result = _parse_param_valueWithTolerance(descriptionParams[j], decimalPoint)
            if parsing_result is not None:
                if parsing_result[0] is not None:
                    #частота и допуск
                    if component.OSC_frequency is None:
                        if string_equal(parsing_result[0][1], ('Hz', 'Гц'), True):
                            component.OSC_frequency = parsing_result[0][0]
                            #допуск
                            if parsing_result[1] is not None:
                                component.OSC_tolerance = parsing_result[1]
                            else:
                                component.flag = component.FlagType.ERROR
                                stats[0] += 1
                                print('\n' + ' ' * 12 + 'error! ' + component.GENERIC_designator + ' - tolerance absent or can not be parsed', end = '', flush = True)
                            #clear parsed parameter and go to next param
                            descriptionParams[j] = ''
                            continue

                    #ёмкость нагрузки
                    if component.OSC_loadCapacitance is None:
                        if string_equal(parsing_result[0][1], ('F', 'Ф'), True):
                            component.OSC_loadCapacitance = parsing_result[0][0]
                            #clear parsed parameter and go to next param
                            descriptionParams[j] = ''
                            continue

                    #эквивалентное последовательное сопротивление
                    if component.OSC_ESR is None:
                        if string_equal(parsing_result[0][1], ('Ohm', 'Ом'), True):
                            component.OSC_ESR = parsing_result[0][0]
                            #clear parsed parameter and go to next param
                            descriptionParams[j] = ''
                            continue

                    #уровень возбуждения
                    if component.OSC_driveLevel is None:
                        if string_equal(parsing_result[0][1], ('W', 'Вт'), True):
                            component.OSC_driveLevel = parsing_result[0][0]
                            #clear parsed parameter and go to next param
                            descriptionParams[j] = ''
                            continue
                else:
                    #стабильность частоты
                    if component.OSC_frequency is not None:
                        if parsing_result[1] is not None:
                            if parsing_result[1][2] is None:
                                component.OSC_stability = parsing_result[1]
                                #clear parsed parameter and go to next param
                                descriptionParams[j] = ''
                                continue

            #гармоника
            if component.OSC_overtone is None:
                if string_equal(descriptionParams[j], ('фунд.', 'fundamental'), False):
                    component.OSC_overtone = 1
                elif string_equal(descriptionParams[j], ('3 гарм.', '3rd overtone'), False):
                    component.OSC_overtone = 3
                #завершаем обработку если нашли нужный параметр
                if component.OSC_overtone is not None:   
                    descriptionParams[j] = '' #clear parsed parameter
                    continue

    #Неопознанный элемент
    else:
        pass

    #Move remaining unparsed parameters to misc array
    for param in descriptionParams:
        if len(param) > 0: component.GENERIC_misc.append(param)

    #--- сопутсвующие компоненты
    if 'BOM_accessory' in bom_entry:
        accessories = bom_entry['BOM_accessory']
        if len(accessories) > 0:                                            #проверяем пустое ли поле
            component.GENERIC_accessory_child = []                              #создаём пустой список чтобы добавлять в него элементы
            accessories = accessories.split(';')
            for accessory in accessories:
                accessory_bom = {
                    'Designator': "",
                    'BOM_type': "",
                    'BOM_value': "",
                    'BOM_description': "",
                    'BOM_manufacturer': "",
                    'BOM_explicit': "",
                    'BOM_substitute': "",
                    'BOM_note': "",
                    'Footprint': "",
                    'Quantity': "1",
                    'Fitted': "Fitted",
                    'BOM_accessory': ""
                    }
                
                accessory = string_extract_enclosed(accessory, ['(', ')'], 0, -1, 1, True)
                if len(accessory) > 1: accessory_bom['BOM_description'] = accessory[1].strip(' ')
                accessory = accessory[0]

                accessory = string_extract_enclosed(accessory, ['[', ']'], 0, -1, 1, True)
                if len(accessory) > 1: accessory_bom['BOM_substitute'] = accessory[1].strip(' ')
                accessory = accessory[0]

                if '*' in accessory:
                    accessory = accessory.split('*', 1)
                    accessory_bom['BOM_note'] = accessory[1].strip(' ')
                    accessory = accessory[0]

                if '#' in accessory:
                    accessory = accessory.split('#', 1)
                    accessory_bom['Quantity'] = accessory[1].strip(' ')
                    accessory = accessory[0]

                if '^' in accessory:
                    accessory = accessory.split('^', 1)
                    accessory_bom['BOM_explicit'] = accessory[1].strip(' ')
                    accessory = accessory[0]

                if '@' in accessory:
                    accessory = accessory.split('@', 1)
                    accessory_bom['BOM_manufacturer'] = accessory[1].strip(' ')
                    accessory = accessory[0]

                if ':' in accessory:
                    accessory = accessory.split(':', 1)
                    accessory_bom['BOM_type'] = accessory[0].strip(' ')
                    accessory_bom['BOM_value'] = accessory[1].strip(' ')
                else: 
                    accessory_bom['BOM_value'] = accessory
                    stats[0] += 1
                    print('error')

                accessory_component = _parse_component(accessory_bom, component, stats)
                accessory_component.GENERIC_quantity *= component.GENERIC_quantity          #количество дочернего компонента умножается на количество родительского
                component.GENERIC_accessory_child.append(accessory_component)

    return component

#разбор параметра: тип монтажа и типоразмер
def _parse_param_mountandsize(param, component):
    if string_find_any(param, ('чип', )):
        component.GENERIC_mount = component.Mounting.Type.SURFACE
    elif string_find_any(param, ('выводной', )):
        component.GENERIC_mount = component.Mounting.Type.THROUGHHOLE
    elif string_find_any(param, ('аксиальный', 'акс.')):
        component.GENERIC_mount = component.Mounting.Type.THROUGHHOLE
        component.GENERIC_THtype = component.Mounting.ThroughHole.AXIAL
    elif string_find_any(param, ('радиальный', 'рад.')):
        component.GENERIC_mount = component.Mounting.Type.THROUGHHOLE
        component.GENERIC_THtype = component.Mounting.ThroughHole.RADIAL
    
    if component.GENERIC_mount is not None:
        tmp = param.rsplit(' ', 1)
        if len(tmp) > 1:
            component.GENERIC_size = tmp[1]
        return True
    else:
        return False

#разбор параметра: значение с указанием допуска при условиях
def _parse_param_valueWithToleranceAtConditions(param, decimalPoint = '.'):
    if param is not None:
        #удаляем пробелы с краёв
        param = param.strip(' ')
        
        #проверяем есть ли что-нибудь
        if len(param.replace(' ', '')) > 0:
            valueToleranceAndConditions = param.split('@', 1)
            valueAndTolerance = _parse_param_valueWithTolerance(valueToleranceAndConditions[0], decimalPoint)            
            if len(valueToleranceAndConditions) > 1:
                conditions = valueToleranceAndConditions[1].split('&')
                for i in range(len(conditions)):
                    conditions[i] = conditions[i].strip(' ')
            else:
                conditions = None

            if valueAndTolerance is not None:
                valueAndTolerance.append(conditions)
                return valueAndTolerance
            elif valueAndTolerance is not None:
                return [None, None, conditions]

        return None

#разбор параметра: значение с указанием допуска
def _parse_param_valueWithTolerance(param, decimalPoint = '.'):
    if param is not None:
        #удаляем все пробелы
        param = param.replace(' ', '')
        
        #проверяем есть ли что-нибудь
        if len(param) > 0:
            valueAndTolerance = _parse_param_splitValueAndTolerance(param)
            value = _parse_param_value(valueAndTolerance[0], decimalPoint)
            tolerance = _parse_param_tolerance(valueAndTolerance[1], decimalPoint)
            if (value is not None) or (tolerance is not None):
                return [value, tolerance]

    return None

#разбор параметра: разделение значения и его допуска
def _parse_param_splitValueAndTolerance(param):
    if param is not None:
        #удаляем пробелы с краёв
        param = param.strip(' ')
        
        #проверяем осталось ли что-нибудь
        if len(param) > 0:
            #смотрим указан ли знак у значения
            if param.startswith('+') or param.startswith('-'):
                #знак указан - сохраняем его и отрезаем от параметра
                sign = param[0:1]
                param = param[1:]
            else:
                #знак не указан
                sign = ''

            #определяем тип записи допуска
            plusmn_pos = param.find('±')
            hellip_pos = param.find('…')
            if plusmn_pos == 0:
                #допуск указан, одинаковый в обе стороны, самой величины нет
                value = None
                tolerance = param[plusmn_pos:].strip(' ')
            elif plusmn_pos > 0:
                #допуск указан, одинаковый в обе стороны, есть какая-то величина
                value = sign + param[0:plusmn_pos].strip(' ')
                tolerance = param[plusmn_pos:].strip(' ')
            elif hellip_pos > 0:
                #допуск указан, разный в + и -
                sign_pos_p = param.find('+')
                sign_pos_n = param.find('-')
                if sign_pos_p >= 0 and sign_pos_n >= 0:
                    #чётко указан где + и где -
                    sign_pos = min(sign_pos_p, sign_pos_n)
                    value = sign + param[0:sign_pos].strip(' ')
                    tolerance = param[sign_pos:].strip(' ')
                else:
                    #нехватает знака
                    if len(sign) > 0:
                        #знак ушёл вначале, делаем вывод что был только допуск
                        value = None
                        tolerance = sign + param
                    else:
                        #какая-то ошибка
                        value = None
                        tolerance = None
            else:
                #допуск не указан
                value = sign + param
                tolerance = None

            return [value, tolerance]
    return None

#разбор параметра: значение
def _parse_param_value(param, decimalPoint = '.'):
    if param is not None:
        #удаляем все пробелы
        param = param.replace(' ', '')
        
        #проверяем осталось ли что-нибудь
        if len(param) > 0:
            #меняем десятичный разделитель на точку
            param = param.replace(decimalPoint, '.')
            
            #определяем знак
            if param[0:1] == '+':
                #знак явно задан: положительное значение
                sign = 1
                param = param[1:]
            elif param[0:1] == '-':
                #знак явно задан: отрицательное значение
                sign = -1
                param = param[1:]
            else:
                #знак не задан: предполагаем положительное значение
                sign = 1
            
            #разделяем многозначный параметр
            param = param.split('/')

            #разделяем значение и единицы измерения
            number = ''
            prefixedunit = ''
            pos = 0
            while pos < len(param[-1]):
                char = param[-1][pos]
                #проверяем является ли символ числом или десятичным разделителем
                if char.isdecimal() or char == '.':
                    #является - добавляем его к числу
                    number += number.join(char)
                else:
                    #не является - записываем оставшуюся часть параметра в единицы измерения
                    prefixedunit = param[-1][pos:]
                    break
                pos += 1
            param[-1] = number

            #разделяем префикс и единицу измерения, определяем множитель
            multiplier = 1
            prefix     = ''
            unit       = prefixedunit
            if unit == 'мкд': unit = 'кд'; multiplier = 1e-3
            else:
                problematic_units = ('m', 'м', 'Гн', 'Гц', 'T', 'Тл', 'ppm', 'ppb', 'кд')
                for entry in problematic_units:
                    if entry == unit: break
                else:
                    dict_prefixes = {
                        1e-15: ('f', 'ф'),
                        1e-12: ('p', 'п'),  #проблема с ppm:'ppm'
                        1e-09: ('n', 'н'),
                        1e-06: ('u', 'мк', 'μ'), #проблема с милликанделами:'мкд'
                        1e-03: ('m', 'м'),  #проблема с метрами:'m/м'
                        1e00:  ('E', ),
                        1e+03: ('k', 'к'),  #проблема с канделами:'кд'
                        1e+06: ('M', 'М'),
                        1e+09: ('G', 'Г'),  #проблема с Генри:'Гн', Герц:'Гц'
                        1e+12: ('T', 'Т'),  #проблема с Тесла:'T/Тл'
                        1e+15: ('P', 'П')
                    }
                    for entry in dict_prefixes:
                        for prfx in dict_prefixes[entry]:
                            if prefixedunit.startswith(prfx):
                                prefix = prfx
                                multiplier = entry
                                unit = prefixedunit[len(prefix):]
                                break
                        if multiplier != 1: break

            #проверяем на ошибки и пытаемся конвертировать значение
            value = []
            for number in param:
                if len(number) == 0:
                    return None 
                else:
                    try:
                        value.append(sign * float(number) * multiplier)
                    except ValueError:
                        return None 
            if len(unit) == 0:
                unit = None

            if len(value) == 1: return [value[0], unit]     #однозначное значение
            else:               return [value, unit]        #многозначное значение
    return None

#разбор параметра: допуск
def _parse_param_tolerance(param, decimalPoint = '.', convertParts = True):
    if param is not None:
        #удаляем все пробелы
        param = param.replace(' ', '')
        
        #проверяем осталось ли что-нибудь
        if len(param) > 0:
            #меняем десятичный разделитель на точку
            param = param.replace(decimalPoint, '.')
            
            #разделяем значение и единицы измерения
            value = ''
            units = ''
            pos = 0
            while pos < len(param):
                char = param[pos]
                #проверяем является ли символ числом, десятичным разделителем или спецсимволом
                if char.isdecimal() or char == '.' or char == '±' or char == '+' or char == '-' or char == '…':
                    #является - добавляем его к значению
                    value += char
                else:
                    #не является - записываем оставшуюся часть параметра в единицы измерения
                    units = param[pos:]
                    break
                pos += 1

            #конвертируем доли если надо
            multiplier = 1e0
            if convertParts:
                #определяем единицы измерения
                if units == '%': 
                    multiplier = 1e-2
                    units = None
                elif units == '‰':
                    multiplier = 1e-3
                    units = None
                elif units == 'ppm':
                    multiplier = 1e-6
                    units = None
                elif units == 'ppb':
                    multiplier = 1e-9
                    units = None

            #определяем формат записи
            if value.startswith('±'):
                #одинаковый допуск в обе стороны (задано явно)
                value = value[1:] #убираем символ и попадаем в неявный обработчик
            elif value.find('…') > 0:
                #разный допуск в + и -
                tolerance = value.split('…')
                
                try:
                    tolerance[0] = float(tolerance[0]) * multiplier
                    tolerance[1] = float(tolerance[1]) * multiplier
                except ValueError:
                    return None
                
                #определяем где какая сторона
                if tolerance[0] == 0 and tolerance[1] == 0:
                    return None                             #обе стороны равны 0 - ошибка
                if tolerance[0] >= 0 and tolerance[1] <= 0:
                    return [tolerance[1], tolerance[0], units]     #+…-
                if tolerance[0] <= 0 and tolerance[1] >= 0:
                    return [tolerance[0], tolerance[1], units]     #-…+
                else:
                    return None                             #оба значения либо положительные либо отрицательные - ошибка
            #одинаковая в обе стороны (без указания '±' - задана неявно)
            try:
                tolerance = float(value) * multiplier
            except ValueError:
                return None
            return [-tolerance, tolerance, units]
    
    return None

#разбор параметра: температура
def _parse_param_temperature(param, decimalPoint = '.'):
    if isinstance(param, str): param = _parse_param_value(param, decimalPoint)
    
    if param is not None:
        if len(param) == 2:
            if   string_equal(param[1], ('°C', '℃'), True): offset = 273.15
            elif string_equal(param[1], ('K', 'К'), True):   offset = 0
            else: return None

            try: value = float(param[0]) + offset
            except ValueError: return None

            if value >= 0: return value             #если меньше абсолютного нуля то что-то пошло не так
    return None

#разбор параметра: температурный диапазон
def _parse_param_temperatureRange(param, decimalPoint = '.'):
    if param is not None:
        #удаляем все пробелы
        param = param.replace(' ', '')           

        #проверяем осталось ли что-нибудь
        if len(param) > 0:
            param = param.replace(decimalPoint, '.')     #меняем десятичный разделитель на точку
            param = param.replace('°C', '℃')            #меняем ANSI комбинацию на Unicode символ
            param = param.replace('К', 'K')              #меняем кириллический кельвин на латниский
            if param.endswith('℃'): offset = 273.15
            elif param.endswith('K'): offset = 0
            else: offset = None

            if (offset is not None) and (param.find('…') > 0):
                #есть все нужные признаки температурного диапазона
                #удаляем единицы измерения
                param = param[0:-1]

                #разбиваем диапазон
                value = param.split('…')
                
                try:
                    value[0] = float(value[0]) + offset
                    value[1] = float(value[1]) + offset
                except ValueError:
                    return None
                
                #если меньше абсолютного нуля то что-то пошло не так
                if min(value[0], value[1]) >= 0:
                    #определяем где какая сторона
                    if value[0] > value[1]: return [value[1], value[0]]     #+…-
                    return [value[0], value[1]]                             #-…+
    return None

#разбор параметра: сборка
def _parse_param_array(param):
    if string_startswith(param, ("array", "сборка"), False):
        asm_blocks = 0
        asm_elements = 0
        asm_type = Components_typeDef.ComponentTypes.Generic.ArrayType.UNKNOWN
        
        param = param.split(' ', 1)
        if len(param) > 1:
            #тип
            asm_formula = param[1].replace(' ', '')
            asm_type = ''
            pos = len(asm_formula) - 1
            while pos >= 0:
                char = asm_formula[pos]
                if char.isdecimal(): break
                asm_type = char + asm_type
                pos -= 1
            asm_formula = asm_formula[0:len(asm_formula) - len(asm_type)]
            if   string_equal(asm_type, ('I', 'IND'), True): asm_type = Components_typeDef.ComponentTypes.Generic.ArrayType.INDEPENDENT
            elif string_equal(asm_type, ('A', 'CA' ), True): asm_type = Components_typeDef.ComponentTypes.Generic.ArrayType.COMMON_ANODE
            elif string_equal(asm_type, ('C', 'CC' ), True): asm_type = Components_typeDef.ComponentTypes.Generic.ArrayType.COMMON_CATHODE
            elif string_equal(asm_type, ('S', 'SER'), True): asm_type = Components_typeDef.ComponentTypes.Generic.ArrayType.SERIES
            elif string_equal(asm_type, ('P', 'PAR'), True): asm_type = Components_typeDef.ComponentTypes.Generic.ArrayType.PARALLEL
            elif string_equal(asm_type, ('M', 'MTX'), True): asm_type = Components_typeDef.ComponentTypes.Generic.ArrayType.MATRIX
            else:                                            asm_type = Components_typeDef.ComponentTypes.Generic.ArrayType.UNKNOWN

            #количество элементов
            asm_formula = asm_formula.replace('.', 'x')
            asm_formula = asm_formula.split('x')
            if len(asm_formula) == 2:
                try:
                    asm_blocks = int(asm_formula[0])
                    asm_elements = int(asm_formula[1])
                except ValueError:
                    return None
            else:
                try:
                    asm_elements = int(asm_formula[0])
                except ValueError:
                    return None
                if asm_elements > 0:
                    asm_blocks = 1

        return [asm_blocks, asm_elements, asm_type]    
    return None

#разбор параметра: цвет
def _parse_param_color(param):
    if len(param) > 0:
        if string_equal(param, ('white', 'белый'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.WHITE
        elif string_equal(param, ('red', 'красный'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.RED
        elif string_equal(param, ('orange', 'оранжевый'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.ORANGE
        elif string_equal(param, ('amber', 'янтарный'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.AMBER
        elif string_equal(param, ('yellow', 'жёлтый'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.YELLOW
        elif string_equal(param, ('lime', 'салатовый'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.LIME
        elif string_equal(param, ('green', 'зелёный'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.GREEN
        elif string_equal(param, ('turquoise', 'бирюзовый'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.TURQUOISE
        elif string_equal(param, ('cyan', 'голубой'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.CYAN
        elif string_equal(param, ('blue', 'синий'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.BLUE
        elif string_equal(param, ('violet', 'фиолетовый'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.VIOLET
        elif string_equal(param, ('purple', 'пурпурный'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.PURPLE
        elif string_equal(param, ('pink', 'розовый'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.PINK
        elif string_equal(param, ('infrared', 'инфракрасный'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.INFRARED
        elif string_equal(param, ('ultraviolet', 'ультрафиолетовый'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.ULTRAVIOLET
        elif string_equal(param, ('multicolor', 'многоцветный'), False):
            return Components_typeDef.ComponentTypes.Generic.Color.MULTI
    return None

#Проверка базы данных компонентов
def designer_check(components):
    print("INFO >> Checking data", end ="... ")
    
    warnings = 0
    errors = 0

    #проверяем чтобы у одинаковых номиналов одного типа элементов были одинаковые остальные поля
    for i in range(len(components.entries)):
        for j in range(i+1, len(components.entries)):
            if components.entries[i].GENERIC_kind == components.entries[j].GENERIC_kind:
                if components.entries[i].GENERIC_value == components.entries[j].GENERIC_value and (components.entries[i].GENERIC_description != components.entries[j].GENERIC_description or components.entries[i].GENERIC_package != components.entries[j].GENERIC_package):
                    components.entries[i].flag = components.entries[i].FlagType.WARNING
                    components.entries[j].flag = components.entries[j].FlagType.WARNING
                    print('\n' + ' ' * 12 + 'warning! ' + str(components.entries[i].GENERIC_designator) + ' | ' + str(components.entries[j].GENERIC_designator)  + ' - data mismatch', end = '')
                    warnings += 1

    #проверяем соответствие типоразмера в описании и корпуса для определённых типов компонентов
    for component in components.entries:
        flag_packageSizeMismatch = False
        if type(component) is components.ComponentTypes.Resistor:
            if component.GENERIC_mount == component.Mounting.Type.SURFACE:
                if component.GENERIC_size != component.GENERIC_package:
                    flag_packageSizeMismatch = True
        elif type(component) is components.ComponentTypes.Capacitor:
            if component.CAP_type == component.Type.ALUM_ELECTROLYTIC or component.CAP_type == component.Type.ALUM_POLYMER:
                flag_packageSizeMismatch = True
                if string_endswith(component.GENERIC_size, ('mm', 'мм'), caseSensitive = True) and component.GENERIC_package is not None:
                    size = component.GENERIC_size[0:-2].replace(' ', '').replace(',', '.').replace('*', '×').split('×')
                    package = component.GENERIC_package.replace(' ', '').replace(',', '.').replace('*', '×').split('×')
                    if len(size) == len(package):
                        for i in range(len(size)):
                            try:
                                if float(size[i]) != float(package[i]): break
                            except ValueError:
                                break
                        else:
                            flag_packageSizeMismatch = False
            elif component.GENERIC_mount == component.Mounting.Type.SURFACE:
                if component.GENERIC_size != component.GENERIC_package:
                    flag_packageSizeMismatch = True
        if flag_packageSizeMismatch:
            component.flag = component.FlagType.ERROR
            print('\n' + ' ' * 12 + 'error! ' + str(component.GENERIC_designator) + ' - size and package mismatch', end = '', flush = True)
            errors += 1

    #проверяем пустые поля в допустимых заменах
    for component in components.entries:
        flag_emptySubsituteData = False
        if component.GENERIC_substitute is not None:
            for entry in component.GENERIC_substitute:
                if entry.value is not None:
                    if len(entry.value.strip(' ')) == 0: flag_emptySubsituteData = True
                else:
                    flag_emptySubsituteData = True
                if entry.manufacturer is not None:
                    if len(entry.manufacturer.strip(' ')) == 0: flag_emptySubsituteData = True
                if entry.note is not None:
                    if len(entry.note.strip(' ')) == 0: flag_emptySubsituteData = True
        if flag_emptySubsituteData:
            component.flag = component.FlagType.WARNING
            print('\n' + ' ' * 12 + 'warning! ' + component.GENERIC_designator + ' - empty fields in substitute data', end = '', flush = True)
            warnings += 1

    if warnings + errors == 0: 
        print("ok.")  
    else:
        print('\n' + ' ' * 12 + 'completed: ' + str(errors) + ' errors, ' +  str(warnings) + ' warnings.')

#========================================================== END Designer functions =================================================

# --------------------------------------------------------------- Dictionaties -----------------------------------------------------
#Словарь корпус - посадочное место
__dict_package = { #запятые на концах чтобы запись с одним значением воспринималась как массив значений, а не массив символов в строке
    #чипы
    '0201': ('MLCC_0201', 'RC_0201', 'FB_0201'),
    '0402': ('MLCC_0402', 'RC_0402', 'LC_0402-0.50', 'FB_0402', 'LEDC_0402-0.50'),
    '0603': ('MLCC_0603', 'SFCC_0603', 'RC_0603', 'LC_0603-1.00', 'FB_0603', 'FC_0603', 'LEDC_0603', 'LEDC_0603-0.75'),
    '0606': ('LEDC_0606-0.50_3IND', ),
    '0805': ('MLCC_0805', 'SFCC_0805', 'RC_0805', 'LC_0805-1.25', 'FB_0805', 'FC_0805', 'LEDC_0805', 'LEDC_0805-0.75', 'LEDC_0805-0.45_2IND'),
    '0806': ('LC_0806-1.60', ),
    '1008': ('LC_1008-2.00', ),
    '1206': ('MLCC_1206', 'SFCC_1206', 'RC_1206', 'LC_1206-1.60', 'FB_1206', 'FC_1206', 'LEDC_1206', 'LEDC_1206-1.80D_2IND'),
    '1209': ('LEDC_1209-2.40', 'LEDC_1209-2.40D_2IND'),
    '1210': ('MLCC_1210', 'SFCC_1210', 'RC_1210', 'LC_1210-2.50', 'FB_1210'),
    '1218': ('RC_1218', ),
    '1808': ('MLCC_1808', ),
    '1812': ('MLCC_1812', 'LC_1812-3.20', 'FB_1812'),
    '1913': ('SFCC_1913', ),
    '2010': ('RC_2010', ),
    '2211': ('MLCC_2211', ),
    '2220': ('MLCC_2220', 'VC_2220'),
    '2225': ('MLCC_2225', ),
    '2410': ('FC_2410', ),
    '2416': ('SFCC_2416', ),
    '2512': ('RC_2512', ),
    'A': ('CCM_3216-18 (A)', ),
    'B': ('CCM_3528-21 (B)', ),
    'C': ('CCM_6032-28 (C)', ),
    'D': ('CCM_7343-31 (D)', ),
    'E': ('CCM_7260-38 (E)', ),
    'X': ('CCM_7343-43 (X)', ),
    #конденсаторы
    '5×6':     ('CAP_RSMD_5.0x6.0', ),
    '5×11':    ('CAP_RTH_05x11-2.0-0.5', ),
    '5×7':     ('CAP_RSMD_5.0x7.0', ),
    '6×12':    ('CAP_RTH_06x12-2.5-0.5', ),
    '6.3×5.7': ('CAP_RSMD_6.3x5.7', ),
    '6.3×7':   ('CAP_RSMD_6.3x7.0', ),
    '6.3×8':   ('CAP_RSMD_6.3x8.0', ),
    '6.3×9.7': ('CAP_RSMD_6.3x9.7', ),
    '8×6.7':   ('CAP_RSMD_8.0x6.7', ),
    '8×7':     ('CAP_RSMD_8.0x7.0', ),
    '8×7.5':   ('CAP_RSMD_8.0x7.5', ),
    '8×9.7':   ('CAP_RSMD_8.0x9.7', ),
    '8×12':    ('CAP_RTH_08x12-3.5-0.6', ),
    '8×12.2':  ('CAP_RSMD_8.0x12.2', ),
    '10×10.2': ('CAP_RSMD_10.0x10.2', ),
    '10×12':   ('CAP_RTH_10x12-5.0-0.6', ),
    '10×12.2': ('CAP_RSMD_10.0x12.2', ),
    '10×12.6': ('CAP_RSMD_10.0x12.6', ),
    '10×16':   ('CAP_RTH_10x16-5.0-0.6', ),
    '10×19':   ('CAP_RTH_10x19-5.0-0.6', 'CAP_RTH_10x19-5.0-0.6_H'),
    '13×20':   ('CAP_RTH_13x20-5.0-0.6', 'CAP_RTH_13x20-5.0-0.6_H'),
    '18×36':   ('CAP_RTH_18x36-7.5-0.8', ),
    '18×60':   ('CAP_RTH_18x60-7.5-1.0', 'CAP_RTH_18x60-7.5-1.0_H', 'CAP_RTH_18x60-7.5-1.0_HR1.5', 'CAP_RTH_18x60-7.5-1.0_HR3.0', 'CAP_RTH_18x60-7.5-1.0_HR4.5'),
    '20×40':   ('CAP_RTH_20x40-10-0.8', 'CAP_RTH_20x40-10-0.8_H', 'CAP_RTH_20x40-10-0.8_HR1.5', 'CAP_RTH_20x40-10-0.8_HR4.5'),
    #резонаторы/осцилляторы
    '2-SMD (3215)': ('2-SMD_3215-0.9', ),
    '2-SMD (5032)': ('2-SMD_5032-1.1', ),
    '4-SMD (2520)': ('4-SMD_2520-0.55', ),
    '4-SMD (3225)': ('4-SMD_3225-0.75', '4-SMD_3225-1.20'),
    '4-SMD (5032)': ('4-SMD_5032-1.1', ),
    '4-SMD (7050)': ('4-SMD_7050-1.30', ),
    'HC-49/US': ('HC-49/US', ),
    'HC-49/US-SMD': ('HC-49/US-SMD', ),
    #диоды/транзисторы/мелкие микросхемы
    'SMA': ('DO-214AC (SMA)', ),
    'SMB': ('DO-214AA (SMB)', ),
    'SMC': ('DO-214AB (SMC)', ),
    'SOD-80': ('SOD-80', ),
    'SOD-123': ('SOD-123', ),
    'SOD-123F': ('SOD-123F', ),
    'SOD-323': ('SOD-323', ),
    'SOD-323F': ('SOD-323F', ),
    'SOD-523F': ('SOD-523F', ),
    'TO-92': ('TO-92-V', ),
    'TO-220': ('TO-220-V', ),
    'TO-220AB': ('TO-220AB-H', 'TO-220AB-V'),
    'TO-247AC': ('TO-247AC-V', ),
    'TO-269AA': ('TO-269AA', ),
    'DPAK': ('TO-252 (DPAK)', ),
    'D²PAK': ('TO-263AB (D2PAK)', ),
    'SOT-5': ('SOT-5', ),
    'SOT-23': ('SOT-23', 'SOT-23-3', ),
    'SOT-23-5': ('SOT-23-5', ),
    'SOT-23-6': ('SOT-23-6', ),
    'SOT-23-8': ('SOT-23-8', ),
    'SOT-89': ('SOT-89', ),
    'SOT-143': ('SOT-143', ),
    'SOT-223': ('SOT-223', ),
    'SOT-223-6': ('SOT-223-6', ),
    'SOT-323': ('SOT-323', 'SOT-323-3', ),
    'SOT-323-5': ('SOT-323-5', ),
    'SOT-323-6': ('SOT-323-6', ),
    'SOT-416': ('SOT-416', ),
    #микросхемы - DIP
    'DIP-4': ('DIP-4', ),
    'DIP-6': ('DIP-6', ),
    'DIP-8': ('DIP-8', ),
    #микросхемы - SOIC
    'SO-8': ('SO-8', 'SO-8-EP', 'SO-8 optocoupler', ),
    'SO-8W': ('SO-8W', ),
    'SO-14': ('SO-14', ),
    'SO-16': ('SO-16', ),
    'SO-16W': ('SO-16W', ),
    'SO-16W-IC': ('SO-16W-IC', ),
    'SO-20W': ('SO-20W', ),
    'SO-20W-IC': ('SO-20W-IC', ),
    'SO-24W': ('SO-24W', ),
    #микросхемы - SOP
    'SOP-28W': ('SOP-28W', ),
    #микросхемы - TSOP
    'TSOP-II-54': ('TSOP2-54', ),
    #микросхемы - TSSOP
    'TSSOP-8': ('TSSOP-8', 'TSSOP-8_3.0x3.0-0.65-4.0', 'TSSOP-8_3.0x3.0-0.65-4.9', 'TSSOP-8_4.4x3.0-0.65'),
    'TSSOP-14': ('TSSOP-14', 'HTSSOP-14'),
    'TSSOP-16': ('TSSOP-16', ),
    'TSSOP-20': ('TSSOP-20', ),
    'TSSOP-24': ('TSSOP-24', ),
    'TSSOP-28': ('TSSOP-28', 'HTSSOP-28'),
    'TSSOP-56': ('TSSOP-56', ),
    #микросхемы - SSOP
    'SSOP-8': ('SSOP-8', ),
    'SSOP-16': ('SSOP-16', ),
    'SSOP-28': ('SSOP-28', ),
    #микросхемы - MSOP
    'MSOP-8': ('MSOP-8', 'MSOP-8-EP'),
    'MSOP-10': ('MSOP-10', ),
    'MSOP-16': ('MSOP-16', 'MSOP-16(12)-2.4.13.15'),
    #микросхемы - VSSOP
    'VSSOP-8': ('VSSOP-8_2.3x2.0-0.50', 'VSSOP-8_3.0x3.0-0.65', ),
    #микросхемы - uSOP
    'uSOP-10': ('uSOP-10', ),
    #микросхемы - QSOP
    'QSOP-20': ('QSOP-20', ),
    'QSOP-24': ('QSOP-24', ),
    #микросхемы - QFP
    'LQFP-48': ('LQFP-48', ),
    'LQFP-64': ('LQFP-64', 'LQFP-64-EP5.00'),
    'LQFP-100': ('LQFP-100', ),
    'LQFP-144': ('LQFP-144', 'LQFP-144-EP7.20'),
    'LQFP-256': ('LQFP-144', 'LQFP-256-EP9.40'),
    'TQFP-32': ('TQFP-32', 'HTQFP-32'),
    'TQFP-44': ('TQFP-44', ),
    'TQFP-64': ('TQFP-64', ),
    'TQFP-128': ('TQFP-128-EP10.0', ),
    #микросхемы - DFN
    'DFN': ('MSDFN-16_10.0x13.0x3.1-1.27', 'MSDFN-16_10.0x14.0x3.1-1.27', 'MSDFN-20_10.0x13.0x3.1-1.27', 'MSDFN-20_10.0x14.0x3.1-1.27'), #MORNSUN isolators
    'DFN-10': ('DFN-10_3.0x3.0-0.50', ),
    'TDFN-8': ('TDFN-8_2.0x2.0-0.50', 'TDFN-8_3.0x3.0-0.65'),
    'UFDFN-10': ('UFDFN-10_1.0x2.5-0.50', ),
    'WDFN-6': ('WDFN-6_2.0x2.0-0.65', ),
    #микросхемы - QFN
    'QFN-16': ('QFN-16_3.0x3.0-0.50', ),
    'MQFN-88': ('MQFN-88_10.0x10.0-0.40', ),
    'SQFN-48': ('SQFN-48_7.0x7.0-0.50', ),
    'VQFN-16': ('VQFN-16_4.0x4.0-0.65', ),
    'VQFN-20': ('VQFN-20_5.0x5.0-0.65', ),
    'VQFN-24': ('VQFN-24_4.0x4.0-0.50', ),
    'VQFN-32': ('VQFN-32_5.0x5.0-0.50', 'VQFN-32_5.0x5.0-0.50'),
    'VQFN-36': ('VQFN-36_6.0x6.0-0.50', ),
    'VQFN-40': ('VQFN-40_5.0x5.0-0.40', ),
    'VQFN-48': ('VQFN-48_6.0x6.0-0.40', ),
    'VQFN-56': ('VQFN-56_8.0x8.0-0.50', ),
    'VQFN-64': ('VQFN-64_8.0x8.0-0.40', ),
    'WQFN-16': ('WQFN-16_3.0x3.0-0.50', ),
    'WQFN-24': ('WQFN-24_4.0x4.0-0.50', 'WQFN-24_4.0x5.0-0.50', ),
    #микросхемы - SON
    'USON-6': ('USON-6_2.0x2.0-0.65', ),
    'WSON-6': ('WSON-6_2.0x2.0-0.65', ),
    'WSON-8': ('WSON-8_2.0x2.0-0.50', 'WSON-8_6.0x5.0-1.27', 'WSON-8_8.0x6.0-1.27'), #дичь от производителей - разные корпуса с одним названием
    #микросхемы - BGA
    'FBGA-96': ('FBGA-96-9x16_11.00x14.00-0.80', ),
    'FCPBGA-624': ('FCPBGA-624-25x25_21.00x21.00-0.80', ),
    'LFBGA-272': ('LFBGA-272-18x18-0.80_16.00x16.00-1.70', ),
    'PBGA-416': ('PBGA-416_26x26-1.00_27.00x27.00-2.23', ),
    'UFBGA-201': ('UFBGA-201-15x15-0.65_10.00x10.00-0.65', ),
    'WFBGA-153': ('WFBGA-153-14x14_11.50x13.00-0.50', ),
    'WFBGA-169': ('WFBGA-169-14x28_14.00x18.00-0.50', )
}

#============================================================== END Dictionaries =====================================================