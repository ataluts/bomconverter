import sys, argparse
import os
import copy
import datetime, pytz
from enum import Enum, IntEnum
from pathlib import Path
import xlsxwriter

import lib_common                                               #библиотека с общими функциями
import dict_locale as lcl
from typedef_bom import BoM                                     #класс BoM
import import_bom_csv                                           #импорт BoM из csv
import export_bom_csv                                           #экспорт BoM в csv

_module_dirname = os.path.dirname(__file__)                     #адрес папки со скриптом
_module_date    = datetime.datetime(2025, 7, 3)
_halt_on_exit   = True
_debug          = False

#-------------------------------------------------------- Class definitions ---------------------------------------------------------

class DifferentialValue():
    def __init__(self, reference, subject, key = False, ignored = False):
        self.reference = reference
        self.subject = subject
        self.key = key
        self.ignored = ignored

        if self.reference == self.subject:
            if self.reference is not None:
                #оба значения есть и равны между собой
                self.state = self.State.EQUAL
            else:
                #обоих значений нет (такого быть не должно)
                self.state = None
        elif self.reference is None:
            #есть сравниваемое значение, но нет исходного
            self.state = self.State.ADDED
        elif self.subject is None:
            #есть исходное значение, но нет сраниваемого
            self.state = self.State.REMOVED
        else:
            #оба значения есть и они разные
            self.state = self.State.MODIFIED

    #Состояние значения
    class State(IntEnum):
        EQUAL    = 0    #значения совпадают
        MODIFIED = 1    #значения отличаются
        ADDED    = 2    #добавлено (поля нет в исходном BoM)
        REMOVED  = 3    #удалено (поля нет в сравниваемом BoM)

    #Возвращает разнится ли значение
    def isdifferent(self):
        if self.state == self.State.EQUAL:
            return False
        if self.state == self.State.MODIFIED:
            return True
        if self.state == self.State.ADDED or self.state == self.State.REMOVED:
            return True
        return None
    
    #Возвращает является ли значение парным
    def ispaired(self):
        if self.reference is not None and self.subject is not None:
            return True
        return False
    
    #Возвращает значение
    def get_value(self, reference_priority = False):
        if reference_priority:
            if self.reference is not None:
                return self.reference
            else:
                return self.subject
        else:
            if self.subject is not None:
                return self.subject
            else:
                return self.reference

#Режим отображения изменений
class XlsxChangesModeID(Enum):
    NONE    = 'none'      #не отображать
    STYLE   = 'style'     #выделять другим стилем
    COMMENT = 'comment'   #выделять другим стилем + добавлять примечание
    DUPLEX  = 'duplex'    #отображать одновременно оба значения

#Варианты выходного формата
class OutputID(Enum):
    XLSX  = 'xlsx'
    CSV   = 'csv'

#====================================================== END Class definitions =======================================================

# ----------------------------------------------------------- Specific functions --------------------------------------------------

#Сравнивает BoM, возвращает массив из 4 BoM
def discriminate(reference, subject, **kwargs):
    #parameters
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)
    comparison_fields_key = kwargs.get('comparison_fields_key', ['Designator'])
    comparison_fields_ignore = kwargs.get('comparison_fields_ignore', [])
    comparison_fields_ignore_unpaired = False
    if '*' in comparison_fields_ignore:
        comparison_fields_ignore_unpaired = True
        comparison_fields_ignore.remove('*')

    #задаём BoM
    bom_reference = copy.deepcopy(reference)                                                    #исходный BoM (в нём останется то что удалилось)
    bom_reference.title = lcl.bomdiscriminator.XLSX_SHEET_TITLE_REMOVED.value[locale_index]
    bom_subject = copy.deepcopy(subject)                                                        #сравниваемый BoM (в нём останется то что добавилось)
    bom_subject.title = lcl.bomdiscriminator.XLSX_SHEET_TITLE_ADDED.value[locale_index]
    bom_modified = BoM(lcl.bomdiscriminator.XLSX_SHEET_TITLE_MODIFIED.value[locale_index])      #BoM с изменениями (в нём появится то что изменилось)
    bom_modified.fields = copy.deepcopy(bom_subject.fields)
    bom_changes = BoM(lcl.bomdiscriminator.XLSX_SHEET_TITLE_CHANGES.value[locale_index])        #BoM с изменениями (что именно изменилось)

    #определяем поля
    fields_all = copy.deepcopy(bom_subject.fields)
    for field in bom_reference.fields:
        if field not in fields_all:
            fields_all.append(field)
    for field in fields_all:
        field_reference = field if field in bom_reference.fields else None
        field_subject   = field if field in bom_subject.fields   else None
        bom_changes.insert_field(DifferentialValue(field_reference, field_subject, field in comparison_fields_key, field in comparison_fields_ignore))

    #проверяем наличие ключа сопоставления, если его нет то работать не можем
    if len(comparison_fields_key) == 0:
        print("ERROR! >> No key fields specified.")
        return
    for field in comparison_fields_key:
        if field in bom_reference.fields and field in bom_subject.fields: break
    else:
        print("ERROR! >> Key fields not present in both BoMs.")
        return

    #перебираем записи сравниваемого BoM
    for i in range(len(bom_subject.entries) - 1, -1, -1):
        #собираем ключ сравниваемого BoM
        key_subject = ""
        for field in comparison_fields_key:
            key_subject += bom_subject.get_entry_field_value(i, field, '')
        #перебираем записи исходного BoM
        for j in range(len(bom_reference.entries) - 1, -1, -1):
            #собираем ключ сравниваемого BoM
            key_reference = ""
            for field in comparison_fields_key:
                key_reference += bom_reference.get_entry_field_value(j, field, '')
            #сравниваем записи
            if key_reference == key_subject:
                #ключи записей совпадают -> сравниваем остальные поля
                changes = []
                for field in fields_all:
                    changes.append(DifferentialValue(bom_reference.get_entry_field_value(j, field), bom_subject.get_entry_field_value(i, field), field in comparison_fields_key, field in comparison_fields_ignore))
                #определяем изменённые записи
                for value in changes:
                    if value.isdifferent() and not value.ignored:
                        if value.ispaired() or not comparison_fields_ignore_unpaired:
                            #записываем изменённые записи в отдлельный BoM
                            bom_modified.insert_entry(bom_subject.entries[i].value)
                            bom_changes.insert_entry(changes)
                            break
                #удаляем записи из начальных BoM
                bom_reference.entries.pop(j)
                bom_subject.entries.pop(i)
                break
    #переворачиваем список изменённых записей так как перебирали их в обратном порядке
    bom_modified.entries.reverse()
    bom_changes.entries.reverse()

    #возвращаем массив: [изменённые записи, добавленные записи, исключённые записи, карта изменений]
    return [bom_modified, bom_subject, bom_reference, bom_changes]

#Сравнивает BoM и сохраняет результат в Excel
def discriminate_file(reference_path, subject_path, result_path, result_format, reference_settings = None, subject_settings = None, result_settings = None, **kwargs):
    #считываем настройки
    settings_reference = lib_common.import_settings(reference_settings)
    if 'bomdiscriminator' in settings_reference: settings_reference = settings_reference['bomdiscriminator']
    settings_subject = lib_common.import_settings(subject_settings)
    if 'bomdiscriminator' in settings_subject: settings_subject = settings_subject['bomdiscriminator']
    settings_result = lib_common.import_settings(result_settings)
    if 'bomdiscriminator' in settings_result: settings_result = settings_result['bomdiscriminator']

    #обрабатываем настройки
    params_reference_input = copy.deepcopy(settings_reference.get('input', {}).get('csv', {}))
    params_subject_input = copy.deepcopy(settings_subject.get('input', {}).get('csv', {}))
    params_result_discriminate = copy.deepcopy(settings_result.get('discriminate', {}))
    if 'discriminate' in kwargs: lib_common.dict_nested_update(params_result_discriminate, kwargs['discriminate'])
    params_result_output = copy.deepcopy(settings_result.get('output', {}).get(result_format.value, {}))
    if 'output' in kwargs and result_format.value in kwargs['output']: lib_common.dict_nested_update(params_result_output, kwargs['output'][result_format.value])

    #считываем BoM
    print('')
    print('INFO >> Importing reference BoM')
    bom_reference = import_bom_csv.importz(reference_path, **params_reference_input)
    print('')
    print('INFO >> Importing subject BoM')
    bom_subject = import_bom_csv.importz(subject_path, **params_subject_input)
    
    print('')
    print("INFO >> Discriminating BoMs", end ="... ")
    result = discriminate(bom_reference, bom_subject, **params_result_discriminate)
    print(f"done. (entries: {len(result[0].entries)} modified, {len(result[1].entries)} added, {len(result[2].entries)} removed)")

    print('')
    print(f"INFO >> Exporting changes as {result_format.value}:")
    if result_format == OutputID.XLSX:
        export_changes_xlsx(result, result_path, **params_result_output)
    elif result_format == OutputID.CSV:
        export_changes_csv(result, result_path, **params_result_output)
    else:
        print(f"ERROR >> {result_format.value} exporter does not present.")

#Экспортирует результат сравнения BoM в xlsx
def export_changes_xlsx(data, address, **kwargs):
    print('INFO >> xlsx export running with parameters:')
    print(' ' * 12 + 'output: ' +  os.path.basename(address))

    #locale
    locale_index = kwargs.get('locale_index', lcl.LocaleIndex.RU.value)

    #параметры
    changes_mode = kwargs.get('changes_mode', XlsxChangesModeID.COMMENT.value)
    for member in XlsxChangesModeID:
        if str(member.value) == changes_mode:
            changes_mode = member
            break
    else:
        print(f"WARNING! Changes mode value not parsed - using '{XlsxChangesModeID.NONE.value}' instead.")
        changes_mode = XlsxChangesModeID.NONE

    #свойства книги
    book_title    = kwargs.get('book_title', '<none>')
    book_subject  = kwargs.get('book_subject', '')
    book_author   = kwargs.get('book_author', '')
    book_manager  = kwargs.get('book_manager', '')
    book_company  = kwargs.get('book_company', '')
    book_category = kwargs.get('book_category', '')
    book_keywords = kwargs.get('book_keywords', '')
    book_created  = kwargs.get('book_created', datetime.datetime.now(pytz.timezone('UTC')))
    book_comments = kwargs.get('book_comments', '')
    book_status   = kwargs.get('book_status', '')
    book_hyperlinkBase = kwargs.get('book_hyperlink', '')
    book_style_arg = kwargs.get('book_style', {})

    #стили
    book_style = {
        'header' : {
            'normal'   : {'valign': 'vcenter', 'bold':True, 'font_color':'#000000', 'bg_color':'#99CCFF', 'align':'center'},
            'key'      : {'valign': 'vcenter', 'bold':True, 'font_color':'#000000', 'bg_color':'#FFA0FF', 'align':'center'},
            'ignored'  : {'valign': 'vcenter', 'bold':True, 'font_color':'#808080', 'bg_color':'#D8D8D8', 'align':'center'},
            'added'    : {'valign': 'vcenter', 'bold':True, 'font_color':'#000000', 'bg_color':'#92D050', 'align':'center'},
            'removed'  : {'valign': 'vcenter', 'bold':True, 'font_color':'#000000', 'bg_color':'#FF7070', 'align':'center'},
        },   
        'field' : {
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
        'comment' : {'x_scale': 1.5},
        'row' : {
            'normal'  : None,
            'header'  : None
        },
        'col' : {
            '<default>'        : {'width': 10.0, 'valign': 'vcenter'},
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
    #обновляем стили по-умолчанию стилями из аргумента
    book_style = lib_common.dict_nested_update(book_style, book_style_arg)
    #выделяем высоту строк в отдельный словарь
    row_heights = {}
    for key in book_style['row']:
        if book_style['row'][key] is not None and 'height' in book_style['row'][key]:
            row_heights[key] = book_style['row'][key].pop('height')
            #если словарь с форматом стал пустым то ставим ему значение None
            if not book_style['row'][key]: book_style['row'][key] = None
    #выделяем ширину столбцов в отдельный словарь
    col_widths = {}
    for key in book_style['col']:
        if book_style['col'][key] is not None and 'width' in book_style['col'][key]:
            col_widths[key] = book_style['col'][key].pop('width')
            #если словарь с форматом стал пустым то ставим ему значение None
            if not book_style['col'][key]: book_style['col'][key] = None

    if len(data) > 0:
        #выбираем какой BoM записывать на лист изменений
        if len(data) > 3:
            if changes_mode == XlsxChangesModeID.NONE: data = [data[0], data[1], data[2]]
            else: data = [data[3], data[1], data[2]]
            
        with xlsxwriter.Workbook(address, {'in_memory': True, 'strings_to_numbers': False}) as workbook:
            #заполняем свойства книги
            workbook.set_properties({
                'title':    book_title,
                'subject':  book_subject,
                'author':   book_author,
                'manager':  book_manager,
                'company':  book_company,
                'category': book_category,
                'keywords': book_keywords,
                'created':  book_created,
                'comments': book_comments,
                'status':   book_status,
                'hyperlink_base':  book_hyperlinkBase})

            #задаём стили
            wb_format_header = {}
            for name, value in book_style['header'].items():
                if value:
                    wb_format_header[name] = workbook.add_format(value)
            wb_format_field = {}
            for name, value in book_style['field'].items():
                if value:
                    wb_format_field[name] = workbook.add_format(value)
            wb_format_row = {}
            for name, value in book_style['row'].items():
                if value:
                    wb_format_row[name] = workbook.add_format(value)
            wb_format_col = {}
            for name, value in book_style['col'].items():
                if value:
                    wb_format_col[name] = workbook.add_format(value)

            #перебираем списки компонентов
            for bom in data:
                #создаём лист в книге с именем сооетветствующим текущему BoM, если имя неправильное то делаем имя листа по-умолчанию
                try:
                    worksheet = workbook.add_worksheet(bom.title)
                except (xlsxwriter.exceptions.InvalidWorksheetName, xlsxwriter.exceptions.DuplicateWorksheetName):
                    worksheet = workbook.add_worksheet()

                #определяем режим записи изменений
                differential_mode = False
                if isinstance(bom.fields[0], DifferentialValue): differential_mode = True

                #записываем заголовок
                #--- определяем название столбцов
                if differential_mode:
                    field_names = []
                    for field in bom.fields:
                        field_names.append(field.get_value())
                else: field_names = bom.fields
                #--- задаём высоту и стиль строки
                worksheet.set_row(0, row_heights.get('header'), wb_format_row.get('header'))
                #--- пишем ряд с заголовком
                worksheet.write_row(0, 0, field_names, wb_format_header.get('normal'))
                #--- задаём ширину и стиль столбцов
                for col_index, col_name in enumerate(field_names):
                    col_width = col_widths.get(col_name, None)
                    col_format = wb_format_col.get(col_name, None)
                    if col_name not in col_widths and col_name not in wb_format_col:
                        if '<default>' in col_widths or '<default>' in wb_format_col:
                            col_width = col_widths.get('<default>', None)
                            col_format = wb_format_col.get('<default>', None)
                    worksheet.set_column(col_index, col_index, col_width, col_format)
                #--- форматируем заголовок в случае выделения изменений
                if differential_mode:
                    for col_index, col_name in enumerate(bom.fields):
                        if   col_name.key:     cell_format = wb_format_header.get('key', None)
                        elif col_name.ignored: cell_format = wb_format_header.get('ignored', None)
                        elif col_name.state == DifferentialValue.State.ADDED: cell_format = wb_format_header.get('added', None)
                        elif col_name.state == DifferentialValue.State.REMOVED: cell_format = wb_format_header.get('removed', None)
                        else: cell_format = wb_format_header.get('normal', None)
                        worksheet.write(0, col_index, col_name.get_value(), cell_format)
                
                #записываем элементы
                row_index = 1    #начальная строка для записей
                for entry in bom.entries:
                    #задаём высоту и стиль строки
                    worksheet.set_row(row_index, row_heights.get('normal'), wb_format_row.get('normal'))
                    if differential_mode:
                        #записываем элементы с указанием изменённых полей
                        #определяем надо ли объединять ячейки
                        merged_cells = False
                        if changes_mode == XlsxChangesModeID.DUPLEX:
                            for field in entry.value:
                                if field.key or field.ignored:
                                    continue
                                if field.state == DifferentialValue.State.MODIFIED:
                                    merged_cells = True
                                    break
                        #записываем ряд
                        for col_index, col_name in enumerate(bom.fields):
                            field = entry.value[col_index]
                            cell_format = None
                            cell_value = None
                            merge = merged_cells    #надо ли объединять ячейки для текущего поля
                            if   field.key:
                                cell_format = wb_format_field.get('key', None)
                                cell_value = field.subject
                            elif field.ignored:
                                cell_format = wb_format_field.get('ignored', None)
                                cell_value = field.subject
                            elif field.state == DifferentialValue.State.EQUAL:
                                cell_format = wb_format_field.get('equal', None)
                                cell_value = field.subject
                            elif field.state == DifferentialValue.State.MODIFIED:
                                if changes_mode == XlsxChangesModeID.DUPLEX:
                                    merge = False
                                    cell_format = wb_format_field.get('modified-subj', None)
                                else:
                                    cell_format = wb_format_field.get('modified', None)
                                cell_value = field.subject
                            elif field.state == DifferentialValue.State.ADDED:
                                cell_format = wb_format_field.get('added', None)
                                cell_value = field.subject
                            elif field.state == DifferentialValue.State.REMOVED:
                                cell_format = wb_format_field.get('removed', None)
                                if changes_mode == XlsxChangesModeID.DUPLEX:
                                    cell_value = field.reference
                                else:
                                    cell_value = field.subject
                            #записываем поле в соответствии с флагом объединения ячеек
                            if merge:
                                worksheet.merge_range(row_index, col_index, row_index + 1, col_index, cell_value, cell_format)
                            else:
                                worksheet.write(row_index, col_index, cell_value, cell_format)
                            #добавляем отображение изменений
                            if not field.key and not field.ignored and (field.state == DifferentialValue.State.MODIFIED or field.state == DifferentialValue.State.REMOVED):
                                if changes_mode == XlsxChangesModeID.COMMENT:
                                    #оторбражаем как примечание к ячейке
                                    comment = lcl.bomdiscriminator.XLSX_FIELD_MODIFIED_COMMENT_PREFIX.value[locale_index] + str(field.reference)
                                    worksheet.write_comment(row_index, col_index, comment, book_style.get('comment'))
                                elif changes_mode == XlsxChangesModeID.DUPLEX:
                                    #оторбражаем как расщеплённую ячейку
                                    worksheet.write(row_index + 1, col_index, field.reference, wb_format_field.get('modified-ref', None))
                        if merged_cells: row_index += 1
                    else:
                        #записываем только изменённые элементы (без указания какие поля изменились)
                        worksheet.write_row(row_index, 0, entry.value, wb_format_field.get('normal'))
                    row_index += 1
                    
        print('INFO >> export completed.')  
    else:
        print("ERROR! >> No output data specified.")

#Экспортирует результат сравнения BoM в csv
def export_changes_csv(data, address, **kwargs):
    print('INFO >> Building changes into single BoM file', end ="... ", flush = True)

    #параметры
    changes_state_name  = kwargs.get('changes_state_name', 'Diff_state')
    changes_state_index = kwargs.get('changes_state_index', -1)
    export = kwargs.get('export', {})

    if len(data) > 0:
        bom_modified = copy.deepcopy(data[0])
        bom_added = copy.deepcopy(data[1])
        bom_removed = copy.deepcopy(data[2])
        if changes_state_name is not None:
            bom_modified.insert_field(changes_state_name, changes_state_index, 'modified')
            bom_added.insert_field(changes_state_name, changes_state_index, 'added')
            bom_removed.insert_field(changes_state_name, changes_state_index, 'removed')

        bom_modified.entries.extend(bom_added.entries)
        for entry in bom_removed.entries:
            bom_modified.insert_entry(entry.to_dict(), -1, False, '')
        print(f"done. ({len(bom_modified.entries)} entries)")

        export_bom_csv.export(bom_modified, address, **export)
    else:
        print("no data provided.")

#========================================================= END Specific functions =================================================

#---------------------------------------------------------- Execution -------------------------------------------------------------

def main() -> None:
    #parse arguments
    argparser = argparse.ArgumentParser(description = f"BoM discriminator v. {_module_date.strftime('%Y-%m-%d')} by Alexander Taluts")
    argparser.add_argument('reference', type=Path, help='Reference BoM')
    argparser.add_argument('subject',   type=Path, help='Subject BoM that is being compared against the reference')
    argparser.add_argument('result',    type=Path, help='Comparison result')
    argparser.add_argument('--output',  type=str, default=OutputID.XLSX.value, help='Output format',  choices=[member.value for member in OutputID])
    argparser.add_argument('--fields-key',    type=str, metavar='list', help='Comma-separated list of fields used as a key')
    argparser.add_argument('--fields-ignore', type=str, metavar='list', help='Comma-separated list of ignored fields (use * for unpaired)')
    argparser.add_argument('--xlsx-changes-mode',   type=str,                    help='Changes display mode for xlsx output format',  choices=[member.value for member in XlsxChangesModeID])
    argparser.add_argument('--settings-reference',  type=Path, metavar='<file>', help='Settings used for reference BoM')
    argparser.add_argument('--settings-subject',    type=Path, metavar='<file>', help='Settings used for subject BoM')
    argparser.add_argument('--settings-result',     type=Path, metavar='<file>', help='Settings to use for result BoM')
    argparser.add_argument('--nohalt',              action='store_true',         help='Do not halt terminal')
    args = argparser.parse_args()

    #take input data files and options from arguments
    if args.nohalt is not None: 
        global _halt_on_exit
        _halt_on_exit = False
    output = OutputID(args.output)
    params = {}
    if args.fields_key is not None:
        fields_key = args.fields_key.split(',')
        for i, value in enumerate(fields_key):
            fields_key[i] = value.strip()
        if not 'discriminate' in params: params['discriminate'] = {}
        params['discriminate']['comparison_fields_key'] = fields_key
    if args.fields_ignore is not None:
        fields_ignore = args.fields_ignore.split(',')
        for i, value in enumerate(fields_ignore):
            fields_ignore[i] = value.strip()
        if not 'discriminate' in params: params['discriminate'] = {}
        params['discriminate']['comparison_fields_ignore'] = fields_ignore
    if args.xlsx_changes_mode is not None:
        if not 'output' in params: params['output'] = {}
        if not 'xlsx' in params: params['output']['xlsx'] = {}
        params['output']['xlsx']['changes_mode'] = args.xlsx_changes_mode

    #process data
    print('')
    print(f"INFO >> BoM discriminator v. {_module_date.strftime('%Y-%m-%d')} by Alexander Taluts")
    print('')
    discriminate_file(args.reference, args.subject, args.result, output, args.settings_reference, args.settings_subject, args.settings_result, **params)
    print('')
    print("INFO >> Job done.")

#exit the program
def exit(code:int = 0) -> None:
    print("")
    if _halt_on_exit: input("Press any key to exit...")
    print("Exiting...")
    if code > 0 and _debug:
        print(f"DEBUG >> Exit code: {code}")
        sys.exit(0)
    else:
        sys.exit(code)

#prevent launch when importing
if __name__ == "__main__":
    lib_common.wrap_stdout_utf8() #force output encoding to be utf-8
    exit_code = 0
    #checking launch from IDE
    if '--debug' in sys.argv:
        sys.argv.remove('--debug')
        _debug = True
        main()
    else:
        #catching all errors to display error info and prevent terminal from closing
        try:
            main()
        except Exception as e:
            exit_code = 1
            print(f"ERROR >> {e}")
            
    exit(exit_code)

#========================================================= END Execution ===========================================================