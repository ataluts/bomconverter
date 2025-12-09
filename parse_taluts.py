import os
import re
import datetime
import lib_common
import dict_locale as lcl
from typedef_adproject import ADProject, SchDoc, PcbDoc, BoMDoc, PnPDoc
from typedef_bom import BoM                                                                     #класс BoM
import typedef_components as Components                                                         #класс базы данных компонентов
from typedef_designator import Designator                                                       #класс десигнатора

script_dirName  = os.path.dirname(__file__)                                                     #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                               #базовое имя модуля
script_date     = datetime.datetime(2025, 12, 9)

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
def parse_project(project:ADProject, **kwargs):
    print(f"{' ' * 12}designer: {designer_name} ({script_baseName})")

    print("INFO >> Identifying BoM files", end ="... ", flush = True)
    #определяем BoM-файлы и имена их конфигураций
    bomfile_prefix = 'bom'   #в моём случае берём файлы с расширением csv начинающиеся с 'BoM'
    bomfile_ext    = 'csv'
    for file in project.generatedFiles:
        if file.suffix.casefold() == os.extsep + bomfile_ext.casefold():
            if file.stem.casefold().startswith(bomfile_prefix.casefold()):
                bomfile_postfix = (file.stem[len(bomfile_prefix):]).strip()
                #определяем соответствующую конфигурацию
                for variant in project.variants:
                    if variant in bomfile_postfix:
                        variant_enclosure = bomfile_postfix.split(variant)
                        break
                else:
                    #соответствующая конфигурация не обнаружена
                    variant = None
                    if len(bomfile_postfix) > 0: variant_enclosure = [bomfile_postfix, '']
                    else:                        variant_enclosure = None
                project.BoMDoc.append(BoMDoc(file, project, variant, variant_enclosure))
    if len(project.BoMDoc) > 0: print(f"done ({len(project.BoMDoc)} files)")
    else:                       print("no BoMs found.")

    print("INFO >> Identifying PnP files", end ="... ", flush = True)
    #определяем PnP-файлы
    pnpfile_prefix = 'Pick Place for '   #в моём случае берём файлы с расширением csv начинающиеся с 'Pick Place for '
    pnpfile_ext    = 'csv'
    for file in project.generatedFiles:
        if file.suffix.casefold() == os.extsep + pnpfile_ext.casefold():
            if file.stem.casefold().startswith(pnpfile_prefix.casefold()):
                pnpfile_postfix = (file.stem[len(pnpfile_prefix):]).strip()
                variant_enclosure = ['(', ')']
                #определяем соответствующий PcbDoc и убираем его имя из имени PnP файла
                for pcb in project.PcbDoc:
                    pcb_stem = pcb.address.stem
                    if pnpfile_postfix == pcb_stem:
                        #оставшееся имя PnP файла совпадает с именем PCB файла -> конфигурации и её обрамления нет
                        variant = None
                        variant_enclosure = None
                        break
                    elif pnpfile_postfix.startswith(pcb_stem) and pnpfile_postfix[len(pcb_stem):len(pcb_stem)+len(variant_enclosure[0])] == variant_enclosure[0]:
                        #оставшееся имя PnP файла начинается с имени PCB файла и после имени PCB файла идёт обрамление -> нашли нужный PCB файл и далее в обрамлении идёт имя конфигурации
                        pnpfile_postfix = pnpfile_postfix[len(pcb_stem):].strip()
                        #определяем соответствующую конфигурацию
                        for variant in project.variants:
                            if variant in pnpfile_postfix:
                                variant_enclosure = pnpfile_postfix.split(variant)
                                break
                        else:
                            #соответствующая конфигурация не обнаружена
                            variant = None
                            if len(pnpfile_postfix) > 0: variant_enclosure = [pnpfile_postfix, '']
                            else:                        variant_enclosure = None
                        break
                else:
                    #соответствующий PcbDoc не обнаружен
                    pcb = None
                    #определяем соответствующую конфигурацию
                    for variant in project.variants:
                        if variant in pnpfile_postfix:
                            variant_enclosure = pnpfile_postfix.split(variant)
                            break
                    else:
                        #соответствующая конфигурация не обнаружена
                        variant = None
                        if len(pnpfile_postfix) > 0: variant_enclosure = [pnpfile_postfix, '']
                        else:                        variant_enclosure = None
                project.PnPDoc.append(PnPDoc(file, project, pcb, variant, variant_enclosure))
    if len(project.PnPDoc) > 0: print(f"done ({len(project.PnPDoc)} files)")
    else:                       print("no PnPs found.")

    print("INFO >> Parsing project parameters", end ="... ", flush = True)
    #определяем откуда брать основную надпись
    schematic = project.SchDoc[0]               #в моём случае это самый первый схемный файл проекта
    schematic.read(**kwargs)                    #читаем его сворачивая регистр имён параметров

    #с какой-то версии Altium после 17 имена полей стали в CamelCase вместо UPPERCASE
    keys = {'RECORD':'RECORD', 'OWNERPARTID':'OWNERPARTID', 'NAME':'NAME', 'TEXT':'TEXT'}
    #поэтому сворачиваем регистр для сравнения имён полей
    for key in keys:
        keys[key] = keys[key].casefold()

    #читаем нужные поля основной надписи из соответствующих полей схемного файла
    titleblock = {}
    for line in schematic.lines:
        #анализируем словарь параметров
        if keys['RECORD'] in line and keys['OWNERPARTID'] in line and keys['NAME'] in line and keys['TEXT'] in line:
            if line[keys['RECORD']] == '41' and line[keys['OWNERPARTID']] == '-1':
                if   line[keys['NAME']] == 'TitleBlock_01a_DocumentName': titleblock['01a_product_name'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_01a_DocumentName_line1': titleblock['01a_product_name'] = line[keys['TEXT']] + titleblock.get('01a_product_name', '')
                elif line[keys['NAME']] == 'TitleBlock_01a_DocumentName_line2': titleblock['01a_product_name'] = titleblock.get('01a_product_name', '') + ' ' + line[keys['TEXT']]
                #elif line[keys['NAME']] == 'TitleBlock_01b_DocumentType': titleblock['01b_document_type'] += line[keys['TEXT']]
                #elif line[keys['NAME']] == 'TitleBlock_01b_DocumentType_line1': titleblock['01b_document_type'] = line[keys['TEXT']] + titleblock.get('01b_document_type', '')
                #elif line[keys['NAME']] == 'TitleBlock_01b_DocumentType_line2': titleblock['01b_document_type'] = titleblock.get('01b_document_type', '') + ' ' + line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_02_DocumentDesignator': titleblock['02_document_designator'] = line[keys['TEXT']].rsplit(' ', 1)[0]
                elif line[keys['NAME']] == 'TitleBlock_04_Letter_left': titleblock['04_letter_left'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_04_Letter_middle': titleblock['04_letter_middle'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_04_Letter_right': titleblock['04_letter_right'] = line[keys['TEXT']]
                #elif line[keys['NAME']] == 'TitleBlock_07_SheetNumber': titleblock['07_sheet_index'] = line[keys['TEXT']]
                #elif line[keys['NAME']] == 'TitleBlock_08_SheetTotal': titleblock['08_sheet_total'] = line[keys['TEXT']]        
                elif line[keys['NAME']] == 'TitleBlock_09_Organization': titleblock['09_organization'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_10d_ActivityType_Extra': titleblock['10d_activityType_Extra'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_11a_Name_Designer': titleblock['11a_name_designer'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_11b_Name_Checker': titleblock['11b_name_checker'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_11c_Name_TechnicalSupervisor': titleblock['11c_name_technicalSupervisor'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_11d_Name_Extra': titleblock['11d_name_extra'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_11e_Name_NormativeSupervisor': titleblock['11e_name_normativeSupervisor'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_11f_Name_Approver': titleblock['11f_name_approver'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_13a_SignatureDate_Designer': titleblock['13a_signatureDate_designer'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_13b_SignatureDate_Checker': titleblock['13b_signatureDate_checker'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_13c_SignatureDate_TechnicalSupervisor': titleblock['13c_signatureDate_technicalSupervisor'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_13d_SignatureDate_Extra': titleblock['13d_signatureDate_extra'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_13e_SignatureDate_NormativeSupervisor': titleblock['13e_signatureDate_normativeSupervisor'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_13f_SignatureDate_Approver': titleblock['13f_signatureDate_approver'] = line[keys['TEXT']]
                #elif line[keys['NAME']] == 'TitleBlock_19_OriginalInventoryNumber': titleblock['19_original_inventoryNumber'] = line[keys['TEXT']]
                #elif line[keys['NAME']] == 'TitleBlock_21_ReplacedOriginalInventoryNumber': titleblock['21_replacedOriginal_inventoryNumber'] = line[keys['TEXT']]
                #elif line[keys['NAME']] == 'TitleBlock_22_DuplicateInventoryNumber': titleblock['22_duplicate_inventoryNumber'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_24_BaseDocumentDesignator': titleblock['24_baseDocument_designator'] = line[keys['TEXT']]
                elif line[keys['NAME']] == 'TitleBlock_25_FirstReferenceDocumentDesignator': titleblock['25_firstReferenceDocument_designator'] = line[keys['TEXT']]
    if titleblock:
        if '02_document_designator' in titleblock:
            designator = titleblock.get('02_document_designator', '').strip()
            if designator.endswith('Э3'):
                designator = project.designator[:-2].strip()
                titleblock['02_document_designator'] = designator
        project.titleblock = titleblock
    
    #заполняем свойства проекта
    project.designator = titleblock.get('02_document_designator', '')
    project.name       = titleblock.get('01a_product_name', '')
    project.author     = titleblock.get('11a_name_designer', '')
    print("done.")

#Создание базы данных компонентов из BoM
def parse_bom(database:Components.Database, bom:BoM, **kwargs):
    print(f"{' ' * 12}designer: {designer_name} ({script_baseName})")

    stats = [0, 0]      #статистика [errors, warnings]

    print("INFO >> Parsing BoM data", end ="... ", flush = True)
    for index, entry in enumerate(bom.entries):
        component = _parse_entry(entry.to_dict(), None, stats)
        if isinstance(component, Components.Component.Generic):
            database.insert_entry(component)
            if component.GNRC_accessory_child is not None:
                for child in component.GNRC_accessory_child:
                    database.insert_entry(child)
        else:
            stats[0] += 1
            print(f"\n{' ' * 12}error! parsing bom entry #{index} failed")
    
    if stats[0] + stats[1] == 0: 
        print(f"done ({len(database.entries)} components created)")
    else:
        print(f"\n{' ' * 12}completed with {stats[0]} errors and {stats[1]} warnings")

#разбор компонента
def _parse_entry(bom_entry:dict, parent:Components.Component = None, stats:list = [0, 0], **kwargs) -> Components.Component:
    decimalPoint = '.'

    #определяем тип элемента
    kind = bom_entry['BOM_type']
    if   string_equal(kind, ("Assembly", "Сборка", "Устройство"), False):
        component = Components.Component.Assembly()
    elif string_equal(kind, ("Photocell", "Фотоэлемент", "Photodiode", "Фотодиод", "Phototransistor", "Фототранзистор", "Photoresistor", "Фоторезистор"), False):
        component = Components.Component.Photocell()
    elif string_equal(kind, ("Capacitor", "Конденсатор"), False):
        component = Components.Component.Capacitor()
    elif string_equal(kind, ("Integrated Circuit", "Микросхема"), False):
        component = Components.Component.IntegratedCircuit()
    elif string_equal(kind, ("Fastener", "Крепёж"), False):
        component = Components.Component.Fastener()
    elif string_equal(kind, ("Heatsink", "Радиатор"), False):
        component = Components.Component.Heatsink()
    elif string_equal(kind, ("Circuit Breaker", "Автоматический выключатель", "Fuse", "Предохранитель"), False):
        component = Components.Component.CircuitBreaker()
    elif string_equal(kind, ("Surge protector", "Ограничитель перенапряжения", "TVS", "Супрессор", "GDT", "Разрядник", "Varistor", "Варистор"), False):
        component = Components.Component.SurgeProtector()
    elif string_equal(kind, ("Cell", "Элемент гальванический", "Battery", "Батарея", "Battery holder", "Держатель батареи"), False):
        component = Components.Component.Battery()
    elif string_equal(kind, ("Display", "Дисплей"), False):
        component = Components.Component.Display()
    elif string_equal(kind, ("LED", "Светодиод"), False):
        component = Components.Component.LED()
    elif string_equal(kind, ("Jumper", "Перемычка"), False):
        component = Components.Component.Jumper()
    elif string_equal(kind, ("Relay", "Реле"), False):
        component = Components.Component.Relay()
    elif string_equal(kind, ("Inductor", "Индуктивность", "Choke", "Дроссель"), False):
        component = Components.Component.Inductor()
    elif string_equal(kind, ("Resistor", "Резистор", "Thermistor", "Термистор", "Posistor", "Позистор", "Potentiometer", "Потенциометр", "Rheostat", "Реостат"), False):
        component = Components.Component.Resistor()
    elif string_equal(kind, ("Switch", "Переключатель", "Выключатель", "Button", "Кнопка"), False):
        component = Components.Component.Switch()
    elif string_equal(kind, ("Transformer", "Трансформатор"), False):
        component = Components.Component.Transformer()
    elif string_equal(kind, ("Diode", "Диод", "Zener", "Стабилитрон", "Varicap", "Варикап"), False):
        component = Components.Component.Diode()
    elif string_equal(kind, ("Thyristor", "Тиристор", "TRIAC", "Symistor", "Симистор", "DIAC", "Dynistor", "Динистор"), False):
        component = Components.Component.Thyristor()
    elif string_equal(kind, ("Transistor", "Транзистор"), False):
        component = Components.Component.Transistor()
    elif string_equal(kind, ("Optoisolator", "Оптоизолятор", "Optocoupler", "Оптопара", "Phototriac", "Оптосимистор"), False):
        component = Components.Component.Optoisolator()
    elif string_equal(kind, ("Connector", "Соединитель", "Разъём"), False):
        component = Components.Component.Connector()
    elif string_equal(kind, ("EMI filter", "Фильтр ЭМП"), False):
        component = Components.Component.EMIFilter()
    elif string_equal(kind, ("Crystal", "Resonator", "Резонатор", "Oscillator", "Осциллятор"), False):
        component = Components.Component.Oscillator()
    else:
        component = Components.Component.Generic()
    component.GNRC_kind = kind

    #Fill-in generic attributes
    component.GNRC_accessory_parent  = parent                            #ссылка на родительский компонент
    
    #--- десигнатор
    if 'Designator' in bom_entry:
        designator = bom_entry['Designator'].strip(' ')
        if designator:
            component.GNRC_designator = Designator.parse(designator)
            if component.GNRC_designator is None:
                stats[0] += 1
                print(f"\n{' ' * 12}error! {designator} - can't parse designator", end = '', flush = True)
    
    #--- уникальный идентификатор
    uid_name = bom_entry.get('UniqueIdName')
    uid_path = bom_entry.get('UniqueIdPath')
    if uid_name is not None or uid_name is not None:
        if component.GNRC_uid is None:
            component.GNRC_uid = Components.UID(uid_name, uid_path)

    #--- артикул
    if 'BOM_value' in bom_entry:
        if len(bom_entry['BOM_value'].strip(' ')) > 0:
            component.GNRC_partnumber = bom_entry['BOM_value']

    #--- количество
    if 'Quantity' in bom_entry:
        quantity = bom_entry['Quantity'].strip(' ')
        if quantity:
            try:
                quantity = int(quantity)
                component.GNRC_quantity = quantity
            except ValueError:
                print(f"\n{' ' * 12}error! {quantity} - can't parse quantity", end = '', flush = True)

    #--- производитель
    if 'BOM_manufacturer' in bom_entry:
        if len(bom_entry['BOM_manufacturer'].strip(' ')) > 0:
            component.GNRC_manufacturer = bom_entry['BOM_manufacturer']
    
    #--- установка на плату
    if 'Fitted' in bom_entry:
        if bom_entry['Fitted'] == 'Not Fitted':
            component.GNRC_fitted = False
    
    #--- допустимые замены
    if 'BOM_substitute' in bom_entry:
        substitutes = bom_entry['BOM_substitute']
        if len(substitutes) > 0:                                             #проверяем пустое ли поле
            component.GNRC_substitute = []                                   #создаём пустой список замен чтобы добавлять в него элементы
            substitutes = substitutes.split(';')
            for entry in substitutes:
                tmp = entry.split('*', 1)
                sub_note = None
                if len(tmp) > 1: sub_note = tmp[1].strip(' ')
                tmp = tmp[0].split('@', 1)
                sub_partnumber = tmp[0].strip(' ')
                sub_manufacturer = None
                if len(tmp) > 1: sub_manufacturer = tmp[1].strip(' ')
                component.GNRC_substitute.append(Components.Substitute(sub_partnumber, sub_manufacturer, sub_note))

    #--- параметрическое задание компонента
    if 'BOM_explicit' in bom_entry:
        #есть данные в BoM
        if   string_equal(bom_entry['BOM_explicit'], ('true', 'истина', '1'), False): component.GNRC_parametric = False
        elif string_equal(bom_entry['BOM_explicit'], ('false', 'ложь', '0'), False): component.GNRC_parametric = True
        else: component.GNRC_parametric = False     #значение по-умолчанию если не смогли распознать значение поля
    else:
        #нет данных в BoM
        component.GNRC_parametric = False

    #--- footprint - переводим в package и mount с помощью словарей
    if 'Footprint' in bom_entry:
        package = lib_common.dict_translate(bom_entry['Footprint'], __dict_package, False, False, None)
        if isinstance(package, tuple): component.GNRC_package = Components.Package(package[0], package[1])
        elif isinstance(package, str): component.GNRC_package = Components.Package(package)
        component.GNRC_mount = lib_common.dict_translate(bom_entry['Footprint'], __dict_mount, False, False, Components.MountType.UNKNOWN)

    #--- примечание
    if 'BOM_note' in bom_entry:
        if len(bom_entry['BOM_note'].strip(' ')) > 0:
            component.GNRC_note = bom_entry['BOM_note']

    #--- описание
    if 'BOM_description' in bom_entry:
        if len(bom_entry['BOM_description'].strip(' ')) > 0:
            component.GNRC_description = bom_entry['BOM_description']

    #Разбираем параметры из описания
    if component.GNRC_description is None: descriptionParams = ['']
    else: descriptionParams = [s.strip() for s in component.GNRC_description.split(',')]

    #Сборка (Устройство)
    if type(component) is Components.Component.Assembly:
        pass

    #Фотоэлемент
    elif type(component) is Components.Component.Photocell:
        pass

    #Конденсатор
    elif type(component) is Components.Component.Capacitor:
        #Parsing params
        for i in range(len(descriptionParams)):
            #тип конденсатора
            if component.CAP_type is None:
                if string_equal(descriptionParams[i], ('керамический', 'керам.'), False):
                    component.CAP_type = Components.Component.Capacitor.Type.CERAMIC
                elif string_equal(descriptionParams[i], ('танталовый', 'тантал.'), False):
                    component.CAP_type = Components.Component.Capacitor.Type.TANTALUM
                elif string_equal(descriptionParams[i], ('плёночный', 'плён.'), False):
                    component.CAP_type = Components.Component.Capacitor.Type.FILM
                elif string_equal(descriptionParams[i], ('ионистор', 'суперконд.'), False):
                    component.CAP_type = Components.Component.Capacitor.Type.SUPERCAPACITOR
                elif string_find_any(descriptionParams[i], ('алюминиевый', 'алюм.'), False):
                    if string_find_any(descriptionParams[i], ('электролитический', 'эл-лит'), False):
                        component.CAP_type = Components.Component.Capacitor.Type.ALUM_ELECTROLYTIC
                    elif string_find_any(descriptionParams[i], ('полимерный', 'полим.'), False):
                        component.CAP_type = Components.Component.Capacitor.Type.ALUM_POLYMER
                    else:
                        component.CAP_type = Components.Component.Capacitor.Type.UNKNOWN
                #завершаем обработку если нашли нужный параметр
                if component.CAP_type is not None:   
                    descriptionParams[i] = '' #clear parsed parameter
                    continue

            #тип диэлектрика (температурный коэффициент)
            if component.CAP_dielectric is None:
                #керамические
                if component.CAP_type == Components.Component.Capacitor.Type.CERAMIC:
                    if string_equal(descriptionParams[i], ('COG', 'C0H', 'C0J', 'C0K', 'CCG', 'CGJ', 'M5U', 'NP0', 'P90', 'SL', 'U2J', 'U2K', 'UNJ', 'X0U', 'X5R', 'X5S', 'X6S', 'X6T','X7R', 'X7S', 'X7T', 'X7U', 'X8G', 'X8L', 'X8M', 'X8R', 'X9M', 'Y5E', 'Y5P', 'Y5R', 'Y5U', 'Y5V', 'Z5U', 'Z7S', 'ZLM'), True):
                        component.CAP_dielectric = descriptionParams[i]
                #плёночные
                elif component.CAP_type == Components.Component.Capacitor.Type.FILM:
                    if string_equal(descriptionParams[i], ('PC', 'PEN', 'PET', 'PPS', 'PP', 'PS'), True):
                        component.CAP_dielectric = descriptionParams[i]
                #завершаем обработку если нашли нужный параметр
                if component.CAP_dielectric is not None:   
                    descriptionParams[i] = '' #clear parsed parameter
                    continue

            parsing_result = _parse_param_valueWithTolerance(descriptionParams[i], decimalPoint)
            if parsing_result is not None:
                value, tolerance, locale = parsing_result
                if value is not None:
                    #ёмкость
                    if component.CAP_capacitance is None:
                        if value.unit == lcl.Unit.Name.FARAD:
                            component.CAP_capacitance = Components.ParameterSpec(value, tolerance)
                            descriptionParams[i] = ''
                            continue

                    #напряжение
                    if component.CAP_voltage is None:
                        if value.unit == lcl.Unit.Name.VOLT:
                            component.CAP_voltage = value
                            descriptionParams[i] = ''
                            continue

            #низкое эквивалентное сопротивление
            if string_equal(descriptionParams[i], ("low ESR", "низк. имп."), False):
                component.CAP_lowESR = True
                descriptionParams[i] = ''
                continue

            #класс безопасности
            if component.CAP_safetyRating is None:
                if string_equal(descriptionParams[i], ('X1', 'X2', 'X3', 'Y1', 'Y2', 'Y3'), True):
                    component.CAP_safetyRating = descriptionParams[i]
                    descriptionParams[i] = ''
                    continue

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
        #Parsing params
        for i in range(len(descriptionParams)):
            #тип предохранителя
            if component.CBRK_type is None:
                if string_equal(descriptionParams[i], ('fuse', 'плавкий'), False):
                    component.CBRK_type = Components.Component.CircuitBreaker.Type.FUSE
                elif string_equal(descriptionParams[i], ('PTC resettable', 'самовосстанавливающийся', 'самовосст.'), False):
                    component.CBRK_type = Components.Component.CircuitBreaker.Type.FUSE_PTC_RESETTABLE
                elif string_equal(descriptionParams[i], ('thermal', 'термо'), False):
                    component.CBRK_type = Components.Component.CircuitBreaker.Type.FUSE_THERMAL
                elif string_equal(descriptionParams[i], ('circuit breaker', 'авт. выкл.'), False):
                    component.CBRK_type = Components.Component.CircuitBreaker.Type.BREAKER
                elif string_equal(descriptionParams[i], ('holder', 'держатель'), False):
                    component.CBRK_type = Components.Component.CircuitBreaker.Type.HOLDER
                #завершаем обработку если нашли нужный параметр
                if component.CBRK_type is not None:   
                    descriptionParams[i] = '' #clear parsed parameter
                    continue

            parsing_result = _parse_param_valueWithTolerance(descriptionParams[i], decimalPoint)
            if parsing_result is not None:
                value, tolerance, locale = parsing_result
                if value is not None:
                    #номинальный ток
                    if component.CBRK_current_rating is None:
                        if value.unit == lcl.Unit.Name.AMPERE:
                            component.CBRK_current_rating = value
                            descriptionParams[i] = ''
                            continue

                    #напряжение
                    if component.CBRK_voltage is None:
                        if value.unit == lcl.Unit.Name.VOLT:
                            component.CBRK_voltage = value
                            descriptionParams[i] = ''
                            continue

                    #точка плавления
                    if component.CBRK_meltingPoint is None:
                        if value.unit == lcl.Unit.Name.AMPERE2_SECOND:
                            component.CBRK_meltingPoint = value
                            #фикс неюникода
                            component.GNRC_description = component.GNRC_description.replace('A?s', 'A²s').replace('A^2s', 'A²s')
                            component.GNRC_description = component.GNRC_description.replace('А?с', 'А²с').replace('А^2с', 'А²с')
                            descriptionParams[i] = ''
                            continue

            #классификация скорости срабатывания
            if component.CBRK_speed_grade is None:
                if string_equal(descriptionParams[i], ('fast', 'быстрый', 'быстр.'), False):
                    component.CBRK_speed_grade = Components.Component.CircuitBreaker.SpeedGrade.FAST
                elif string_equal(descriptionParams[i], ('medium', 'средний', 'средн.'), False):
                    component.CBRK_speed_grade = Components.Component.CircuitBreaker.SpeedGrade.MEDIUM
                elif string_equal(descriptionParams[i], ('slow', 'медленный', 'медл.'), False):
                    component.CBRK_speed_grade = Components.Component.CircuitBreaker.SpeedGrade.SLOW
                #завершаем обработку если нашли нужный параметр
                if component.CBRK_speed_grade is not None:   
                    descriptionParams[i] = ''
                    continue

    #Ограничитель перенапряжения
    elif type(component) is Components.Component.SurgeProtector:
        #Определяем тип по разновидности компонента
        if string_equal(component.GNRC_kind, ("TVS", "Супрессор"), False):
            component.SPD_type = Components.Component.SurgeProtector.Type.DIODE
        elif string_equal(component.GNRC_kind, ("Varistor", "Варистор"), False):
            component.SPD_type = Components.Component.SurgeProtector.Type.VARISTOR
        elif string_equal(component.GNRC_kind, ("GDT", "Разрядник"), False):
            component.SPD_type = Components.Component.SurgeProtector.Type.GAS_DISCHARGE_TUBE

        #Parsing params
        for i in range(len(descriptionParams)):
            #направленность
            if component.SPD_bidirectional is None:
                if string_equal(descriptionParams[i], ('однонаправленный', 'однонаправ.'), False):
                    component.SPD_bidirectional = False
                elif string_equal(descriptionParams[i], ('двунаправленный', 'двунаправ.'), False):
                    component.SPD_bidirectional = True
                if component.SPD_bidirectional is not None:   
                    descriptionParams[i] = ''
                    continue

            parsing_result = _parse_param_valueWithToleranceAtConditions(descriptionParams[i], decimalPoint)
            if parsing_result is not None:
                value, tolerance, conditions, locale = parsing_result
                if value is not None:
                    #максимальное рабочее напряжение
                    if component.SPD_voltage_standoff is None:
                        if value.unit == lcl.Unit.Name.VOLT:
                            component.SPD_voltage_standoff = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                _conditions_dump_unparsed(component.SPD_voltage_standoff, conditions)
                            descriptionParams[i] = ''
                            continue

                    #ток гашения выброса
                    if component.SPD_current_clamping is None:
                        if value.unit == lcl.Unit.Name.AMPERE:
                            component.SPD_current_clamping = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                for j in range(len(conditions)):
                                    if isinstance(conditions[j], Components.Quantity):
                                        #форма/длительность импульса перенапряжения
                                        if conditions[j].unit == lcl.Unit.Name.SECOND:
                                            if conditions[j].ismulti(): component.SPD_current_clamping.conditions[Components.ParameterSpec.ConditionType.SURGE_WAVEFORM] = conditions[j]
                                            else:                       component.SPD_current_clamping.conditions[Components.ParameterSpec.ConditionType.SURGE_DURATION] = conditions[j]
                                            conditions[j] = None
                                            continue
                                _conditions_dump_unparsed(component.SPD_current_clamping, conditions)
                            descriptionParams[i] = ''
                            continue

                    #мощность
                    if component.SPD_power is None:
                        if value.unit == lcl.Unit.Name.WATT:
                            component.SPD_power = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                for j in range(len(conditions)):
                                    if isinstance(conditions[j], Components.Quantity):
                                        #форма/длительность импульса перенапряжения
                                        if conditions[j].unit == lcl.Unit.Name.SECOND:
                                            if conditions[j].ismulti(): component.SPD_power.conditions[Components.ParameterSpec.ConditionType.SURGE_WAVEFORM] = conditions[j]
                                            else:                       component.SPD_power.conditions[Components.ParameterSpec.ConditionType.SURGE_DURATION] = conditions[j]
                                            conditions[j] = None
                                            continue
                                _conditions_dump_unparsed(component.SPD_power, conditions)
                            descriptionParams[i] = ''
                            continue

                    #энергия
                    if component.SPD_power is None:
                        if value.unit == lcl.Unit.Name.JOULE:
                            component.SPD_energy = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                for j in range(len(conditions)):
                                    if isinstance(conditions[j], Components.Quantity):
                                        #форма/длительность импульса перенапряжения
                                        if conditions[j].unit == lcl.Unit.Name.SECOND:
                                            if conditions[j].ismulti(): component.SPD_energy.conditions[Components.ParameterSpec.ConditionType.SURGE_WAVEFORM] = conditions[j]
                                            else:                       component.SPD_energy.conditions[Components.ParameterSpec.ConditionType.SURGE_DURATION] = conditions[j]
                                            conditions[j] = None
                                            continue
                                _conditions_dump_unparsed(component.SPD_energy, conditions)
                            descriptionParams[i] = ''
                            continue

    #Батарея
    elif type(component) is Components.Component.Battery:
        #Определяем тип по разновидности компонента
        if string_equal(component.GNRC_kind, ("Battery holder", "Держатель батареи"), False):
            component.BAT_type = Components.Component.Battery.Type.HOLDER
        elif string_equal(component.GNRC_kind, ("Cell", "Элемент гальванический"), False):
            component.BAT_type = Components.Component.Battery.Type.CELL
        elif string_equal(component.GNRC_kind, ("Battery", "Батарея"), False):
            component.BAT_type = Components.Component.Battery.Type.BATTERY
    
        #Parsing params
        for i in range(len(descriptionParams)):
            #тип (ищем признак держателя в описании)
            if component.BAT_type != component.Type.HOLDER:
                if string_equal(descriptionParams[i], ('holder', 'держатель'), False):
                    component.BAT_type = component.Type.HOLDER
                    descriptionParams[i] = ''
                    continue

            #химический тип + возможность заряда
            if component.BAT_chemistry is None:
                if string_equal(descriptionParams[i], ('Zn-MnO2', ), False):
                    component.BAT_chemistry = Components.Component.Battery.Chemistry.ZINC_MANGANESE_DIOXIDE
                    component.BAT_rechargable = False
                elif string_equal(descriptionParams[i], ('Li-MnO2', ), False):
                    component.BAT_chemistry = Components.Component.Battery.Chemistry.LITHIUM_MANGANESE_DIOXIDE
                    component.BAT_rechargable = False
                elif string_equal(descriptionParams[i], ('Li-SOCl2', ), False):
                    component.BAT_chemistry = Components.Component.Battery.Chemistry.LITHIUM_THIONYL_CHLORIDE
                    component.BAT_rechargable = False
                elif string_equal(descriptionParams[i], ('Li-FeS2', ), False):
                    component.BAT_chemistry = Components.Component.Battery.Chemistry.LITHIUM_IRON_DISULFIDE
                    component.BAT_rechargable = False
                elif string_equal(descriptionParams[i], ('Li-CFx', ), False):
                    component.BAT_chemistry = Components.Component.Battery.Chemistry.LITHIUM_CARBON_MONOFLOURIDE
                    component.BAT_rechargable = False
                elif string_equal(descriptionParams[i], ('Li-ion', ), False):
                    component.BAT_chemistry = Components.Component.Battery.Chemistry.LITHIUM_ION
                    component.BAT_rechargable = True
                elif string_equal(descriptionParams[i], ('Li-Po', ), False):
                    component.BAT_chemistry = Components.Component.Battery.Chemistry.LITHIUM_POLYMER
                    component.BAT_rechargable = True
                elif string_equal(descriptionParams[i], ('LiFePO4', ), False):
                    component.BAT_chemistry = Components.Component.Battery.Chemistry.LITHIUM_IRON_PHOSPHATE
                    component.BAT_rechargable = True
                elif string_equal(descriptionParams[i], ('Ni-Cd', ), False):
                    component.BAT_chemistry = Components.Component.Battery.Chemistry.NICKEL_CADMIUM
                    component.BAT_rechargable = True
                elif string_equal(descriptionParams[i], ('Ni-MH', ), False):
                    component.BAT_chemistry = Components.Component.Battery.Chemistry.NICKEL_METAL_HYDRIDE
                    component.BAT_rechargable = True
                elif string_equal(descriptionParams[i], ('Pb-acid', ), False):
                    component.BAT_chemistry = Components.Component.Battery.Chemistry.LEAD_ACID
                    component.BAT_rechargable = True
                elif string_equal(descriptionParams[i], ('Zn-Air', ), False):
                    component.BAT_chemistry = Components.Component.Battery.Chemistry.ZINC_AIR
                    component.BAT_rechargable = False
                elif string_equal(descriptionParams[i], ('Hg', ), False):
                    component.BAT_chemistry = Components.Component.Battery.Chemistry.MERCURY
                    component.BAT_rechargable = False
                elif string_equal(descriptionParams[i], ('Ag-O', ), False):
                    component.BAT_chemistry = Components.Component.Battery.Chemistry.SILVER_OXIDE
                    component.BAT_rechargable = False
                if component.BAT_chemistry is not None:   
                    descriptionParams[i] = ''
                    continue

            parsing_result = _parse_param_valueWithToleranceAtConditions(descriptionParams[i], decimalPoint)
            if parsing_result is not None:
                value, tolerance, conditions, locale = parsing_result
                if value is not None:
                    #номинальное напряжение
                    if component.BAT_voltage is None:
                        if value.unit == lcl.Unit.Name.VOLT:
                            component.BAT_voltage = value
                            descriptionParams[i] = ''
                            continue

                    #ёмкость
                    if component.BAT_capacity is None:
                        if value.unit == lcl.Unit.Name.AMPERE_HOUR:
                            component.BAT_capacity = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                for j in range(len(conditions)):
                                    if isinstance(conditions[j], Components.Quantity):
                                        #напряжение отсечки
                                        if conditions[j].unit == lcl.Unit.Name.VOLT:
                                            component.BAT_capacity.conditions[Components.ParameterSpec.ConditionType.VOLTAGE] = conditions[j]
                                            conditions[j] = None
                                            continue
                                        #ток нагрузки
                                        if conditions[j].unit == lcl.Unit.Name.AMPERE:
                                            component.BAT_capacity.conditions[Components.ParameterSpec.ConditionType.CURRENT] = conditions[j]
                                            conditions[j] = None
                                            continue
                                        #сопротивление нагрузки
                                        if conditions[j].unit == lcl.Unit.Name.OHM:
                                            component.BAT_capacity.conditions[Components.ParameterSpec.ConditionType.RESISTANCE] = conditions[j]
                                            conditions[j] = None
                                            continue
                                        #температура
                                        if conditions[j].unit == lcl.Unit.Name.CELCIUS_DEG:
                                            component.BAT_capacity.conditions[Components.ParameterSpec.ConditionType.TEMPERATURE] = conditions[j]
                                            conditions[j] = None
                                            continue
                                _conditions_dump_unparsed(component.BAT_capacity, conditions)
                            descriptionParams[i] = ''
                            continue

    #Дисплей
    elif type(component) is Components.Component.Display:
        #Parsing params
        for i in range(len(descriptionParams)):
            #тип
            if component.DISP_type is None:
                if string_equal(descriptionParams[i], ('7-seg', '7-сегм.', '7 segment'), False):
                    component.DISP_type = Components.Component.Display.Type.NUMERIC_7SEG
                elif string_equal(descriptionParams[i], ('14-seg', '14-сегм.', '14 segment'), False): 
                    component.DISP_type = Components.Component.Display.Type.ALPHANUMERIC_14SEG
                elif string_equal(descriptionParams[i], ('16-seg', '16-сегм.', '16 segment'), False): 
                    component.DISP_type = Components.Component.Display.Type.ALPHANUMERIC_16SEG
                elif string_equal(descriptionParams[i], ('bar graph', 'шкальный'), False): 
                    component.DISP_type = Components.Component.Display.Type.BARGRAPH
                elif string_equal(descriptionParams[i], ('dot matrix', 'матричный'), False): 
                    component.DISP_type = Components.Component.Display.Type.DOTMATRIX
                elif string_equal(descriptionParams[i], ('graphic', 'графический'), False): 
                    component.DISP_type = Components.Component.Display.Type.GRAPHIC
                if component.DISP_type is not None:   
                    descriptionParams[i] = ''
                    continue

            #структура
            if component.DISP_structure is None:
                if string_equal(descriptionParams[0], ('LED', 'светодиодный'), False):
                    component.DISP_structure = Components.Component.Display.Structure.LED
                elif string_equal(descriptionParams[0], ('OLED', 'орг. светодиодный'), False):
                    component.DISP_structure = Components.Component.Display.Structure.OLED
                elif string_equal(descriptionParams[0], ('LCD', 'жидкокрист.'), False):
                    component.DISP_structure = Components.Component.Display.Structure.LCD
                elif string_equal(descriptionParams[0], ('VFD', 'вак. люм.'), False):
                    component.DISP_structure = Components.Component.Display.Structure.VFD
                if component.DISP_structure is not None:   
                    descriptionParams[i] = ''
                    continue

            #цвет
            if component.DISP_color is None:
                parsing_result = _parse_param_color(descriptionParams[i])
                if parsing_result is not None:
                    component.DISP_color = parsing_result
                    descriptionParams[i] = ''
                    continue

    #Светодиод
    elif type(component) is Components.Component.LED:
        #Parsing params
        for i in range(len(descriptionParams)):
            #цвет
            if component.LED_color is None:
                parsing_result = _parse_param_color(descriptionParams[i])
                if parsing_result is not None:
                    component.LED_color = parsing_result
                    descriptionParams[i] = ''
                    continue

            #индекс цветопередачи
            if component.LED_color_renderingIndex is None:
                if descriptionParams[i].startswith('CRI'):
                    parsing_result = _parse_param_value(descriptionParams[i][3:], decimalPoint)
                    if parsing_result is not None:
                        component.LED_color_renderingIndex = parsing_result[0]
                        descriptionParams[i] = ''
                        continue

            parsing_result = _parse_param_valueWithToleranceAtConditions(descriptionParams[i], decimalPoint)
            if parsing_result is not None:
                value, tolerance, conditions, locale = parsing_result
                if value is not None:
                    #длина волны [основная, пиковая]
                    if (component.LED_color is None) or (component.LED_color <= Components.ColorType.VIOLET):
                        if component.LED_wavelength is None:
                            if value.unit == lcl.Unit.Name.METRE:
                                component.LED_wavelength = value
                                descriptionParams[i] = ''
                                continue

                    #цветовая температура
                    if component.LED_color == Components.ColorType.WHITE:
                        if component.LED_color_temperature is None:
                            if value.unit == lcl.Unit.Name.KELVIN:
                                component.LED_color_temperature = value
                                descriptionParams[i] = ''
                                continue
                        
                    #сила света
                    if component.LED_luminous_intensity is None:
                        if value.unit == lcl.Unit.Name.CANDELA:
                            component.LED_luminous_intensity = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                for j in range(len(conditions)):
                                    if isinstance(conditions[j], Components.Quantity):
                                        #ток
                                        if conditions[j].unit == lcl.Unit.Name.AMPERE:
                                            component.LED_luminous_intensity.conditions[Components.ParameterSpec.ConditionType.CURRENT] = conditions[j]
                                            conditions[j] = None
                                            continue
                                _conditions_dump_unparsed(component.LED_luminous_intensity, conditions)
                            descriptionParams[i] = ''
                            continue

                    #световой поток
                    if component.LED_luminous_flux is None:
                        if value.unit == lcl.Unit.Name.LUMEN:
                            component.LED_luminous_flux = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                for j in range(len(conditions)):
                                    if isinstance(conditions[j], Components.Quantity):
                                        #ток
                                        if conditions[j].unit == lcl.Unit.Name.AMPERE:
                                            component.LED_luminous_flux.conditions[Components.ParameterSpec.ConditionType.CURRENT] = conditions[j]
                                            conditions[j] = None
                                            continue
                                _conditions_dump_unparsed(component.LED_luminous_flux, conditions)
                            descriptionParams[i] = ''
                            continue

                    #угол обзора
                    if component.LED_viewingAngle is None:
                        if value.unit == lcl.Unit.Name.DEGREE:
                            component.LED_viewingAngle = value
                            descriptionParams[i] = ''
                            continue

                    #прямой ток [номинальный, максимальный]
                    if component.LED_current is None:
                        if value.unit == lcl.Unit.Name.AMPERE:
                            component.LED_current = value
                            descriptionParams[i] = ''
                            continue

                    #прямое падение напряжения
                    if component.LED_voltage_forward is None:
                        if value.unit == lcl.Unit.Name.VOLT:
                            component.LED_voltage_forward = value
                            descriptionParams[i] = ''
                            continue

    #Перемычка
    elif type(component) is Components.Component.Jumper:
        #вначале определяем тип перемычки
        if component.JMP_type is None:
            for i in range(len(descriptionParams)):
                if string_equal(descriptionParams[i], ('thermal', 'термо'), False):
                    component.JMP_type = Components.Component.Jumper.Type.THERMAL
                    descriptionParams[i] = ''
                    break
            else:
                #если тип не был распознан среди параметров то перемычка электрическая
                component.JMP_type = Components.Component.Jumper.Type.ELECTRICAL

        #затем анализируем параметры для каждого типа отдельно
        if component.JMP_type == Components.Component.Jumper.Type.ELECTRICAL:
            for i in range(len(descriptionParams)):
                parsing_result = _parse_param_value(descriptionParams[i], decimalPoint)
                if parsing_result is not None:
                    value, locale = parsing_result
                    if value is not None:
                        #электрический ток [рабочий/максимальный]
                        if component.JMP_electrical_current is None:
                            if value.unit == lcl.Unit.Name.AMPERE:
                                component.JMP_electrical_current = value
                                descriptionParams[i] = ''
                                continue
                            
        elif component.JMP_type == Components.Component.Jumper.Type.THERMAL:
            for i in range(len(descriptionParams)):
                parsing_result = _parse_param_value(descriptionParams[i], decimalPoint)
                if parsing_result is not None:
                    value, locale = parsing_result
                    if value is not None:
                        #электрическая ёмкость
                        if component.JMP_electrical_capacitance is None:
                            if value.unit == lcl.Unit.Name.FARAD:
                                component.JMP_electrical_capacitance = value
                                descriptionParams[i] = ''
                                continue
                            
                        #максимальное напряжение электрической изоляции
                        if component.JMP_electrical_voltage_isolation is None:
                            if value.unit == lcl.Unit.Name.VOLT:
                                component.JMP_electrical_voltage_isolation = value
                                descriptionParams[i] = ''
                                continue

                        #термическое сопротивление
                        if component.JMP_thermal_resistance is None:
                            if value.unit == lcl.Unit.Name.CELCIUS_DEG_PER_WATT:
                                component.JMP_thermal_resistance = value
                                descriptionParams[i] = ''
                                continue

                        #термическая проводимость
                        if component.JMP_thermal_conductance is None:
                            if value.unit == lcl.Unit.Name.WATT_PER_CELCIUS_DEG:
                                component.JMP_thermal_conductance = value
                                descriptionParams[i] = ''
                                continue

    #Реле
    elif type(component) is Components.Component.Relay:
        pass

    #Индуктивность
    elif type(component) is Components.Component.Inductor:
        #Определяем тип
        if string_equal(component.GNRC_kind, ("Inductor", "Индуктивность"), False):
            component.IND_type = Components.Component.Inductor.Type.INDUCTOR
        elif string_equal(component.GNRC_kind, ("Choke", "Дроссель"), False):
            component.IND_type = Components.Component.Inductor.Type.CHOKE

        #Parsing params
        for i in range(len(descriptionParams)):
            parsing_result = _parse_param_valueWithToleranceAtConditions(descriptionParams[i], decimalPoint)
            if parsing_result is not None:
                value, tolerance, conditions, locale = parsing_result
                if value is not None:
                    #индуктивность
                    if component.IND_inductance is None:
                        if value.unit == lcl.Unit.Name.HENRY:
                            component.IND_inductance = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                for j in range(len(conditions)):
                                    if isinstance(conditions[j], Components.Quantity):
                                        #напряжение
                                        if conditions[j].unit == lcl.Unit.Name.VOLT:
                                            component.IND_inductance.conditions[Components.ParameterSpec.ConditionType.VOLTAGE] = conditions[j]
                                            conditions[j] = None
                                            continue
                                        #частота
                                        if conditions[j].unit == lcl.Unit.Name.HERTZ:
                                            component.IND_inductance.conditions[Components.ParameterSpec.ConditionType.FREQUENCY] = conditions[j]
                                            conditions[j] = None
                                            continue
                                _conditions_dump_unparsed(component.IND_inductance, conditions)
                            descriptionParams[i] = ''
                            continue

                    #ток [Irms, Isat]
                    if component.IND_current is None:
                        if value.unit == lcl.Unit.Name.AMPERE:
                            component.IND_current = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                for j in range(len(conditions)):
                                    if isinstance(conditions[j], Components.Quantity):
                                        #повышение температуры (для Irms)
                                        if conditions[j].unit == lcl.Unit.Name.CELCIUS_DEG:
                                            component.IND_current.conditions[Components.ParameterSpec.ConditionType.TEMPERATURE_RISE] = conditions[j]
                                            conditions[j] = None
                                            continue
                                        #изменение основного значения (для Isat)
                                        if conditions[j].unit == lcl.Unit.Name.PERCENT:
                                            component.IND_current.conditions[Components.ParameterSpec.ConditionType.PRIMARY_VALUE_DEVIATION] = conditions[j]
                                            conditions[j] = None
                                            continue
                                _conditions_dump_unparsed(component.IND_current, conditions)
                            descriptionParams[i] = ''
                            continue

                    #сопротивление (по постоянному току)
                    if component.IND_resistance is None:
                        if value.unit == lcl.Unit.Name.OHM:
                            component.IND_resistance = value
                            descriptionParams[i] = ''
                            continue

                    #добротность
                    if component.IND_qualityFactor is None:
                        if value.unit == lcl.Unit.Name.VIRTUAL_IND_QFACTOR:
                            component.IND_qualityFactor = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                for j in range(len(conditions)):
                                    if isinstance(conditions[j], Components.Quantity):
                                        #частота
                                        if conditions[j].unit == lcl.Unit.Name.HERTZ:
                                            component.IND_qualityFactor[Components.ParameterSpec.ConditionType.FREQUENCY] = conditions[j]
                                            conditions[j] = None
                                            continue
                                _conditions_dump_unparsed(component.IND_qualityFactor, conditions)
                            descriptionParams[i] = ''
                            continue

                    #частота собственного резонанса
                    if component.IND_selfResonance_frequency is None:
                        if value.unit == lcl.Unit.Name.HERTZ:
                            component.IND_selfResonance_frequency = value
                            descriptionParams[i] = ''
                            continue

            #низкая ёмкость
            if string_equal(descriptionParams[i], ("low cap", "низк. ёмк."), False):
                component.IND_lowCap = True
                descriptionParams[i] = ''
                continue

    #Резистор
    elif type(component) is Components.Component.Resistor:
        #тип
        if string_equal(component.GNRC_kind, ("Resistor", "Резистор"), False):
            component.RES_type = Components.Component.Resistor.Type.FIXED
        elif string_equal(component.GNRC_kind, ("Potentiometer", "Потенциометр", "Rheostat", "Реостат"), False):
            component.RES_type = Components.Component.Resistor.Type.VARIABLE
        elif string_equal(component.GNRC_kind, ("Thermistor", "Термистор", "Posistor", "Позистор"), False):
            component.RES_type = Components.Component.Resistor.Type.THERMAL

        #Parsing params
        for i in range(len(descriptionParams)):
            #структура
            if component.RES_structure is None:
                if   string_equal(descriptionParams[0], ('толстоплёночный', 'толстоплён.'), False):
                    component.RES_structure = Components.Component.Resistor.Structure.THICK_FILM
                elif string_equal(descriptionParams[0], ('тонкоплёночный', 'тонкоплён.'), False):
                    component.RES_structure = Components.Component.Resistor.Structure.THIN_FILM
                elif string_equal(descriptionParams[0], ('металло-плёночный', 'мет-плён.'), False):
                    component.RES_structure = Components.Component.Resistor.Structure.METAL_FILM
                elif string_equal(descriptionParams[0], ('металло-оксидный', 'мет-окс.'), False):
                    component.RES_structure = Components.Component.Resistor.Structure.METAL_OXIDE
                elif string_equal(descriptionParams[0], ('углеродистый', 'углерод.'), False):
                    component.RES_structure = Components.Component.Resistor.Structure.CARBON_FILM
                elif string_equal(descriptionParams[0], ('проволочный', 'провол.'), False):
                    component.RES_structure = Components.Component.Resistor.Structure.WIREWOUND
                elif string_equal(descriptionParams[0], ('керамический', 'керам.'), False):
                    component.RES_structure = Components.Component.Resistor.Structure.CERAMIC
                if component.RES_structure is not None:   
                    descriptionParams[i] = ''
                    continue

            parsing_result = _parse_param_valueWithTolerance(descriptionParams[i], decimalPoint)
            if parsing_result is not None:
                value, tolerance, locale = parsing_result
                if value is not None:
                    #сопротивление
                    if component.RES_resistance is None:
                        if value.unit == lcl.Unit.Name.OHM:
                            component.RES_resistance = Components.ParameterSpec(value, tolerance)
                            descriptionParams[i] = ''
                            continue

                    #напряжение
                    if component.RES_voltage is None:
                        if value.unit == lcl.Unit.Name.VOLT:
                            component.RES_voltage = value
                            descriptionParams[i] = ''
                            continue

                    #мощность
                    if component.RES_power is None:
                        if value.unit == lcl.Unit.Name.WATT:
                            component.RES_power = value
                            descriptionParams[i] = ''
                            continue

                elif tolerance is not None:
                    #ТКС
                    if component.RES_resistance is not None:
                        if component.RES_TCR is None:
                            component.RES_TCR = tolerance
                            descriptionParams[i] = ''
                            continue

    #Переключатель
    elif type(component) is Components.Component.Switch:
        pass

    #Трансформатор
    elif type(component) is Components.Component.Transformer:
        pass

    #Диод
    elif type(component) is Components.Component.Diode:
        #определяем тип по разновидности компонента
        if string_equal(component.GNRC_kind, ("Zener", "Стабилитрон"), False):
            component.DIODE_type = Components.Component.Diode.Type.ZENER
        elif string_equal(component.GNRC_kind, ("Varicap", "Варикап"), False):
            component.DIODE_type = Components.Component.Diode.Type.VARICAP
    
        #Parsing params
        for i in range(len(descriptionParams)):
            #тип диода
            if component.DIODE_type is None:
                if string_equal(descriptionParams[i], ("general purpose", "общего применения", "общ. прим."), False):
                    component.DIODE_type = Components.Component.Diode.Type.GENERAL_PURPOSE
                elif string_equal(descriptionParams[i], ("Schottky", "Шоттки"), False):
                    component.DIODE_type = Components.Component.Diode.Type.SCHOTTKY
                elif string_equal(descriptionParams[i], ("tunnel", "туннельный", ), False):
                    component.DIODE_type = Components.Component.Diode.Type.TUNNEL
                if component.DIODE_type is not None:   
                    descriptionParams[i] = ''
                    continue

            parsing_result = _parse_param_valueWithToleranceAtConditions(descriptionParams[i], decimalPoint)
            if parsing_result is not None:
                value, tolerance, conditions, locale = parsing_result
                if value is not None:
                    #прямой ток
                    if component.DIODE_current_forward is None:
                        if value.unit == lcl.Unit.Name.AMPERE:
                            component.DIODE_current_forward = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                for j in range(len(conditions)):
                                    if isinstance(conditions[j], Components.Quantity):
                                        #температура
                                        if conditions[j].unit == lcl.Unit.Name.CELCIUS_DEG:
                                            component.DIODE_current_forward.conditions[Components.ParameterSpec.ConditionType.TEMPERATURE] = conditions[j]
                                            conditions[j] = None
                                            continue
                                _conditions_dump_unparsed(component.DIODE_current_forward, conditions)
                            descriptionParams[i] = ''
                            continue

                    #обратное напряжение
                    if component.DIODE_voltage_reverse is None:
                        if value.unit == lcl.Unit.Name.VOLT:
                            component.DIODE_voltage_reverse = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                _conditions_dump_unparsed(component.DIODE_voltage_reverse, conditions)
                            descriptionParams[i] = ''
                            continue

                    #максимальная мощность
                    if component.DIODE_power is None:
                        if value.unit == lcl.Unit.Name.WATT:
                            component.DIODE_power = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                for j in range(len(conditions)):
                                    if isinstance(conditions[j], Components.Quantity):
                                        #температура
                                        if conditions[j].unit == lcl.Unit.Name.CELCIUS_DEG:
                                            component.DIODE_power.conditions[Components.ParameterSpec.ConditionType.TEMPERATURE] = conditions[j]
                                            conditions[j] = None
                                _conditions_dump_unparsed(component.DIODE_power, conditions)
                            descriptionParams[i] = ''
                            continue

                    #ёмкость перехода
                    if component.DIODE_capacitance is None:
                        if value.unit == lcl.Unit.Name.FARAD:
                            component.DIODE_capacitance = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                for j in range(len(conditions)):
                                    if isinstance(conditions[j], Components.Quantity):
                                        #напряжение (обратное)
                                        if conditions[j].unit == lcl.Unit.Name.VOLT:
                                            component.DIODE_capacitance.conditions[Components.ParameterSpec.ConditionType.VOLTAGE] = conditions[j]
                                            conditions[j] = None
                                            continue
                                        #частота
                                        if conditions[j].unit == lcl.Unit.Name.HERTZ:
                                            component.DIODE_capacitance.conditions[Components.ParameterSpec.ConditionType.FREQUENCY] = conditions[j]
                                            conditions[j] = None
                                            continue
                                _conditions_dump_unparsed(component.DIODE_capacitance, conditions)
                            descriptionParams[i] = ''
                            continue

                    #время восстановления
                    if component.DIODE_recovery_time is None:
                        if value.unit == lcl.Unit.Name.SECOND:
                            component.DIODE_recovery_time = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                _conditions_dump_unparsed(component.DIODE_recovery_time, conditions)
                            descriptionParams[i] = ''
                            continue

    #Тиристор
    elif type(component) is Components.Component.Thyristor:
        #определяем тип по разновидности компонента
        if string_equal(component.GNRC_kind, ("Thyristor", "Тиристор"), False):
            component.THYR_type = Components.Component.Thyristor.Type.THYRISTOR
        elif string_equal(component.GNRC_kind, ("TRIAC", "Symistor", "Симистор"), False):
            component.THYR_type = Components.Component.Thyristor.Type.TRIAC
        elif string_equal(component.GNRC_kind, ("DIAC", "Dynistor", "Динистор"), False):
            component.THYR_type = Components.Component.Thyristor.Type.DYNISTOR

    #Транзистор
    elif type(component) is Components.Component.Transistor:
        pass

    #Оптоизолятор
    elif type(component) is Components.Component.Optoisolator:
        #Определяем тип по разновидности компонента
        if string_equal(component.GNRC_kind, ("Optocoupler", "Оптопара"), False):
            component.OPTOISO_outputType = Components.Component.Optoisolator.OutputType.TRANSISTOR
        elif string_equal(component.GNRC_kind, ("Phototriac", "Оптосимистор"), False):
            component.OPTOISO_outputType = Components.Component.Optoisolator.OutputType.TRIAC

    #Соединитель
    elif type(component) is Components.Component.Connector:
        #Parsing params
        for i in range(len(descriptionParams)):
            #пол
            if component.CON_gender is None:
                if string_equal(descriptionParams[i], ('plug', 'вилка', 'male', 'папа'), False):
                    component.CON_gender = Components.Component.Connector.Gender.PLUG
                elif string_equal(descriptionParams[i], ('receptacle', 'socket', 'розетка', 'female', 'мама'), False):
                    component.CON_gender = Components.Component.Connector.Gender.RECEPTACLE
                if component.CON_gender is not None:   
                    descriptionParams[i] = ''
                    continue

    #Фильтр ЭМП
    elif type(component) is Components.Component.EMIFilter:
        #Parsing params
        for i in range(len(descriptionParams)):
            #тип фильтра
            if component.EMIF_type is None:
                if string_equal(descriptionParams[0], ('ферритовая бусина', 'фер. бус.'), False):
                    component.EMIF_type = Components.Component.EMIFilter.Type.FERRITE_BEAD
                elif string_equal(descriptionParams[0], ('синфазный дроссель', 'синф. дроссель', 'синф. др.'), False):
                    component.EMIF_type = Components.Component.EMIFilter.Type.COMMON_MODE_CHOKE
                if component.EMIF_type is not None:   
                    descriptionParams[i] = ''
                    continue

            parsing_result = _parse_param_valueWithToleranceAtConditions(descriptionParams[i], decimalPoint)
            if parsing_result is not None:
                value, tolerance, conditions, locale = parsing_result
                if value is not None:
                    #импеданс / активное сопротивление
                    if value.unit == lcl.Unit.Name.OHM:
                        #определяем импеданс или активное сопротивление по условиям
                        resistance_flag = False
                        if conditions:
                            for j in range(len(conditions)):
                                if isinstance(conditions[j], str):
                                    if string_equal(conditions[j], ('DC', ), False):
                                        resistance_flag = True
                                        conditions.pop(j)
                                        break
                        if resistance_flag:
                            #активное сопротивление
                            if component.EMIF_resistance is None:
                                component.EMIF_resistance = Components.ParameterSpec(value, tolerance)
                                if conditions:
                                    _conditions_dump_unparsed(component.EMIF_resistance, conditions)
                                descriptionParams[i] = ''
                                continue
                        else:
                            #импеданс
                            if component.EMIF_impedance is None:
                                component.EMIF_impedance = Components.ParameterSpec(value, tolerance)
                                if conditions:
                                    for j in range(len(conditions)):
                                        if isinstance(conditions[j], Components.Quantity):
                                            #частота
                                            if conditions[j].unit == lcl.Unit.Name.HERTZ:
                                                component.EMIF_impedance.conditions[Components.ParameterSpec.ConditionType.FREQUENCY] = conditions[j]
                                                conditions[j] = None
                                                continue
                                    _conditions_dump_unparsed(component.EMIF_impedance, conditions)
                                descriptionParams[i] = ''
                                continue

                    #индуктивность
                    if component.EMIF_inductance is None:
                        if value.unit == lcl.Unit.Name.HENRY:
                            component.EMIF_inductance = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                for j in range(len(conditions)):
                                    if isinstance(conditions[j], Components.Quantity):
                                        #частота
                                        if conditions[j].unit == lcl.Unit.Name.HERTZ:
                                            component.EMIF_inductance.conditions[Components.ParameterSpec.ConditionType.FREQUENCY] = conditions[j]
                                            conditions[j] = None
                                            continue
                                        #напряжение
                                        if conditions[j].unit == lcl.Unit.Name.VOLT:
                                            component.EMIF_inductance.conditions[Components.ParameterSpec.ConditionType.VOLTAGE] = conditions[j]
                                            conditions[j] = None
                                            continue
                                        #ток
                                        if conditions[j].unit == lcl.Unit.Name.AMPERE:
                                            component.EMIF_inductance.conditions[Components.ParameterSpec.ConditionType.CURRENT] = conditions[j]
                                            conditions[j] = None
                                            continue
                                _conditions_dump_unparsed(component.EMIF_inductance, conditions)
                            descriptionParams[i] = ''
                            continue

                    #ёмкость
                    if component.EMIF_capacitance is None:
                        if value.unit == lcl.Unit.Name.FARAD:
                            component.EMIF_capacitance = Components.ParameterSpec(value, tolerance)
                            if conditions:
                                for j in range(len(conditions)):
                                    if isinstance(conditions[j], Components.Quantity):
                                        #частота
                                        if conditions[j].unit == lcl.Unit.Name.HERTZ:
                                            component.EMIF_capacitance.conditions[Components.ParameterSpec.ConditionType.FREQUENCY] = conditions[j]
                                            conditions[j] = None
                                            continue
                                        #напряжение
                                        if conditions[j].unit == lcl.Unit.Name.VOLT:
                                            component.EMIF_capacitance.conditions[Components.ParameterSpec.ConditionType.VOLTAGE] = conditions[j]
                                            conditions[j] = None
                                            continue
                                _conditions_dump_unparsed(component.EMIF_capacitance, conditions)
                            descriptionParams[i] = ''
                            continue

                    #ток
                    if component.EMIF_current is None:
                        if value.unit == lcl.Unit.Name.AMPERE:
                            component.EMIF_current = value
                            descriptionParams[i] = ''
                            continue

                    #напряжение
                    if component.EMIF_voltage is None:
                        if value.unit == lcl.Unit.Name.VOLT:
                            component.EMIF_voltage = value
                            descriptionParams[i] = ''
                            continue

    #Осциллятор (Резонатор)
    elif type(component) is Components.Component.Oscillator:
        #Определяем тип по разновидности компонента
        if string_equal(component.GNRC_kind, ("Oscillator", "Осциллятор"), False):
            component.OSC_type = Components.Component.Oscillator.Type.OSCILLATOR
        elif string_equal(component.GNRC_kind, ("Resonator", "Резонатор", ), False):
            component.OSC_type = Components.Component.Oscillator.Type.RESONATOR
        
        #Parsing params
        for i in range(len(descriptionParams)):
            #тип резонатора
            if component.OSC_structure is None:
                if string_equal(descriptionParams[i], ('кварцевый', 'кварц.'), False):
                    component.OSC_structure = Components.Component.Oscillator.Structure.QUARTZ
                elif string_equal(descriptionParams[i], ('керамический', 'керам.'), False):
                    component.OSC_structure = Components.Component.Oscillator.Structure.CERAMIC
                if component.OSC_structure is not None:   
                    descriptionParams[i] = ''
                    continue

            parsing_result = _parse_param_valueWithTolerance(descriptionParams[i], decimalPoint)
            if parsing_result is not None:
                value, tolerance, locale = parsing_result
                if value is not None:
                    #частота
                    if component.OSC_frequency is None:
                        if value.unit == lcl.Unit.Name.HERTZ:
                            component.OSC_frequency = Components.ParameterSpec(value, tolerance)
                            descriptionParams[i] = ''
                            continue

                    #ёмкость нагрузки
                    if component.OSC_loadCapacitance is None:
                        if value.unit == lcl.Unit.Name.FARAD:
                            component.OSC_loadCapacitance = value
                            descriptionParams[i] = ''
                            continue

                    #эквивалентное последовательное сопротивление
                    if component.OSC_ESR is None:
                        if value.unit == lcl.Unit.Name.OHM:
                            component.OSC_ESR = value
                            descriptionParams[i] = ''
                            continue

                    #уровень возбуждения
                    if component.OSC_driveLevel is None:
                        if value.unit == lcl.Unit.Name.WATT:
                            component.OSC_driveLevel = value
                            descriptionParams[i] = ''
                            continue
                        
                elif tolerance is not None:
                    #стабильность частоты
                    if component.OSC_frequency is not None:
                        if component.OSC_stability is None:
                            component.OSC_stability = tolerance
                            descriptionParams[i] = ''
                            continue

            #гармоника
            if component.OSC_overtone is None:
                if string_equal(descriptionParams[i], ('fundamental', 'фунд.'), False):
                    component.OSC_overtone = 1
                elif string_equal(descriptionParams[i], ('3rd overtone', '3 гарм.'), False):
                    component.OSC_overtone = 3
                if component.OSC_overtone is not None:   
                    descriptionParams[i] = ''
                    continue

    #Неопознанный элемент
    else:
        pass

    #распознаём параметры из описания общие для всех типов 
    for i in range(len(descriptionParams)):
        #тип монтажа и типоразмер
        if component.GNRC_mount is None or component.GNRC_size is None:
            if _parse_param_mountandsize(descriptionParams[i], component):
                descriptionParams[i] = '' #clear parsed parameter
                continue

        #сборка !!!TODO сделать нормально
        parsing_result = _parse_param_array(descriptionParams[i])
        if parsing_result is not None:
            component.GNRC_array = parsing_result
            descriptionParams[i] = ''
            continue

        #диапазон рабочих температур
        if component.GNRC_temperatureRange is None:
            parsing_result = _parse_param_range(descriptionParams[i], decimalPoint)
            if parsing_result is not None:
                value, locale = parsing_result
                if value.unit == lcl.Unit.Name.CELCIUS_DEG:
                    component.GNRC_temperatureRange = value
                    descriptionParams[i] = ''
                    continue

    #собираем нераспознанные параметры в список
    for param in descriptionParams:
        if param: component.GNRC_misc.append(param)

    #--- сопутсвующие компоненты
    if 'BOM_accessory' in bom_entry:
        accessories = bom_entry['BOM_accessory']
        if len(accessories) > 0:                                            #проверяем пустое ли поле
            component.GNRC_accessory_child = []                              #создаём пустой список чтобы добавлять в него элементы
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

                accessory_component = _parse_entry(accessory_bom, component, stats)
                accessory_component.GNRC_quantity *= component.GNRC_quantity          #количество дочернего компонента умножается на количество родительского
                component.GNRC_accessory_child.append(accessory_component)

    return component

#добавляет список нераспознанных условий (если они есть) в специальную запись в словаре условий параметра
def _conditions_dump_unparsed(parameter:Components.ParameterSpec, conditions:list) -> None:
    result = []
    for condition in conditions:
        if condition: result.append(condition)
    if result:
        parameter.conditions[Components.ParameterSpec.ConditionType.UNPARSED] = result

#разбор параметра: тип монтажа и типоразмер
def _parse_param_mountandsize(param:str, component):
    mount = None
    package_type = None
    if string_find_any(param, ('чип', )):
        mount = Components.MountType.SURFACE
    elif string_find_any(param, ('выводной', )):
        mount = Components.MountType.THROUGHHOLE
    elif string_find_any(param, ('аксиальный', 'акс.')):
        mount = Components.MountType.THROUGHHOLE
        package_type = Components.Package.Type.ThroughHole.AXIAL
    elif string_find_any(param, ('радиальный', 'рад.')):
        mount = Components.MountType.THROUGHHOLE
        package_type = Components.Package.Type.ThroughHole.RADIAL
    elif string_find_any(param, ('циллиндрический', 'цил.')):
        mount = Components.MountType.HOLDER
        package_type = Components.Package.Type.Holder.CYLINDRICAL
    elif string_find_any(param, ('ножевой', 'нож.')):
        mount = Components.MountType.HOLDER
        package_type = Components.Package.Type.Holder.BLADE

    if mount is not None:
        component.GNRC_mount = mount
        tmp = param.rsplit(' ', 1)
        if len(tmp) > 1:
            component.GNRC_size = tmp[1]
        return True
    else:
        return False

#разбор параметра: значение с указанием допуска при условиях
def _parse_param_valueWithToleranceAtConditions(param:str, decimalPoint:str = '.', normalize:bool|tuple[bool] = False, locale:lcl.Locale = None) -> tuple[Components.Quantity, Components.Tolerance, list, lcl.Locale]:
    if param is not None:
        #удаляем пробелы с краёв
        param = param.strip(' ')
        
        #проверяем есть ли что-нибудь
        if len(param.replace(' ', '')) > 0:
            valueToleranceAndConditions = param.split('@', 1)
            if len(valueToleranceAndConditions) > 1:
                conditions = _parse_param_conditions(valueToleranceAndConditions[1], decimalPoint, normalize, locale)
            else:
                conditions = None
            valueAndTolerance = _parse_param_valueWithTolerance(valueToleranceAndConditions[0], decimalPoint, normalize, locale)  
            if valueAndTolerance is not None:
                value, tolerance, locale = valueAndTolerance
                if value is not None or tolerance is not None or conditions is not None:
                    return value, tolerance, conditions, locale
            else:
                if conditions is not None:
                    return None, None, conditions, locale
    return None

#разбор параметра: условия
def _parse_param_conditions(param:str, decimalPoint:str = '.', normalize:bool = False, locale:lcl.Locale = None) -> list:
    if param is not None:
        param = param.strip()
        #проверяем осталось ли что-нибудь
        if len(param) > 0:
            #меняем десятичный разделитель на точку
            param = param.replace(decimalPoint, '.')
            
            conditions = param.split('&')
            result = []
            for condition in conditions:
                condition = condition.strip()
                if condition:
                    quantity = _parse_param_value(condition, decimalPoint, normalize, locale)
                    if quantity is not None:
                        quantity = quantity[0]
                        if normalize:
                            quantity.normilize(True)
                        result.append(quantity)
                    else:
                        result.append(condition)
            if len(result) > 0:
                return result
    return None

#разбор параметра: значение с указанием допуска
def _parse_param_valueWithTolerance(param:str, decimalPoint:str = '.', normalize:bool|tuple[bool] = False, locale:lcl.Locale = None) -> tuple[Components.Quantity, Components.Tolerance, lcl.Locale]:
    if param is not None:
        #удаляем все пробелы
        param = param.replace(' ', '')
        
        #проверяем есть ли что-нибудь
        if len(param) > 0:
            if isinstance(normalize, bool): normalize = (normalize, normalize)
            value, tolerance = _parse_param_splitValueAndTolerance(param)
            value = _parse_param_value(value, decimalPoint, normalize[0], locale)
            if value is not None:
                value, locale = value
            tolerance = _parse_param_tolerance(tolerance, decimalPoint, normalize[1], locale)
            if tolerance is not None:
                tolerance, locale = tolerance
            if value is not None or tolerance is not None:
                return value, tolerance, locale
    return None

#разбор параметра: разделение значения и его допуска
#TODO сделать чтобы нормально отделяло нулевой допуск
def _parse_param_splitValueAndTolerance(param:str) -> tuple[str, str]:
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

            return value, tolerance
    return None

#разбор параметра: значение
def _parse_param_value(param:str, decimalPoint:str = '.', normalize:bool = False, locale:lcl.Locale = None) -> tuple[Components.Quantity, lcl.Locale]:
    if param is not None:
        #удаляем все пробелы
        param = param.replace(' ', '')
        
        #проверяем осталось ли что-нибудь
        if len(param) > 0:
            #меняем десятичный разделитель на точку
            param = param.replace(decimalPoint, '.')
            
            #разделяем значение и единицы измерения
            param_numeric, param_unit = _parse_param_splitNumberAndUnit(param, "0123456789.+-/e")

            #определяем префикс и единицу измерения
            units = _parse_param_unit(param_unit)
            if units is None: return None
            unit, prefix, locale = units

            #разделяем многозначный параметр и преобразуем его составляющие в числа
            param_numeric = param_numeric.split('/')
            try:
                value = [float(v) for v in param_numeric]
            except ValueError:
                return None 
            
            #создаём объект
            quantity = Components.Quantity(value, unit, prefix)
            if normalize: quantity.normilize(True)

            return quantity, locale
    return None

#разбор параметра: диапазон
def _parse_param_range(param:str, decimalPoint:str = '.', normalize:bool = False, locale:lcl.Locale = None) -> tuple[Components.QuantityRange, lcl.Locale]:
    if param is not None:
        #удаляем все пробелы
        param = param.replace(' ', '')
        
        #проверяем осталось ли что-нибудь
        if len(param) > 0:
            #меняем десятичный разделитель на точку
            param = param.replace(decimalPoint, '.')

            #разделяем значение и единицы измерения
            param_numeric, param_unit = _parse_param_splitNumberAndUnit(param, "0123456789.±+-e…")

            #определяем префикс и единицу измерения
            units = _parse_param_unit(param_unit, locale)
            if units is None: return None               #не удалось распознать единицы измерения
            unit, prefix, locale = units
            if unit == lcl.Unit.Name.NONE: return None  #единицы измерения не указаны

            #определяем формат записи и преобразуем значения в числа
            if param_numeric.startswith('±'):
                #одинаковые значения в обе стороны (задано явно) -> убираем символ и попадаем в неявный обработчик
                param_numeric = param_numeric[1:]
            if '…' in param_numeric:
                #разные значения в + и -
                value = param_numeric.split('…')
                
                try:
                    value[0] = float(value[0])
                    value[1] = float(value[1])
                except ValueError:
                    return None
                
                #определяем где какая сторона
                if value[0] < value[1]:
                    value = [value[0], value[1]]
                else:
                    value = [value[1], value[0]]   
            else:
                #одинаковые значения в обе стороны (без указания '±' - задано неявно)
                try:
                    value = float(param_numeric)
                    value = [-value, value]
                except ValueError:
                    return None

            #создаём объект
            quantity_range = Components.QuantityRange(value, unit, prefix)
            if normalize: quantity_range.normilize(True)

            return quantity_range, locale
    return None

#разбор параметра: допуск
def _parse_param_tolerance(param:str, decimalPoint:str = '.', normalize:bool = False, locale:lcl.Locale = None) -> tuple[Components.Tolerance, lcl.Locale]:
    param_range = _parse_param_range(param, decimalPoint, normalize, locale)
    if param_range is not None:
        magnitude = param_range[0].magnitude
        unit      = param_range[0].unit
        prefix    = param_range[0].prefix
        locale    = param_range[1]
        if magnitude[0] == 0 and magnitude[1] == 0:
            #обе стороны равны 0 -> допуска нет
            return None
        elif (magnitude[0] > 0 and magnitude[1] > 0) or (magnitude[0] < 0 and magnitude[1] < 0):
            #обе стороны положительные или отрицательные -> ошибка
            return None
        else:
            #создаём объект
            tolerance = Components.Tolerance(magnitude, unit, prefix)
            if normalize: tolerance.normilize(True)
            return tolerance, locale
    return None

#разбор параметра: сборка
def _parse_param_array(param:str) -> Components.Array:
    if string_startswith(param, ("array", "сборка"), False):
        result = Components.Array()
        
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
            if   string_equal(asm_type, ('I', 'IND'), True): result.type = Components.Array.Type.INDEPENDENT
            elif string_equal(asm_type, ('A', 'CA' ), True): result.type = Components.Array.Type.COMMON_ANODE
            elif string_equal(asm_type, ('C', 'CC' ), True): result.type = Components.Array.Type.COMMON_CATHODE
            elif string_equal(asm_type, ('S', 'SER'), True): result.type = Components.Array.Type.SERIES
            elif string_equal(asm_type, ('P', 'PAR'), True): result.type = Components.Array.Type.PARALLEL
            elif string_equal(asm_type, ('M', 'MTX'), True): result.type = Components.Array.Type.MATRIX
            else:                                            result.type = Components.Array.Type.UNKNOWN

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
            result.block_count = asm_blocks
            result.elements_per_block = asm_elements
        return result
    return None

#разбор параметра: цвет
def _parse_param_color(param:str) -> Components.ColorType:
    if len(param) > 0:
        if string_equal(param, ('white', 'белый'), False):
            return Components.ColorType.WHITE
        elif string_equal(param, ('red', 'красный'), False):
            return Components.ColorType.RED
        elif string_equal(param, ('orange', 'оранжевый'), False):
            return Components.ColorType.ORANGE
        elif string_equal(param, ('amber', 'янтарный'), False):
            return Components.ColorType.AMBER
        elif string_equal(param, ('yellow', 'жёлтый'), False):
            return Components.ColorType.YELLOW
        elif string_equal(param, ('lime', 'салатовый'), False):
            return Components.ColorType.LIME
        elif string_equal(param, ('green', 'зелёный'), False):
            return Components.ColorType.GREEN
        elif string_equal(param, ('turquoise', 'бирюзовый'), False):
            return Components.ColorType.TURQUOISE
        elif string_equal(param, ('cyan', 'голубой'), False):
            return Components.ColorType.CYAN
        elif string_equal(param, ('blue', 'синий'), False):
            return Components.ColorType.BLUE
        elif string_equal(param, ('violet', 'фиолетовый'), False):
            return Components.ColorType.VIOLET
        elif string_equal(param, ('purple', 'пурпурный'), False):
            return Components.ColorType.PURPLE
        elif string_equal(param, ('pink', 'розовый'), False):
            return Components.ColorType.PINK
        elif string_equal(param, ('infrared', 'инфракрасный'), False):
            return Components.ColorType.INFRARED
        elif string_equal(param, ('ultraviolet', 'ультрафиолетовый'), False):
            return Components.ColorType.ULTRAVIOLET
        elif string_equal(param, ('multicolor', 'многоцветный'), False):
            return Components.ColorType.MULTI
    return None

#разбор параметра: разделение числовой части и единиц измерения
def _parse_param_splitNumberAndUnit(param:str, numeric_chars:str = "0123456789.+-/e") -> tuple[str, str]:
    if param is not None and numeric_chars is not None:
        param = param.replace(' ', '')
        NUMCHARSET = set(numeric_chars)
        for pos, char in enumerate(param):
            if char not in NUMCHARSET:
                #нашли единицы измерения
                return param[:pos], param[pos:]
        #единиц измерения нет
        return param, ''
    return None

#разбор параметра: единица измерения
def _parse_param_unit(token:str, locale:lcl.Locale = None) -> tuple[lcl.Unit.Name, lcl.Unit.Prefix, lcl.Locale]:
    if token is not None:
        token = token.replace(' ', '')
        if token:
            if locale is None: locale_list = list(lcl.Locale)
            else:              locale_list = [locale]
            result_unit = None
            result_prefix = None
            for locale in locale_list:
                for value, unit in _prefixedUnitsMap[locale][1].items():
                    if token.endswith(value):
                        token = token[0:-len(value)]
                        result_unit = unit
                        break
                else:
                    #не распознали единицу измерения -> смотрим следующую локаль
                    continue
                if token:
                    for value, prefix in _prefixedUnitsMap[locale][0].items():
                        if token == value:
                            result_prefix = prefix
                            break
                    else:
                        #не распознали приставку -> смотрим следующую локаль
                        continue
                else:
                    #приставки нет
                    result_prefix = lcl.Unit.Prefix.NONE
                #нашли единицу измерения -> возвращаем результат
                return result_unit, result_prefix, locale
            else:
                #не нашли совпадений ни в одной локали -> возвращаем None
                return None
        else:
            #строка пустая -> возвращаем безразмерное значение в исходной локали
            return lcl.Unit.Name.NONE, lcl.Unit.Prefix.NONE, locale
    return None

#возвращает карту со всеми вариантами префиксов и единиц измерения
def _build_prefixedUnitsMap():
    map = {}
    for locale in lcl.Locale:
        map_prefix = {}
        for prefix in lcl.Unit.Prefix:
            value = prefix.value[locale.value]
            if isinstance(value, tuple):
                for sub in value:
                    map_prefix[sub] = prefix
            elif value:
                map_prefix[value] = prefix
        map_prefix = dict(sorted(map_prefix.items(), key=lambda kv: len(kv[0]), reverse=True))
        map_unit = {}
        for unit in lcl.Unit.Name:
            value = unit.value[locale.value]
            if isinstance(value, tuple):
                for sub in value:
                    map_unit[sub] = unit
            elif value:
                map_unit[value] = unit
        map_unit = dict(sorted(map_unit.items(), key=lambda kv: len(kv[0]), reverse=True))
        map[locale] = [map_prefix, map_unit]
    return map
_prefixedUnitsMap = _build_prefixedUnitsMap()

#Проверка базы данных компонентов
def check(database, **kwargs):
    print("INFO >> Checking data (designer)", end ="... ")
    complaints = Components.Database.Complaints()

    #проверяем чтобы у одинаковых артикулов одного типа элементов были одинаковые остальные поля
    for i in range(len(database.entries)):
        for j in range(i+1, len(database.entries)):
            if database.entries[i].GNRC_kind == database.entries[j].GNRC_kind:
                if database.entries[i].GNRC_partnumber == database.entries[j].GNRC_partnumber and \
                    (database.entries[i].GNRC_description != database.entries[j].GNRC_description or \
                     database.entries[i].GNRC_package != database.entries[j].GNRC_package):
                    database.entries[i].flag = Components.Component.FlagType.WARNING
                    database.entries[j].flag = Components.Component.FlagType.WARNING
                    complaints.warning += 1
                    print(f"\n{' ' * 12}warning! {database.entries[i].GNRC_designator} | {database.entries[j].GNRC_designator} - data mismatch", end = '', flush = True)

    #проверяем наличие обязательных полей (основной параметр, допуск и т.п.)
    for component in database.entries:
        #конденсатор
        if type(component) is Components.Component.Capacitor:
            #ёмкость
            if component.CAP_capacitance is None:
                print(f"\n{' ' * 12}error! {component.GNRC_designator} - capacitance not specified", end = '', flush = True)
                complaints.error += 1
            else:
                #допуск
                if component.CAP_capacitance.tolerance is None:
                    print(f"\n{' ' * 12}error! {component.GNRC_designator} - capacitance tolerance not specified", end = '', flush = True)
                    complaints.error += 1
            #напряжение
            if component.CAP_voltage is None:
                print(f"\n{' ' * 12}error! {component.GNRC_designator} - voltage not specified", end = '', flush = True)
                complaints.error += 1
        
        #индуктивность
        elif type(component) is Components.Component.Inductor:
            #индуктивность
            if component.IND_inductance is None:
                print(f"\n{' ' * 12}error! {component.GNRC_designator} - inductance not specified", end = '', flush = True)
                complaints.error += 1
            else:
                #допуск
                if component.IND_inductance.tolerance is None:
                    print(f"\n{' ' * 12}error! {component.GNRC_designator} - inductance tolerance not specified", end = '', flush = True)
                    complaints.error += 1
            #ток
            if component.IND_current is None:
                print(f"\n{' ' * 12}error! {component.GNRC_designator} - current not specified", end = '', flush = True)
                complaints.error += 1
        
        #резистор
        elif type(component) is Components.Component.Resistor:
            #сопротивление
            if component.RES_resistance is None:
                print(f"\n{' ' * 12}error! {component.GNRC_designator} - resistance not specified", end = '', flush = True)
                complaints.error += 1
            else:
                #допуск
                if component.RES_resistance.tolerance is None:
                    print(f"\n{' ' * 12}error! {component.GNRC_designator} - resistance tolerance not specified", end = '', flush = True)
                    complaints.error += 1

    #проверяем соответствие типоразмера в описании и корпуса для определённых типов компонентов
    for component in database.entries:
        if component.GNRC_size is not None and component.GNRC_package is not None:
            #проверяем стандартные и формованные чипы
            issue_flag = False
            if component.GNRC_package.type == Components.Package.Type.Surface.CHIP or \
                component.GNRC_package.type == Components.Package.Type.Surface.MOLDED:
                if component.GNRC_size != component.GNRC_package.name:
                    issue_flag = True
            #проверяем конденсаторы-"бочонки" TODO: придумать решение костыля с единицами иизмерения
            elif type(component) is Components.Component.Capacitor and \
                (component.GNRC_package.type == Components.Package.Type.Surface.VCHIP or \
                component.GNRC_package.type == Components.Package.Type.ThroughHole.AXIAL or \
                component.GNRC_package.type == Components.Package.Type.ThroughHole.RADIAL):
                issue_flag = True
                if string_endswith(component.GNRC_size, ('mm', 'мм'), caseSensitive = True):
                    size = component.GNRC_size[0:-2].replace(' ', '').replace(',', '.').replace('*', '×').split('×')
                    package = component.GNRC_package.name.replace(' ', '').replace(',', '.').replace('*', '×').split('×')
                    if len(size) == len(package):
                        for i in range(len(size)):
                            try:
                                if float(size[i]) != float(package[i]): break
                            except ValueError:
                                break
                        else:
                            issue_flag = False
            if issue_flag:
                component.flag = Components.Component.FlagType.ERROR
                complaints.error += 1
                print(f"\n{' ' * 12}error! {component.GNRC_designator} - size and package mismatch", end = '', flush = True)

    #проверяем пустые поля в допустимых заменах
    for component in database.entries:
        if component.GNRC_substitute is not None:
            issue_flag = False
            for entry in component.GNRC_substitute:
                if entry.partnumber is None or len(entry.partnumber.strip(' ')) == 0:
                    issue_flag = True
                    break
                if entry.manufacturer is not None and len(entry.manufacturer.strip(' ')) == 0:
                    issue_flag = True
                    break
                if entry.note is not None and len(entry.note.strip(' ')) == 0:
                    issue_flag = True
                    break
            if issue_flag:
                component.flag = Components.Component.FlagType.WARNING
                complaints.warning += 1
                print(f"\n{' ' * 12}warning! {component.GNRC_designator} - empty fields in substitute data", end = '', flush = True)

    if complaints.none(): 
        print("ok.")  
    else:
        print(f"\n{' ' * 12}completed: {complaints.critical} critical, {complaints.error} errors, {complaints.warning} warnings.")
    return complaints

#========================================================== END Designer functions =================================================

# --------------------------------------------------------------- Dictionaties -----------------------------------------------------
#Словарь корпус - посадочное место
__dict_package = { #запятые на концах чтобы запись с одним значением воспринималась как массив значений, а не массив символов в строке
    #чипы
    ('0201', Components.Package.Type.Surface.CHIP):     ('MLCC_0201', 'RC_0201', 'FBC_0201'),
    ('0402', Components.Package.Type.Surface.CHIP):     ('MLCC_0402', 'RC_0402', 'JC_0402', 'LC_0402-0.50', 'FBC_0402', 'LEDC_0402-0.50'),
    ('0603', Components.Package.Type.Surface.CHIP):     ('MLCC_0603', 'SFCC_0603', 'RC_0603', 'LC_0603-1.00', 'FBC_0603', 'FUC_0603', 'LEDC_0603', 'LEDC_0603-0.75'),
    ('0606', Components.Package.Type.Surface.CHIP):     'LEDC_0606-0.50_3IND',
    ('0612', Components.Package.Type.Surface.CHIP):     'JC_0612',
    ('0805', Components.Package.Type.Surface.CHIP):     ('MLCC_0805', 'SFCC_0805', 'RC_0805', 'LC_0805-1.25', 'FBC_0805', 'FUC_0805', 'LEDC_0805', 'LEDC_0805-0.75', 'LEDC_0805-0.45_2IND'),
    ('0806', Components.Package.Type.Surface.CHIP):     'LC_0806-1.60',
    ('1008', Components.Package.Type.Surface.CHIP):     'LC_1008-2.00',
    ('1206', Components.Package.Type.Surface.CHIP):     ('MLCC_1206', 'SFCC_1206', 'RC_1206', 'LC_1206-1.60', 'FBC_1206', 'FUC_1206', 'LEDC_1206', 'LEDC_1206-1.80D_2IND'),
    ('1209', Components.Package.Type.Surface.CHIP):     ('LEDC_1209-2.40', 'LEDC_1209-2.40D_2IND'),
    ('1210', Components.Package.Type.Surface.CHIP):     ('MLCC_1210', 'SFCC_1210', 'RC_1210', 'LC_1210-2.50', 'FBC_1210'),
    ('1218', Components.Package.Type.Surface.CHIP):     'RC_1218',
    ('1225', Components.Package.Type.Surface.CHIP):     'JC_1225',
    ('1808', Components.Package.Type.Surface.CHIP):     'MLCC_1808',
    ('1812', Components.Package.Type.Surface.CHIP):     ('MLCC_1812', 'LC_1812-3.20', 'FBC_1812'),
    ('1913', Components.Package.Type.Surface.CHIP):     'SFCC_1913',
    ('2010', Components.Package.Type.Surface.CHIP):     'RC_2010',
    ('2211', Components.Package.Type.Surface.CHIP):     'MLCC_2211',
    ('2220', Components.Package.Type.Surface.CHIP):     ('MLCC_2220', 'VC_2220'),
    ('2225', Components.Package.Type.Surface.CHIP):     'MLCC_2225',
    ('2410', Components.Package.Type.Surface.CHIP):     'FUC_2410',
    ('2416', Components.Package.Type.Surface.CHIP):     'SFCC_2416',
    ('2512', Components.Package.Type.Surface.CHIP):     'RC_2512',
    ('A',    Components.Package.Type.Surface.MOLDED):   re.compile(r"^CCM_3216-18"),
    ('B',    Components.Package.Type.Surface.MOLDED):   re.compile(r"^CCM_3528-21"),
    ('C',    Components.Package.Type.Surface.MOLDED):   re.compile(r"^CCM_6032-28"),
    ('D',    Components.Package.Type.Surface.MOLDED):   re.compile(r"^CCM_7343-31"),
    ('E',    Components.Package.Type.Surface.MOLDED):   re.compile(r"^CCM_7260-38"),
    ('X',    Components.Package.Type.Surface.MOLDED):   re.compile(r"^CCM_7343-43"),
    #конденсаторы
    ('5×6',     Components.Package.Type.Surface.VCHIP):         'CAP_RSMD_5.0x6.0',
    ('5×11',    Components.Package.Type.ThroughHole.RADIAL):    'CAP_RTH_05x11-2.0-0.5',
    ('5×7',     Components.Package.Type.Surface.VCHIP):         'CAP_RSMD_5.0x7.0',
    ('6×12',    Components.Package.Type.ThroughHole.RADIAL):    'CAP_RTH_06x12-2.5-0.5',
    ('6.3×5.7', Components.Package.Type.Surface.VCHIP):         'CAP_RSMD_6.3x5.7',
    ('6.3×7',   Components.Package.Type.Surface.VCHIP):         'CAP_RSMD_6.3x7.0',
    ('6.3×8',   Components.Package.Type.Surface.VCHIP):         'CAP_RSMD_6.3x8.0',
    ('6.3×9.7', Components.Package.Type.Surface.VCHIP):         'CAP_RSMD_6.3x9.7',
    ('8×6.7',   Components.Package.Type.Surface.VCHIP):         'CAP_RSMD_8.0x6.7',
    ('8×7',     Components.Package.Type.Surface.VCHIP):         'CAP_RSMD_8.0x7.0',
    ('8×7.5',   Components.Package.Type.Surface.VCHIP):         'CAP_RSMD_8.0x7.5',
    ('8×9.7',   Components.Package.Type.Surface.VCHIP):         'CAP_RSMD_8.0x9.7',
    ('8×12',    Components.Package.Type.ThroughHole.RADIAL):    'CAP_RTH_08x12-3.5-0.6',
    ('8×12.2',  Components.Package.Type.Surface.VCHIP):         'CAP_RSMD_8.0x12.2',
    ('10×10.2', Components.Package.Type.Surface.VCHIP):         'CAP_RSMD_10.0x10.2',
    ('10×12',   Components.Package.Type.ThroughHole.RADIAL):    'CAP_RTH_10x12-5.0-0.6',
    ('10×12.2', Components.Package.Type.Surface.VCHIP):         'CAP_RSMD_10.0x12.2',
    ('10×12.6', Components.Package.Type.Surface.VCHIP):         'CAP_RSMD_10.0x12.6',
    ('10×16',   Components.Package.Type.ThroughHole.RADIAL):    'CAP_RTH_10x16-5.0-0.6',
    ('10×19',   Components.Package.Type.ThroughHole.RADIAL):    re.compile(r"^CAP_RTH_10x19"),
    ('13×20',   Components.Package.Type.ThroughHole.RADIAL):    re.compile(r"^CAP_RTH_13x20"),
    ('18×36',   Components.Package.Type.ThroughHole.RADIAL):    'CAP_RTH_18x36-7.5-0.8',
    ('18×60',   Components.Package.Type.ThroughHole.RADIAL):    re.compile(r"^CAP_RTH_18x60"),
    ('20×40',   Components.Package.Type.ThroughHole.RADIAL):    re.compile(r"^CAP_RTH_20x40"),
    #индуктивности
    ('3×3×1.5',         Components.Package.Type.Surface.NONSTANDARD): 'LQH3NP*M',
    ('4.9×4.9×4',       Components.Package.Type.Surface.NONSTANDARD): 'LQH5BP*38',
    ('5×5×2.2',         Components.Package.Type.Surface.NONSTANDARD): 'LQH5BP*T0',
    ('3.2×2.5×1.7',     Components.Package.Type.Surface.NONSTANDARD): 'LQH32P*N',
    ('4.5×3.2×2.8',     Components.Package.Type.Surface.NONSTANDARD): 'LQH43MN*03',
    ('4×4×1.8',         Components.Package.Type.Surface.NONSTANDARD): 'LQH44P*P0',
    ('5×4.8×3.3',       Components.Package.Type.Surface.NONSTANDARD): 'SDR0503',
    ('7×7×3.22',        Components.Package.Type.Surface.NONSTANDARD): 'SLF7030',
    ('7×7×4.8',         Components.Package.Type.Surface.NONSTANDARD): 'SLF7045',
    ('10.1×10.1×4.8',   Components.Package.Type.Surface.NONSTANDARD): 'SLF10145',
    ('5×5×4',           Components.Package.Type.Surface.NONSTANDARD): 'SRN5040',
    ('6×6×2.8',         Components.Package.Type.Surface.NONSTANDARD): 'SRN6028',
    ('6×6×4.5',         Components.Package.Type.Surface.NONSTANDARD): 'SRN6045TA',
    ('5.7×5.2×3',       Components.Package.Type.Surface.NONSTANDARD): 'SRP5030T',
    ('6.6×6.4×5',       Components.Package.Type.Surface.NONSTANDARD): 'SRP6050CA',
    ('6.5×6.5×3',       Components.Package.Type.Surface.NONSTANDARD): 'SRR0603',
    ('6.5×6.5×4.8',     Components.Package.Type.Surface.NONSTANDARD): 'SRR0604',
    ('12.7×12.7×8.5',   Components.Package.Type.Surface.NONSTANDARD): 'SRR1208',
    ('12×12×10',        Components.Package.Type.Surface.NONSTANDARD): 'SRR1210',
    ('12.5×12.5×8',     Components.Package.Type.Surface.NONSTANDARD): 'SRR1280',
    ('3.8×3.8×2',       Components.Package.Type.Surface.NONSTANDARD): 'SRR3818A',
    ('6.8×6.8×4',       Components.Package.Type.Surface.NONSTANDARD): 'SRR6038',
    ('10×10×3.1',       Components.Package.Type.Surface.NONSTANDARD): 'SRU1028',
    ('10×10×4.1',       Components.Package.Type.Surface.NONSTANDARD): 'SRU1038',
    ('10×10×5.1',       Components.Package.Type.Surface.NONSTANDARD): 'SRU1048',
    #резонаторы/осцилляторы
    '2-SMD (3215)': '2-SMD_3215-0.9',
    '2-SMD (5032)': '2-SMD_5032-1.1',
    '4-SMD (2520)': '4-SMD_2520-0.55',
    '4-SMD (3225)': ('4-SMD_3225-0.75', '4-SMD_3225-1.20'),
    '4-SMD (5032)': '4-SMD_5032-1.1',
    '4-SMD (7050)': '4-SMD_7050-1.30',
    'HC-49/US':     'HC-49/US',
    'HC-49/US-SMD': 'HC-49/US-SMD',
    #диоды/транзисторы/мелкие микросхемы
    ('SMA', Components.Package.Type.Surface.MOLDED): re.compile(r"^DO-214AC"),
    ('SMB', Components.Package.Type.Surface.MOLDED): re.compile(r"^DO-214AA"),
    ('SMC', Components.Package.Type.Surface.MOLDED): re.compile(r"^DO-214AB"),
    'SOD-80': 'SOD-80',
    'SOD-123': 'SOD-123',
    'SOD-123F': 'SOD-123F',
    'SOD-323': 'SOD-323',
    'SOD-323F': 'SOD-323F',
    'SOD-523F': 'SOD-523F',
    'TO-92': 'TO-92-V',
    'TO-220': 'TO-220-V',
    'TO-220AB': ('TO-220AB-H', 'TO-220AB-V'),
    'TO-247AC': 'TO-247AC-V',
    'TO-269AA': 'TO-269AA',
    'DPAK': re.compile(r"^TO-252"),
    'D²PAK': re.compile(r"^TO-263AB"),
    'SOT-5': 'SOT-5',
    'SOT-23': ('SOT-23', 'SOT-23-3'),
    'SOT-23-5': 'SOT-23-5',
    'SOT-23-6': 'SOT-23-6',
    'SOT-23-8': 'SOT-23-8',
    'SOT-89': 'SOT-89',
    'SOT-143': 'SOT-143',
    'SOT-223': 'SOT-223',
    'SOT-223-6': 'SOT-223-6',
    'SOT-323': ('SOT-323', 'SOT-323-3'),
    'SOT-323-5': 'SOT-323-5',
    'SOT-323-6': 'SOT-323-6',
    'SOT-416': 'SOT-416',
    #микросхемы - DIP
    'DIP-4': 'DIP-4',
    'DIP-6': 'DIP-6',
    'DIP-8': 'DIP-8',
    #микросхемы - SOIC
    'SO-8': ('SO-8', 'SO-8-EP', 'SO-8-OC'),
    'SO-8W': 'SO-8W',
    'SO-14': 'SO-14',
    'SO-16': 'SO-16',
    'SO-16W': 'SO-16W',
    'SO-16W-IC': 'SO-16W-IC',
    'SO-20W': 'SO-20W',
    'SO-20W-IC': 'SO-20W-IC',
    'SO-24W': 'SO-24W',
    #микросхемы - SOP
    'SOP-28W': 'SOP-28W',
    #микросхемы - TSOP
    'TSOP-II-54': 'TSOP2-54',
    #микросхемы - TSSOP
    'TSSOP-8': ('TSSOP-8', 'TSSOP-8_3.0x3.0-0.65-4.0', 'TSSOP-8_3.0x3.0-0.65-4.9', 'TSSOP-8_4.4x3.0-0.65'),
    'TSSOP-14': ('TSSOP-14', 'HTSSOP-14'),
    'TSSOP-16': 'TSSOP-16',
    'TSSOP-20': 'TSSOP-20',
    'TSSOP-24': 'TSSOP-24',
    'TSSOP-28': ('TSSOP-28', 'HTSSOP-28'),
    'TSSOP-56': 'TSSOP-56',
    #микросхемы - SSOP
    'SSOP-8': 'SSOP-8',
    'SSOP-16': 'SSOP-16',
    'SSOP-28': 'SSOP-28',
    #микросхемы - MSOP
    'MSOP-8': ('MSOP-8', 'MSOP-8-EP'),
    'MSOP-10': 'MSOP-10',
    'MSOP-16': ('MSOP-16', 'MSOP-16(12)-2.4.13.15'),
    #микросхемы - VSSOP
    'VSSOP-8': ('VSSOP-8_2.3x2.0-0.50', 'VSSOP-8_3.0x3.0-0.65', ),
    #микросхемы - uSOP
    'uSOP-10': 'uSOP-10',
    #микросхемы - QSOP
    'QSOP-20': 'QSOP-20',
    'QSOP-24': 'QSOP-24',
    #микросхемы - QFP
    'LQFP-48': 'LQFP-48',
    'LQFP-64': ('LQFP-64', 'LQFP-64-EP5.00'),
    'LQFP-100': 'LQFP-100',
    'LQFP-144': ('LQFP-144', 'LQFP-144-EP7.20'),
    'LQFP-256': ('LQFP-144', 'LQFP-256-EP9.40'),
    'TQFP-32': ('TQFP-32', 'HTQFP-32'),
    'TQFP-44': 'TQFP-44',
    'TQFP-64': 'TQFP-64',
    'TQFP-128': 'TQFP-128-EP10.0',
    #микросхемы - DFN
    'DFN': ('MSDFN-16_10.0x13.0x3.1-1.27', 'MSDFN-16_10.0x14.0x3.1-1.27', 'MSDFN-20_10.0x13.0x3.1-1.27', 'MSDFN-20_10.0x14.0x3.1-1.27'), #MORNSUN isolators
    'DFN-10': 'DFN-10_3.0x3.0-0.50',
    'TDFN-8': ('TDFN-8_2.0x2.0-0.50', 'TDFN-8_3.0x3.0-0.65'),
    'UFDFN-10': 'UFDFN-10_1.0x2.5-0.50',
    'WDFN-6': 'WDFN-6_2.0x2.0-0.65',
    #микросхемы - QFN
    'QFN-16': 'QFN-16_3.0x3.0-0.50',
    'MQFN-88': 'MQFN-88_10.0x10.0-0.40',
    'SQFN-48': 'SQFN-48_7.0x7.0-0.50',
    'VQFN-16': 'VQFN-16_4.0x4.0-0.65',
    'VQFN-20': 'VQFN-20_5.0x5.0-0.65',
    'VQFN-24': 'VQFN-24_4.0x4.0-0.50',
    'VQFN-32': ('VQFN-32_5.0x5.0-0.50', 'VQFN-32_5.0x5.0-0.50'),
    'VQFN-36': 'VQFN-36_6.0x6.0-0.50',
    'VQFN-40': 'VQFN-40_5.0x5.0-0.40',
    'VQFN-48': 'VQFN-48_6.0x6.0-0.40',
    'VQFN-56': 'VQFN-56_8.0x8.0-0.50',
    'VQFN-64': 'VQFN-64_8.0x8.0-0.40',
    'WQFN-16': 'WQFN-16_3.0x3.0-0.50',
    'WQFN-24': ('WQFN-24_4.0x4.0-0.50', 'WQFN-24_4.0x5.0-0.50', ),
    #микросхемы - SON
    'USON-6': 'USON-6_2.0x2.0-0.65',
    'WSON-6': 'WSON-6_2.0x2.0-0.65',
    'WSON-8': ('WSON-8_2.0x2.0-0.50', 'WSON-8_6.0x5.0-1.27', 'WSON-8_8.0x6.0-1.27'), #дичь от производителей - разные корпуса с одним названием
    #микросхемы - BGA
    'FBGA-96': 'FBGA-96-9x16_11.00x14.00-0.80',
    'FCPBGA-624': 'FCPBGA-624-25x25_21.00x21.00-0.80',
    'LFBGA-272': 'LFBGA-272-18x18-0.80_16.00x16.00-1.70',
    'PBGA-416': 'PBGA-416_26x26-1.00_27.00x27.00-2.23',
    'UFBGA-201': 'UFBGA-201-15x15-0.65_10.00x10.00-0.65',
    'WFBGA-153': 'WFBGA-153-14x14_11.50x13.00-0.50',
    'WFBGA-169': 'WFBGA-169-14x28_14.00x18.00-0.50'
}

#Словарь тип монтажа - посадочное место
__dict_mount = { #запятые на концах чтобы запись с одним значением воспринималась как массив значений, а не массив символов в строке
    #поверхностный
    Components.MountType.SURFACE: (
        #резисторы
        re.compile(r"^RC_"), 
        #перемычки
        re.compile(r"^JC_"), 
        #конденсаторы
        re.compile(r"^MLCC_"), re.compile(r"^SFCC_"), re.compile(r"^CCM_"), re.compile(r"^CAP_RSMD_"),
        #индуктивности
        re.compile(r"^LC_"), re.compile(r"^LQH\d"), re.compile(r"^SDR\d{4}"), re.compile(r"^SLF\d{4}"), re.compile(r"^SRN\d{4}"), re.compile(r"^SRP\d{4}"), re.compile(r"^SRR\d{4}"), re.compile(r"^SRU\d{4}"),
        #диоды
        re.compile(r"^DO-214"), re.compile(r"^SOD-"), re.compile(r"^PowerDI"),
        #транзисторы
        re.compile(r"^PowerPAK-"), re.compile(r"^PowerVDFN-"),
        #микросхемы
        re.compile(r"^S?SOT-\d"), #SOT
        re.compile(r"^SO-\d"), #SO
        re.compile(r'^(?:HTS?|TS?|S?|M?|Q?|VS?|u?)SOP-\d'), re.compile(r'^TSOP2-\d'), #SOP
        re.compile(r'^(?:U?|W?)SON-\d'), #SON
        re.compile(r'^(?:MS?|T?|U?|UF?|V?|W?)DFN-\d'), #DFN
        re.compile(r'^(?:M?|Q?|S?|V?|W?)QFN-\d'), #QFN
        re.compile(r'^(?:HT?|L?|T?)QFP-\d'), #QFP
        re.compile(r"^TO-(?:252|263|269)"), #TO
        re.compile(r"^DIP-\d+-GW"), #DIP
        re.compile(r'^(?:F?|FCP?|LF?|P?|UF?|WF?)BGA-\d'), #BGA
        #оптоэлектроника
        re.compile(r"^LEDC_"), re.compile(r"^KPBA-"), re.compile(r"^KPBDA-"), "KM2520*03", "PLCC-6", "XP-C", "XQ-E-HD", "XQ-E-HI",
        "TEMD5510FX01",
        re.compile(r"^SOP-4"), "SO-8-OC",
        #защитные элементы
        re.compile(r"^FUC_"), re.compile(r"^VC_"),
        re.compile(r"^MF-MSMF"), re.compile(r"^RXEF-"), 
        #фильтры ЭМП
        re.compile(r"^FBC_"), re.compile(r"^CMC_4SMD_"), 
        #разное
        re.compile(r"^2-SMD_"), re.compile(r"^4-SMD_"), "SG7050", "SG-8002JF"
        "HC-49/US-SMD",
        "BR-2477A-FBN",
        re.compile(r"^FK244-"),
        re.compile(r"^SMTSO-"),
        #GNSS
        "GNSS_adapter", "G7A", "L26", "LC79D", "ML8088s", "NEO-M8",
        #источники питания
        re.compile(r"^SMD-8(5)_"),
        #реле
        "IMxxG",
        #датчики
        re.compile(r"^6-SMD_"),
        #переключатели
        re.compile(r"^DTSM-"), "KSC2xxJ", "PTS647-Sx38", "TVCM16", "MS-22D18", re.compile(r"^DHN-"), re.compile(r"^CHS-"),
        #системы на модуле
        "MG-RK3568-3535",
        #трансформаторы
        "749020023A", "H5008", "HX11xx", "PT61020EL", "SM-LP-5001",
        #соединители
        "1734035", "HDMI-S-RA-TSMT", "MUSB-B5-S-VT-TSMT", #Interface
        "78800-0001", "1473005-4", "2041119", re.compile(r"^2199230-"), "5035000993", "DM3CS-SF", "SIM8060-6-1", #Card slot
        "U.FL-R-SMT-1(01)", #RF & coax
        re.compile(r'^PLS-\d+(?:\.\d+)?-\d+(?:R)?S'), re.compile(r'^PBS-\d+(?:\.\d+)?-\d+(?:R)?S'), #PLS/PBS
        re.compile(r'^PLD-\d+(?:\.\d+)?-\d+(?:R)?S'), re.compile(r'^PBD-\d+(?:\.\d+)?-\d+(?:R)?S'), #PLD/PBD
        re.compile(r'^IDC-\d+(?:\.\d+)?-\d+[MF](?:R)?S'), #IDC
        re.compile(r'^PH-\d+M(?:R)?S'), re.compile(r'^PHD-\d+M(?:R)?S'), #PH/PHD
        "FI-RE51S-HF", #FI-R
        re.compile(r"^DS1020-03-\d+MR?"), #DS1020-03
    ),
    #полу-поверхностный
    Components.MountType.SEMI_SURFACE: (
        #соединители
        "5-1903015-1", "47080-4001", "06780050xx", "10029449-111RLF", "MF3.0-1x02MR-SMD-PF"
    ),
    #выводной
    Components.MountType.THROUGHHOLE: (
        #резисторы
        re.compile(r"^RT_"),
        "POT_3006P", "POT_CA9-V10",
        #конденсаторы
        re.compile(r"^CAP_RTH_"), re.compile(r"^CTD_"), re.compile(r"^K15-5_"), re.compile(r"^B32021_"),
        "DEC-9.0-C4", 
        #индуктивности
        re.compile(r"^LT_"),
        #диоды
        re.compile(r"^DO-201"),
        "WXXM",
        #микросхемы
        re.compile(r"^TO-(?:92|220|247)"), #TO
        re.compile(r"^(?:P?|C?)DIP-\d+(?!-GW)"), #DIP
        #оптоэлектроника
        re.compile(r"^LEDT_"),
        "Bx56-11", "Cx56-12", "Dx08-11", "FYA-R102510xBx", "PSx08-11", "Sx08-21", "553-2222-100F", "553-xx22",
        re.compile(r"^PDT_"),
        re.compile(r"^HFBR-\d{2}"),
        #защитные элементы
        re.compile(r"^VT_"), 
        "ZH242", "ZH250",
        #фильтры ЭМП
        "PLT09H",
        #разное
        "HC-49/US",
        "1/10D", "CR1/2AA-S-PCBD", "CR2477NFH", "TL-2450", "BH-25F-1", "BH-32F-1",
        "FK22", "FK216SACB",
        "0906-0",
        #источники питания
        re.compile(r"^PB_DIP-"), re.compile(r"^DOSA-HalfBrick-"), re.compile(r"^DOSA-QuarterBrick-"),
        re.compile(r"^AM1G-"), re.compile(r"^AM1S-"), re.compile(r"^AM2D-"), re.compile(r"^AM2G-"), re.compile(r"^AM3T-"),
        "U(V)RB_ZP-6WR3", "WRB_S-3WR2",
        re.compile(r"^TEN\d"), re.compile(r"^TRN1-"),
        #реле
        "BS-115C", "RTx74xxx", "RZxx-5.0", "РГК55",
        #датчики
        re.compile(r"^PEC11R-"), "HX0x-P", "LV25-P",
        #переключатели
        "SWT-20", "SSSF012100", re.compile(r"^SWD-"), re.compile(r"^SMTS-"),
        #трансформаторы
        "EFD-20", "EFD-30/15/9"
        #соединители
        "292303", "1734510-1", "2041517-1", "5787617", "651005136421", "UE25BE5510H", #Interface
        "5-1814400-1", "5-1814807", "132203-18", "132203-18RP", "731310240" "NB8405A-9000", #RF & coax
        re.compile(r'^PLS-\d+(?:\.\d+)?-\d+(?:R$|R-|-|$)'), re.compile(r'^PBS-\d+(?:\.\d+)?-\d+(?:R$|R-|-|$)'), #PLS/PBS
        re.compile(r'^PLD-\d+(?:\.\d+)?-\d+(?:R$|R-|-|$)'), re.compile(r'^PBD-\d+(?:\.\d+)?-\d+(?:R$|R-|-|$)'), #PLD/PBD
        re.compile(r'^IDC-\d+(?:\.\d+)?-\d+[MF](?:R$|R-|-|$)'), #IDC
        re.compile(r"^2EDG[RV]C-"), #2EDG
        re.compile(r'^2CDG[RV]M-'), #2CDG
        re.compile(r'^15EDG[RV]C-'), #15EDG
        re.compile(r'^DG308-'), #DG308
        re.compile(r'^STL1550/'), #STL1550
        "09-45-551-1102", "52-42-5224-8P(TJ8P8C)", "5521-S6P(TJ11-6P6C)", "ARJM11D7-502-NN", "DS1126", "SS-60000-009", #TJ
        re.compile(r"^WF-\d+[MF]R?"), #WF
        re.compile(r"^DBS-\d+[MF]R?"), re.compile(r"^DHR-\d+[MF]R?"), re.compile(r"^DSUB-2-\d+[MF]R?"), #D-SUB
        re.compile(r"^PWL-\d+[MF]R?"), #PWL
        re.compile(r"^WAGO-236-"), #WAGO
        re.compile(r'^PH-\d+M(?:R$|R-|-|$)'), re.compile(r'^PHD-\d+M(?:R$|R-|-|$)'), #PH/PHD
        "MF3.0-1x02MR-TH-PP", #MF3.0
        re.compile(r"^DIN41612-"), #DIN41612
        re.compile(r"^SP-M\d"), re.compile(r"^SPSH-M\d"), re.compile(r"^SR-M\d"), re.compile(r"^SRSH-M\d"), re.compile(r"^MSAS-\d+P(?:MM|FF)[PR]"), re.compile(r"^MSDS-\d+P(?:MM|FF)[PR]"), #M series
        re.compile(r"^AMP_EI-\d+R?"), #AMP EI series
        "54-00167", #Barrel
        "39-53-2044", #ZIF
        re.compile(r"^СН6-"), #СН6,
        re.compile(r"^СН2М-"), #СН2М
        re.compile(r"^2РМ"), #2РМ
        re.compile(r"^СНЦ23-") #СНЦ23
      ),
    #на край
    Components.MountType.EDGE: (
        "SMA-J-PCB-EL", #RF & coax
        re.compile(r'^PLS-\d+(?:\.\d+)?-\d+(?:R)?E'), re.compile(r'^PBS-\d+(?:\.\d+)?-\d+(?:R)?E'), #PLS/PBS
        re.compile(r'^PLD-\d+(?:\.\d+)?-\d+(?:R)?E'), re.compile(r'^PBD-\d+(?:\.\d+)?-\d+(?:R)?E'), #PLD/PBD
        re.compile(r'^IDC-\d+(?:\.\d+)?-\d+[MF](?:R)?E'), #IDC
        re.compile(r"^EDGE-"), #EDGE
    ),
    #на корпус
    Components.MountType.CHASSIS: (
        #защитные элементы
        "ДПБ",
    ),
    #в держатель
    Components.MountType.HOLDER: (
        '<HOLDER>', #заглушка
    )
}
#============================================================== END Dictionaries =====================================================