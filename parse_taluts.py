import os
import datetime
from typedef_bom import BoM_typeDef                                                             #класс BoM
from typedef_components import Components_typeDef                                               #класс базы данных компонентов
from typedef_titleBlock import TitleBlock_typeDef                                               #класс основной надписи

script_dirName  = os.path.dirname(__file__)                                                     #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                               #базовое имя модуля
script_date     = datetime.datetime(2022, 9, 2)

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
    if end < 0: end = len(string)
    if caseSensitive:
        for item in prefixTuple:
            if string.startswith(item, start, end) >= 0: return True
    else:
        string = string.casefold()
        for item in prefixTuple:
            if string.startswith(item.casefold(), start, end) >= 0: return True
    return False

#Check if string ends with tuple items
def string_endswith(string, prefixTuple, start = 0, end = -1, caseSensitive = False):
    if end < 0: end = len(string)
    if caseSensitive:
        for item in prefixTuple:
            if string.endswith(item, start, end) >= 0: return True
    else:
        string = string.casefold()
        for item in prefixTuple:
            if string.endswith(item.casefold(), start, end) >= 0: return True
    return False

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
    decimalPoint = '.'
    
    warnings = 0
    errors = 0

    print("INFO >> Parsing BoM data", end ="... ", flush = True)
    for i in range(len(BoM.entries)):
        #определяем тип элемента
        kind = BoM.entries[i]['BOM_type']
        if string_equal(kind, ("Resistor", "Резистор"), False):
            component = components.ComponentTypes.Resistor()
        elif string_equal(kind, ("Jumper", "Перемычка"), False):
            component = components.ComponentTypes.Jumper()
        elif string_equal(kind, ("Capacitor", "Конденсатор"), False):
            component = components.ComponentTypes.Capacitor()
        elif string_equal(kind, ("Inductor", "Индуктивность", "Choke", "Дроссель"), False):
            component = components.ComponentTypes.Inductor()
        elif string_equal(kind, ("Diode", "Диод", "Zener", "Стабилитрон", "Varicap", "Варикап"), False):
            component = components.ComponentTypes.Diode()
        elif string_equal(kind, ("Transistor", "Транзистор"), False):
            component = components.ComponentTypes.Transistor()
        elif string_equal(kind, ("Integrated Circuit", "Микросхема"), False):
            component = components.ComponentTypes.IntegratedCircuit()
        elif string_equal(kind, ("TVS", "Супрессор", "Разрядник", "Варистор"), False):
            component = components.ComponentTypes.TVS()
        elif string_equal(kind, ("Circuit Breaker", "Предохранитель"), False):
            component = components.ComponentTypes.CircuitBreaker()
        elif string_equal(kind, ("Crystal", "Resonator", "Резонатор", "Oscillator", "Осциллятор"), False):
            component = components.ComponentTypes.Oscillator()
        elif string_equal(kind, ("EMI filter", "Фильтр ЭМП"), False):
            component = components.ComponentTypes.EMIFilter()
        elif string_equal(kind, ("LED", "Светодиод"), False):
            component = components.ComponentTypes.LED()
        else:
            component = components.ComponentTypes.Generic()

        #Fill-in generic attributes
        component.GENERIC_designator   = BoM.entries[i]['Designator']           #позиционное обозначение
        component.GENERIC_kind         = BoM.entries[i]['BOM_type']             #тип элемента
        component.GENERIC_value        = BoM.entries[i]['BOM_value']            #номинал
        component.GENERIC_quantity     = int(BoM.entries[i]['Quantity'])        #количество
        #--- описание
        if len(BoM.entries[i]['BOM_description'].strip(' ')) > 0:
            component.GENERIC_description  = BoM.entries[i]['BOM_description']
        #--- производитель
        if len(BoM.entries[i]['BOM_manufacturer'].strip(' ')) > 0:
            component.GENERIC_manufacturer = BoM.entries[i]['BOM_manufacturer']
        #--- установка на плату
        component.GENERIC_fitted       = True
        if 'Fitted' in BoM.fieldNames:
            if BoM.entries[i]['Fitted'] == 'Not Fitted':
                component.GENERIC_fitted = False
        #--- допустимые замены
        if 'BOM_substitute' in BoM.fieldNames:
            substitutes = BoM.entries[i]['BOM_substitute']
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
        if 'BOM_explicit' in BoM.fieldNames:
            #есть данные в BoM
            explicit = BoM.entries[i]['BOM_explicit']
            if   string_equal(explicit, ('true', 'истина', '1'), False): component.GENERIC_explicit = True
            elif string_equal(explicit, ('false', 'ложь', '0'), False): component.GENERIC_explicit = False
            else: component.GENERIC_explicit = True     #значение по-умолчанию если не смогли распознать значение поля
        else:
            #нет данных в BoM
            #legacy: у резисторов и конденсаторов если не указан производитель то задание неявное
            component.GENERIC_explicit = True
            if isinstance(component, (components.ComponentTypes.Resistor, components.ComponentTypes.Capacitor, components.ComponentTypes.Jumper)):
                if component.GENERIC_manufacturer is None: component.GENERIC_explicit = False

        #Переводим footprint в package с помощью словаря
        for entry in dict_package:
            for word in dict_package[entry]:
                if word == BoM.entries[i]['Footprint']:
                    component.GENERIC_package = entry
                    break
            if component.GENERIC_package is not None: break

        #Разбираем десигнатор
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
        component.GENERIC_designator_index   = int(''.join([s for s in tmp if s.isdigit()]))

        #Разбираем параметры из описания
        if component.GENERIC_description is not None:
            descriptionParams = component.GENERIC_description.split(', ')

            #Резистор
            if type(component) is components.ComponentTypes.Resistor:
                #legacy: затычка для старого формата где сопротивление и допуск в разных параметрах
                for j in range(len(descriptionParams)):
                    if descriptionParams[j].endswith('Ом') and j < len(descriptionParams) - 1:
                        if descriptionParams[j + 1].endswith('%'):
                            descriptionParams[j] += ' ±' + descriptionParams.pop(j + 1).replace('±', '')
                        break
                
                #Parsing params
                for j in range(len(descriptionParams)):
                    #тип резистора
                    if component.RES_type is None:
                        if string_equal(descriptionParams[0], ('тонкоплёночный', 'тонкоплён.'), False):
                            component.RES_type = component.Type.THIN_FILM
                        elif string_equal(descriptionParams[0], ('толстоплёночный', 'толстоплён.'), False):
                            component.RES_type = component.Type.THICK_FILM
                        elif string_equal(descriptionParams[0], ('металло-плёночный', 'мет-плён.'), False):
                            component.RES_type = component.Type.METAL_FILM
                        elif string_equal(descriptionParams[0], ('углеродистый', 'углерод.'), False):
                            component.RES_type = component.Type.CARBON_FILM
                        elif string_equal(descriptionParams[0], ('проволочный', 'провол.'), False):
                            component.RES_type = component.Type.WIREWOUND
                        elif string_equal(descriptionParams[0], ('керамический', 'керам.'), False):
                            component.RES_type = component.Type.CERAMIC
                        #завершаем обработку если нашли нужный параметр
                        if component.RES_type is not None:   
                            descriptionParams[j] = '' #clear parsed parameter
                            continue

                    #тип монтажа и типоразмер
                    if component.GENERIC_mount is None:
                        if parse_param_mountandsize(descriptionParams[j], component):
                            descriptionParams[j] = '' #clear parsed parameter
                            continue

                    parsing_result = parse_param_valueWithTolerance(descriptionParams[j], decimalPoint)
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
                                    errors += 1
                                    print('\n' + ' ' * 12 + 'error! ' + component.GENERIC_designator + ' - tolerance absent or can not be parsed', end = '', flush = True)
                                #clear parsed parameter and go to next param
                                descriptionParams[j] = ''
                                continue

                        #ТКС
                        if component.RES_tempCoeff is None:
                            if parsing_result[1] is not None:
                                if string_equal(parsing_result[1][2], ('ppm/°C', ), True):
                                    component.RES_tempCoeff = parsing_result[1]
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
                    parsing_result = parse_param_assembly(descriptionParams[j])
                    if parsing_result is not None:
                        component.GENERIC_assembly = parsing_result
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

            #Перемычка
            elif type(component) is components.ComponentTypes.Jumper:
                #Parsing params
                for j in range(len(descriptionParams)):
                    #тип монтажа и типоразмер
                    if component.GENERIC_mount is None:
                        if parse_param_mountandsize(descriptionParams[j], component):
                            descriptionParams[j] = '' #clear parsed parameter
                            continue

            #Конденсатор
            elif type(component) is components.ComponentTypes.Capacitor:
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
                        if parse_param_mountandsize(descriptionParams[j], component):
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
                    
                    parsing_result = parse_param_valueWithTolerance(descriptionParams[j], decimalPoint)
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
                                    errors += 1
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
                    parsing_result = parse_param_assembly(descriptionParams[j])
                    if parsing_result is not None:
                        component.GENERIC_assembly = parsing_result
                        descriptionParams[j] = '' #clear parsed parameter
                        continue

            #Индуктивность
            elif type(component) is components.ComponentTypes.Inductor:
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
                        if parse_param_mountandsize(descriptionParams[j], component):
                            descriptionParams[j] = '' #clear parsed parameter
                            continue

                    parsing_result = parse_param_valueWithTolerance(descriptionParams[j], decimalPoint)
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
                                    errors += 1
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

            #Диод
            elif type(component) is components.ComponentTypes.Diode:
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

                    parsing_result = parse_param_valueWithToleranceAtConditions(descriptionParams[j], decimalPoint)
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
                                        errors += 1
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
                                        condition = parse_param_value(parsing_result[2][k], decimalPoint)
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
                    parsing_result = parse_param_assembly(descriptionParams[j])
                    if parsing_result is not None:
                        component.GENERIC_assembly = parsing_result
                        descriptionParams[j] = '' #clear parsed parameter
                        continue

            #Транзистор
            elif type(component) is components.ComponentTypes.Transistor:
                pass

            #Микросхема
            elif type(component) is components.ComponentTypes.IntegratedCircuit:
                pass

            #TVS
            elif type(component) is components.ComponentTypes.TVS:
                #Определяем тип по разновидности компонента
                if string_equal(component.GENERIC_kind, ("Супрессор", ), False):
                    component.TVS_type = component.Type.DIODE
                elif string_equal(component.GENERIC_kind, ('Варистор', ), False):
                    component.TVS_type = component.Type.VARISTOR
                elif string_equal(component.GENERIC_kind, ('Разрядник', ), False):
                    component.TVS_type = component.Type.GAS_DISCHARGE_TUBE
                
                #Parsing params
                for j in range(len(descriptionParams)):
                    #тип монтажа и типоразмер
                    if component.GENERIC_mount is None:
                        if parse_param_mountandsize(descriptionParams[j], component):
                            descriptionParams[j] = '' #clear parsed parameter
                            continue

                    #ток гашения выброса
                    if component.TVS_clamping_current is None:
                        parsing_result = parse_param_valueWithToleranceAtConditions(descriptionParams[j], decimalPoint)
                        if parsing_result is not None:
                            if string_equal(parsing_result[0][1], ('A', 'А'), True):
                                component.TVS_clamping_current = parsing_result[0][0]
                                if component.TVS_testPulse is None and parsing_result[2] is not None:
                                    conditions = parsing_result[2][0].replace(' ', '')
                                    if string_equal(conditions, ('8/20us', '8/20мкс'), False):
                                        component.TVS_testPulse = component.TestPulse.US_8_20
                                    elif  string_equal(conditions, ('10/1000us', '10/1000мкс'), False):
                                        component.TVS_testPulse = component.TestPulse.US_10_1000
                                    else:
                                        component.TVS_testPulse = component.TestPulse.UNKNOWN
                                #clear parsed parameter and go to next param
                                descriptionParams[j] = ''
                                continue

                    #диод
                    if component.TVS_type == component.Type.DIODE:
                        #направленность
                        if component.TVS_bidirectional is None:
                            if string_equal(descriptionParams[j], ('однонаправленный', 'однонаправ.'), False):
                                component.TVS_bidirectional = False
                            elif string_equal(descriptionParams[j], ('двунаправленный', 'двунаправ.'), False):
                                component.TVS_bidirectional = True
                            #завершаем обработку если нашли нужный параметр
                            if component.TVS_bidirectional is not None:   
                                descriptionParams[j] = '' #clear parsed parameter
                                continue

                        parsing_result = parse_param_valueWithToleranceAtConditions(descriptionParams[j], decimalPoint)
                        if parsing_result is not None:
                            #максимальное рабочее напряжение
                            if component.TVS_standoff_voltage is None:
                                if string_equal(parsing_result[0][1], ('V', 'В'), True):
                                    component.TVS_standoff_voltage = parsing_result[0][0]
                                    #clear parsed parameter and go to next param
                                    descriptionParams[j] = ''
                                    continue

                            #мощность
                            if component.TVS_power is None:
                                if string_equal(parsing_result[0][1], ('W', 'Вт'), True):
                                    component.TVS_power = parsing_result[0][0]
                                    if component.TVS_testPulse is None and parsing_result[2] is not None:
                                        conditions = parsing_result[2][0].replace(' ', '')
                                        if string_equal(conditions, ('8/20us', '8/20мкс'), False):
                                            component.TVS_testPulse = component.TestPulse.US_8_20
                                        elif  string_equal(conditions, ('10/1000us', '10/1000мкс'), False):
                                            component.TVS_testPulse = component.TestPulse.US_10_1000
                                        else:
                                            component.TVS_testPulse = component.TestPulse.UNKNOWN
                                    #clear parsed parameter and go to next param
                                    descriptionParams[j] = ''
                                    continue


                    #варистор
                    elif component.TVS_type == component.Type.VARISTOR:
                        parsing_result = parse_param_valueWithToleranceAtConditions(descriptionParams[j], decimalPoint)
                        if parsing_result is not None:
                            #максимальное рабочее напряжение
                            if component.TVS_standoff_voltage is None:
                                if string_equal(parsing_result[0][1], ('V', 'В'), True):
                                    component.TVS_standoff_voltage = parsing_result[0][0]
                                    #clear parsed parameter and go to next param
                                    descriptionParams[j] = ''
                                    continue

                            #энергия
                            if component.TVS_energy is None:
                                if string_equal(parsing_result[0][1], ('J', 'Дж'), True):
                                    component.TVS_energy = parsing_result[0][0]
                                    #clear parsed parameter and go to next param
                                    descriptionParams[j] = ''
                                    continue

                    #газоразрядник
                    elif component.TVS_type == component.Type.GAS_DISCHARGE_TUBE:
                        pass

                    #сборка
                    parsing_result = parse_param_assembly(descriptionParams[j])
                    if parsing_result is not None:
                        component.GENERIC_assembly = parsing_result
                        descriptionParams[j] = '' #clear parsed parameter
                        continue

            #Предохранитель
            elif type(component) is components.ComponentTypes.CircuitBreaker:
                #Parsing params
                for j in range(len(descriptionParams)):
                    #тип предохранителя
                    if component.CBRK_type is None:
                        if string_equal(descriptionParams[j], ('плавкий', ), False):
                            component.CBRK_type = component.Type.FUSE
                        elif string_equal(descriptionParams[j], ('самовосстанавливающийся', 'самовосст.'), False):
                            component.CBRK_type = component.Type.PTC_RESETTABLE
                        elif string_equal(descriptionParams[j], ('термо', ), False):
                            component.CBRK_type = component.Type.THERMAL
                        #завершаем обработку если нашли нужный параметр
                        if component.CBRK_type is not None:   
                            descriptionParams[j] = '' #clear parsed parameter
                            continue

                    #тип монтажа и типоразмер
                    if component.GENERIC_mount is None:
                        if parse_param_mountandsize(descriptionParams[j], component):
                            descriptionParams[j] = '' #clear parsed parameter
                            continue

                    parsing_result = parse_param_valueWithTolerance(descriptionParams[j], decimalPoint)
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

            #Резонатор
            elif type(component) is components.ComponentTypes.Oscillator:
                #Parsing params
                for j in range(len(descriptionParams)):
                    #тип резонатора
                    if component.OSC_type is None:
                        if string_equal(descriptionParams[j], ('кварцевый', 'кварц.'), False):
                            component.OSC_type = component.Type.CRYSTAL
                        elif string_equal(descriptionParams[j], ('керамический', 'керам.'), False):
                            component.OSC_type = component.Type.CERAMIC
                        elif string_equal(descriptionParams[j], ('МЭМС', ), False):
                            component.OSC_type = component.Type.MEMS
                        #завершаем обработку если нашли нужный параметр
                        if component.OSC_type is not None:   
                            descriptionParams[j] = '' #clear parsed parameter
                            continue

                    #тип монтажа и типоразмер (поидее не надо, но пусть будет)
                    if component.GENERIC_mount is None:
                        if parse_param_mountandsize(descriptionParams[j], component):
                            descriptionParams[j] = '' #clear parsed parameter
                            continue

                    #диапазон рабочих температур
                    if component.GENERIC_temperature_range is None:
                        parsing_result = parse_param_temperatureRange(descriptionParams[j], decimalPoint)
                        if parsing_result is not None:
                            component.GENERIC_temperature_range = parsing_result
                            descriptionParams[j] = '' #clear parsed parameter
                            continue

                    parsing_result = parse_param_valueWithTolerance(descriptionParams[j], decimalPoint)
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
                                        errors += 1
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

            #Фильтр ЭМП
            elif type(component) is components.ComponentTypes.EMIFilter:
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
                        if parse_param_mountandsize(descriptionParams[j], component):
                            descriptionParams[j] = '' #clear parsed parameter
                            continue

                    parsing_result = parse_param_valueWithToleranceAtConditions(descriptionParams[j], decimalPoint)
                    if parsing_result is not None:
                        #импеданс
                        if component.EMIF_impedance is None:
                            if parsing_result[2] is not None:
                                conditions = parse_param_value(parsing_result[2][0], decimalPoint)
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
                                                errors += 1
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
                                    errors += 1
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
                            if string_equal(parsing_result[0][1], ('Ohm', 'Ом'), True):
                                component.EMIF_resistance = parsing_result[0][0]
                                #clear parsed parameter and go to next param
                                descriptionParams[j] = ''
                                continue
                                
            #Светодиод
            elif type(component) is components.ComponentTypes.LED:
                #Parsing params
                for j in range(len(descriptionParams)):
                    #тип монтажа и типоразмер
                    if component.GENERIC_mount is None:
                        if parse_param_mountandsize(descriptionParams[j], component):
                            descriptionParams[j] = '' #clear parsed parameter
                            continue

                    #цвет
                    if component.LED_color is None:
                        if string_equal(descriptionParams[j], ('white', 'белый'), False):
                            component.LED_color = component.Color.WHITE
                        elif string_equal(descriptionParams[j], ('red', 'красный'), False):
                            component.LED_color = component.Color.RED
                        elif string_equal(descriptionParams[j], ('orange', 'оранжевый'), False):
                            component.LED_color = component.Color.ORANGE
                        elif string_equal(descriptionParams[j], ('amber', 'янтарный'), False):
                            component.LED_color = component.Color.AMBER
                        elif string_equal(descriptionParams[j], ('yellow', 'жёлтый'), False):
                            component.LED_color = component.Color.YELLOW
                        elif string_equal(descriptionParams[j], ('lime', 'салатовый'), False):
                            component.LED_color = component.Color.LIME
                        elif string_equal(descriptionParams[j], ('green', 'зелёный'), False):
                            component.LED_color = component.Color.GREEN
                        elif string_equal(descriptionParams[j], ('turquoise', 'бирюзовый'), False):
                            component.LED_color = component.Color.TURQUOISE
                        elif string_equal(descriptionParams[j], ('cyan', 'голубой'), False):
                            component.LED_color = component.Color.CYAN
                        elif string_equal(descriptionParams[j], ('blue', 'синий'), False):
                            component.LED_color = component.Color.BLUE
                        elif string_equal(descriptionParams[j], ('violet', 'фиолетовый'), False):
                            component.LED_color = component.Color.VIOLET
                        elif string_equal(descriptionParams[j], ('purple', 'пурпурный'), False):
                            component.LED_color = component.Color.PURPLE
                        elif string_equal(descriptionParams[j], ('pink', 'розовый'), False):
                            component.LED_color = component.Color.PINK
                        elif string_equal(descriptionParams[j], ('infrared', 'инфракрасный'), False):
                            component.LED_color = component.Color.INFRARED
                        elif string_equal(descriptionParams[j], ('ultraviolet', 'ультрафиолетовый'), False):
                            component.LED_color = component.Color.ULTRAVIOLET
                        elif string_equal(descriptionParams[j], ('multicolor', 'многоцветный'), False):
                            component.LED_color = component.Color.MULTI
                        #завершаем обработку если нашли нужный параметр
                        if component.LED_color is not None:   
                            descriptionParams[j] = '' #clear parsed parameter
                            continue

                    #индекс цветопередачи
                    if component.LED_color_renderingIndex is None:
                        if descriptionParams[j].startswith('CRI'):
                            parsing_result = parse_param_value(descriptionParams[j][3:], decimalPoint)
                            if parsing_result is not None:
                                component.LED_color_renderingIndex = parsing_result[0]
                                #clear parsed parameter and go to next param
                                descriptionParams[j] = ''
                                continue

                    parsing_result = parse_param_valueWithToleranceAtConditions(descriptionParams[j], decimalPoint)
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
                                    conditions = parse_param_value(parsing_result[2][0], decimalPoint)
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
                                    conditions = parse_param_value(parsing_result[2][0], decimalPoint)
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
                    parsing_result = parse_param_assembly(descriptionParams[j])
                    if parsing_result is not None:
                        component.GENERIC_assembly = parsing_result
                        descriptionParams[j] = '' #clear parsed parameter
                        continue

            #Неопознанный элемент
            else:
                pass

            #Move remaining unparsed parameters to misc array
            for param in descriptionParams:
                if len(param) > 0: component.GENERIC_misc.append(param)
        
        #добавление элемента в массив
        components.entries.append(component)
    
    if warnings + errors == 0: 
        print('done (' + str(len(components.entries)) + ' components created)')
    else:
        print('\n' + ' ' * 12 + 'completed with ' + str(errors) + ' errors and ' +  str(warnings) + ' warnings.')

    designer_check(components)

#разбор параметра: тип монтажа и типоразмер
def parse_param_mountandsize(param, component):
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
def parse_param_valueWithToleranceAtConditions(param, decimalPoint = '.'):
    if param is not None:
        #удаляем пробелы с краёв
        param = param.strip(' ')
        
        #проверяем есть ли что-нибудь
        if len(param.replace(' ', '')) > 0:
            valueToleranceAndConditions = param.split('@', 1)
            valueAndTolerance = parse_param_valueWithTolerance(valueToleranceAndConditions[0], decimalPoint)            
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
def parse_param_valueWithTolerance(param, decimalPoint = '.'):
    if param is not None:
        #удаляем все пробелы
        param = param.replace(' ', '')
        
        #проверяем есть ли что-нибудь
        if len(param) > 0:
            valueAndTolerance = parse_param_splitValueAndTolerance(param)
            value = parse_param_value(valueAndTolerance[0], decimalPoint)
            tolerance = parse_param_tolerance(valueAndTolerance[1], decimalPoint)
            if (value is not None) or (tolerance is not None):
                return [value, tolerance]

    return None

#разбор параметра: разделение значения и его допуска
def parse_param_splitValueAndTolerance(param):
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
def parse_param_value(param, decimalPoint = '.'):
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
def parse_param_tolerance(param, decimalPoint = '.', convertParts = True):
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

#разбор параметра: температурный диапазон
def parse_param_temperatureRange(param, decimalPoint = '.'):
    if param is not None:
        #удаляем все пробелы
        param = param.replace(' ', '')           

        #проверяем осталось ли что-нибудь
        if len(param) > 0:
            param = param.replace(decimalPoint, '.')     #меняем десятичный разделитель на точку
            param = param.replace('°C', '℃')             #меняем ANSI комбинацию на Unicode символ
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
def parse_param_assembly(param):
    if string_startswith(param, ("assembly", "сборка"), False):
        asm_blocks = 0
        asm_elements = 0
        asm_type = Components_typeDef.ComponentTypes.Generic.AssemblyType.UNKNOWN
        
        param = param.split(' ')
        if len(param) > 1:
            #тип
            asm_formula = param[1]
            asm_type = ''
            pos = len(asm_formula) - 1
            while pos >= 0:
                char = asm_formula[pos]
                if char.isdecimal(): break
                asm_type = char + asm_type
                pos -= 1
            asm_formula = asm_formula[0:len(asm_formula) - len(asm_type)]
            if   string_equal(asm_type, ('I', 'IND'), True): asm_type = Components_typeDef.ComponentTypes.Generic.AssemblyType.INDEPENDENT
            elif string_equal(asm_type, ('A', 'CA' ), True): asm_type = Components_typeDef.ComponentTypes.Generic.AssemblyType.COMMON_ANODE
            elif string_equal(asm_type, ('C', 'CC' ), True): asm_type = Components_typeDef.ComponentTypes.Generic.AssemblyType.COMMON_CATHODE
            elif string_equal(asm_type, ('S', 'SER'), True): asm_type = Components_typeDef.ComponentTypes.Generic.AssemblyType.SERIES
            else:                                            asm_type = Components_typeDef.ComponentTypes.Generic.AssemblyType.UNKNOWN

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
                    print('\n' + ' ' * 12 + 'warning! ' + components.entries[i].GENERIC_designator + ' | ' + components.entries[j].GENERIC_designator  + ' - data mismatch', end = '')
                    warnings += 1

    #проверяем соответствие типоразмера в описании и корпуса для определённых типов компонентов
    for component in components.entries:
        flag_packageSizeMismatch = False
        if type(component) is components.ComponentTypes.Resistor or type(component) is components.ComponentTypes.Capacitor:
            if component.GENERIC_mount == component.Mounting.Type.SURFACE:
                if component.GENERIC_size != component.GENERIC_package:
                    flag_packageSizeMismatch = True
        if flag_packageSizeMismatch:
            component.flag = component.FlagType.ERROR
            print('\n' + ' ' * 12 + 'error! ' + component.GENERIC_designator + ' - size and package mismatch', end = '', flush = True)
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
dict_package = { #запятые на концах чтобы запись с одним значением воспринималась как массив значений, а не массив символов в строке
    #чипы
    '0201': ('MLCC_0201', 'RC_0201', 'FB_0201', ),
    '0402': ('MLCC_0402', 'RC_0402', 'LC_0402', 'FB_0402', ),
    '0603': ('MLCC_0603', 'SFCC_0603', 'RC_0603', 'LC_0603', 'FB_0603', 'FC_0603', 'LEDC_0603', 'LEDC_0603-0.75', ),
    '0805': ('MLCC_0805', 'SFCC_0805', 'RC_0805', 'LC_0805', 'FB_0805', 'FC_0805', 'LEDC_0805', 'LEDC_0805-0.75', ),
    '1206': ('MLCC_1206', 'SFCC_1206', 'RC_1206', 'LC_1206', 'FB_1206', 'FC_1206', 'LEDC_1206', ),
    '1210': ('MLCC_1210', 'SFCC_1210', 'RC_1210', 'LC_1210', 'FB_1210', ),
    '1218': ('RC_1218', ),
    '1808': ('MLCC_1808', ),
    '1812': ('MLCC_1812', 'LC_1812', 'FB_1812', ),
    '1913': ('SFCC_1913', ),
    '2010': ('RC_2010', ),
    '2211': ('MLCC_2211', ),
    '2220': ('MLCC_2220', 'VC_2220', ),
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
    #резонаторы
    '2-SMD (3215)': ('2-SMD_3215-0.9', ),
    '2-SMD (5032)': ('2-SMD_5032-1.1', ),
    '4-SMD (2520)': ('4-SMD_2520-0.55', ),
    '4-SMD (3225)': ('4-SMD_3225-0.75', ),
    '4-SMD (5032)': ('4-SMD_5032-1.1', ),
    '4-SMD (7050)': ('4-SMD_7050-1.30', ),
    'HC-49/US': ('HC-49/US', ),
    'HC-49/US-SMD': ('HC-49/US-SMD', ),
    #диоды/транзисторы/мелкие микросхемы
    'SMA': ('DO-214AC (SMA)', ),
    'SMB': ('DO-214AA (SMB)', ),
    'SMC': ('DO-214AB (SMC)', ),
    'SOD-123': ('SOD-123', ),
    'SOD-123F': ('SOD-123F', ),
    'SOD-323': ('SOD-323', ),
    'SOD-323F': ('SOD-323F', ),
    'SOD-523F': ('SOD-523F', ),
    'TO-92': ('TO-92-V', ),
    'TO-220': ('TO-220-V', ),
    'TO-220AB': ('TO-220AB-H', 'TO-220AB-V', ),
    'TO-247AC': ('TO-247AC-V', ),
    'DPAK': ('TO-252 (DPAK)', ),
    'D²PAK': ('TO-263AB (D2PAK)', ),
    'SOT-23': ('SOT-23', 'SOT-23-3', ),
    'SOT-23-5': ('SOT-23-5', ),
    'SOT-23-6': ('SOT-23-6', ),
    'SOT-23-8': ('SOT-23-8', ),
    'SOT-223': ('SOT-223', ),
    'SOT-223-6': ('SOT-223-6', ),
    'SOT-323': ('SOT-323', 'SOT-323-3', ),
    'SOT-323-5': ('SOT-323-5', ),
    'SOT-323-6': ('SOT-323-6', ),
    'SOT-5': ('SOT-5', ),
    'SOT-89': ('SOT-89', ),
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
    #микросхемы - TSSOP
    'TSSOP-8': ('TSSOP-8', ),
    'TSSOP-14': ('TSSOP-14', ),
    'TSSOP-16': ('TSSOP-16', ),
    'TSSOP-20': ('TSSOP-20', ),
    'TSSOP-24': ('TSSOP-24', ),
    'TSSOP-28': ('TSSOP-28', ),
    'TSSOP-56': ('TSSOP-56', ),
    #микросхемы - SSOP
    'SSOP-8': ('SSOP-8', ),
    'SSOP-16': ('SSOP-16', ),
    'SSOP-28': ('SSOP-28', ),
    #микросхемы - MSOP
    'MSOP-8': ('MSOP-8', 'MSOP-8-EP', ),
    'MSOP-10': ('MSOP-10', ),
    #микросхемы - VSSOP
    'VSSOP-8': ('VSSOP-8_2.3x2.0-0.50', 'VSSOP-8_3.0x3.0-0.65', ),
    #микросхемы - uSOP
    'uSOP-10': ('uSOP-10', ),
    #микросхемы - QSOP
    'QSOP-20': ('QSOP-20', ),
    'QSOP-24': ('QSOP-24', ),
    #микросхемы - QFP
    'TQFP-32': ('TQFP-32', 'HTQFP-32', ),
    'TQFP-44': ('TQFP-44', ),
    'TQFP-64': ('TQFP-64', ),
    'LQFP-48': ('LQFP-48', ),
    'LQFP-64': ('LQFP-64', 'LQFP-64-EP5.00', ),
    'LQFP-100': ('LQFP-100', ),
    'LQFP-144': ('LQFP-144', 'LQFP-144-EP7.20', ),
    #микросхемы - DFN
    'DFN-10': ('DFN-10_3.0x3.0-0.50', ),
    'TDFN-8': ('TDFN-8_2.0x2.0-0.50', 'TDFN-8_3.0x3.0-0.65', ),
    'WDFN-6': ('WDFN-6_2.0x2.0-0.65', ),
    #микросхемы - QFN
    'QFN-16': ('QFN-16_3.0x3.0-0.50', ),
    'VQFN-16': ('VQFN-16_4.0x4.0-0.65', ),
    'VQFN-20': ('VQFN-20_5.0x5.0-0.65', ),
    'VQFN-24': ('VQFN-24_4.0x4.0-0.50', ),
    'VQFN-32': ('VQFN-32_5.0x5.0-0.50', ),
    'VQFN-36': ('VQFN-36_6.0x6.0-0.50', ),
    'VQFN-64': ('VQFN-64_8.0x8.0-0.40', ),
    'WQFN-16': ('WQFN-16_3.0x3.0-0.50', ),
    'WQFN-24': ('WQFN-24_4.0x4.0-0.50', 'WQFN-24_4.0x5.0-0.50', ),
    #микросхемы - SON
    'USON-6': ('USON-6_2.0x2.0-0.65', ),
    'WSON-6': ('WSON-6_2.0x2.0-0.65', ),
    'WSON-8': ('WSON-8_6.0x5.0-1.27', ),
    #микросхемы - BGA
    'FBGA-96': ('FBGA-96-9x16_11.00x14.00-0.80', ),
    'FCPBGA-624': ('FCPBGA-624-25x25_21.00x21.00-0.80', ),
    'WFBGA-153': ('WFBGA-153-14x14_11.50x13.00-0.50', ),
    'WFBGA-169': ('WFBGA-169-14x28_14.00x18.00-0.50', )
}

#============================================================== END Dictionaries =====================================================