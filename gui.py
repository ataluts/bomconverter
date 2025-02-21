#!/usr/bin/env python

import wx
import sys
import os
import subprocess, threading
import time
import datetime
import configparser
import enum

_module_dirname = os.path.dirname(__file__)                      #адрес папки со скриптом
_module_date    = datetime.datetime(2025, 2, 20)

class OutputID(enum.Enum):
    ALL      = 'all'
    CL_XLSX  = 'cl-xlsx'
    PE3_DOCX = 'pe3-docx'
    PE3_PDF  = 'pe3-pdf'
    PE3_CSV  = 'pe3-csv'
    SP_CSV   = 'sp-csv'
    NONE     = 'none'

class OptimizationID(enum.Enum):
    ALL       = 'all'
    MFR_NAME  = 'mfr-name'
    RES_TOL   = 'res-tol'
    NONE      = 'none'

class App(wx.App):
    def OnInit(self):
        #Масштабирование интерфейса
        if sys.platform.startswith("win"):
            #Windows
            import ctypes
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  #enable Per-monitor v2 DPI Awareness
                pass
            except AttributeError:
                ctypes.windll.user32.SetProcessDPIAware()       #fallback for older Windows versions
        elif sys.platform.startswith("linux"):
            #Linux
            wx.SystemOptions.SetOption("gtk.window.force-hidpi", 1)
        elif sys.platform.startswith("darwin"):
            #Mac
            wx.SystemOptions.SetOption("mac.window.force-hidpi", 1)
        
        #Локализация
        self.locale = wx.Locale(wx.LANGUAGE_RUSSIAN)

        return True

#Главное окно программы
class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(None, title="BoM converter - GUI")                      #инициализация
        self.SetSizeHints(self.FromDIP(664), self.FromDIP(728))                                 #минимальные размеры окна

        self.cli_log = []                                                                       #журнал командной строки

        self.layout_statusBar()                                                                 #строка состояния
        self.statusbar.SetStatusText("Инициализация...")
        self.layout_menuBar()                                                                   #главное меню

        self.panel = wx.Panel(self)                                                             #панель где будут располагаться элементы управления
        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)                                             #основной компоновщик на этой панели
        
        self.notebook = wx.Notebook(self.panel)                                                 #создаём блокнот (вкладки)
        self.notebook.AddPage(self.layout_controlPanel(self.notebook), "Управление")            #добавляем панель управления на вкладку #0
        self.notebook.AddPage(self.layout_logPanel(self.notebook), "Журнал")                    #добавляем панель журнал на вкладку #1

        self.panel_sizer.Add(self.notebook, 1, flag = wx.EXPAND)                                #добавляем блокнот на панель
        self.panel.SetSizer(self.panel_sizer)                                                   #добавляем основной компоновщик на панель

        #отображаем окно и центруем окно на экране
        self.Show()
        wx.CallAfter(self.Centre)
        screen_width, screen_height = wx.DisplaySize()                                          #размеры экрана
        frame_width,  frame_height  = self.GetSize()                                            #размеры окна
        frame_pos_x = (screen_width - frame_width) // 2                                         #координаты окна
        frame_pos_y = (screen_height - frame_height) // 2
        self.SetPosition((frame_pos_x, frame_pos_y))

        #инициализация событий интерфейса
        self.OnControlPanelValueChange(None)
        self.OnSearchLogTextChange(None)
        self.OnLogValueChange(None)

        self.statusbar.SetStatusText("Готов")

    # Menu bar -----------------------------------------------------------------------------------------------------------------------------------------------------------------
    def layout_menuBar(self):
        #Файл
        menu_file = wx.Menu()
        # The "\t..." syntax defines an accelerator key that also triggers the same event
        menuitem_params_save = menu_file.Append(-1, "Сохранить параметры\tCtrl-S", "Сохранить параметры запуска в файл")
        menuitem_params_load = menu_file.Append(-1, "Загрузить параметры\tCtrl-O", "Загрузить параметры запуска из файла")
        menuitem_params_defaults = menu_file.Append(-1, "Сбросить параметры\tCtrl-N", "Сбросить параметры запуска на значения по-умолчанию")
        menu_file.AppendSeparator()
        # When using a stock ID we don't need to specify the menu item's label
        manuitem_exit = menu_file.Append(wx.ID_EXIT)

        #Справка
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT)

        #создаём панель и добавляем ранее созданные меню в него 
        menuBar = wx.MenuBar()
        menuBar.Append(menu_file, "&Файл")
        menuBar.Append(helpMenu, "&Справка")
        self.SetMenuBar(menuBar)

        #назначаем события пунктам меню
        self.Bind(wx.EVT_MENU, self.OnParamsSave, menuitem_params_save)
        self.Bind(wx.EVT_MENU, self.OnParamsLoad, menuitem_params_load)
        self.Bind(wx.EVT_MENU, self.OnParamsDefaults, menuitem_params_defaults)
        self.Bind(wx.EVT_MENU, self.OnExit,  manuitem_exit)
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)

    # Status bar ---------------------------------------------------------------------------------------------------------------------------------------------------------------
    def layout_statusBar(self):
        self.statusbar = self.CreateStatusBar()

    # Control panel ---------------------------------------------------------------------------------------------------------------------------------------------------------------
    def layout_controlPanel(self, parent):
        #общие параметры панели
        label_browse_size   = self.FromDIP(wx.Size(80, -1))
        button_browse_size  = self.FromDIP(wx.Size(30, -1))
        button_browse_label = "..."
        checkbox_flag_size  = self.FromDIP(wx.Size(200, -1))
        group_border_outer  = self.FromDIP(2)
        group_border_inner  = self.FromDIP(2)
        fgs_filebrowser_gap = (self.FromDIP(5), self.FromDIP(5))
        gbs_variants_gap    = (self.FromDIP(5), self.FromDIP(5))
        gbs_variants_border = self.FromDIP(3)

        self.control_panel = wx.Panel(parent)                                                      #панель управления
        self.control_panel_sizer = wx.BoxSizer(wx.VERTICAL)                                        #основной компоновщик на панели

        #--- Ввод
        self.control_input_sbox = wx.StaticBox(self.control_panel, label="Ввод")                             #контейнер (именная группа) для ввода
        self.control_input_sbox_sizer = wx.StaticBoxSizer(self.control_input_sbox, wx.VERTICAL)                     #компоновщик группы
        #--- --- Выбор файлов/папок
        self.control_input_filebrowser_sizer = wx.FlexGridSizer(3, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1]) #табличный компоновщик элементов управления
        self.control_input_filebrowser_sizer.AddGrowableCol(1)                                              #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Флаг проекта Altium Designer
        self.control_input_adproject_chkbox = wx.CheckBox(self.control_input_sbox, label="Проект Altium Designer")
        self.control_input_adproject_chkbox.Bind(wx.EVT_CHECKBOX, self.OnControlPanelValueChange)
        self.control_input_filebrowser_sizer.Add((0, 0))
        self.control_input_filebrowser_sizer.Add(self.control_input_adproject_chkbox, flag=wx.ALIGN_LEFT)
        self.control_input_filebrowser_sizer.Add((0, 0))
        #--- --- --- Файл данных
        self.control_input_data_label = wx.StaticText(self.control_input_sbox, label="Данные:\n[0]", style = wx.ALIGN_RIGHT, size = label_browse_size)
        self.control_input_filebrowser_sizer.Add(self.control_input_data_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.control_input_data_text = wx.TextCtrl(self.control_input_sbox, style = wx.TE_MULTILINE)
        self.control_input_data_text.Bind(wx.EVT_TEXT, self.OnControlPanelValueChange)
        self.control_input_filebrowser_sizer.Add(self.control_input_data_text, flag = wx.EXPAND)
        self.control_input_data_browse = wx.Button(self.control_input_sbox, label = button_browse_label, size = button_browse_size)
        self.control_input_data_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.control_input_data_text, True, "Altium Designer project (*.PrjPcb)|*.PrjPcb|CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|All files (*.*)|*.*"))
        self.control_input_filebrowser_sizer.Add(self.control_input_data_browse, flag = wx.EXPAND)
        #--- --- --- Файл основной надписи
        self.control_input_titleblock_label = wx.StaticText(self.control_input_sbox, label="Осн. надпись:", style = wx.ALIGN_RIGHT, size = label_browse_size)
        self.control_input_filebrowser_sizer.Add(self.control_input_titleblock_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.control_input_titleblock_text = wx.TextCtrl(self.control_input_sbox)
        self.control_input_titleblock_text.Bind(wx.EVT_TEXT, self.OnControlPanelValueChange)
        self.control_input_filebrowser_sizer.Add(self.control_input_titleblock_text, flag = wx.EXPAND)
        self.control_input_titleblock_browse = wx.Button(self.control_input_sbox, wx.ID_ANY, label = button_browse_label, size = button_browse_size)
        self.control_input_titleblock_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.control_input_titleblock_text, False, "Python source (*.py)|*.py|All files (*.*)|*.*"))
        self.control_input_filebrowser_sizer.Add(self.control_input_titleblock_browse)
        #--- --- компоновка: Выбор файлов/папок -> Ввод
        self.control_input_sbox_sizer.Add(self.control_input_filebrowser_sizer, proportion = 1, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Ввод -> Управление
        self.control_panel_sizer.Add(self.control_input_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Конфигурация
        self.control_config_sbox = wx.StaticBox(self.control_panel, label="Конфигурация")                   #контейнер (именная группа) для конфигурации
        self.control_config_sbox_sizer = wx.StaticBoxSizer(self.control_config_sbox, wx.VERTICAL)                   #компоновщик группы
        #--- --- Выбор файлов/папок
        self.control_config_filebrowser_sizer = wx.FlexGridSizer(2, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1])    #табличный компоновщик для выбора файлов
        self.control_config_filebrowser_sizer.AddGrowableCol(1)                                             #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Модуль настроек
        self.control_config_settings_label = wx.StaticText(self.control_config_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Настройки:")
        self.control_config_filebrowser_sizer.Add(self.control_config_settings_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.control_config_settings_text = wx.TextCtrl(self.control_config_sbox)
        self.control_config_settings_text.Bind(wx.EVT_TEXT, self.OnControlPanelValueChange)
        self.control_config_filebrowser_sizer.Add(self.control_config_settings_text, flag = wx.EXPAND)
        self.control_config_settings_browse = wx.Button(self.control_config_sbox, size = button_browse_size, label = button_browse_label)
        self.control_config_settings_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.control_config_settings_text, False, "Python source (*.py)|*.py|All files (*.*)|*.*"))
        self.control_config_filebrowser_sizer.Add(self.control_config_settings_browse)
        #--- --- --- Модуль анализатора
        self.control_config_parser_label = wx.StaticText(self.control_config_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Анализатор:")
        self.control_config_filebrowser_sizer.Add(self.control_config_parser_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.control_config_parser_text = wx.TextCtrl(self.control_config_sbox)
        self.control_config_parser_text.Bind(wx.EVT_TEXT, self.OnControlPanelValueChange)
        self.control_config_filebrowser_sizer.Add(self.control_config_parser_text,flag = wx.EXPAND)
        self.control_config_parser_browse = wx.Button(self.control_config_sbox, size = button_browse_size, label = button_browse_label)
        self.control_config_parser_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.control_config_parser_text, False, "Python source (*.py)|*.py|All files (*.*)|*.*"))
        self.control_config_filebrowser_sizer.Add(self.control_config_parser_browse)
        #--- --- компоновка: Выбор файлов/папок -> Конфигурация
        self.control_config_sbox_sizer.Add(self.control_config_filebrowser_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- --- Оптимизации
        self.control_config_optimize_sbox = wx.StaticBox(self.control_config_sbox, label="Оптимизации")             #контейнер (именная группа) для оптимизаций
        self.control_config_optimize_sbox_sizer = wx.StaticBoxSizer(self.control_config_optimize_sbox, wx.VERTICAL) #компоновщик группы
        #--- --- --- Варианты
        self.control_config_optimize_grid_sizer = wx.GridBagSizer(gbs_variants_gap[0], gbs_variants_gap[1]) #табличный компоновщик для вариантов
        self.control_config_optimize_all_chkbox = wx.CheckBox(self.control_config_optimize_sbox,      size = checkbox_flag_size, label="Все доступные")
        self.control_config_optimize_all_chkbox.Bind(wx.EVT_CHECKBOX, self.OnControlPanelValueChange)
        self.control_config_optimize_grid_sizer.Add(self.control_config_optimize_all_chkbox, pos = (0, 0), flag=wx.ALIGN_LEFT)
        self.control_config_optimize_none_chkbox = wx.CheckBox(self.control_config_optimize_sbox, size = checkbox_flag_size, label="Никакие")
        self.control_config_optimize_none_chkbox.Bind(wx.EVT_CHECKBOX, self.OnControlPanelValueChange)
        self.control_config_optimize_grid_sizer.Add(self.control_config_optimize_none_chkbox, pos = (0, 1), flag=wx.ALIGN_LEFT)
        self.control_config_optimize_sline = wx.StaticLine(self.control_config_optimize_sbox, style = wx.LI_HORIZONTAL)
        self.control_config_optimize_grid_sizer.Add(self.control_config_optimize_sline, pos = (1, 0), span = (1, 2), flag=wx.EXPAND | wx.HORIZONTAL)
        self.control_config_optimize_mfrname_chkbox = wx.CheckBox(self.control_config_optimize_sbox, size = checkbox_flag_size, label="Названия производителей")
        self.control_config_optimize_mfrname_chkbox.Bind(wx.EVT_CHECKBOX, self.OnControlPanelValueChange)
        self.control_config_optimize_grid_sizer.Add(self.control_config_optimize_mfrname_chkbox, pos = (2, 0), flag=wx.ALIGN_LEFT)
        self.control_config_optimize_restol_chkbox = wx.CheckBox(self.control_config_optimize_sbox, size = checkbox_flag_size, label="Допуски резисторов")
        self.control_config_optimize_restol_chkbox.Bind(wx.EVT_CHECKBOX, self.OnControlPanelValueChange)
        self.control_config_optimize_grid_sizer.Add(self.control_config_optimize_restol_chkbox, pos = (2, 1), flag=wx.ALIGN_LEFT)
        #--- --- --- компоновка: Варианты -> Оптимизации
        self.control_config_optimize_sbox_sizer.Add(self.control_config_optimize_grid_sizer, flag = wx.EXPAND | wx.ALL, border = gbs_variants_border)
        #--- --- компоновка: Оптимизации -> Конфигурация
        self.control_config_sbox_sizer.Add(self.control_config_optimize_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Конфигурация -> Управление
        self.control_panel_sizer.Add(self.control_config_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Вывод
        self.control_output_sbox = wx.StaticBox(self.control_panel, label="Вывод")                          #контейнер (именная группа) для вывода
        self.control_output_sbox_sizer = wx.StaticBoxSizer(self.control_output_sbox, wx.VERTICAL)                   #компоновщик группы
        #--- --- Выбор файлов/папок
        self.control_output_filebrowser_sizer = wx.FlexGridSizer(1, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1])    #табличный компоновщик для выбора файлов
        self.control_output_filebrowser_sizer.AddGrowableCol(1)                                             #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Выходная папка
        self.control_output_directory_label = wx.StaticText(self.control_output_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Папка:")
        self.control_output_filebrowser_sizer.Add(self.control_output_directory_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.control_output_directory_text = wx.TextCtrl(self.control_output_sbox)
        self.control_output_directory_text.Bind(wx.EVT_TEXT, self.OnControlPanelValueChange)
        self.control_output_filebrowser_sizer.Add(self.control_output_directory_text, flag = wx.EXPAND)
        self.control_output_directory_browse = wx.Button(self.control_output_sbox, size = button_browse_size, label = button_browse_label)
        self.control_output_directory_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnDirBrowse(event, self.control_output_directory_text))
        self.control_output_filebrowser_sizer.Add(self.control_output_directory_browse)
        #--- --- компоновка: Выбор файлов/папок -> Вывод
        self.control_output_sbox_sizer.Add(self.control_output_filebrowser_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- --- Выходные форматы
        self.control_output_format_sbox = wx.StaticBox(self.control_output_sbox, label="Форматы")                   #контейнер (именная группа) для форматов
        self.control_output_format_sbox_sizer = wx.StaticBoxSizer(self.control_output_format_sbox, wx.VERTICAL)     #компоновщик группы
        #--- --- --- Варианты
        self.control_output_format_grid_sizer = wx.GridBagSizer(gbs_variants_gap[0], gbs_variants_gap[1])  #табличный компоновщик для вариантов
        self.control_output_format_all_chkbox = wx.CheckBox(self.control_output_format_sbox, id=wx.ID_ANY, label="Все доступные", size = checkbox_flag_size)
        self.control_output_format_all_chkbox.Bind(wx.EVT_CHECKBOX, self.OnControlPanelValueChange)
        self.control_output_format_grid_sizer.Add(self.control_output_format_all_chkbox, pos = (0, 0), flag=wx.ALIGN_LEFT)
        self.control_output_format_none_chkbox = wx.CheckBox(self.control_output_format_sbox, id=wx.ID_ANY, label="Никакие", size = checkbox_flag_size)
        self.control_output_format_none_chkbox.Bind(wx.EVT_CHECKBOX, self.OnControlPanelValueChange)
        self.control_output_format_grid_sizer.Add(self.control_output_format_none_chkbox, pos = (0, 1), flag=wx.ALIGN_LEFT)
        self.control_output_format_sline = wx.StaticLine(self.control_output_format_sbox, style = wx.LI_HORIZONTAL)
        self.control_output_format_grid_sizer.Add(self.control_output_format_sline, pos = (1, 0), span = (1, 3), flag = wx.EXPAND | wx.HORIZONTAL)
        self.control_output_format_pe3docx_chkbox = wx.CheckBox(self.control_output_format_sbox, id=wx.ID_ANY, label="Перечень Элементов (Word)", size = checkbox_flag_size)
        self.control_output_format_pe3docx_chkbox.Bind(wx.EVT_CHECKBOX, self.OnControlPanelValueChange)
        self.control_output_format_grid_sizer.Add(self.control_output_format_pe3docx_chkbox, pos = (2, 0), flag=wx.ALIGN_LEFT)
        self.control_output_format_pe3pdf_chkbox = wx.CheckBox(self.control_output_format_sbox, id=wx.ID_ANY, label="Перечень Элементов (PDF)", size = checkbox_flag_size)
        self.control_output_format_pe3pdf_chkbox.Bind(wx.EVT_CHECKBOX, self.OnControlPanelValueChange)
        self.control_output_format_grid_sizer.Add(self.control_output_format_pe3pdf_chkbox, pos = (2, 1), flag=wx.ALIGN_LEFT)
        self.control_output_format_pe3csv_chkbox = wx.CheckBox(self.control_output_format_sbox, id=wx.ID_ANY, label="Перечень Элементов (CSV)", size = checkbox_flag_size)
        self.control_output_format_pe3csv_chkbox.Bind(wx.EVT_CHECKBOX, self.OnControlPanelValueChange)
        self.control_output_format_grid_sizer.Add(self.control_output_format_pe3csv_chkbox, pos = (2, 2), flag=wx.ALIGN_LEFT)
        self.control_output_format_clxlsx_chkbox = wx.CheckBox(self.control_output_format_sbox, id=wx.ID_ANY, label="Список Компонентов (Excel)", size = checkbox_flag_size)
        self.control_output_format_clxlsx_chkbox.Bind(wx.EVT_CHECKBOX, self.OnControlPanelValueChange)
        self.control_output_format_grid_sizer.Add(self.control_output_format_clxlsx_chkbox, pos = (3, 0), flag=wx.ALIGN_LEFT)
        self.control_output_format_spcsv_chkbox = wx.CheckBox(self.control_output_format_sbox, id=wx.ID_ANY, label="Спецификация (CSV)", size = checkbox_flag_size)
        self.control_output_format_spcsv_chkbox.Bind(wx.EVT_CHECKBOX, self.OnControlPanelValueChange)
        self.control_output_format_grid_sizer.Add(self.control_output_format_spcsv_chkbox, pos = (4, 0), flag=wx.ALIGN_LEFT)
        #--- --- --- компоновка: Варианты -> Выходные форматы
        self.control_output_format_sbox_sizer.Add(self.control_output_format_grid_sizer, flag = wx.EXPAND | wx.ALL, border = gbs_variants_border)
        #--- --- компоновка: Выходные форматы -> Вывод
        self.control_output_sbox_sizer.Add(self.control_output_format_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Вывод -> Управление
        self.control_panel_sizer.Add(self.control_output_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Процесс
        self.control_process_sbox = wx.StaticBox(self.control_panel, label="Процесс")                   #контейнер (именная группа) для процесса
        self.control_process_sbox_sizer = wx.StaticBoxSizer(self.control_process_sbox, wx.VERTICAL)             #компоновщик группы
        #--- --- Выбор файлов/папок
        self.control_process_filebrowser_sizer = wx.FlexGridSizer(1, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1]) #табличный компоновщик для выбора файлов
        self.control_process_filebrowser_sizer.AddGrowableCol(1)                                          #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Исполняемый файл
        self.control_process_exe_label = wx.StaticText(self.control_process_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Исп. файл:")
        self.control_process_filebrowser_sizer.Add(self.control_process_exe_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.control_process_exe_text = wx.TextCtrl(self.control_process_sbox)
        self.control_process_exe_text.Bind(wx.EVT_TEXT, self.OnControlPanelValueChange)
        self.control_process_filebrowser_sizer.Add(self.control_process_exe_text, flag = wx.EXPAND)
        self.control_process_exe_browse = wx.Button(self.control_process_sbox, size = button_browse_size, label = button_browse_label)
        self.control_process_exe_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.control_process_exe_text, False, "Python source (*.py)|*.py|Windows executable (*.exe)|*.exe|Shell scripts (*.bat;*.sh;*.command)|*.bat;*.sh;*.command|All files (*.*)|*.*"))
        self.control_process_filebrowser_sizer.Add(self.control_process_exe_browse, flag = wx.FIXED_MINSIZE | wx.FIXED_LENGTH)
        #--- --- компоновка: Выбор файлов/папок -> Вывод
        self.control_process_sbox_sizer.Add(self.control_process_filebrowser_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- --- Поведение
        self.control_process_behaviour_sbox = wx.StaticBox(self.control_process_sbox, label="Поведение")                #контейнер (именная группа) для поведения
        self.control_process_behaviour_sbox_sizer = wx.StaticBoxSizer(self.control_process_behaviour_sbox, wx.VERTICAL) #компоновщик группы
        #--- --- --- Варианты
        self.control_process_behaviour_grid_sizer = wx.GridBagSizer(gbs_variants_gap[0], gbs_variants_gap[1])   #табличный компоновщик для вариантов
        self.control_process_behaviour_noquestions_chkbox = wx.CheckBox(self.control_process_behaviour_sbox, size = checkbox_flag_size, label="Не задавать вопросов")
        self.control_process_behaviour_noquestions_chkbox.Bind(wx.EVT_CHECKBOX, self.OnControlPanelValueChange)
        self.control_process_behaviour_grid_sizer.Add(self.control_process_behaviour_noquestions_chkbox, pos = (0, 0), flag=wx.ALIGN_LEFT)
        self.control_process_behaviour_nohalt_chkbox = wx.CheckBox(self.control_process_behaviour_sbox, size = checkbox_flag_size, label="Закрываться при завершении")
        self.control_process_behaviour_nohalt_chkbox.Bind(wx.EVT_CHECKBOX, self.OnControlPanelValueChange)
        self.control_process_behaviour_nohalt_chkbox.SetValue(True)
        self.control_process_behaviour_nohalt_chkbox.Disable()
        self.control_process_behaviour_grid_sizer.Add(self.control_process_behaviour_nohalt_chkbox,      pos = (0, 1), flag=wx.ALIGN_LEFT)
        #--- --- --- --- Уровень лога
        self.control_process_behaviour_loglevel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.control_process_behaviour_loglevel_label = wx.StaticText(self.control_process_behaviour_sbox, label="Уровень журнала: ")
        self.control_process_behaviour_loglevel_label.Disable()
        self.control_process_behaviour_loglevel_sizer.Add(self.control_process_behaviour_loglevel_label)
        self.control_process_behaviour_loglevel_choice = wx.Choice(self.control_process_behaviour_sbox, choices=["", "debug", "info", "warn", "error", "fatal"])
        self.control_process_behaviour_loglevel_choice.Disable()
        self.control_process_behaviour_loglevel_choice.Bind(wx.EVT_CHOICE, self.OnControlPanelValueChange)
        self.control_process_behaviour_loglevel_sizer.Add(self.control_process_behaviour_loglevel_choice)
        self.control_process_behaviour_grid_sizer.Add(self.control_process_behaviour_loglevel_sizer, pos = (0, 2), flag=wx.ALIGN_LEFT)
        #--- --- --- компоновка: Варианты -> Поведение
        self.control_process_behaviour_sbox_sizer.Add(self.control_process_behaviour_grid_sizer, flag = wx.EXPAND | wx.ALL, border = gbs_variants_border)
        #--- --- компоновка: Поведение -> Процесс
        self.control_process_sbox_sizer.Add(self.control_process_behaviour_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Процесс -> Управление
        self.control_panel_sizer.Add(self.control_process_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Выполнение
        self.control_execution_sbox = wx.StaticBox(self.control_panel, label="Выполнение")              #контейнер (именная группа) для выполнения
        self.control_execution_sbox_sizer = wx.StaticBoxSizer(self.control_execution_sbox, wx.VERTICAL)         #компоновщик группы
        #--- --- Команда
        self.control_execution_command_text = wx.TextCtrl(self.control_execution_sbox, style = wx.TE_MULTILINE | wx.TE_READONLY)
        self.control_execution_sbox_sizer.Add(self.control_execution_command_text, proportion = 1, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- --- Кнопка запуска
        self.control_execution_start_button = wx.Button(self.control_execution_sbox, label = "Запуск")
        self.control_execution_start_button.Bind(wx.EVT_BUTTON, self.OnStartButtonPress)
        self.control_execution_sbox_sizer.Add(self.control_execution_start_button, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Выполнение -> Управление
        self.control_panel_sizer.Add(self.control_execution_sbox_sizer, proportion = 1, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #компоновка: Управление -> Панель
        self.control_panel.SetSizer(self.control_panel_sizer)

        #возвращаем ссылку на панель
        return self.control_panel

    # Log panel ---------------------------------------------------------------------------------------------------------------------------------------------------------------
    def layout_logPanel(self, parent):
        #общие параметры панели
        button_control_size = self.FromDIP(wx.Size(100, -1))
        panel_border  = self.FromDIP(2)
        fgs_control_gap     = (self.FromDIP(5), self.FromDIP(5))
        
        #определяем шрифт лога
        scaling_factor = self.FromDIP(1000) / 1000
        if scaling_factor != 1.0:
            #масштабабирование используется
            log_font_name = "Consolas"
            log_font_size = 9
        else:
            #масштабирование не используется
            log_font_name = "Courier New"
            log_font_size = 9
        #log_font_encoding = wx.FONTENCODING_CP866

        self.log_panel = wx.Panel(parent)                                                        #панель управления
        self.log_panel_sizer = wx.BoxSizer(wx.VERTICAL)                                          #основной компоновщик на панели

        #--- Отступ сверху
        self.log_panel_sizer.Add((0, self.FromDIP(4)))
        #--- Панель управления
        self.log_control_sizer = wx.FlexGridSizer(1, 5, fgs_control_gap[0], fgs_control_gap[1])
        self.log_control_sizer.AddGrowableCol(4)
        self.log_control_clear_button = wx.Button(self.log_panel, size = button_control_size, label = "Очистить")
        self.log_control_clear_button.Bind(wx.EVT_BUTTON, self.OnClearLogButtonPress)
        self.log_control_sizer.Add(self.log_control_clear_button, flag = wx.FIXED_MINSIZE | wx.FIXED_LENGTH)
        self.log_control_copy_button = wx.Button(self.log_panel, size = button_control_size, label = "Копировать")
        self.log_control_copy_button.Bind(wx.EVT_BUTTON, self.OnCopyLogButtonPress)
        self.log_control_sizer.Add(self.log_control_copy_button, flag = wx.FIXED_MINSIZE | wx.FIXED_LENGTH)
        self.log_control_search_button = wx.Button(self.log_panel, size = button_control_size, label = "Поиск")
        self.log_control_search_button.SetToolTip("ЛКМ - поиск вперёд\nПКМ - поиск назад\nСКМ - очистить поиск")
        self.log_control_search_button.Bind(wx.EVT_BUTTON, self.OnSearchLogButtonClick)
        self.log_control_search_button.Bind(wx.EVT_RIGHT_DOWN, self.OnSearchLogButtonClick)
        self.log_control_search_button.Bind(wx.EVT_MIDDLE_DOWN, self.OnSearchLogButtonClick)
        self.log_control_sizer.Add(self.log_control_search_button, flag = wx.FIXED_MINSIZE | wx.FIXED_LENGTH)
        self.log_control_search_casesensitive_chkbox = wx.CheckBox(self.log_panel, label="")
        self.log_control_search_casesensitive_chkbox.SetToolTip("Учитывать регистр")
        self.log_control_sizer.Add(self.log_control_search_casesensitive_chkbox, flag = wx.ALIGN_CENTER_VERTICAL)
        self.log_control_search_text = wx.TextCtrl(self.log_panel)
        self.log_control_search_text.Bind(wx.EVT_TEXT, self.OnSearchLogTextChange)
        self.log_control_sizer.Add(self.log_control_search_text, flag = wx.EXPAND)
        #--- компоновка: Панель управления -> Основная панель
        self.log_panel_sizer.Add(self.log_control_sizer, flag = wx.EXPAND | wx.ALL, border = panel_border)

        #--- Отступ
        self.log_panel_sizer.Add((0, self.FromDIP(2)))

        #--- Журнал
        self.log_text = wx.TextCtrl(self.log_panel, style = wx.TE_MULTILINE | wx.TE_RICH2 | wx.TE_DONTWRAP | wx.TE_READONLY | wx.TE_NOHIDESEL)
        font = wx.Font(log_font_size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, log_font_name)
        self.log_text.SetFont(font)
        self.log_text.Bind(wx.EVT_TEXT, self.OnLogValueChange)
        self.log_text.Bind(wx.EVT_KEY_UP, self.OnLogCursorPositionChange)
        self.log_text.Bind(wx.EVT_KEY_DOWN, self.OnLogCursorPositionChange)
        self.log_text.Bind(wx.EVT_LEFT_UP, self.OnLogCursorPositionChange)
        self.log_text.Bind(wx.EVT_LEFT_DOWN, self.OnLogCursorPositionChange)
        self.log_text.Bind(wx.EVT_MOTION, self.OnLogCursorPositionChange)
        self.log_panel_sizer.Add(self.log_text, proportion = 1, flag = wx.EXPAND | wx.ALL, border = panel_border)

        #--- Строка статуса для журнала
        self.log_statusbar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        #self.log_statusbar_sizer.AddGrowableCol(0)
        self.log_statusbar_length_label = wx.StaticText(self.log_panel, label="", style = wx.ALIGN_LEFT)
        self.log_statusbar_sizer.Add(self.log_statusbar_length_label, proportion = 1,  flag = wx.EXPAND | wx.ALL)
        self.log_statusbar_linecount_label = wx.StaticText(self.log_panel, label="", style = wx.ALIGN_LEFT)
        self.log_statusbar_sizer.Add(self.log_statusbar_linecount_label, proportion = 1,  flag = wx.EXPAND | wx.ALL)
        self.log_statusbar_pos_line_label = wx.StaticText(self.log_panel, label="", style = wx.ALIGN_LEFT)
        self.log_statusbar_sizer.Add(self.log_statusbar_pos_line_label, proportion = 1,  flag = wx.EXPAND | wx.ALL)
        self.log_statusbar_pos_col_label = wx.StaticText(self.log_panel, label="", style = wx.ALIGN_LEFT)
        self.log_statusbar_sizer.Add(self.log_statusbar_pos_col_label, proportion = 1,  flag = wx.EXPAND | wx.ALL)
        self.log_statusbar_pos_abs_label = wx.StaticText(self.log_panel, label="", style = wx.ALIGN_LEFT)
        self.log_statusbar_sizer.Add(self.log_statusbar_pos_abs_label, proportion = 1, flag = wx.EXPAND | wx.ALL)
        #--- компоновка: Строка статуса -> Основная панель
        self.log_panel_sizer.Add(self.log_statusbar_sizer, flag = wx.EXPAND | wx.ALL, border = panel_border)

        #добавляем основной компоновщик на панель
        self.log_panel.SetSizer(self.log_panel_sizer)

        #Таймер для работы журнала
        self.log_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnLogTimer, self.log_timer)

        #возвращаем ссылку на панель
        return self.log_panel

    def OnFileBrowse(self, event, text_ctrl, multiple = False, wildcard = "All files (*.*)|*.*"):
        """ Opens file dialog and sets selected file path in the text field """
        style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        if multiple: style |= wx.FD_MULTIPLE
        with wx.FileDialog(self, "Select a file", style = style, wildcard = wildcard) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                files = file_dialog.GetPaths()
                text = "\n".join(files)
                text_ctrl.SetValue(text)

    def OnDirBrowse(self, event, text_ctrl):
        """ Opens folder dialog and sets selected directory path in the text field """
        with wx.DirDialog(self, "Select a directory") as dir_dialog:
            if dir_dialog.ShowModal() == wx.ID_OK:
                text_ctrl.SetValue(dir_dialog.GetPath())

    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    def OnParamsSave(self, event):
        #получаем параметры с панели управления
        params = self.get_controlpanel_params()

        style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        wildcard = "Configuration files (*.ini)|*.ini|All files (*.*)|*.*"
        with wx.FileDialog(self, "Сохранить параметры в файл", style = style, wildcard = wildcard) as file_dialog:
            file_dialog.SetDirectory(_module_dirname)
            file_dialog.SetFilename('gui.ini')
            if file_dialog.ShowModal() == wx.ID_OK:
                path = file_dialog.GetPath()
                path = os.path.join(_module_dirname, path)
                self.params_save(params, path)

    def OnParamsLoad(self, event):
        style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        wildcard = "Configuration files (*.ini)|*.ini|All files (*.*)|*.*"
        with wx.FileDialog(self, "Загрузить параметры из файла", style = style, wildcard = wildcard) as file_dialog:
            file_dialog.SetDirectory(_module_dirname)
            file_dialog.SetFilename('gui.ini')
            if file_dialog.ShowModal() == wx.ID_OK:
                path = file_dialog.GetPath()
                path = os.path.join(_module_dirname, path)
                params = self.params_load(path)
                if params is not None:
                    self.params_apply(params)
                    self.statusbar.SetStatusText("Параметры запуска успешно загружены")

    def OnParamsDefaults(self, event):
        params = self.params_defaults()
        self.params_apply(params)

    def OnAbout(self, event):
        """Display an About Dialog"""
        message = f"Графический интерфейс пользователя для программы BoM converter.\nВерсия от {_module_date:%Y-%m-%d}"
        wx.MessageBox(message, "О программе", wx.OK|wx.ICON_INFORMATION)

    def OnControlPanelValueChange(self, event):
        """Changes on control panel were made"""
        #получаем параметры с интерфейса
        params = self.get_controlpanel_params()
        
        #изменения на интерфейсе
        #--- количество файлов данных
        datafiles = params['input']['datafiles']
        datafiles_num = 0
        if len(datafiles) > 0:
            datafiles = datafiles.split('\n')
            for file in datafiles:
                if len(file) > 0: datafiles_num += 1
        label = self.control_input_data_label.GetLabelText()
        label = label.split('\n')
        self.control_input_data_label.SetLabelText(f"{label[0]}\n[{datafiles_num}]")
        #--- кнопка запуска
        if datafiles_num > 0: self.control_execution_start_button.Enable()
        else:                 self.control_execution_start_button.Disable()
        #--- флаги оптимизации
        config_optimize_all  = OptimizationID.ALL.value in params['config']['optimize']
        config_optimize_none = OptimizationID.NONE.value in params['config']['optimize']
        config_optimize_global = config_optimize_all | config_optimize_none
        self.control_config_optimize_mfrname_chkbox.Enable(not config_optimize_global)
        self.control_config_optimize_restol_chkbox.Enable(not config_optimize_global)
        self.control_config_optimize_all_chkbox.Enable(not config_optimize_none)
        self.control_config_optimize_none_chkbox.Enable(not config_optimize_all)
        #--- флаги выходных форматов
        output_format_all  = OutputID.ALL.value in params['output']['format']
        output_format_none = OutputID.NONE.value in params['output']['format']
        output_format_global = output_format_all | output_format_none
        self.control_output_format_pe3docx_chkbox.Enable(not output_format_global)
        self.control_output_format_pe3pdf_chkbox.Enable(not output_format_global)
        self.control_output_format_pe3csv_chkbox.Enable(not output_format_global)
        self.control_output_format_clxlsx_chkbox.Enable(not output_format_global)
        self.control_output_format_spcsv_chkbox.Enable(not output_format_global)
        self.control_output_format_all_chkbox.Enable(not output_format_none)
        self.control_output_format_none_chkbox.Enable(not output_format_all)

        #получаем аргументы для вызова
        argv = self.build_argv(params)

        #собираем команду для отображения
        command = ""
        for arg in argv:
            if arg.find(" ") >= 0 or arg.find("\\") >= 0:
                command += ' "' + arg + '"'
            else:
                command += ' '  + arg
        command = command[1:]
        self.control_execution_command_text.SetValue(command)

    def OnStartButtonPress(self, event):
        """Start button press event handler"""
        params = self.get_controlpanel_params()
        argv = self.build_argv(params)
        self.notebook.SetSelection(1)
        self.cli_execute(argv)
        self.log_lines_shown = len(self.cli_log)
        self.log_lines_last = self.cli_log[-1]
        self.log_last_update = time.monotonic()
        self.log_timer.Start(250)
        self.control_execution_start_button.Disable()
        
    def OnClearLogButtonPress(self, event):
        """Clear log button press event handler"""
        self.log_text.Clear()

    def OnCopyLogButtonPress(self, event):
        """Copy log button press event handler"""
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(self.log_text.GetValue()))
            wx.TheClipboard.Close()

    def OnSearchLogButtonClick(self, event):
        """Search log button press event handler"""
        source = 1
        if isinstance(event, wx.MouseEvent):
            if event.RightDown():
                source = 3
            elif event.MiddleDown():
                #clear search text
                self.log_control_search_text.Clear()
                return

        search_text = self.log_control_search_text.GetValue()
        if not search_text: return
        case_sensitive = self.log_control_search_casesensitive_chkbox.GetValue()
        log_text = self.log_text.GetValue()
        
        if not case_sensitive:
            search_text = search_text.casefold()
            log_text = log_text.casefold()
        
        start_pos = self.log_text.GetInsertionPoint() + 1  # Start after current selection
        if source == 1:
            #search forward
            found_pos = log_text.find(search_text, start_pos)
            if found_pos == -1:  # Not found, wrap around
                found_pos = log_text.find(search_text, 0)
        elif source == 3:
            #search backward
            found_pos = log_text.rfind(search_text, 0, start_pos)
            if found_pos == -1:  # Not found, wrap around to the bottom
                found_pos = log_text.rfind(search_text)

        if found_pos != -1:
            self.log_text.SetInsertionPoint(found_pos)
            self.log_text.SetSelection(found_pos, found_pos + len(search_text))

        event.Skip()  # Ensure the event propagates properly
        
    def OnSearchLogTextChange(self, event):
        search_text = self.log_control_search_text.GetValue()
        if len(search_text) > 0: self.log_control_search_button.Enable()
        else: self.log_control_search_button.Disable()

    def OnLogValueChange(self, event):
        text = self.log_text.GetValue()
        lines = text.count("\n") + 1
        chars = len(text)

        self.log_statusbar_length_label.SetLabelText(f"length: {chars:,}".replace(',', ' '))
        self.log_statusbar_linecount_label.SetLabelText(f"lines: {lines:,}".replace(',', ' '))
        self.OnLogCursorPositionChange(None)
        if event is not None: event.Skip()

    def OnLogCursorPositionChange(self, event):
        text = self.log_text.GetValue()
        pos = self.log_text.GetInsertionPoint()
        sel_start, sel_end = self.log_text.GetSelection()
        
        line = text[:pos].count("\n") + 1
        last_newline = text[:pos].rfind("\n")
        col = pos - last_newline if last_newline != -1 else pos + 1

        self.log_statusbar_pos_line_label.SetLabelText(f"ln: {line:,}".replace(',', ' '))
        self.log_statusbar_pos_col_label.SetLabelText(f"col: {col:,}".replace(',', ' '))

        if sel_start != sel_end:
            sel_length = sel_end - sel_start
            sel_text = self.log_text.GetStringSelection()
            sel_lines = sel_text.count('\n') + 1 if sel_text else 0
            self.log_statusbar_pos_abs_label.SetLabelText(f"sel: {sel_length:,} | {sel_lines:,}".replace(',', ' '))
        else:
            self.log_statusbar_pos_abs_label.SetLabelText(f"pos: {pos:,}".replace(',', ' '))

        if event is not None: event.Skip()

    def OnLogTimer(self, event):
        self.log_update("")

    def get_controlpanel_params(self):
        """Get params from control panel"""
        #собираем сырые данные с формы

        config_optimize = []
        if self.control_config_optimize_none_chkbox.GetValue(): config_optimize.append(OptimizationID.NONE.value)
        if self.control_config_optimize_all_chkbox.GetValue(): config_optimize.append(OptimizationID.ALL.value)
        if self.control_config_optimize_mfrname_chkbox.GetValue(): config_optimize.append(OptimizationID.MFR_NAME.value)
        if self.control_config_optimize_restol_chkbox.GetValue(): config_optimize.append(OptimizationID.RES_TOL.value)
        config_optimize = ",".join(config_optimize)

        output_format = []
        if self.control_output_format_none_chkbox.GetValue(): output_format.append(OutputID.NONE.value)
        if self.control_output_format_all_chkbox.GetValue(): output_format.append(OutputID.ALL.value)
        if self.control_output_format_pe3docx_chkbox.GetValue(): output_format.append(OutputID.PE3_DOCX.value)
        if self.control_output_format_pe3pdf_chkbox.GetValue(): output_format.append(OutputID.PE3_PDF.value)
        if self.control_output_format_pe3csv_chkbox.GetValue(): output_format.append(OutputID.PE3_CSV.value)
        if self.control_output_format_clxlsx_chkbox.GetValue(): output_format.append(OutputID.CL_XLSX.value)
        if self.control_output_format_spcsv_chkbox.GetValue(): output_format.append(OutputID.SP_CSV.value)
        output_format = ",".join(output_format)

        params = {
            'input': {
                'adproject'     : self.control_input_adproject_chkbox.GetValue(),
                'datafiles'     : self.control_input_data_text.GetValue(),
                'titleblock'    : self.control_input_titleblock_text.GetValue()
            },
            'config': {
                'settings'      : self.control_config_settings_text.GetValue(),
                'parser'        : self.control_config_parser_text.GetValue(),
                'optimize'      : config_optimize
            },
            'output': {
                'directory'     : self.control_output_directory_text.GetValue(),
                'format'        : output_format
            },
            'process': {
                'executable'    : self.control_process_exe_text.GetValue(),
                'noquestions'   : self.control_process_behaviour_noquestions_chkbox.GetValue(),
                'nohalt'        : self.control_process_behaviour_nohalt_chkbox.GetValue(),
                'loglevel'      : self.control_process_behaviour_loglevel_choice.GetSelection()
            }
        }

        #обрабатываем собранные данные
        loglevel = params['process']['loglevel']
        if loglevel < 0: loglevel = 0
        params['process']['loglevel'] = self.control_process_behaviour_loglevel_choice.GetString(loglevel)

        return params

    def params_apply(self, params):
        if 'input' in params:
            section = params['input']
            if 'adproject' in section: self.control_input_adproject_chkbox.SetValue(section['adproject'])
            if 'datafiles' in section: self.control_input_data_text.SetValue(section['datafiles'])
            if 'titleblock' in section: self.control_input_titleblock_text.SetValue(section['titleblock'])
        if 'config' in params:
            section = params['config']
            if 'settings' in section: self.control_config_settings_text.SetValue(section['settings'])
            if 'parser' in section: self.control_config_parser_text.SetValue(section['parser'])
            if 'optimize' in section:
                self.control_config_optimize_none_chkbox.SetValue(OptimizationID.NONE.value in section['optimize'])
                self.control_config_optimize_all_chkbox.SetValue(OptimizationID.ALL.value in section['optimize'])
                self.control_config_optimize_mfrname_chkbox.SetValue(OptimizationID.MFR_NAME.value in section['optimize'])
                self.control_config_optimize_restol_chkbox.SetValue(OptimizationID.RES_TOL.value in section['optimize'])
        if 'output' in params:
            section = params['output']
            if 'output' in section: self.control_output_directory_text.SetValue(section['directory'])
            if 'format' in section:
                self.control_output_format_none_chkbox.SetValue(OutputID.NONE.value in section['format'])
                self.control_output_format_all_chkbox.SetValue(OutputID.ALL.value in section['format'])
                self.control_output_format_pe3docx_chkbox.SetValue(OutputID.PE3_DOCX.value in section['format'])
                self.control_output_format_pe3pdf_chkbox.SetValue(OutputID.PE3_PDF.value in section['format'])
                self.control_output_format_pe3csv_chkbox.SetValue(OutputID.PE3_CSV.value in section['format'])
                self.control_output_format_clxlsx_chkbox.SetValue(OutputID.CL_XLSX.value in section['format'])
                self.control_output_format_spcsv_chkbox.SetValue(OutputID.SP_CSV.value in section['format'])
        if 'process' in params:
            section = params['process']
            if 'executable' in section: self.control_process_exe_text.SetValue(section['executable'])
            if 'noquestions' in section: self.control_process_behaviour_noquestions_chkbox.SetValue(section['noquestions'])
            if 'nohalt' in section: self.control_process_behaviour_nohalt_chkbox.SetValue(section['nohalt'])
            if 'loglevel' in section:
                for i in range(self.control_process_behaviour_loglevel_choice.GetCount()):
                    if self.control_process_behaviour_loglevel_choice.GetString(i) == section['loglevel']:
                        self.control_process_behaviour_loglevel_choice.SetSelection(i)

        self.OnControlPanelValueChange(None)

    def params_save(self, params, filename):
        config = configparser.ConfigParser()

        for section, values in params.items():
            config[section] = values

        with open(filename, "w", encoding="utf-8") as configfile:
            config.write(configfile)

    def params_load(self, filename):
        config = configparser.ConfigParser()

        try:
            config.read(filename, encoding="utf-8")

            params = {
                section: {key: self.parse_value(value) for key, value in config[section].items()}
                for section in config.sections()
            }

            return params

        except FileNotFoundError as e:
            self.statusbar.SetStatusText(f"Error: {e}")
        except (OSError, IOError) as e:
            self.statusbar.SetStatusText(f"File access error: {e}")
        except (configparser.Error, ValueError, KeyError) as e:
            self.statusbar.SetStatusText(f"Config parsing error: {e}")

        return None

    def params_defaults(self):
        params = {
            'input': {
                'adproject'     : False,
                'datafiles'     : "",
                'titleblock'    : ""
            },
            'config': {
                'settings'      : "",
                'parser'        : "",
                'optimize'      : ""
            },
            'output': {
                'directory'     : "",
                'format'        : ""
            },
            'process': {
                'executable'    : "",
                'noquestions'   : False,
                'nohalt'        : True,
                'loglevel'      : ""
            }
        }
        return params

    def parse_value(self, value):
        """Convert string values to int, float, or bool when possible."""
        if value.lower() in ("true", "yes", "on"):
            return True
        elif value.lower() in ("false", "no", "off"):
            return False
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value  # Return as string if conversion fails

    def build_argv(self, params):
        """Build command line argument vector from control panel params"""
        argv = []

        #исполняемый файл
        executable = params.get('process', {}).get('executable', '')
        if len(executable) == 0: executable = 'bomconverter.py'
        if os.path.splitext(executable)[1].lstrip(os.extsep) == 'py':
            argv.append('python')
        argv.append(executable)

        #файлы данных
        datafiles = params.get('input', {}).get('datafiles', '')
        if len(datafiles) > 0:
            datafiles = datafiles.split('\n')
            for file in datafiles:
                if len(file) > 0: argv.append(file)

        #проект Altium Designer
        adproject = params.get('input', {}).get('adproject', False)
        if adproject: argv.append('--adproject')

        #словарь с данными основной надписи
        titleblock = params.get('input', {}).get('titleblock', '')
        if len(titleblock) > 0:
            argv.extend(['--titleblock', titleblock])

        #модуль настроек
        settings = params.get('config', {}).get('settings', '')
        if len(settings) > 0:
            argv.extend(['--settings', settings])

        #модуль анализатора
        parser = params.get('config', {}).get('parser', '')
        if len(parser) > 0:
            argv.extend(['--parser', parser])

        #оптимизации
        optimize = params.get('config', {}).get('optimize', "")
        if optimize:
            argv.append('--optimize')
            optimize = optimize.replace(' ', '').split(',')
            if OptimizationID.NONE.value in optimize: argv.append(OptimizationID.NONE.value)
            elif OptimizationID.ALL.value in optimize: argv.append(OptimizationID.ALL.value)
            else:
                for opt in optimize:
                    if any(opt == item.value for item in OptimizationID):
                        argv.append(opt)

        #выходная папка
        directory = params.get('output', {}).get('directory', '')
        if len(directory) > 0:
            argv.extend(['--output-dir', directory])
            
        #выходные форматы
        format = params.get('output', {}).get('format', "")
        if format:
            argv.append('--output')
            format = format.replace(' ', '').split(',')
            if OutputID.NONE.value in format: argv.append(OutputID.NONE.value)
            elif OutputID.ALL.value in format: argv.append(OutputID.ALL.value)
            else:
                for opt in format:
                    if any(opt == item.value for item in OutputID):
                        argv.append(opt)

        #не задавать вопросов
        noquestions = params.get('process', {}).get('noquestions', False)
        if noquestions: argv.append('--noquestions')

        #не закрывать окно по завершению
        nohalt = params.get('process', {}).get('nohalt', False)
        if nohalt: argv.append('--nohalt')

        #уровень лога
        #loglevel = params.get('process', {}).get('loglevel', '')
        #if len(loglevel) > 0:
        #    if   loglevel == 'debug': argv.extend(['--loglevel', 'debug'])
        #    elif loglevel == 'info':  argv.extend(['--loglevel', 'info'])
        #    elif loglevel == 'warn':  argv.extend(['--loglevel', 'warn'])
        #    elif loglevel == 'error': argv.extend(['--loglevel', 'error'])
        #    elif loglevel == 'fatal': argv.extend(['--loglevel', 'fatal'])

        return argv

    def cli_execute(self, argv):
        """Executes CLI program"""
        self.statusbar.SetStatusText("Процесс обработки запущен...")
        self.cli_log.clear()
        self.cli_log.append('')
        self.process = subprocess.Popen(argv,
            stdout = subprocess.PIPE,
            stdin = subprocess.PIPE,
            stderr = subprocess.PIPE,
            text = True,
            encoding = 'utf-8',
            errors="replace"
        )
        threading.Thread(target = self.cli_read, daemon = True).start()
        
    def cli_read(self):
        """Reads CLI output"""
        while True:
            #читаем по одному символу
            char = self.process.stdout.read(1)
            #проверяем завершение процесса
            if not char:
                exit_code = self.process.poll()
                if exit_code is not None:
                    wx.CallAfter(self.cli_finished, exit_code)
                    break
            #обновляем лог и следим за запросами
            if char:
                wx.CallAfter(self.log_update, char)
                wx.CallAfter(self.cli_request)

    def cli_finished(self, code):
        self.log_timer.Stop()
        self.control_execution_start_button.Enable()

        message = ""
        if code == 0:
            message = "Обработка успешно завершена"
        elif code == 3:
            message = "Операция отменена пользователем"
        else:
            message = "Программа завершилась с ошибкой"
        self.statusbar.SetStatusText(message)

    def cli_request(self):
        current_line = self.cli_log[-1]
        #определяем есть ли запрос
        if current_line.startswith("REQUEST") and (current_line.endswith(": ") or current_line.endswith("? ")):
            #в текущей строке есть запрос и он закончен -> определяем чего именно
            if "Choose which BoMs to process" in current_line:
                #запрос какие BoM-файлы обрабатывать -> надо получить список файлов
                self.select_bom()

    def log_update(self, text):
        #обновляем лог в списке
        if len(text) > 0:
            text = text.split('\n')
            self.cli_log[-1] += text[0]
            self.cli_log.extend(text[1:])

        #обновляем лог на интерфейсе построчно (так как посимвольно сильно тромозит процесс) или текущую строку по задержке (если долго не было вывода)
        log_lines_total = len(self.cli_log)
        if log_lines_total > self.log_lines_shown or time.monotonic() - self.log_last_update > 0.25:
            lines_appended = self.cli_log[self.log_lines_shown - 1:]
            text = lines_appended[0][len(self.log_lines_last):]
            if len(lines_appended) > 1:
                text += "\n" + "\n".join(lines_appended[1:])
            self.log_text.AppendText(text)
            self.log_lines_shown = log_lines_total
            self.log_lines_last = lines_appended[-1]
            self.log_last_update = time.monotonic()

    def select_bom(self):
        """Opens dialog for BoM file selection"""
        #получаем список файлов из консоли (журнала)
        choices = []
        for line in reversed(self.cli_log[:-1]):
            if "BoMs found" in line: break
            choices.append(line.strip())
        choices.reverse()

        #выдаём запрос на выбор файлов
        message = "Обнаружены следующие BoM-файлы.\nВыберите какие из них требуется обработать."
        dlg = MultiChoiceWDialog(frame, "Выбор BoM-файлов", message, choices, selectall = "Выбрать все", selections = -1, message_style = wx.ALIGN_CENTER)
        if dlg.ShowModal() == wx.ID_OK:
            selections = dlg.GetSelections()
            if len(selections) > 0:
                if len(selections) == len(choices):
                    answer = "0\n"
                else:
                    answer = ""
                    for i in selections:
                        answer += choices[i].split(':')[0] + ", "
                    answer = answer.strip(', ') + '\n'
            else:
                answer = "q\n"
        else:
            answer = "q\n"

        self.log_update(answer)
        self.process.stdin.write(answer)
        self.process.stdin.flush()

class MultiChoiceWDialog(wx.Dialog):
    """This class represents a dialog that shows a list of strings, and allows the user to select one or more (with select all option)"""
    def __init__(self, parent, title:str, message:str, choices:list[str], selectall:str = None, selections:int|list[int] = None, message_style = wx.ALIGN_LEFT, message_font = None, pos = None, size = None, maxsize = None):
        super().__init__(parent, wx.ID_ANY, title, style = wx.DEFAULT_DIALOG_STYLE & ~wx.RESIZE_BORDER)

        self.message = message
        self.selectall = selectall
        self.choices = choices

        #Generic panel params
        frame_border = self.FromDIP(10)
        panel_border = self.FromDIP(0)
        choices_spacer = self.FromDIP(5)
        
        #Frame sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        #Main panel
        self.panel = wx.Panel(self)
        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)

        #--- Message
        self.message_label = wx.StaticText(self.panel, label = self.message, style = message_style)
        if message_font is not None: self.message_label.SetFont(message_font)
        self.panel_sizer.Add(self.message_label, proportion = 0, flag = wx.EXPAND | wx.BOTTOM, border = panel_border)

        #--- Select all
        if self.selectall is not None:
            self.panel_sizer.Add((0, self.FromDIP(10)))
            self.selectall_chkbox = wx.CheckBox(self.panel, label = self.selectall, style = wx.CHK_3STATE)
            self.selectall_chkbox.Bind(wx.EVT_CHECKBOX, self.OnSelectAll)
            self.panel_sizer.Add(self.selectall_chkbox, proportion = 0, flag = wx.EXPAND | wx.ALL, border = panel_border)
        #--- --- Static line
            self.selectall_sline_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.panel_sizer.Add((0, self.FromDIP(5)))
            self.selectall_sline = wx.StaticLine(self.panel, style = wx.LI_HORIZONTAL)
            self.selectall_sline_sizer.Add(self.selectall_sline, proportion = 1, flag = wx.EXPAND)
            self.panel_sizer.Add(self.selectall_sline_sizer, flag = wx.EXPAND | wx.ALL, border = panel_border)
            self.panel_sizer.Add(wx.StaticText(self.panel, label = "", size = self.FromDIP((0, 5))))
        else:
        #--- Spacer
            self.panel_sizer.Add(wx.StaticText(self.panel, label = "", size = self.FromDIP((0, 10))))

        #--- Panel for choices
        self.choices_panel = wx.Panel(self.panel)
        #self.choices_panel.SetScrollRate(self.FromDIP(6), self.FromDIP(6))  # Set scrolling speed (if wx.ScrolledWindow is used as a panel)
        self.choices_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        #--- --- Add checkboxes for each choice
        self.checkbox_list = []
        for choice in self.choices:
            checkbox = wx.CheckBox(self.choices_panel, label=choice)
            checkbox.Bind(wx.EVT_CHECKBOX, self.OnChoice)
            self.checkbox_list.append(checkbox)
            self.choices_panel_sizer.Add(checkbox, proportion = 0, flag = wx.ALL, border = panel_border)
            self.choices_panel_sizer.Add((0, choices_spacer))
        #--- Set the sizer for the scrollable panel
        self.choices_panel.SetSizer(self.choices_panel_sizer)
        #--- Add the scrollable panel to the main dialog sizer
        self.panel_sizer.Add(self.choices_panel, proportion = 1, flag = wx.EXPAND | wx.ALL, border = panel_border)
        
         #--- Spacer
        self.panel_sizer.Add((0, self.FromDIP(10)))

        #--- OK and Cancel buttons
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ok_button = wx.Button(self.panel, id = wx.ID_OK)
        self.button_sizer.Add(self.ok_button, proportion = 0, flag = wx.RIGHT, border = self.FromDIP(5))
        self.cancel_button = wx.Button(self.panel, id = wx.ID_CANCEL)
        self.button_sizer.Add(self.cancel_button, proportion = 0, flag = wx.LEFT, border = self.FromDIP(5))
        self.panel_sizer.Add(self.button_sizer, 0, wx.ALIGN_CENTER)

        #Add panel sizer to the main panel
        self.panel.SetSizer(self.panel_sizer)
        #Add main panel to frame sizer
        self.sizer.Add(self.panel, proportion = 1, flag = wx.EXPAND | wx.ALL, border = frame_border)
        self.SetSizer(self.sizer)

        #Window size and position
        screen_width, screen_height = wx.DisplaySize()
        bestsize_width, bestsize_height = self.GetBestSize()
        if size is not None:
            self.SetSize(size)
        else:
            maxsize_width = int(0.95 * screen_width)
            maxsize_height = int(0.95 * screen_height)
            if maxsize is not None:
                if maxsize[0] >= 0: maxsize_width = maxsize[0]
                if maxsize[1] >= 0: maxsize_height = maxsize[1]
            frame_width  = min(bestsize_width,  maxsize_width)
            frame_height = min(bestsize_height, maxsize_height)
            self.SetSizeHints((frame_width, frame_height), (frame_width, frame_height))
            self.Fit()
        if pos is not None:
            self.SetPosition(pos)
        else:
            wx.CallAfter(self.Centre)
            frame_width, frame_height = self.GetSize()
            frame_pos_x = (screen_width - frame_width) // 2
            frame_pos_y = (screen_height - frame_height) // 2
            self.SetPosition((frame_pos_x, frame_pos_y))

        #Selections state
        self.SetSelections(selections)

    def OnSelectAll(self, event):
        """Select all state change event handler"""
        value = self.selectall_chkbox.GetValue()
        for checkbox in self.checkbox_list:
            checkbox.SetValue(value)

    def OnChoice(self, event):
        """Choice state change event handler"""
        if self.selectall is not None:
            checked_num = 0
            for checkbox in self.checkbox_list:
                if checkbox.GetValue(): checked_num += 1
            if checked_num == 0:
                self.selectall_chkbox.SetValue(False)
            elif checked_num == len(self.checkbox_list):
                self.selectall_chkbox.SetValue(True)
            else:
                self.selectall_chkbox.Set3StateValue(wx.CHK_UNDETERMINED)

    def GetSelections(self) -> list[int]:
        """Returns array with indexes of selected items"""
        selections = []
        for i, checkbox in enumerate(self.checkbox_list):
            if checkbox.GetValue(): selections.append(i)
        return selections

    def SetSelections(self, selections:int|list[int]) -> None:
        """Sets selected items from the array of selected items’ indexes"""
        if selections is not None:
            if isinstance(selections, int):
                if selections == -1:
                    self.selectall_chkbox.SetValue(True)
                    self.OnSelectAll(None)
                else:
                    if selections >= 0 and selections < len(self.checkbox_list):
                        self.checkbox_list[selections].SetValue(True)
            elif isinstance(selections, list):
                for i in selections:
                    if isinstance(i, int):
                        if i >= 0 and i < len(self.checkbox_list):
                            self.checkbox_list[i].SetValue(True)
                self.OnChoice(None)

if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the frame, show it, and start the event loop.
    app = App()
    frame = MainFrame()

    #загружаем параметры из файла 'gui.ini'
    params = None
    params_file = 'gui.ini'
    if os.path.isfile(params_file): params = frame.params_load(params_file)
    if params is None: params = frame.params_defaults()
    frame.params_apply(params)

    app.MainLoop()