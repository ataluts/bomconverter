import os
import csv
import copy
from datetime import datetime
from dict_locale import LocaleIndex     #словарь с локализациями

_module_dirname = os.path.dirname(__file__)                                     #адрес папки со словарём
now = datetime.now()                                                            #текущее дата/время

#================================================================================= Общие настройки =================================================================================
_settings_generic_locale                            = LocaleIndex.RU.value      #локализация

#--------------------------------------------------------------------------------------- csv ---------------------------------------------------------------------------------------
#настройки импорта из csv (базовые)
_settings_generic_csv_import = {
    'encoding'                                      : 'cp1251',                     #кодировка
    'dialect'                                       : {                             #диалект csv (вместо параметров ниже можно указать имя встроенного диалекта, например 'excel', 'excel-tab' или 'unix')
        'delimiter'                                     : ',',                          #разделитель значений
        'doublequote'                                   : True,                         #заменять " на "" в значениях
        'escapechar'                                    : None,                         #символ экранирования
        'lineterminator'                                : '\r\n',                       #окончание строки
        'quotechar'                                     : '"',                          #"кавычки" для значений со спецсимволами
        'quoting'                                       : csv.QUOTE_ALL,                #метод заключения значений в "кавычки"
        'skipinitialspace'                              : False                         #пропускать пробел следующий сразу за разделителем
    }
}

#настройки экспорта в csv (базовые)
_settings_generic_csv_export = {
    'encoding'                                      : 'cp1251',                     #кодировка
    'dialect'                                       : {                             #диалект csv (вместо параметров ниже можно указать имя встроенного диалекта, например 'excel', 'excel-tab' или 'unix')
        'delimiter'                                     : ',',                          #разделитель значений
        'doublequote'                                   : True,                         #заменять " на "" в значениях
        'escapechar'                                    : None,                         #символ экранирования
        'lineterminator'                                : '\r\n',                       #окончание строки
        'quotechar'                                     : '"',                          #"кавычки" для значений со спецсимволами
        'quoting'                                       : csv.QUOTE_ALL,                #метод заключения значений в "кавычки"
        'skipinitialspace'                              : False                         #пропускать пробел следующий сразу за разделителем
    },
    'replace'                                       : {                             #замена символов
        '¹'                                             : '^1',                         #верхний индекс 1
        '²'                                             : '^2',                         #верхний индекс 2
        '³'                                             : '^3',                         #верхний индекс 3
        '⁴'                                             : '^4',                         #верхний индекс 4
        '℃'                                            : '°C',                         #градус Цельсия
        '\n'                                            : '|'                           #перенос строки
    }
}

#------------------------------------------------------------------------------- Список компонентов --------------------------------------------------------------------------------
#настройки экспорта СК в xlsx (базовые)
_settings_generic_cl_xlsx_export = {
    'locale_index'                                  : _settings_generic_locale,     #локализация
    'content_accs_location'                         : 'sheet',                      #расположение аксессуаров {'sheet' - на отдельном листе | 'start' - в начале общего списка | 'end' - в конце общего списка}
    'content_accs_indent'                           : 1,                            #отступ (в строках) списка аксесуаров от списка компонентов при размещении на одном листе
    'format_groupvalue_delimiter'                   : ', ',                         #разделитель значений в полях с группировкой значений
    'format_singlevalue_delimiter'                  : '|',                          #разделитель значений в полях с одиночным значением
    #'book_title'                                    : '',                           #название              <- свойства книги
    #'book_subject'                                  : '',                           #тема
    #'book_author'                                   : '',                           #автор, кем изменено
    #'book_manager'                                  : '',                           #руководитель
    #'book_company'                                  : '',                           #организация
    #'book_category'                                 : '',                           #категории
    #'book_keywords'                                 : '',                           #теги
    #'book_created'                                  : datetime(Y, M, D, h, m, s),   #создан, изменён
    #'book_comments'                                 : '',                           #примечания
    #'book_status'                                   : '',                           #состояние
    #'book_hyperlink'                                : '',                           #база гиперссылки      ^
    'book_style'                                    : {                              #стили в книге
        'row'                                           : {                             #строки
            'generic'                                       : None,
            'header'                                        : {'valign': 'vcenter', 'bold':True, 'font_color':'#000000', 'bg_color':'#99CCFF', 'align':'center'},
            'ok'                                            : {'valign': 'vcenter', 'bold':False, 'font_color':'green'},
            'warning'                                       : {'valign': 'vcenter', 'bold':False, 'font_color':'orange'},
            'error'                                         : {'valign': 'vcenter', 'bold':False, 'font_color':'red'}
        },
        'col'                                           : {                             #столбцы
            'desig'                                         : {'width': 50.0, 'valign': 'vcenter'},
            'kind'                                          : {'width': 25.0, 'valign': 'vcenter'},
            'value'                                         : {'width': 25.0, 'valign': 'vcenter'},
            'description'                                   : {'width': 60.0, 'valign': 'vcenter'},
            'package'                                       : {'width': 15.0, 'valign': 'vcenter'},
            'mfr'                                           : {'width': 25.0, 'valign': 'vcenter'},
            'quantity'                                      : {'width':  8.0, 'valign': 'vcenter'},
            'note'                                          : {'width': 36.0, 'valign': 'vcenter'},
            'subst_orig_value'                              : {'width': 25.0, 'valign': 'vcenter'},
            'subst_orig_mfr'                                : {'width': 25.0, 'valign': 'vcenter'},
            'subst_orig_quantity'                           : {'width': 15.0, 'valign': 'vcenter'},
            'subst_desig'                                   : {'width': 70.0, 'valign': 'vcenter'},
            'subst_quantity'                                : {'width': 15.0, 'valign': 'vcenter'},
            'subst_value'                                   : {'width': 25.0, 'valign': 'vcenter'},
            'subst_mfr'                                     : {'width': 25.0, 'valign': 'vcenter'},
            'subst_note'                                    : {'width': 44.0, 'valign': 'vcenter'}
        }
    }
}

#-------------------------------------------------------------------------------- Основная надпись ---------------------------------------------------------------------------------
#значения основной надписи (базовые)
_settings_generic_titleblock = {                                                            #если тип значения 'tuple' то оно будет добавлено к уже имеющемуся в полученных данных
    #'01a_product_name'                              : '',                           #графа 1  - наименование изделия
    #'01b_document_type'                             : '',                           #графа 1  - наименование документа
    #'02_document_designator'                        : '',                           #графа 2  - обозначение документа
    #'04_letter_left'                                : '',                           #графа 4  - литера (левая)
    #'04_letter_middle'                              : '',                           #графа 4  - литера (средняя)
    #'04_letter_right'                               : '',                           #графа 4  - литера (правая)
    '07_sheet_index'                                : '',                           #графа 7  - порядковый номер листа
    '08_sheet_total'                                : '',                           #графа 8  - общее количество листов документа
    #'09_organization'                               : '',                           #графа 9  - наименование или код организации, выпускающей документ
    '10d_activityType_extra'                        : '',                           #графа 10 - характер работы, выполняемой лицом, подписывающим документ: дополнительная строка
    #'11a_name_designer'                             : '',                           #графа 11 - фамилия лица разработавшего документ
    #'11b_name_checker'                              : '',                           #графа 11 - фамилия лица проверившего документ
    '11c_name_technicalSupervisor'                  : '',                           #графа 11 - фамилия технического контролёра
    '11d_name_extra'                                : '',                           #графа 11 - фамилия в дополнительной строке
    #'11e_name_normativeSupervisor'                  : '',                           #графа 11 - фамилия нормоконтролёра
    #'11f_name_approver'                             : '',                           #графа 11 - фамилия лица утвердившего документ
    '13a_signatureDate_designer'                    : now.strftime('%d.%m.%Y'),     #графа 13 - дата подписания лица разработавшего документ
    '13b_signatureDate_checker'                     : now.strftime('%d.%m.%Y'),     #графа 13 - дата подписания лица проверившего документ
    '13c_signatureDate_technicalSupervisor'         : now.strftime('%d.%m.%Y'),     #графа 13 - дата подписания технического контролёра
    '13d_signatureDate_extra'                       : '',                           #графа 13 - дата подписания в дополнительной строке
    '13e_signatureDate_normativeSupervisor'         : now.strftime('%d.%m.%Y'),     #графа 13 - дата подписания нормоконтролёра
    '13f_signatureDate_approver'                    : now.strftime('%d.%m.%Y'),     #графа 13 - дата подписания лица утвердившего документ
    '19_original_inventoryNumber'                   : '',                           #графа 19 - инвентарный номер подлинника
    '21_replacedOriginal_inventoryNumber'           : '',                           #графа 21 - инвентарный номер подлинника, взамен которого выпущен данный подлинник
    '22_duplicate_inventoryNumber'                  : '',                           #графа 22 - инвентарный номер дубликата
    #'24_baseDocument_designator'                    : '',                           #графа 24 - обозначение документа, взамен или на основании которого выпущен данный документ
    #'25_firstReferenceDocument_designator'          : ''                            #графа 25 - обозначение соответствующего документа, в котором впервые записан данный документ
}

#================================================================================== BoM converter ==================================================================================
#--------------------------------------------------------------------------------------- BoM ---------------------------------------------------------------------------------------
#настройки импорта BoM из csv
_settings_bomconverter_bom_csv_import = copy.deepcopy(_settings_generic_csv_import)
#--- изменения к настройкам импорта по-умолчанию
_settings_bomconverter_bom_csv_import.update({
    'conversion_int'                                : None,                         #список полей значения которых конвертировать в целочисленные (None - не делать конвертацию)
    'conversion_float'                              : None,                         #список полей значения которых конвертировать в дробные (None - не делать конвертацию)
    'conversion_bool'                               : None,                         #список полей значения которых конвертировать в двоичные (None - не делать конвертацию)
})

#------------------------------------------------------------------------------- Перечень элементов --------------------------------------------------------------------------------
#основная надпись ПЭ3
_settings_bomconverter_pe3_titleblock = copy.deepcopy(_settings_generic_titleblock)
#--- изменения к основной надписи по-умолчанию
_settings_bomconverter_pe3_titleblock.update({
    '01b_document_type'                             : 'Перечень элементов',         #графа 1  - наименование документа
    '02_document_designator'                        : (' ПЭ3', ),                   #графа 2  - обозначение документа
})

#настройки сборки ПЭ3 (по-умолчанию)
_settings_bomconverter_pe3_build = {
    'data_titleblock'                               : _settings_bomconverter_pe3_titleblock, #значения полей основной надписи (обновляют значения из полученных данных)
    'locale_index'                                  : _settings_generic_locale,     #локализация
    'content_table_group_header'                    : True,                         #добавлять заголовок для группы элементов
    'content_accs'                                  : True,                         #добавлять аксессуары
    'content_accs_parent'                           : True,                         #добавлять в примечание позиционное обозначение родительского элемента для аксессуара
    'content_value'                                 : True,                         #добавлять номинал
    'content_value_value'                           : True,                         #добавлять значение номинала (по сути тоже самое что и выше, но используется в другой функции)
    'content_value_explicit'                        : False,                        #принудительно сделать номиналы явными
    'content_mfr'                                   : True,                         #добавлять производителя
    'content_mfr_value'                             : True,                         #добавлять значение производителя (такая же ситуация как с value)
    'content_param'                                 : True,                         #добавлять параметрическое описание
    'content_param_basic'                           : True,                         #добавлять базовые (распознанные) параметры в описание
    'content_param_misc'                            : True,                         #добавлять дополнительные (не распознанные) параметры в описание
    'content_subst'                                 : True,                         #добавлять допустимые замены
    'content_subst_value'                           : True,                         #добавлять номинал допустимой замены
    'content_subst_mfr'                             : True,                         #добавлять производителя допустимой замены
    'content_subst_note'                            : True,                         #добавлять примечание для допустимой замены
    'content_annot'                                 : True,                         #добавлять примечание компонента
    'content_annot_value'                           : True,                         #добавлять значение примечания
    'content_annot_fitted'                          : True,                         #добавлять значение установки в примечание
    'assemble_desig'                                : False,                        #пересобирать позиционное обозначение
    'assemble_kind'                                 : True,                         #пересобирать тип элемента (для аксессуаров и не распознанных)
    'assemble_param'                                : True,                         #пересобирать параметрическое описание
    'format_table_group_indent'                     : 1,                            #количество пустых строк между группами элементов
    'format_table_group_header_indent'              : 0,                            #количество пустых строк после заголовка группы
    'format_table_entry_indent'                     : 0,                            #количество пустых строк между записями
    'format_table_entry_composite_indent'           : 1,                            #количество пустых строк вокруг составной записи
    'format_table_entry_deviation_indent'           : 0,                            #количество пустых строк между вариациями записи
    'format_desig_delimiter'                        : [', ', '\u2013'],             #разделитель позиционных обозначений [<перечисление>, <диапазон>]
    'format_kind_capitalize'                        : True,                         #типы элементов с заглавной буквы
    'format_value_enclosure'                        : ['', ''],                     #обрамление номинала
    'format_mfr_enclosure'                          : [' ф.\xa0', ''],              #обрамление производителя
    'format_param_enclosure'                        : [' (', ')'],                  #обрамление параметров
    'format_param_decimalPoint'                     : '.',                          #десятичный разделитель
    'format_param_rangeSymbol'                      : '\u2026',                     #символ диапазона
    'format_param_delimiter'                        : ', ',                         #разделитель параметров
    'format_param_unit_enclosure'                   : ['', ''],                     #обрамление единиц измерения
    'format_param_multivalue_delimiter'             : '/',                          #разделитель значений многозначного параметра
    'format_param_tolerance_enclosure'              : ['\xa0', ''],                 #обрамление допуска
    'format_param_tolerance_signDelimiter'          : '',                           #разделитель между значением допуска и его знаком
    'format_param_conditions_enclosure'             : ['\xa0[', ']'],               #обрамление условий измерения параметра
    'format_param_conditions_delimiter'             : '; ',                         #разделитель условий измерения параметра
    'format_param_temperature_positiveSign'         : True,                         #указывать знак для положительных значений температуры
    'format_subst_enclosure'                        : ['', ''],                     #обрамление блока с допустимыми заменами
    'format_subst_entry_enclosure'                  : ['\nдоп.\xa0замена ', ''],    #обрамление допустимой замены
    'format_subst_value_enclosure'                  : ['', ''],                     #обрамление номинала допустимой замены
    'format_subst_mfr_enclosure'                    : [' ф.\xa0', ''],              #обрамление производителя допустимой замены
    'format_subst_note_enclosure'                   : [' (', ')'],                  #обрамление примечения допустимой замены
    'format_annot_enclosure'                        : ['', ''],                     #обрамление примечания
    'format_annot_delimiter'                        : ';\n',                        #разделитель значений в примечании
    'format_accs_parent_first'                      : True,                         #ставить в начало родительские элементы аксессуаров
    'format_accs_parent_delimiter'                  : '; ',                         #разделитель значения примечания и родительских элементов аксессуаров
    'format_accs_parent_enclosure'                  : ['для ', ''],                 #обрамление для родительских элементов аксессуаров
    'format_fitted_quantity'                        : [-1, 1],                      #количество указываемое для компонента (отрицательное значение - брать из свойств компонента) [<устанавливаемый>, <не устанавливаемый>] (чтобы не было 0 у неустанавливаемых компонентов)
    #'format_fitted_label'                           : ['', 'не устанавливать']      #метка (не) установки компонента ['устанавливать', 'не устанавливать']
    #'dict_groups'                                   : 'dict_pe3.py'                 #словарь с названиями групп элементов; либо адрес файла, либо сам словарь
}

#настройки сборки ПЭ3 и его экспорта в docx
_settings_bomconverter_pe3_docx_build = copy.deepcopy(_settings_bomconverter_pe3_build)
#--- изменения к настройкам сборки по-умолчанию
_settings_bomconverter_pe3_docx_build.update({
    'format_param_decimalPoint'                     : ',',                          #десятичный разделитель
    'format_param_rangeSymbol'                      : '\xa0\u2026\xa0',             #символ диапазона
    'format_param_delimiter'                        : ' \u2013 ',                   #разделитель параметров
    'format_param_unit_enclosure'                   : ['\xa0', ''],                 #обрамление единиц измерения
    'format_param_multivalue_delimiter'             : '\xa0/\xa0',                  #разделитель значений многозначного параметра
    'format_param_tolerance_signDelimiter'          : '\xa0',                       #разделитель между значением допуска и его знаком
    'format_param_conditions_enclosure'             : ['\xa0(', ')'],               #обрамление условий измерения параметра
})  
#--- настройки экспорта
_settings_bomconverter_pe3_docx_export = {
    #'template'                                      : "export_pe3_docx.docx"        #адрес шаблона для экспорта
    'format_table_desig_wordwrap'                   : False,                        #позиционное обозначение    <- переносить значение в нижестоящую ячейку таблицы, если оно не влезает в текущую 
    'format_table_label_wordwrap'                   : True,                         #наименование
    'format_table_annot_wordwrap'                   : True,                         #примечание                 ^
    'format_table_desig_wordwrap_delimiter'         : ' ',                          #позиционное обозначение    <- разделитель после которого можно делать перенос
    'format_table_label_wordwrap_delimiter'         : _settings_bomconverter_pe3_docx_build['format_param_delimiter'], #наименование
    'format_table_annot_wordwrap_delimiter'         : ' '                           #примечание                 ^
    #'document_author'                               : '',                          #автор                      <- свойства документа (если не заданы то остаются как в шаблоне)
    #'document_category'                             : '',                          #категории
    #'document_comments'                             : '',                          #примечания
    #'document_contentStatus'                        : '',                          #состояние
    #'document_created'                              : datetime(Y, M, D, h, m, s),  #создан (UTC)
    #'document_identifier'                           : '',                          #
    #'document_keywords'                             : '',                          #теги
    #'document_language'                             : '',                          #
    #'document_lastModifiedBy'                       : '',                          #кем изменено
    #'document_lastPrinted'                          : datetime(Y, M, D, h, m, s),  #напечатан (UTC)
    #'document_modified'                             : datetime(Y, M, D, h, m, s),  #изменён (UTC)
    #'document_revision'                             : 1,                           #
    #'document_subject'                              : '',                          #тема
    #'document_title'                                : '',                          #название
    #'document_version'                              : ''                           #                           ^
}

#настройки сборки ПЭ3 и его экспорта в pdf
_settings_bomconverter_pe3_pdf_build = copy.deepcopy(_settings_bomconverter_pe3_build)
#--- изменения к настройкам сборки по-умолчанию
_settings_bomconverter_pe3_pdf_build.update({
})
#--- настройки экспорта
_settings_bomconverter_pe3_pdf_export = {
    #'template'                                      : "export_pe3_pdf.tex"         #адрес шаблона для экспорта
}

#настройки сборки ПЭ3 и его экспорта в csv
_settings_bomconverter_pe3_csv_build = copy.deepcopy(_settings_bomconverter_pe3_build)
#--- изменения к настройкам сборки по-умолчанию
_settings_bomconverter_pe3_csv_build.update({
})
#--- настройки экспорта
_settings_bomconverter_pe3_csv_export = copy.deepcopy(_settings_generic_csv_export)
#--- изменения к настройкам экспорта по-умолчанию
_settings_bomconverter_pe3_csv_export.update({
})

#---------------------------------------------------------------------------------- Спецификация -----------------------------------------------------------------------------------
#основная надпись СП
_settings_bomconverter_sp_titleblock = copy.deepcopy(_settings_generic_titleblock)
#--- изменения к основной надписи по-умолчанию
_settings_bomconverter_sp_titleblock.update({
    '01b_document_type'                             : 'Спецификация',               #графа 1  - наименование документа
})

#настройки сборки СП (по-умолчанию)
_settings_bomconverter_sp_build = {
    'data_titleblock'                               : _settings_bomconverter_sp_titleblock, #значения полей основной надписи (обновляют значения из полученных данных)
    'locale_index'                                  : _settings_generic_locale,     #локализация
    'content_accs'                                  : True,                         #добавлять аксессуары
    'content_accs_parent'                           : False,                        #указывать в качестве позиционного обозначения родительский элемент для аксессуара
    'content_value'                                 : True,                         #добавлять номинал
    'content_value_value'                           : True,                         #добавлять значение номинала (по сути тоже самое что и выше, но используется в другой функции)
    'content_value_explicit'                        : False,                        #принудительно сделать номиналы явными
    'content_mfr'                                   : True,                         #добавлять производителя
    'content_mfr_value'                             : True,                         #добавлять значение производителя (такая же ситуация как с value)
    'content_param'                                 : True,                         #добавлять параметрическое описание
    'content_param_basic'                           : True,                         #добавлять базовые (распознанные) параметры в описание
    'content_param_misc'                            : True,                         #добавлять дополнительные (не распознанные) параметры в описание
    'content_subst'                                 : True,                         #добавлять допустимые замены
    'content_subst_value'                           : True,                         #добавлять номинал допустимой замены
    'content_subst_mfr'                             : True,                         #добавлять производителя допустимой замены
    'content_subst_note'                            : True,                         #добавлять примечание для допустимой замены
    'content_annot'                                 : True,                         #добавлять примечание компонента (в наименование)
    'content_annot_value'                           : True,                         #добавлять значение примечания
    'content_annot_fitted'                          : False,                        #добавлять значение установки в примечание
    'assemble_desig'                                : False,                        #пересобирать позиционное обозначение
    'assemble_kind'                                 : True,                         #пересобирать тип элемента (для аксессуаров и не распознанных)
    'assemble_param'                                : True,                         #пересобирать параметрическое описание
    'format_value_enclosure'                        : ['', ''],                     #обрамление номинала
    'format_mfr_enclosure'                          : [' ф.\xa0', ''],              #обрамление производителя
    'format_param_enclosure'                        : [' (', ')'],                  #обрамление параметров
    'format_param_decimalPoint'                     : ',',                          #десятичный разделитель
    'format_param_rangeSymbol'                      : '\xa0\u2026\xa0',             #символ диапазона
    'format_param_delimiter'                        : ' \u2013 ',                   #разделитель параметров
    'format_param_unit_enclosure'                   : ['\xa0', ''],                 #обрамление единиц измерения
    'format_param_multivalue_delimiter'             : '\xa0/\xa0',                  #разделитель значений многозначного параметра
    'format_param_tolerance_enclosure'              : ['\xa0', ''],                 #обрамление допуска
    'format_param_tolerance_signDelimiter'          : '\xa0',                       #разделитель между значением допуска и его знаком
    'format_param_conditions_enclosure'             : ['\xa0(', ')'],               #обрамление условий измерения параметра
    'format_param_conditions_delimiter'             : '; ',                         #разделитель условий измерения параметра
    'format_param_temperature_positiveSign'         : True,                         #указывать знак для положительных значений температуры
    'format_subst_enclosure'                        : ['', ''],                     #обрамление блока с допустимыми заменами
    'format_subst_entry_enclosure'                  : ['|доп.\xa0замена ', ''],     #обрамление допустимой замены
    'format_subst_value_enclosure'                  : ['', ''],                     #обрамление номинала допустимой замены
    'format_subst_mfr_enclosure'                    : [' ф.\xa0', ''],              #обрамление производителя допустимой замены
    'format_subst_note_enclosure'                   : [' (', ')'],                  #обрамление примечения допустимой замены
    'format_annot_enclosure'                        : ['|прим. ', ''],              #обрамление примечания
    'format_annot_delimiter'                        : ', ',                         #разделитель значений в примечании
    'format_fitted_quantity'                        : [-1, 0],                      #количество указываемое для компонента (отрицательное значение - брать из свойств компонента) [<устанавливаемый>, <не устанавливаемый>]
    'format_fitted_label'                           : ['', '']                      #метка (не) установки компонента ['устанавливать', 'не устанавливать']
}

#настройки сборки СП и её экспорта в csv
_settings_bomconverter_sp_csv_build = copy.deepcopy(_settings_bomconverter_sp_build)
#--- изменения к настройкам сборки по-умолчанию
_settings_bomconverter_sp_csv_build.update({
})
#--- настройки экспорта
_settings_bomconverter_sp_csv_export = copy.deepcopy(_settings_generic_csv_export)
#--- изменения к настройкам экспорта по-умолчанию
_settings_bomconverter_sp_csv_export.update({
    'format_desig_delimiter'                        : ', '                          #разделитель позиционных обозначений
})

#------------------------------------------------------------------------------- Список компонентов --------------------------------------------------------------------------------
#настройки сборки СК (по-умолчанию)
_settings_bomconverter_cl_build = {
    'locale_index'                                  : _settings_generic_locale,     #локализация
    'sorting_method'                                : 'params',                     #метод сортировки компонентов [designator|value|kind|params]
    'sorting_reverse'                               : False,                        #сортировать компоненты в обратном порядке
    'content_accs'                                  : True,                         #добавлять аксессуары
    'content_accs_segregate'                        : True,                         #выделить аксессуары в отдельную группу
    'content_subst'                                 : True,                         #добавлять список допустимых замен
    'assemble_desig'                                : False,                        #пересобирать позиционное обозначение
    'assemble_kind'                                 : False,                        #пересобирать тип элемента (аргументы ниже относятся к этому сборщику)
        'format_kind_capitalize'                    : True,                             #типы элементов с заглавной буквы
    'assemble_param'                                : False,                        #пересобирать параметрическое описание (аргументы ниже относятся к этому сборщику)
        'content_param_basic'                       : True,                             #добавлять базовые (распознанные) параметры в описание
        'content_param_misc'                        : True,                             #добавлять дополнительные (не распознанные) параметры в описание
        'format_param_enclosure'                    : ['', ''],                         #обрамление параметров
        'format_param_decimalPoint'                 : '.',                              #десятичный разделитель
        'format_param_rangeSymbol'                  : '\u2026',                         #символ диапазона
        'format_param_delimiter'                    : ', ',                             #разделитель параметров
        'format_param_unit_enclosure'               : ['', ''],                         #обрамление единиц измерения
        'format_param_multivalue_delimiter'         : '/',                              #разделитель значений многозначного параметра
        'format_param_tolerance_enclosure'          : ['\xa0', ''],                     #обрамление допуска
        'format_param_tolerance_signDelimiter'      : '',                               #разделитель между значением допуска и его знаком
        'format_param_conditions_enclosure'         : ['\xa0[', ']'],                   #обрамление условий измерения параметра
        'format_param_conditions_delimiter'         : '; ',                             #разделитель условий измерения параметра
        'format_param_temperature_positiveSign'     : True                              #указывать знак для положительных значений температуры
}

#настройки сборки СК и его экспорта в xlsx
_settings_bomconverter_cl_xlsx_build = copy.deepcopy(_settings_bomconverter_cl_build)
#--- изменения к настройкам сборки по-умолчанию
_settings_bomconverter_cl_xlsx_build.update({
})
#--- настройки экспорта
_settings_bomconverter_cl_xlsx_export = copy.deepcopy(_settings_generic_cl_xlsx_export)
#--- изменения к настройкам экспорта по-умолчанию
_settings_bomconverter_cl_xlsx_export.update({
})

#================================================================================ BoM discriminator ================================================================================
#-------------------------------------------------------------------------------------- input --------------------------------------------------------------------------------------
#настройки импорта BoM из csv
_settings_bomdiscriminator_input_csv = copy.deepcopy(_settings_generic_csv_import)
#--- изменения к настройкам импорта по-умолчанию
_settings_bomdiscriminator_input_csv.update({
    'conversion_int'                                : ['Quantity'],                 #список полей значения которых конвертировать в целочисленные (None - не делать конвертацию)
    'conversion_float'                              : None,                         #список полей значения которых конвертировать в дробные (None - не делать конвертацию)
    'conversion_bool'                               : None,                         #список полей значения которых конвертировать в двоичные (None - не делать конвертацию)
})

#------------------------------------------------------------------------------------- process -------------------------------------------------------------------------------------
#настройки сравнения
_settings_bomdiscriminator_discriminate = {
    'locale_index'                                  : _settings_generic_locale      #локализация
    #'comparison_fields_key'                         : ['Designator'],               #названия полей по которым определять соответствие элементов, список
    #'comparison_fields_ignore'                      : [],                           #названия полей игнорируемых при сравнении, список ('~' - игнорировать непарные поля)
}

#------------------------------------------------------------------------------------- output --------------------------------------------------------------------------------------
#настройки экспорта в xlsx
_settings_bomdiscriminator_output_xlsx = {
    'locale_index'                                  : _settings_generic_locale,     #локализация
    'changes_mode'                                  : 'comment',                    #метод отображения изменений {none|highlight|comment|duplex}
    #'book_title'                                    : '',                           #название              <- свойства книги
    #'book_subject'                                  : '',                           #тема
    #'book_author'                                   : '',                           #автор, кем изменено
    #'book_manager'                                  : '',                           #руководитель
    #'book_company'                                  : '',                           #организация
    #'book_category'                                 : '',                           #категории
    #'book_keywords'                                 : '',                           #теги
    #'book_created'                                  : datetime(Y, M, D, h, m, s),   #создан, изменён
    #'book_comments'                                 : '',                           #примечания
    #'book_status'                                   : '',                           #состояние
    #'book_hyperlink'                                : '',                           #база гиперссылки      ^
    'book_style'                                    : {                              #стили в книге
        'header' : {    #заголовок таблицы
            'normal'   : {'valign': 'vcenter', 'bold':True, 'font_color':'#000000', 'bg_color':'#99CCFF', 'align':'center'},
            'key'      : {'valign': 'vcenter', 'bold':True, 'font_color':'#000000', 'bg_color':'#FFA0FF', 'align':'center'},
            'ignored'  : {'valign': 'vcenter', 'bold':True, 'font_color':'#808080', 'bg_color':'#D8D8D8', 'align':'center'},
            'added'    : {'valign': 'vcenter', 'bold':True, 'font_color':'#000000', 'bg_color':'#92D050', 'align':'center'},
            'removed'  : {'valign': 'vcenter', 'bold':True, 'font_color':'#000000', 'bg_color':'#FF7070', 'align':'center'},
        },   
        'field' : {     #поле (ячейка)
            'normal'        : {'valign': 'vcenter'},
            'key'           : {'valign': 'vcenter', 'font_color':'#FF00FF'},
            'equal'         : {'valign': 'vcenter', 'font_color':'#000000'},
            'modified'      : {'valign': 'vcenter', 'font_color':'#0000FF', 'bold':True},
            'modified-ref'  : {'valign': 'vcenter', 'font_color':'#FF0000', 'font_strikeout': True},
            'modified-subj' : {'valign': 'vcenter', 'font_color':'#008000'},
            'ignored'       : {'valign': 'vcenter', 'font_color':'#808080'},
            'added'         : {'valign': 'vcenter', 'font_color':'#008000'},
            'removed'       : {'valign': 'vcenter', 'font_color':'#FF0000', 'font_strikeout': True}
        },
        'comment' : {'x_scale': 1.75},   #примечание к полю (ячейке)
        'row' : {   #ряд
            'normal'  : None,   #ряд с полями (значениями)
            'header'  : None    #ряд с заголовком таблицы
        },
        'col' : {   #столбец (стили для столбцов по их названиям)
            '<default>'        : {'width': 10.0, 'valign': 'vcenter'}, #стиль по-умолчанию
            'Designator'       : {'width':  9.0, 'valign': 'vcenter'},
            'BOM_type'         : {'width': 15.0, 'valign': 'vcenter'},
            'BOM_value'        : {'width': 30.0, 'valign': 'vcenter'},
            'BOM_description'  : {'width': 60.0, 'valign': 'vcenter'},
            'BOM_manufacturer' : {'width': 30.0, 'valign': 'vcenter'},
            'BOM_explicit'     : {'width': 11.0, 'valign': 'vcenter'},
            'BOM_substitute'   : {'width': 30.0, 'valign': 'vcenter'},
            'BOM_note'         : {'width': 30.0, 'valign': 'vcenter'},
            'BOM_accessory'    : {'width': 30.0, 'valign': 'vcenter'},
            'Footprint'        : {'width': 25.0, 'valign': 'vcenter'},
            'Quantity'         : {'width':  8.0, 'valign': 'vcenter'},
            'Fitted'           : {'width':  8.0, 'valign': 'vcenter'},
            'UniqueIdName'     : {'width': 12.0, 'valign': 'vcenter'},
            'UniqueIdPath'     : {'width': 25.0, 'valign': 'vcenter'}
        }
    }
}

#настройки экспорта в csv
_settings_bomdiscriminator_output_csv = {
    'changes_state_name'                            : 'Diff_state',                 #название поля с типом изменения в записи (None - не добавлять)
    'changes_state_index'                           : 0,                            #индекс поля с типом изменения в записи (отрицательные значения отсчитывают с конца)
    'export'                                        : copy.deepcopy(_settings_generic_csv_export)  #настройки экспорта в csv
}

#================================================================================= CL discriminator ================================================================================
#настройки экспорта СК в xlsx
_settings_cldiscriminator_export_xlsx = copy.deepcopy(_settings_generic_cl_xlsx_export)
#--- изменения к настройкам экспорта по-умолчанию
_settings_cldiscriminator_export_xlsx.update({
})

#============================================================================== Словарь с настройками ==============================================================================
data = {
    #bomconverter
    'bomconverter': {
        #вход
        'input': {
            'adproject': {                                                          #настройки импорта проекта Altium Designer
                #нет настроек
            },
            'bom-csv'                   : _settings_bomconverter_bom_csv_import     #настройки импорта BoM из CSV
        },
        
        #анализ данных
        'parse': {
            #'parser'                    : "parse_taluts.py"                    #адрес парсера
            'project': {                                                            #настройки анализа проекта
                #нет настроек
            },
            'bom': {                                                                #настройки анализа BoM
                #нет настроек
            },
            'check': {                                                              #настройки проверки данных после анализа
                #нет настроек
            }
        },

        #оптимизация данных
        'optimize': {
            'mfr-name': {                                                           #имена производителей
                'enabled'               : False,                                        #включено
                #'dictionary'            : dict_mfr_names.py"                            #адрес словаря
            },
            'res-tol': {                                                            #точность резиторов
                'enabled'               : False                                         #включено
            }
        },

        #выход
        'output': {
            'cl-xlsx' : {                                                           #список компонентов в Excel
                'enabled'               : True,                                         #включено
                'filename'              : "$basename СК $postfix.xlsx",                 #имя выходного файла
                'build'                 : _settings_bomconverter_cl_xlsx_build,         #настройки сборки
                'export'                : _settings_bomconverter_cl_xlsx_export         #настройки экспорта
            },
            'pe3-docx': {                                                           #перечень элементов в Word
                'enabled'               : True,                                         #включено
                'filename'              : "$basename ПЭ3 $postfix.docx",                #имя выходного файла
                'build'                 : _settings_bomconverter_pe3_docx_build,        #настройки сборки
                'export'                : _settings_bomconverter_pe3_docx_export        #настройки экспорта
            },
            'pe3-pdf' : {                                                           #перечень элементов в PDF
                'enabled'               : True,                                         #включено
                'filename'              : "$basename ПЭ3 $postfix.pdf",                 #имя выходного файла
                'build'                 : _settings_bomconverter_pe3_pdf_build,         #настройки сборки
                'export'                : _settings_bomconverter_pe3_pdf_export
            },
            'pe3-csv' : {                                                           #перечень элементов в CSV
                'enabled'               : True,                                         #включено
                'filename'              : "$basename ПЭ3 $postfix.csv",                 #имя выходного файла
                'build'                 : _settings_bomconverter_pe3_csv_build,         #настройки сборки
                'export'                : _settings_bomconverter_pe3_csv_export         #настройки экспорта
            },
            'sp-csv'  : {                                                           #спецификация в CSV
                'enabled'               : True,                                         #включено
                'filename'              : "$basename СП $postfix.csv",                  #имя выходного файла
                'build'                 : _settings_bomconverter_sp_csv_build,          #настройки сборки
                'export'                : _settings_bomconverter_sp_csv_export          #настройки экспорта
            }
        }
    },

    #bomdiscriminator
    'bomdiscriminator' : {
        #вход
        'input': {
            'csv'                       : _settings_bomdiscriminator_input_csv
        },

        #обработка
        'discriminate'                  : _settings_bomdiscriminator_discriminate,

        #выход
        'output': {
            'xlsx'                      : _settings_bomdiscriminator_output_xlsx,   #xlsx
            'csv'                       : _settings_bomdiscriminator_output_csv     #csv
        }
    },

    #cldiscriminator
    'cldiscriminator' : {
        #вход
        'input': {
            'xlsx' : {                                                              #xlsx
                'locale_index'          : _settings_generic_locale,                     #локализация
            }
        },

        #обработка
        'discriminate': {
            'locale_index'              : _settings_generic_locale,                     #локализация
        },

        #выход
        'output': {
            'xlsx'                      : _settings_cldiscriminator_export_xlsx     #xlsx
        }
    }
}