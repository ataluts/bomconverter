#!/usr/bin/env python

import wx
import sys
import os
import subprocess, threading
import time
import datetime
import configparser, ast
from enum import Enum
from bomconverter import OutputID as Bomconverter_OutputID
from bomconverter import OptimizationID as Bomconverter_OptimizationID
from bomdiscriminator import OutputID as Bomdiscriminator_OutputID
from bomdiscriminator import XlsxChangesModeID as Bomdiscriminator_XlsxChangesModeID

_module_dirname = os.path.dirname(__file__)                      #адрес папки со скриптом
_module_date    = datetime.datetime(2025, 7, 3)

class FileBrowseWildcards(Enum):
    ALL            = "All files (*.*)|*.*"
    PYTHON         = "Python source (*.py)|*.py"
    WINDOWS_EXE    = "Windows executable (*.exe)|*.exe"
    SHELL_SCRIPT   = "Shell scripts (*.bat;*.sh;*.command)|*.bat;*.sh;*.command"
    ALTIUM_PROJECT = "Altium Designer project (*.PrjPcb)|*.PrjPcb"
    TEXT           = "Text files (*.txt)|*.txt"
    CSV            = "CSV files (*.csv)|*.csv"
    XLSX           = "Excel workbook (*.xlsx)|*.xlsx"

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
        super(MainFrame, self).__init__(None, title="BoM converter - GUI")                          #инициализация
        self.SetSizeHints(self.FromDIP(664), self.FromDIP(728))                                     #минимальные размеры окна

        self.cli_log = []                                                                           #журнал командной строки

        self.layout_statusBar()                                                                     #строка состояния
        self.statusbar.SetStatusText("Инициализация...")
        self.layout_menuBar()                                                                       #главное меню

        self.panel = wx.Panel(self)                                                                 #панель где будут располагаться элементы управления
        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)                                                 #основной компоновщик на этой панели
        
        self.notebook = wx.Notebook(self.panel)                                                     #создаём блокнот (вкладки)
        self.notebook.AddPage(self.layout_panel_bomconverter(self.notebook), "Конвертация BoM")     #добавляем панель bomconverter на вкладку #0
        self.notebook.AddPage(self.layout_panel_bomdiscriminator(self.notebook), "Сравнение BoM")   #добавляем панель bomdiscriminator на вкладку #1
        self.notebook.AddPage(self.layout_panel_cldiscriminator(self.notebook), "Сравнение CL")     #добавляем панель cldiscriminator на вкладку #2
        self.notebook.AddPage(self.layout_panel_log(self.notebook), "Журнал")                       #добавляем панель журнал на вкладку #3

        self.panel_sizer.Add(self.notebook, 1, flag = wx.EXPAND)                                    #добавляем блокнот на панель
        self.panel.SetSizer(self.panel_sizer)                                                       #добавляем основной компоновщик на панель

        #отображаем окно и центруем окно на экране
        self.Show()
        wx.CallAfter(self.Centre)
        screen_width, screen_height = wx.DisplaySize()                                              #размеры экрана
        frame_width,  frame_height  = self.GetSize()                                                #размеры окна
        frame_pos_x = (screen_width - frame_width) // 2                                             #координаты окна
        frame_pos_y = (screen_height - frame_height) // 2
        self.SetPosition((frame_pos_x, frame_pos_y))

        #инициализация событий интерфейса
        self.OnBomconverterPanelValueChange(None)
        self.OnBomdiscriminatorPanelValueChange(None)
        self.OnCldiscriminatorPanelValueChange(None)
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

    # BoM converter panel ---------------------------------------------------------------------------------------------------------------------------------------------------------------
    def layout_panel_bomconverter(self, parent):
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

        self.bomconverter_panel = wx.Panel(parent)                                                      #панель управления
        self.bomconverter_panel_sizer = wx.BoxSizer(wx.VERTICAL)                                        #основной компоновщик на панели

        #--- Ввод
        self.bomconverter_input_sbox = wx.StaticBox(self.bomconverter_panel, label="Ввод")                             #контейнер (именная группа) для ввода
        self.bomconverter_input_sbox_sizer = wx.StaticBoxSizer(self.bomconverter_input_sbox, wx.VERTICAL)                     #компоновщик группы
        #--- --- Выбор файлов/папок
        self.bomconverter_input_filebrowser_sizer = wx.FlexGridSizer(3, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1]) #табличный компоновщик элементов управления
        self.bomconverter_input_filebrowser_sizer.AddGrowableCol(1)                                              #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Флаг проекта Altium Designer
        self.bomconverter_input_adproject_chkbox = wx.CheckBox(self.bomconverter_input_sbox, label="Проект Altium Designer")
        self.bomconverter_input_adproject_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.bomconverter_input_filebrowser_sizer.Add((0, 0))
        self.bomconverter_input_filebrowser_sizer.Add(self.bomconverter_input_adproject_chkbox, flag=wx.ALIGN_LEFT)
        self.bomconverter_input_filebrowser_sizer.Add((0, 0))
        #--- --- --- Файлы данных
        self.bomconverter_input_data_label = wx.StaticText(self.bomconverter_input_sbox, label="Данные:\n[0]", style = wx.ALIGN_RIGHT, size = label_browse_size)
        self.bomconverter_input_filebrowser_sizer.Add(self.bomconverter_input_data_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomconverter_input_data_text = wx.TextCtrl(self.bomconverter_input_sbox, style = wx.TE_MULTILINE)
        self.bomconverter_input_data_text.Bind(wx.EVT_TEXT, self.OnBomconverterPanelValueChange)
        self.bomconverter_input_data_text.SetDropTarget(FileDropTarget(self.bomconverter_input_data_text))
        self.bomconverter_input_filebrowser_sizer.Add(self.bomconverter_input_data_text, flag = wx.EXPAND)
        self.bomconverter_input_data_browse = wx.Button(self.bomconverter_input_sbox, label = button_browse_label, size = button_browse_size)
        self.bomconverter_input_data_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.bomconverter_input_data_text, True, wildcard = "|".join([FileBrowseWildcards.ALTIUM_PROJECT.value, FileBrowseWildcards.CSV.value, FileBrowseWildcards.TEXT.value, FileBrowseWildcards.ALL.value])))
        self.bomconverter_input_data_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.bomconverter_input_data_text.Clear())
        self.bomconverter_input_filebrowser_sizer.Add(self.bomconverter_input_data_browse, flag = wx.EXPAND)
        #--- --- --- Файл основной надписи
        self.bomconverter_input_titleblock_label = wx.StaticText(self.bomconverter_input_sbox, label="Осн. надпись:", style = wx.ALIGN_RIGHT, size = label_browse_size)
        self.bomconverter_input_filebrowser_sizer.Add(self.bomconverter_input_titleblock_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomconverter_input_titleblock_text = wx.TextCtrl(self.bomconverter_input_sbox)
        self.bomconverter_input_titleblock_text.Bind(wx.EVT_TEXT, self.OnBomconverterPanelValueChange)
        self.bomconverter_input_titleblock_text.SetDropTarget(FileDropTarget(self.bomconverter_input_titleblock_text))
        self.bomconverter_input_filebrowser_sizer.Add(self.bomconverter_input_titleblock_text, flag = wx.EXPAND)
        self.bomconverter_input_titleblock_browse = wx.Button(self.bomconverter_input_sbox, wx.ID_ANY, label = button_browse_label, size = button_browse_size)
        self.bomconverter_input_titleblock_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.bomconverter_input_titleblock_text, False, wildcard = "|".join([FileBrowseWildcards.PYTHON.value, FileBrowseWildcards.ALL.value])))
        self.bomconverter_input_titleblock_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.bomconverter_input_titleblock_text.Clear())
        self.bomconverter_input_filebrowser_sizer.Add(self.bomconverter_input_titleblock_browse)
        #--- --- компоновка: Выбор файлов/папок -> Ввод
        self.bomconverter_input_sbox_sizer.Add(self.bomconverter_input_filebrowser_sizer, proportion = 1, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Ввод -> Компоновщик панели
        self.bomconverter_panel_sizer.Add(self.bomconverter_input_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Конфигурация
        self.bomconverter_config_sbox = wx.StaticBox(self.bomconverter_panel, label="Конфигурация")                   #контейнер (именная группа) для конфигурации
        self.bomconverter_config_sbox_sizer = wx.StaticBoxSizer(self.bomconverter_config_sbox, wx.VERTICAL)                   #компоновщик группы
        #--- --- Выбор файлов/папок
        self.bomconverter_config_filebrowser_sizer = wx.FlexGridSizer(2, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1])    #табличный компоновщик для выбора файлов
        self.bomconverter_config_filebrowser_sizer.AddGrowableCol(1)                                             #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Модуль настроек
        self.bomconverter_config_settings_label = wx.StaticText(self.bomconverter_config_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Настройки:")
        self.bomconverter_config_filebrowser_sizer.Add(self.bomconverter_config_settings_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomconverter_config_settings_text = wx.TextCtrl(self.bomconverter_config_sbox)
        self.bomconverter_config_settings_text.Bind(wx.EVT_TEXT, self.OnBomconverterPanelValueChange)
        self.bomconverter_config_settings_text.SetDropTarget(FileDropTarget(self.bomconverter_config_settings_text))
        self.bomconverter_config_filebrowser_sizer.Add(self.bomconverter_config_settings_text, flag = wx.EXPAND)
        self.bomconverter_config_settings_browse = wx.Button(self.bomconverter_config_sbox, size = button_browse_size, label = button_browse_label)
        self.bomconverter_config_settings_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.bomconverter_config_settings_text, False, wildcard = "|".join([FileBrowseWildcards.PYTHON.value, FileBrowseWildcards.ALL.value])))
        self.bomconverter_config_settings_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.bomconverter_config_settings_text.Clear())
        self.bomconverter_config_filebrowser_sizer.Add(self.bomconverter_config_settings_browse)
        #--- --- --- Модуль анализатора
        self.bomconverter_config_parser_label = wx.StaticText(self.bomconverter_config_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Анализатор:")
        self.bomconverter_config_filebrowser_sizer.Add(self.bomconverter_config_parser_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomconverter_config_parser_text = wx.TextCtrl(self.bomconverter_config_sbox)
        self.bomconverter_config_parser_text.Bind(wx.EVT_TEXT, self.OnBomconverterPanelValueChange)
        self.bomconverter_config_parser_text.SetDropTarget(FileDropTarget(self.bomconverter_config_parser_text))
        self.bomconverter_config_filebrowser_sizer.Add(self.bomconverter_config_parser_text,flag = wx.EXPAND)
        self.bomconverter_config_parser_browse = wx.Button(self.bomconverter_config_sbox, size = button_browse_size, label = button_browse_label)
        self.bomconverter_config_parser_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.bomconverter_config_parser_text, False, wildcard = "|".join([FileBrowseWildcards.PYTHON.value, FileBrowseWildcards.ALL.value])))
        self.bomconverter_config_parser_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.bomconverter_config_parser_text.Clear())
        self.bomconverter_config_filebrowser_sizer.Add(self.bomconverter_config_parser_browse)
        #--- --- компоновка: Выбор файлов/папок -> Конфигурация
        self.bomconverter_config_sbox_sizer.Add(self.bomconverter_config_filebrowser_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- --- Оптимизации
        self.bomconverter_config_optimize_sbox = wx.StaticBox(self.bomconverter_config_sbox, label="Оптимизации")             #контейнер (именная группа) для оптимизаций
        self.bomconverter_config_optimize_sbox_sizer = wx.StaticBoxSizer(self.bomconverter_config_optimize_sbox, wx.VERTICAL) #компоновщик группы
        #--- --- --- Варианты
        self.bomconverter_config_optimize_grid_sizer = wx.GridBagSizer(gbs_variants_gap[0], gbs_variants_gap[1]) #табличный компоновщик для вариантов
        self.bomconverter_config_optimize_all_chkbox = wx.CheckBox(self.bomconverter_config_optimize_sbox,      size = checkbox_flag_size, label="Все доступные")
        self.bomconverter_config_optimize_all_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.bomconverter_config_optimize_grid_sizer.Add(self.bomconverter_config_optimize_all_chkbox, pos = (0, 0), flag=wx.ALIGN_LEFT)
        self.bomconverter_config_optimize_none_chkbox = wx.CheckBox(self.bomconverter_config_optimize_sbox, size = checkbox_flag_size, label="Никакие")
        self.bomconverter_config_optimize_none_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.bomconverter_config_optimize_grid_sizer.Add(self.bomconverter_config_optimize_none_chkbox, pos = (0, 1), flag=wx.ALIGN_LEFT)
        self.bomconverter_config_optimize_sline = wx.StaticLine(self.bomconverter_config_optimize_sbox, style = wx.LI_HORIZONTAL)
        self.bomconverter_config_optimize_grid_sizer.Add(self.bomconverter_config_optimize_sline, pos = (1, 0), span = (1, 2), flag=wx.EXPAND | wx.HORIZONTAL)
        self.bomconverter_config_optimize_mfrname_chkbox = wx.CheckBox(self.bomconverter_config_optimize_sbox, size = checkbox_flag_size, label="Названия производителей")
        self.bomconverter_config_optimize_mfrname_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.bomconverter_config_optimize_grid_sizer.Add(self.bomconverter_config_optimize_mfrname_chkbox, pos = (2, 0), flag=wx.ALIGN_LEFT)
        self.bomconverter_config_optimize_restol_chkbox = wx.CheckBox(self.bomconverter_config_optimize_sbox, size = checkbox_flag_size, label="Допуски резисторов")
        self.bomconverter_config_optimize_restol_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.bomconverter_config_optimize_grid_sizer.Add(self.bomconverter_config_optimize_restol_chkbox, pos = (2, 1), flag=wx.ALIGN_LEFT)
        #--- --- --- компоновка: Варианты -> Оптимизации
        self.bomconverter_config_optimize_sbox_sizer.Add(self.bomconverter_config_optimize_grid_sizer, flag = wx.EXPAND | wx.ALL, border = gbs_variants_border)
        #--- --- компоновка: Оптимизации -> Конфигурация
        self.bomconverter_config_sbox_sizer.Add(self.bomconverter_config_optimize_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Конфигурация -> Компоновщик панели
        self.bomconverter_panel_sizer.Add(self.bomconverter_config_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Вывод
        self.bomconverter_output_sbox = wx.StaticBox(self.bomconverter_panel, label="Вывод")                          #контейнер (именная группа) для вывода
        self.bomconverter_output_sbox_sizer = wx.StaticBoxSizer(self.bomconverter_output_sbox, wx.VERTICAL)                   #компоновщик группы
        #--- --- Выбор файлов/папок
        self.bomconverter_output_filebrowser_sizer = wx.FlexGridSizer(1, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1])    #табличный компоновщик для выбора файлов
        self.bomconverter_output_filebrowser_sizer.AddGrowableCol(1)                                             #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Выходная папка
        self.bomconverter_output_directory_label = wx.StaticText(self.bomconverter_output_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Папка:")
        self.bomconverter_output_filebrowser_sizer.Add(self.bomconverter_output_directory_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomconverter_output_directory_text = wx.TextCtrl(self.bomconverter_output_sbox)
        self.bomconverter_output_directory_text.Bind(wx.EVT_TEXT, self.OnBomconverterPanelValueChange)
        self.bomconverter_output_directory_text.SetDropTarget(FileDropTarget(self.bomconverter_output_directory_text))
        self.bomconverter_output_filebrowser_sizer.Add(self.bomconverter_output_directory_text, flag = wx.EXPAND)
        self.bomconverter_output_directory_browse = wx.Button(self.bomconverter_output_sbox, size = button_browse_size, label = button_browse_label)
        self.bomconverter_output_directory_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnDirBrowse(event, self.bomconverter_output_directory_text))
        self.bomconverter_output_directory_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.bomconverter_output_directory_text.Clear())
        self.bomconverter_output_filebrowser_sizer.Add(self.bomconverter_output_directory_browse)
        #--- --- компоновка: Выбор файлов/папок -> Вывод
        self.bomconverter_output_sbox_sizer.Add(self.bomconverter_output_filebrowser_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- --- Выходные форматы
        self.bomconverter_output_format_sbox = wx.StaticBox(self.bomconverter_output_sbox, label="Форматы")                   #контейнер (именная группа) для форматов
        self.bomconverter_output_format_sbox_sizer = wx.StaticBoxSizer(self.bomconverter_output_format_sbox, wx.VERTICAL)     #компоновщик группы
        #--- --- --- Варианты
        self.bomconverter_output_format_grid_sizer = wx.GridBagSizer(gbs_variants_gap[0], gbs_variants_gap[1])  #табличный компоновщик для вариантов
        self.bomconverter_output_format_all_chkbox = wx.CheckBox(self.bomconverter_output_format_sbox, id=wx.ID_ANY, label="Все доступные", size = checkbox_flag_size)
        self.bomconverter_output_format_all_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.bomconverter_output_format_grid_sizer.Add(self.bomconverter_output_format_all_chkbox, pos = (0, 0), flag=wx.ALIGN_LEFT)
        self.bomconverter_output_format_none_chkbox = wx.CheckBox(self.bomconverter_output_format_sbox, id=wx.ID_ANY, label="Никакие", size = checkbox_flag_size)
        self.bomconverter_output_format_none_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.bomconverter_output_format_grid_sizer.Add(self.bomconverter_output_format_none_chkbox, pos = (0, 1), flag=wx.ALIGN_LEFT)
        self.bomconverter_output_format_sline = wx.StaticLine(self.bomconverter_output_format_sbox, style = wx.LI_HORIZONTAL)
        self.bomconverter_output_format_grid_sizer.Add(self.bomconverter_output_format_sline, pos = (1, 0), span = (1, 3), flag = wx.EXPAND | wx.HORIZONTAL)
        self.bomconverter_output_format_pe3docx_chkbox = wx.CheckBox(self.bomconverter_output_format_sbox, id=wx.ID_ANY, label="Перечень Элементов (Word)", size = checkbox_flag_size)
        self.bomconverter_output_format_pe3docx_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.bomconverter_output_format_grid_sizer.Add(self.bomconverter_output_format_pe3docx_chkbox, pos = (2, 0), flag=wx.ALIGN_LEFT)
        self.bomconverter_output_format_pe3pdf_chkbox = wx.CheckBox(self.bomconverter_output_format_sbox, id=wx.ID_ANY, label="Перечень Элементов (PDF)", size = checkbox_flag_size)
        self.bomconverter_output_format_pe3pdf_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.bomconverter_output_format_grid_sizer.Add(self.bomconverter_output_format_pe3pdf_chkbox, pos = (2, 1), flag=wx.ALIGN_LEFT)
        self.bomconverter_output_format_pe3csv_chkbox = wx.CheckBox(self.bomconverter_output_format_sbox, id=wx.ID_ANY, label="Перечень Элементов (CSV)", size = checkbox_flag_size)
        self.bomconverter_output_format_pe3csv_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.bomconverter_output_format_grid_sizer.Add(self.bomconverter_output_format_pe3csv_chkbox, pos = (2, 2), flag=wx.ALIGN_LEFT)
        self.bomconverter_output_format_clxlsx_chkbox = wx.CheckBox(self.bomconverter_output_format_sbox, id=wx.ID_ANY, label="Список Компонентов (Excel)", size = checkbox_flag_size)
        self.bomconverter_output_format_clxlsx_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.bomconverter_output_format_grid_sizer.Add(self.bomconverter_output_format_clxlsx_chkbox, pos = (3, 0), flag=wx.ALIGN_LEFT)
        self.bomconverter_output_format_spcsv_chkbox = wx.CheckBox(self.bomconverter_output_format_sbox, id=wx.ID_ANY, label="Спецификация (CSV)", size = checkbox_flag_size)
        self.bomconverter_output_format_spcsv_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.bomconverter_output_format_grid_sizer.Add(self.bomconverter_output_format_spcsv_chkbox, pos = (4, 0), flag=wx.ALIGN_LEFT)
        #--- --- --- компоновка: Варианты -> Выходные форматы
        self.bomconverter_output_format_sbox_sizer.Add(self.bomconverter_output_format_grid_sizer, flag = wx.EXPAND | wx.ALL, border = gbs_variants_border)
        #--- --- компоновка: Выходные форматы -> Вывод
        self.bomconverter_output_sbox_sizer.Add(self.bomconverter_output_format_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Вывод -> Компоновщик панели
        self.bomconverter_panel_sizer.Add(self.bomconverter_output_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Процесс
        self.bomconverter_process_sbox = wx.StaticBox(self.bomconverter_panel, label="Процесс")                   #контейнер (именная группа) для процесса
        self.bomconverter_process_sbox_sizer = wx.StaticBoxSizer(self.bomconverter_process_sbox, wx.VERTICAL)             #компоновщик группы
        #--- --- Выбор файлов/папок
        self.bomconverter_process_filebrowser_sizer = wx.FlexGridSizer(1, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1]) #табличный компоновщик для выбора файлов
        self.bomconverter_process_filebrowser_sizer.AddGrowableCol(1)                                          #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Исполняемый файл
        self.bomconverter_process_exe_label = wx.StaticText(self.bomconverter_process_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Исп. файл:")
        self.bomconverter_process_filebrowser_sizer.Add(self.bomconverter_process_exe_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomconverter_process_exe_text = wx.TextCtrl(self.bomconverter_process_sbox)
        self.bomconverter_process_exe_text.Bind(wx.EVT_TEXT, self.OnBomconverterPanelValueChange)
        self.bomconverter_process_exe_text.SetDropTarget(FileDropTarget(self.bomconverter_process_exe_text))
        self.bomconverter_process_filebrowser_sizer.Add(self.bomconverter_process_exe_text, flag = wx.EXPAND)
        self.bomconverter_process_exe_browse = wx.Button(self.bomconverter_process_sbox, size = button_browse_size, label = button_browse_label)
        self.bomconverter_process_exe_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.bomconverter_process_exe_text, False, wildcard = "|".join([FileBrowseWildcards.PYTHON.value, FileBrowseWildcards.WINDOWS_EXE.value, FileBrowseWildcards.SHELL_SCRIPT.value, FileBrowseWildcards.ALL.value])))
        self.bomconverter_process_exe_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.bomconverter_process_exe_text.Clear())
        self.bomconverter_process_filebrowser_sizer.Add(self.bomconverter_process_exe_browse, flag = wx.FIXED_MINSIZE | wx.FIXED_LENGTH)
        #--- --- компоновка: Выбор файлов/папок -> Вывод
        self.bomconverter_process_sbox_sizer.Add(self.bomconverter_process_filebrowser_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- --- Поведение
        self.bomconverter_process_behaviour_sbox = wx.StaticBox(self.bomconverter_process_sbox, label="Поведение")                #контейнер (именная группа) для поведения
        self.bomconverter_process_behaviour_sbox_sizer = wx.StaticBoxSizer(self.bomconverter_process_behaviour_sbox, wx.VERTICAL) #компоновщик группы
        #--- --- --- Варианты
        self.bomconverter_process_behaviour_grid_sizer = wx.GridBagSizer(gbs_variants_gap[0], gbs_variants_gap[1])   #табличный компоновщик для вариантов
        self.bomconverter_process_behaviour_noquestions_chkbox = wx.CheckBox(self.bomconverter_process_behaviour_sbox, size = checkbox_flag_size, label="Не задавать вопросов")
        self.bomconverter_process_behaviour_noquestions_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.bomconverter_process_behaviour_grid_sizer.Add(self.bomconverter_process_behaviour_noquestions_chkbox, pos = (0, 0), flag=wx.ALIGN_LEFT)
        self.bomconverter_process_behaviour_nohalt_chkbox = wx.CheckBox(self.bomconverter_process_behaviour_sbox, size = checkbox_flag_size, label="Закрываться при завершении")
        self.bomconverter_process_behaviour_nohalt_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.bomconverter_process_behaviour_nohalt_chkbox.SetValue(True)
        self.bomconverter_process_behaviour_nohalt_chkbox.Disable()
        self.bomconverter_process_behaviour_grid_sizer.Add(self.bomconverter_process_behaviour_nohalt_chkbox,      pos = (0, 1), flag=wx.ALIGN_LEFT)
        #--- --- --- --- Уровень лога
        self.bomconverter_process_behaviour_loglevel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bomconverter_process_behaviour_loglevel_label = wx.StaticText(self.bomconverter_process_behaviour_sbox, label="Уровень журнала: ")
        self.bomconverter_process_behaviour_loglevel_label.Disable()
        self.bomconverter_process_behaviour_loglevel_sizer.Add(self.bomconverter_process_behaviour_loglevel_label)
        self.bomconverter_process_behaviour_loglevel_choice = wx.Choice(self.bomconverter_process_behaviour_sbox, choices=["", "debug", "info", "warn", "error", "fatal"])
        self.bomconverter_process_behaviour_loglevel_choice.Disable()
        self.bomconverter_process_behaviour_loglevel_choice.Bind(wx.EVT_CHOICE, self.OnBomconverterPanelValueChange)
        self.bomconverter_process_behaviour_loglevel_sizer.Add(self.bomconverter_process_behaviour_loglevel_choice)
        self.bomconverter_process_behaviour_grid_sizer.Add(self.bomconverter_process_behaviour_loglevel_sizer, pos = (0, 2), flag=wx.ALIGN_LEFT)
        #--- --- --- компоновка: Варианты -> Поведение
        self.bomconverter_process_behaviour_sbox_sizer.Add(self.bomconverter_process_behaviour_grid_sizer, flag = wx.EXPAND | wx.ALL, border = gbs_variants_border)
        #--- --- компоновка: Поведение -> Процесс
        self.bomconverter_process_sbox_sizer.Add(self.bomconverter_process_behaviour_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Процесс -> Компоновщик панели
        self.bomconverter_panel_sizer.Add(self.bomconverter_process_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Выполнение
        self.bomconverter_execution_sbox = wx.StaticBox(self.bomconverter_panel, label="Выполнение")              #контейнер (именная группа) для выполнения
        self.bomconverter_execution_sbox_sizer = wx.StaticBoxSizer(self.bomconverter_execution_sbox, wx.VERTICAL)         #компоновщик группы
        #--- --- Команда
        self.bomconverter_execution_command_text = wx.TextCtrl(self.bomconverter_execution_sbox, style = wx.TE_MULTILINE | wx.TE_READONLY)
        self.bomconverter_execution_sbox_sizer.Add(self.bomconverter_execution_command_text, proportion = 1, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- --- Кнопка запуска
        self.bomconverter_execution_start_button = wx.Button(self.bomconverter_execution_sbox, label = "Запуск")
        self.bomconverter_execution_start_button.Bind(wx.EVT_BUTTON, self.OnBomconverterStartButtonPress)
        self.bomconverter_execution_sbox_sizer.Add(self.bomconverter_execution_start_button, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Выполнение -> Компоновщик панели
        self.bomconverter_panel_sizer.Add(self.bomconverter_execution_sbox_sizer, proportion = 1, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #компоновка: Компоновщик панели -> Панель
        self.bomconverter_panel.SetSizer(self.bomconverter_panel_sizer)

        #возвращаем ссылку на панель
        return self.bomconverter_panel

   # BoM discriminator panel ---------------------------------------------------------------------------------------------------------------------------------------------------------------
    def layout_panel_bomdiscriminator(self, parent):
        #общие параметры панели
        label_browse_size    = self.FromDIP(wx.Size(80, -1))
        button_browse_size   = self.FromDIP(wx.Size(30, -1))
        button_browse_label  = "..."
        label_fields_size    = self.FromDIP(wx.Size(90, -1))
        checkbox_flag_size   = self.FromDIP(wx.Size(200, -1))
        group_border_outer   = self.FromDIP(2)
        group_border_inner   = self.FromDIP(2)
        fgs_filebrowser_gap  = (self.FromDIP(5), self.FromDIP(5))
        gbs_variants_gap     = (self.FromDIP(5), self.FromDIP(5))
        gbs_variants_border  = self.FromDIP(3)

        self.bomdiscriminator_panel = wx.Panel(parent)                                                      #панель
        self.bomdiscriminator_panel_sizer = wx.BoxSizer(wx.VERTICAL)                                        #основной компоновщик на панели

        #--- Базовый
        self.bomdiscriminator_reference_sbox = wx.StaticBox(self.bomdiscriminator_panel, label="Базовый")                                     #контейнер (именная группа)
        self.bomdiscriminator_reference_sbox_sizer = wx.StaticBoxSizer(self.bomdiscriminator_reference_sbox, wx.VERTICAL)                     #компоновщик группы
        #--- --- Выбор файлов/папок
        self.bomdiscriminator_reference_filebrowser_sizer = wx.FlexGridSizer(2, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1])   #табличный компоновщик для выбора файлов
        self.bomdiscriminator_reference_filebrowser_sizer.AddGrowableCol(1)                                                          #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Файл BoM
        self.bomdiscriminator_reference_bom_label = wx.StaticText(self.bomdiscriminator_reference_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="BoM:")
        self.bomdiscriminator_reference_filebrowser_sizer.Add(self.bomdiscriminator_reference_bom_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomdiscriminator_reference_bom_text = wx.TextCtrl(self.bomdiscriminator_reference_sbox)
        self.bomdiscriminator_reference_bom_text.Bind(wx.EVT_TEXT, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_reference_bom_text.SetDropTarget(FileDropTarget(self.bomdiscriminator_reference_bom_text))
        self.bomdiscriminator_reference_filebrowser_sizer.Add(self.bomdiscriminator_reference_bom_text, flag = wx.EXPAND)
        self.bomdiscriminator_reference_bom_browse = wx.Button(self.bomdiscriminator_reference_sbox, size = button_browse_size, label = button_browse_label)
        self.bomdiscriminator_reference_bom_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.bomdiscriminator_reference_bom_text, False, wildcard = "|".join([FileBrowseWildcards.CSV.value, FileBrowseWildcards.ALL.value])))
        self.bomdiscriminator_reference_bom_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.bomdiscriminator_reference_bom_text.Clear())
        self.bomdiscriminator_reference_filebrowser_sizer.Add(self.bomdiscriminator_reference_bom_browse)
        #--- --- --- Модуль настроек
        self.bomdiscriminator_reference_settings_label = wx.StaticText(self.bomdiscriminator_reference_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Настройки:")
        self.bomdiscriminator_reference_filebrowser_sizer.Add(self.bomdiscriminator_reference_settings_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomdiscriminator_reference_settings_text = wx.TextCtrl(self.bomdiscriminator_reference_sbox)
        self.bomdiscriminator_reference_settings_text.Bind(wx.EVT_TEXT, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_reference_settings_text.SetDropTarget(FileDropTarget(self.bomdiscriminator_reference_settings_text))
        self.bomdiscriminator_reference_filebrowser_sizer.Add(self.bomdiscriminator_reference_settings_text, flag = wx.EXPAND)
        self.bomdiscriminator_reference_settings_browse = wx.Button(self.bomdiscriminator_reference_sbox, size = button_browse_size, label = button_browse_label)
        self.bomdiscriminator_reference_settings_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.bomdiscriminator_reference_settings_text, False, wildcard = "|".join([FileBrowseWildcards.PYTHON.value, FileBrowseWildcards.ALL.value])))
        self.bomdiscriminator_reference_settings_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.bomdiscriminator_reference_settings_text.Clear())
        self.bomdiscriminator_reference_filebrowser_sizer.Add(self.bomdiscriminator_reference_settings_browse)
        #--- --- компоновка: Выбор файлов/папок -> Базовый
        self.bomdiscriminator_reference_sbox_sizer.Add(self.bomdiscriminator_reference_filebrowser_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Базовый -> Компоновщик панели
        self.bomdiscriminator_panel_sizer.Add(self.bomdiscriminator_reference_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Сравниваемый
        self.bomdiscriminator_subject_sbox = wx.StaticBox(self.bomdiscriminator_panel, label="Сравниваемый")                                  #контейнер (именная группа)
        self.bomdiscriminator_subject_sbox_sizer = wx.StaticBoxSizer(self.bomdiscriminator_subject_sbox, wx.VERTICAL)                         #компоновщик группы
        #--- --- Выбор файлов/папок
        self.bomdiscriminator_subject_filebrowser_sizer = wx.FlexGridSizer(2, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1])     #табличный компоновщик для выбора файлов
        self.bomdiscriminator_subject_filebrowser_sizer.AddGrowableCol(1)                                                            #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Файл BoM
        self.bomdiscriminator_subject_bom_label = wx.StaticText(self.bomdiscriminator_subject_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="BoM:")
        self.bomdiscriminator_subject_filebrowser_sizer.Add(self.bomdiscriminator_subject_bom_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomdiscriminator_subject_bom_text = wx.TextCtrl(self.bomdiscriminator_subject_sbox)
        self.bomdiscriminator_subject_bom_text.Bind(wx.EVT_TEXT, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_subject_bom_text.SetDropTarget(FileDropTarget(self.bomdiscriminator_subject_bom_text))
        self.bomdiscriminator_subject_filebrowser_sizer.Add(self.bomdiscriminator_subject_bom_text, flag = wx.EXPAND)
        self.bomdiscriminator_subject_bom_browse = wx.Button(self.bomdiscriminator_subject_sbox, size = button_browse_size, label = button_browse_label)
        self.bomdiscriminator_subject_bom_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.bomdiscriminator_subject_bom_text, False, wildcard = "|".join([FileBrowseWildcards.CSV.value, FileBrowseWildcards.ALL.value])))
        self.bomdiscriminator_subject_bom_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.bomdiscriminator_subject_bom_text.Clear())
        self.bomdiscriminator_subject_filebrowser_sizer.Add(self.bomdiscriminator_subject_bom_browse)
        #--- --- --- Модуль настроек
        self.bomdiscriminator_subject_settings_label = wx.StaticText(self.bomdiscriminator_subject_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Настройки:")
        self.bomdiscriminator_subject_filebrowser_sizer.Add(self.bomdiscriminator_subject_settings_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomdiscriminator_subject_settings_text = wx.TextCtrl(self.bomdiscriminator_subject_sbox)
        self.bomdiscriminator_subject_settings_text.Bind(wx.EVT_TEXT, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_subject_settings_text.SetDropTarget(FileDropTarget(self.bomdiscriminator_subject_settings_text))
        self.bomdiscriminator_subject_filebrowser_sizer.Add(self.bomdiscriminator_subject_settings_text, flag = wx.EXPAND)
        self.bomdiscriminator_subject_settings_browse = wx.Button(self.bomdiscriminator_subject_sbox, size = button_browse_size, label = button_browse_label)
        self.bomdiscriminator_subject_settings_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.bomdiscriminator_subject_settings_text, False, wildcard = "|".join([FileBrowseWildcards.PYTHON.value, FileBrowseWildcards.ALL.value])))
        self.bomdiscriminator_subject_settings_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.bomdiscriminator_subject_settings_text.Clear())
        self.bomdiscriminator_subject_filebrowser_sizer.Add(self.bomdiscriminator_subject_settings_browse)
        #--- --- компоновка: Выбор файлов/папок -> Сравниваемый
        self.bomdiscriminator_subject_sbox_sizer.Add(self.bomdiscriminator_subject_filebrowser_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Сравниваемый -> Компоновщик панели
        self.bomdiscriminator_panel_sizer.Add(self.bomdiscriminator_subject_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Результат
        self.bomdiscriminator_result_sbox = wx.StaticBox(self.bomdiscriminator_panel, label="Результат")                                      #контейнер (именная группа)
        self.bomdiscriminator_result_sbox_sizer = wx.StaticBoxSizer(self.bomdiscriminator_result_sbox, wx.VERTICAL)                           #компоновщик группы
        #--- --- ?
        self.bomdiscriminator_result_sizer = wx.FlexGridSizer(2, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1])
        self.bomdiscriminator_result_sizer.AddGrowableCol(1)
        #--- --- --- Формат
        self.bomdiscriminator_result_format_label = wx.StaticText(self.bomdiscriminator_result_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Формат:")
        self.bomdiscriminator_result_sizer.Add(self.bomdiscriminator_result_format_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomdiscriminator_result_format_choice = wx.Choice(self.bomdiscriminator_result_sbox, choices = [member.value for member in Bomdiscriminator_OutputID])
        self.bomdiscriminator_result_format_choice.SetSelection(0)
        self.bomdiscriminator_result_format_choice.Bind(wx.EVT_CHOICE, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_result_sizer.Add(self.bomdiscriminator_result_format_choice, flag = wx.ALIGN_CENTER_VERTICAL)
        self.bomdiscriminator_result_sizer.Add((0, 0))
        #--- --- --- Файл
        self.bomdiscriminator_result_file_label = wx.StaticText(self.bomdiscriminator_result_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Файл:")
        self.bomdiscriminator_result_sizer.Add(self.bomdiscriminator_result_file_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomdiscriminator_result_file_text = wx.TextCtrl(self.bomdiscriminator_result_sbox)
        self.bomdiscriminator_result_file_text.Bind(wx.EVT_TEXT, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_result_file_text.SetDropTarget(FileDropTarget(self.bomdiscriminator_result_file_text))
        self.bomdiscriminator_result_sizer.Add(self.bomdiscriminator_result_file_text, flag = wx.EXPAND)
        self.bomdiscriminator_result_file_browse = wx.Button(self.bomdiscriminator_result_sbox, size = button_browse_size, label = button_browse_label)
        self.bomdiscriminator_result_file_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.bomdiscriminator_result_file_text, False, True, wildcard = "|".join([FileBrowseWildcards.XLSX.value, FileBrowseWildcards.CSV.value, FileBrowseWildcards.ALL.value])))
        self.bomdiscriminator_result_file_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.bomdiscriminator_result_file_text.Clear())
        self.bomdiscriminator_result_sizer.Add(self.bomdiscriminator_result_file_browse)
        #--- --- компоновка: Выбор файлов/папок -> Результат
        self.bomdiscriminator_result_sbox_sizer.Add(self.bomdiscriminator_result_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Результат -> Компоновщик панели
        self.bomdiscriminator_panel_sizer.Add(self.bomdiscriminator_result_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Конфигурация
        self.bomdiscriminator_config_sbox = wx.StaticBox(self.bomdiscriminator_panel, label="Конфигурация")                   #контейнер (именная группа) для конфигурации
        self.bomdiscriminator_config_sbox_sizer = wx.StaticBoxSizer(self.bomdiscriminator_config_sbox, wx.VERTICAL)                   #компоновщик группы
        #--- --- Выбор файлов/папок
        self.bomdiscriminator_config_filebrowser_sizer = wx.FlexGridSizer(1, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1])    #табличный компоновщик для выбора файлов
        self.bomdiscriminator_config_filebrowser_sizer.AddGrowableCol(1)                                             #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Модуль настроек
        self.bomdiscriminator_config_settings_label = wx.StaticText(self.bomdiscriminator_config_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Настройки:")
        self.bomdiscriminator_config_filebrowser_sizer.Add(self.bomdiscriminator_config_settings_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomdiscriminator_config_settings_text = wx.TextCtrl(self.bomdiscriminator_config_sbox)
        self.bomdiscriminator_config_settings_text.Bind(wx.EVT_TEXT, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_config_settings_text.SetDropTarget(FileDropTarget(self.bomdiscriminator_config_settings_text))
        self.bomdiscriminator_config_filebrowser_sizer.Add(self.bomdiscriminator_config_settings_text, flag = wx.EXPAND)
        self.bomdiscriminator_config_settings_browse = wx.Button(self.bomdiscriminator_config_sbox, size = button_browse_size, label = button_browse_label)
        self.bomdiscriminator_config_settings_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.bomdiscriminator_config_settings_text, False, wildcard = "|".join([FileBrowseWildcards.PYTHON.value, FileBrowseWildcards.ALL.value])))
        self.bomdiscriminator_config_settings_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.bomdiscriminator_config_settings_text.Clear())
        self.bomdiscriminator_config_filebrowser_sizer.Add(self.bomdiscriminator_config_settings_browse)
        #--- --- компоновка: Выбор файлов/папок -> Конфигурация
        self.bomdiscriminator_config_sbox_sizer.Add(self.bomdiscriminator_config_filebrowser_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- --- Поля
        self.bomdiscriminator_config_fields_sbox = wx.StaticBox(self.bomdiscriminator_config_sbox, label="Поля")
        self.bomdiscriminator_config_fields_sbox_sizer = wx.StaticBoxSizer(self.bomdiscriminator_config_fields_sbox, wx.VERTICAL) #компоновщик группы
        #--- --- --- Выбор полей
        self.bomdiscriminator_config_fields_sizer = wx.FlexGridSizer(2, 2, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1])
        self.bomdiscriminator_config_fields_sizer.AddGrowableCol(1)
        #--- --- --- --- Ключевые
        self.bomdiscriminator_config_fields_key_label = wx.StaticText(self.bomdiscriminator_config_fields_sbox, style = wx.ALIGN_RIGHT, size = label_fields_size, label="Ключевые:")
        self.bomdiscriminator_config_fields_sizer.Add(self.bomdiscriminator_config_fields_key_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomdiscriminator_config_fields_key_combobox = wx.ComboBox(self.bomdiscriminator_config_fields_sbox, style = wx.CB_DROPDOWN)
        self.bomdiscriminator_config_fields_key_combobox.Bind(wx.EVT_TEXT, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_config_fields_sizer.Add(self.bomdiscriminator_config_fields_key_combobox, flag = wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        #--- --- --- --- Игнорируемые
        self.bomdiscriminator_config_fields_ignore_label = wx.StaticText(self.bomdiscriminator_config_fields_sbox, style = wx.ALIGN_RIGHT, size = label_fields_size, label="Игнорировать:")
        self.bomdiscriminator_config_fields_sizer.Add(self.bomdiscriminator_config_fields_ignore_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomdiscriminator_config_fields_ignore_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bomdiscriminator_config_fields_ignore_combobox = wx.ComboBox(self.bomdiscriminator_config_fields_sbox, style = wx.CB_DROPDOWN)
        self.bomdiscriminator_config_fields_ignore_combobox.Bind(wx.EVT_TEXT, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_config_fields_ignore_sizer.Add(self.bomdiscriminator_config_fields_ignore_combobox, flag = wx.EXPAND, proportion = 1)
        self.bomdiscriminator_config_fields_ignore_sizer.AddSpacer(fgs_filebrowser_gap[0])
        self.bomdiscriminator_config_fields_ignore_unpaired_chkbox = wx.CheckBox(self.bomdiscriminator_config_fields_sbox, label="непарные")
        self.bomdiscriminator_config_fields_ignore_unpaired_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_config_fields_ignore_sizer.Add(self.bomdiscriminator_config_fields_ignore_unpaired_chkbox, flag = wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.bomdiscriminator_config_fields_sizer.Add(self.bomdiscriminator_config_fields_ignore_sizer, flag = wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        #--- --- --- компоновка: Выбор полей -> Поля
        self.bomdiscriminator_config_fields_sbox_sizer.Add(self.bomdiscriminator_config_fields_sizer, flag = wx.EXPAND)
        self.bomdiscriminator_config_fields_sbox_sizer.AddSpacer(fgs_filebrowser_gap[1])
        #--- --- Метод подсветки изменений
        self.bomdiscriminator_config_changes_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bomdiscriminator_config_xlsx_changes_mode_label = wx.StaticText(self.bomdiscriminator_config_sbox, label="Метод отображения изменений: ")
        self.bomdiscriminator_config_changes_sizer.Add(self.bomdiscriminator_config_xlsx_changes_mode_label, flag = wx.ALIGN_CENTER_VERTICAL)
        self.bomdiscriminator_config_xlsx_changes_mode_choice = wx.Choice(self.bomdiscriminator_config_sbox, choices = [member.value for member in Bomdiscriminator_XlsxChangesModeID])
        self.bomdiscriminator_config_xlsx_changes_mode_choice.SetSelection(0)
        self.bomdiscriminator_config_xlsx_changes_mode_choice.Bind(wx.EVT_CHOICE, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_config_changes_sizer.Add(self.bomdiscriminator_config_xlsx_changes_mode_choice, flag = wx.ALIGN_CENTER_VERTICAL)
        self.bomdiscriminator_config_xlsx_changes_mode_note = wx.StaticText(self.bomdiscriminator_config_sbox, label="  * для xlsx")
        font = self.bomdiscriminator_config_xlsx_changes_mode_note.GetFont()
        font.MakeItalic()
        self.bomdiscriminator_config_xlsx_changes_mode_note.SetFont(font)
        self.bomdiscriminator_config_changes_sizer.Add(self.bomdiscriminator_config_xlsx_changes_mode_note, flag = wx.ALIGN_CENTER_VERTICAL)
        #--- --- компоновка: Поля -> Конфигурация
        self.bomdiscriminator_config_sbox_sizer.Add(self.bomdiscriminator_config_fields_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- --- компоновка: Метод подсветки изменений -> Конфигурация
        self.bomdiscriminator_config_sbox_sizer.AddSpacer(group_border_outer)
        self.bomdiscriminator_config_sbox_sizer.Add(self.bomdiscriminator_config_changes_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Конфигурация -> Компоновщик панели
        self.bomdiscriminator_panel_sizer.Add(self.bomdiscriminator_config_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Процесс
        self.bomdiscriminator_process_sbox = wx.StaticBox(self.bomdiscriminator_panel, label="Процесс")                   #контейнер (именная группа) для процесса
        self.bomdiscriminator_process_sbox_sizer = wx.StaticBoxSizer(self.bomdiscriminator_process_sbox, wx.VERTICAL)             #компоновщик группы
        #--- --- Выбор файлов/папок
        self.bomdiscriminator_process_filebrowser_sizer = wx.FlexGridSizer(1, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1]) #табличный компоновщик для выбора файлов
        self.bomdiscriminator_process_filebrowser_sizer.AddGrowableCol(1)                                          #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Исполняемый файл
        self.bomdiscriminator_process_exe_label = wx.StaticText(self.bomdiscriminator_process_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Исп. файл:")
        self.bomdiscriminator_process_filebrowser_sizer.Add(self.bomdiscriminator_process_exe_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.bomdiscriminator_process_exe_text = wx.TextCtrl(self.bomdiscriminator_process_sbox)
        self.bomdiscriminator_process_exe_text.Bind(wx.EVT_TEXT, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_process_exe_text.SetDropTarget(FileDropTarget(self.bomdiscriminator_process_exe_text))
        self.bomdiscriminator_process_filebrowser_sizer.Add(self.bomdiscriminator_process_exe_text, flag = wx.EXPAND)
        self.bomdiscriminator_process_exe_browse = wx.Button(self.bomdiscriminator_process_sbox, size = button_browse_size, label = button_browse_label)
        self.bomdiscriminator_process_exe_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.bomdiscriminator_process_exe_text, False, wildcard = "|".join([FileBrowseWildcards.PYTHON.value, FileBrowseWildcards.WINDOWS_EXE.value, FileBrowseWildcards.SHELL_SCRIPT.value, FileBrowseWildcards.ALL.value])))
        self.bomdiscriminator_process_exe_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.bomdiscriminator_process_exe_text.Clear())
        self.bomdiscriminator_process_filebrowser_sizer.Add(self.bomdiscriminator_process_exe_browse, flag = wx.FIXED_MINSIZE | wx.FIXED_LENGTH)
        #--- --- компоновка: Выбор файлов/папок -> Вывод
        self.bomdiscriminator_process_sbox_sizer.Add(self.bomdiscriminator_process_filebrowser_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- --- Поведение
        self.bomdiscriminator_process_behaviour_sbox = wx.StaticBox(self.bomdiscriminator_process_sbox, label="Поведение")                #контейнер (именная группа) для поведения
        self.bomdiscriminator_process_behaviour_sbox_sizer = wx.StaticBoxSizer(self.bomdiscriminator_process_behaviour_sbox, wx.VERTICAL) #компоновщик группы
        #--- --- --- Варианты
        self.bomdiscriminator_process_behaviour_grid_sizer = wx.GridBagSizer(gbs_variants_gap[0], gbs_variants_gap[1])   #табличный компоновщик для вариантов
        self.bomdiscriminator_process_behaviour_noquestions_chkbox = wx.CheckBox(self.bomdiscriminator_process_behaviour_sbox, size = checkbox_flag_size, label="Не задавать вопросов")
        self.bomdiscriminator_process_behaviour_noquestions_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_process_behaviour_noquestions_chkbox.SetValue(False)
        self.bomdiscriminator_process_behaviour_noquestions_chkbox.Disable()
        self.bomdiscriminator_process_behaviour_grid_sizer.Add(self.bomdiscriminator_process_behaviour_noquestions_chkbox, pos = (0, 0), flag=wx.ALIGN_LEFT)
        self.bomdiscriminator_process_behaviour_nohalt_chkbox = wx.CheckBox(self.bomdiscriminator_process_behaviour_sbox, size = checkbox_flag_size, label="Закрываться при завершении")
        self.bomdiscriminator_process_behaviour_nohalt_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_process_behaviour_nohalt_chkbox.SetValue(True)
        self.bomdiscriminator_process_behaviour_nohalt_chkbox.Disable()
        self.bomdiscriminator_process_behaviour_grid_sizer.Add(self.bomdiscriminator_process_behaviour_nohalt_chkbox,      pos = (0, 1), flag=wx.ALIGN_LEFT)
        #--- --- --- --- Уровень лога
        self.bomdiscriminator_process_behaviour_loglevel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bomdiscriminator_process_behaviour_loglevel_label = wx.StaticText(self.bomdiscriminator_process_behaviour_sbox, label="Уровень журнала: ")
        self.bomdiscriminator_process_behaviour_loglevel_label.Disable()
        self.bomdiscriminator_process_behaviour_loglevel_sizer.Add(self.bomdiscriminator_process_behaviour_loglevel_label)
        self.bomdiscriminator_process_behaviour_loglevel_choice = wx.Choice(self.bomdiscriminator_process_behaviour_sbox, choices=["", "debug", "info", "warn", "error", "fatal"])
        self.bomdiscriminator_process_behaviour_loglevel_choice.Disable()
        self.bomdiscriminator_process_behaviour_loglevel_choice.Bind(wx.EVT_CHOICE, self.OnBomdiscriminatorPanelValueChange)
        self.bomdiscriminator_process_behaviour_loglevel_sizer.Add(self.bomdiscriminator_process_behaviour_loglevel_choice)
        self.bomdiscriminator_process_behaviour_grid_sizer.Add(self.bomdiscriminator_process_behaviour_loglevel_sizer, pos = (0, 2), flag=wx.ALIGN_LEFT)
        #--- --- --- компоновка: Варианты -> Поведение
        self.bomdiscriminator_process_behaviour_sbox_sizer.Add(self.bomdiscriminator_process_behaviour_grid_sizer, flag = wx.EXPAND | wx.ALL, border = gbs_variants_border)
        #--- --- компоновка: Поведение -> Процесс
        self.bomdiscriminator_process_sbox_sizer.Add(self.bomdiscriminator_process_behaviour_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Процесс -> Компоновщик панели
        self.bomdiscriminator_panel_sizer.Add(self.bomdiscriminator_process_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Выполнение
        self.bomdiscriminator_execution_sbox = wx.StaticBox(self.bomdiscriminator_panel, label="Выполнение")                      #контейнер (именная группа) для выполнения
        self.bomdiscriminator_execution_sbox_sizer = wx.StaticBoxSizer(self.bomdiscriminator_execution_sbox, wx.VERTICAL)         #компоновщик группы
        #--- --- Команда
        self.bomdiscriminator_execution_command_text = wx.TextCtrl(self.bomdiscriminator_execution_sbox, style = wx.TE_MULTILINE | wx.TE_READONLY)
        self.bomdiscriminator_execution_sbox_sizer.Add(self.bomdiscriminator_execution_command_text, proportion = 1, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- --- Кнопка запуска
        self.bomdiscriminator_execution_start_button = wx.Button(self.bomdiscriminator_execution_sbox, label = "Запуск")
        self.bomdiscriminator_execution_start_button.Bind(wx.EVT_BUTTON, self.OnBomdiscriminatorStartButtonPress)
        self.bomdiscriminator_execution_sbox_sizer.Add(self.bomdiscriminator_execution_start_button, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Выполнение -> Компоновщик панели
        self.bomdiscriminator_panel_sizer.Add(self.bomdiscriminator_execution_sbox_sizer, proportion = 1, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #компоновка: Компоновщик панели -> Панель
        self.bomdiscriminator_panel.SetSizer(self.bomdiscriminator_panel_sizer)

        #возвращаем ссылку на панель
        return self.bomdiscriminator_panel

   # CL discriminator panel ---------------------------------------------------------------------------------------------------------------------------------------------------------------
    def layout_panel_cldiscriminator(self, parent):
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

        self.cldiscriminator_panel = wx.Panel(parent)                                                      #панель
        self.cldiscriminator_panel_sizer = wx.BoxSizer(wx.VERTICAL)                                        #основной компоновщик на панели

        #--- Базовый
        self.cldiscriminator_reference_sbox = wx.StaticBox(self.cldiscriminator_panel, label="Базовый")                                     #контейнер (именная группа)
        self.cldiscriminator_reference_sbox_sizer = wx.StaticBoxSizer(self.cldiscriminator_reference_sbox, wx.VERTICAL)                     #компоновщик группы
        #--- --- Выбор файлов/папок
        self.cldiscriminator_reference_filebrowser_sizer = wx.FlexGridSizer(2, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1])   #табличный компоновщик для выбора файлов
        self.cldiscriminator_reference_filebrowser_sizer.AddGrowableCol(1)                                                          #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Файл списка
        self.cldiscriminator_reference_cl_label = wx.StaticText(self.cldiscriminator_reference_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Список:")
        self.cldiscriminator_reference_filebrowser_sizer.Add(self.cldiscriminator_reference_cl_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.cldiscriminator_reference_cl_text = wx.TextCtrl(self.cldiscriminator_reference_sbox)
        self.cldiscriminator_reference_cl_text.Bind(wx.EVT_TEXT, self.OnCldiscriminatorPanelValueChange)
        self.cldiscriminator_reference_cl_text.SetDropTarget(FileDropTarget(self.cldiscriminator_reference_cl_text))
        self.cldiscriminator_reference_filebrowser_sizer.Add(self.cldiscriminator_reference_cl_text, flag = wx.EXPAND)
        self.cldiscriminator_reference_cl_browse = wx.Button(self.cldiscriminator_reference_sbox, size = button_browse_size, label = button_browse_label)
        self.cldiscriminator_reference_cl_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.cldiscriminator_reference_cl_text, False, wildcard = "|".join([FileBrowseWildcards.XLSX.value, FileBrowseWildcards.ALL.value])))
        self.cldiscriminator_reference_cl_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.cldiscriminator_reference_cl_text.Clear())
        self.cldiscriminator_reference_filebrowser_sizer.Add(self.cldiscriminator_reference_cl_browse)
        #--- --- --- Модуль настроек
        self.cldiscriminator_reference_settings_label = wx.StaticText(self.cldiscriminator_reference_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Настройки:")
        self.cldiscriminator_reference_filebrowser_sizer.Add(self.cldiscriminator_reference_settings_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.cldiscriminator_reference_settings_text = wx.TextCtrl(self.cldiscriminator_reference_sbox)
        self.cldiscriminator_reference_settings_text.Bind(wx.EVT_TEXT, self.OnCldiscriminatorPanelValueChange)
        self.cldiscriminator_reference_settings_text.SetDropTarget(FileDropTarget(self.cldiscriminator_reference_settings_text))
        self.cldiscriminator_reference_filebrowser_sizer.Add(self.cldiscriminator_reference_settings_text, flag = wx.EXPAND)
        self.cldiscriminator_reference_settings_browse = wx.Button(self.cldiscriminator_reference_sbox, size = button_browse_size, label = button_browse_label)
        self.cldiscriminator_reference_settings_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.cldiscriminator_reference_settings_text, False, wildcard = "|".join([FileBrowseWildcards.PYTHON.value, FileBrowseWildcards.ALL.value])))
        self.cldiscriminator_reference_settings_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.cldiscriminator_reference_settings_text.Clear())
        self.cldiscriminator_reference_filebrowser_sizer.Add(self.cldiscriminator_reference_settings_browse)
        #--- --- компоновка: Выбор файлов/папок -> Базовый
        self.cldiscriminator_reference_sbox_sizer.Add(self.cldiscriminator_reference_filebrowser_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Базовый -> Компоновщик панели
        self.cldiscriminator_panel_sizer.Add(self.cldiscriminator_reference_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Сравниваемый СК
        self.cldiscriminator_subject_sbox = wx.StaticBox(self.cldiscriminator_panel, label="Сравниваемый")                                  #контейнер (именная группа)
        self.cldiscriminator_subject_sbox_sizer = wx.StaticBoxSizer(self.cldiscriminator_subject_sbox, wx.VERTICAL)                         #компоновщик группы
        #--- --- Выбор файлов/папок
        self.cldiscriminator_subject_filebrowser_sizer = wx.FlexGridSizer(2, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1])     #табличный компоновщик для выбора файлов
        self.cldiscriminator_subject_filebrowser_sizer.AddGrowableCol(1)                                                            #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Файл списка
        self.cldiscriminator_subject_cl_label = wx.StaticText(self.cldiscriminator_subject_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Список:")
        self.cldiscriminator_subject_filebrowser_sizer.Add(self.cldiscriminator_subject_cl_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.cldiscriminator_subject_cl_text = wx.TextCtrl(self.cldiscriminator_subject_sbox)
        self.cldiscriminator_subject_cl_text.Bind(wx.EVT_TEXT, self.OnCldiscriminatorPanelValueChange)
        self.cldiscriminator_subject_cl_text.SetDropTarget(FileDropTarget(self.cldiscriminator_subject_cl_text))
        self.cldiscriminator_subject_filebrowser_sizer.Add(self.cldiscriminator_subject_cl_text, flag = wx.EXPAND)
        self.cldiscriminator_subject_cl_browse = wx.Button(self.cldiscriminator_subject_sbox, size = button_browse_size, label = button_browse_label)
        self.cldiscriminator_subject_cl_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.cldiscriminator_subject_cl_text, False, wildcard = "|".join([FileBrowseWildcards.XLSX.value, FileBrowseWildcards.ALL.value])))
        self.cldiscriminator_subject_cl_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.cldiscriminator_subject_cl_text.Clear())
        self.cldiscriminator_subject_filebrowser_sizer.Add(self.cldiscriminator_subject_cl_browse)
        #--- --- --- Модуль настроек
        self.cldiscriminator_subject_settings_label = wx.StaticText(self.cldiscriminator_subject_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Настройки:")
        self.cldiscriminator_subject_filebrowser_sizer.Add(self.cldiscriminator_subject_settings_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.cldiscriminator_subject_settings_text = wx.TextCtrl(self.cldiscriminator_subject_sbox)
        self.cldiscriminator_subject_settings_text.Bind(wx.EVT_TEXT, self.OnCldiscriminatorPanelValueChange)
        self.cldiscriminator_subject_settings_text.SetDropTarget(FileDropTarget(self.cldiscriminator_subject_settings_text))
        self.cldiscriminator_subject_filebrowser_sizer.Add(self.cldiscriminator_subject_settings_text, flag = wx.EXPAND)
        self.cldiscriminator_subject_settings_browse = wx.Button(self.cldiscriminator_subject_sbox, size = button_browse_size, label = button_browse_label)
        self.cldiscriminator_subject_settings_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.cldiscriminator_subject_settings_text, False, wildcard = "|".join([FileBrowseWildcards.PYTHON.value, FileBrowseWildcards.ALL.value])))
        self.cldiscriminator_subject_settings_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.cldiscriminator_subject_settings_text.Clear())
        self.cldiscriminator_subject_filebrowser_sizer.Add(self.cldiscriminator_subject_settings_browse)
        #--- --- компоновка: Выбор файлов/папок -> Сравниваемый
        self.cldiscriminator_subject_sbox_sizer.Add(self.cldiscriminator_subject_filebrowser_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Сравниваемый -> Компоновщик панели
        self.cldiscriminator_panel_sizer.Add(self.cldiscriminator_subject_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Результат
        self.cldiscriminator_result_sbox = wx.StaticBox(self.cldiscriminator_panel, label="Результат")                                      #контейнер (именная группа)
        self.cldiscriminator_result_sbox_sizer = wx.StaticBoxSizer(self.cldiscriminator_result_sbox, wx.VERTICAL)                           #компоновщик группы
        #--- --- Выбор файлов/папок
        self.cldiscriminator_result_filebrowser_sizer = wx.FlexGridSizer(2, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1])      #табличный компоновщик для выбора файлов
        self.cldiscriminator_result_filebrowser_sizer.AddGrowableCol(1)                                                             #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Файл списка
        self.cldiscriminator_result_cl_label = wx.StaticText(self.cldiscriminator_result_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Список:")
        self.cldiscriminator_result_filebrowser_sizer.Add(self.cldiscriminator_result_cl_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.cldiscriminator_result_cl_text = wx.TextCtrl(self.cldiscriminator_result_sbox)
        self.cldiscriminator_result_cl_text.Bind(wx.EVT_TEXT, self.OnCldiscriminatorPanelValueChange)
        self.cldiscriminator_result_cl_text.SetDropTarget(FileDropTarget(self.cldiscriminator_result_cl_text))
        self.cldiscriminator_result_filebrowser_sizer.Add(self.cldiscriminator_result_cl_text, flag = wx.EXPAND)
        self.cldiscriminator_result_cl_browse = wx.Button(self.cldiscriminator_result_sbox, size = button_browse_size, label = button_browse_label)
        self.cldiscriminator_result_cl_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.cldiscriminator_result_cl_text, False, True, wildcard = "|".join([FileBrowseWildcards.XLSX.value, FileBrowseWildcards.ALL.value])))
        self.cldiscriminator_result_cl_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.cldiscriminator_result_cl_text.Clear())
        self.cldiscriminator_result_filebrowser_sizer.Add(self.cldiscriminator_result_cl_browse)
        #--- --- --- Модуль настроек
        self.cldiscriminator_result_settings_label = wx.StaticText(self.cldiscriminator_result_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Настройки:")
        self.cldiscriminator_result_filebrowser_sizer.Add(self.cldiscriminator_result_settings_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.cldiscriminator_result_settings_text = wx.TextCtrl(self.cldiscriminator_result_sbox)
        self.cldiscriminator_result_settings_text.Bind(wx.EVT_TEXT, self.OnCldiscriminatorPanelValueChange)
        self.cldiscriminator_result_settings_text.SetDropTarget(FileDropTarget(self.cldiscriminator_result_settings_text))
        self.cldiscriminator_result_filebrowser_sizer.Add(self.cldiscriminator_result_settings_text, flag = wx.EXPAND)
        self.cldiscriminator_result_settings_browse = wx.Button(self.cldiscriminator_result_sbox, size = button_browse_size, label = button_browse_label)
        self.cldiscriminator_result_settings_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.cldiscriminator_result_settings_text, False, wildcard = "|".join([FileBrowseWildcards.PYTHON.value, FileBrowseWildcards.ALL.value])))
        self.cldiscriminator_result_settings_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.cldiscriminator_result_settings_text.Clear())
        self.cldiscriminator_result_filebrowser_sizer.Add(self.cldiscriminator_result_settings_browse)
        #--- --- компоновка: Выбор файлов/папок -> Результат
        self.cldiscriminator_result_sbox_sizer.Add(self.cldiscriminator_result_filebrowser_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Результат -> Компоновщик панели
        self.cldiscriminator_panel_sizer.Add(self.cldiscriminator_result_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Процесс
        self.cldiscriminator_process_sbox = wx.StaticBox(self.cldiscriminator_panel, label="Процесс")                   #контейнер (именная группа) для процесса
        self.cldiscriminator_process_sbox_sizer = wx.StaticBoxSizer(self.cldiscriminator_process_sbox, wx.VERTICAL)             #компоновщик группы
        #--- --- Выбор файлов/папок
        self.cldiscriminator_process_filebrowser_sizer = wx.FlexGridSizer(1, 3, fgs_filebrowser_gap[0], fgs_filebrowser_gap[1]) #табличный компоновщик для выбора файлов
        self.cldiscriminator_process_filebrowser_sizer.AddGrowableCol(1)                                          #задаём расширяемость для столбца с текстовыми полями
        #--- --- --- Исполняемый файл
        self.cldiscriminator_process_exe_label = wx.StaticText(self.cldiscriminator_process_sbox, style = wx.ALIGN_RIGHT, size = label_browse_size, label="Исп. файл:")
        self.cldiscriminator_process_filebrowser_sizer.Add(self.cldiscriminator_process_exe_label, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.cldiscriminator_process_exe_text = wx.TextCtrl(self.cldiscriminator_process_sbox)
        self.cldiscriminator_process_exe_text.Bind(wx.EVT_TEXT, self.OnCldiscriminatorPanelValueChange)
        self.cldiscriminator_process_exe_text.SetDropTarget(FileDropTarget(self.cldiscriminator_process_exe_text))
        self.cldiscriminator_process_filebrowser_sizer.Add(self.cldiscriminator_process_exe_text, flag = wx.EXPAND)
        self.cldiscriminator_process_exe_browse = wx.Button(self.cldiscriminator_process_sbox, size = button_browse_size, label = button_browse_label)
        self.cldiscriminator_process_exe_browse.Bind(wx.EVT_BUTTON, lambda event: self.OnFileBrowse(event, self.cldiscriminator_process_exe_text, False, wildcard = "|".join([FileBrowseWildcards.PYTHON.value, FileBrowseWildcards.WINDOWS_EXE.value, FileBrowseWildcards.SHELL_SCRIPT.value, FileBrowseWildcards.ALL.value])))
        self.cldiscriminator_process_exe_browse.Bind(wx.EVT_MIDDLE_DOWN, lambda event: self.cldiscriminator_process_exe_text.Clear())
        self.cldiscriminator_process_filebrowser_sizer.Add(self.cldiscriminator_process_exe_browse, flag = wx.FIXED_MINSIZE | wx.FIXED_LENGTH)
        #--- --- компоновка: Выбор файлов/папок -> Вывод
        self.cldiscriminator_process_sbox_sizer.Add(self.cldiscriminator_process_filebrowser_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- --- Поведение
        self.cldiscriminator_process_behaviour_sbox = wx.StaticBox(self.cldiscriminator_process_sbox, label="Поведение")                #контейнер (именная группа) для поведения
        self.cldiscriminator_process_behaviour_sbox_sizer = wx.StaticBoxSizer(self.cldiscriminator_process_behaviour_sbox, wx.VERTICAL) #компоновщик группы
        #--- --- --- Варианты
        self.cldiscriminator_process_behaviour_grid_sizer = wx.GridBagSizer(gbs_variants_gap[0], gbs_variants_gap[1])   #табличный компоновщик для вариантов
        self.cldiscriminator_process_behaviour_noquestions_chkbox = wx.CheckBox(self.cldiscriminator_process_behaviour_sbox, size = checkbox_flag_size, label="Не задавать вопросов")
        self.cldiscriminator_process_behaviour_noquestions_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.cldiscriminator_process_behaviour_noquestions_chkbox.SetValue(False)
        self.cldiscriminator_process_behaviour_noquestions_chkbox.Disable()
        self.cldiscriminator_process_behaviour_grid_sizer.Add(self.cldiscriminator_process_behaviour_noquestions_chkbox, pos = (0, 0), flag=wx.ALIGN_LEFT)
        self.cldiscriminator_process_behaviour_nohalt_chkbox = wx.CheckBox(self.cldiscriminator_process_behaviour_sbox, size = checkbox_flag_size, label="Закрываться при завершении")
        self.cldiscriminator_process_behaviour_nohalt_chkbox.Bind(wx.EVT_CHECKBOX, self.OnBomconverterPanelValueChange)
        self.cldiscriminator_process_behaviour_nohalt_chkbox.SetValue(True)
        self.cldiscriminator_process_behaviour_nohalt_chkbox.Disable()
        self.cldiscriminator_process_behaviour_grid_sizer.Add(self.cldiscriminator_process_behaviour_nohalt_chkbox,      pos = (0, 1), flag=wx.ALIGN_LEFT)
        #--- --- --- --- Уровень лога
        self.cldiscriminator_process_behaviour_loglevel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cldiscriminator_process_behaviour_loglevel_label = wx.StaticText(self.cldiscriminator_process_behaviour_sbox, label="Уровень журнала: ")
        self.cldiscriminator_process_behaviour_loglevel_label.Disable()
        self.cldiscriminator_process_behaviour_loglevel_sizer.Add(self.cldiscriminator_process_behaviour_loglevel_label)
        self.cldiscriminator_process_behaviour_loglevel_choice = wx.Choice(self.cldiscriminator_process_behaviour_sbox, choices=["", "debug", "info", "warn", "error", "fatal"])
        self.cldiscriminator_process_behaviour_loglevel_choice.Disable()
        self.cldiscriminator_process_behaviour_loglevel_choice.Bind(wx.EVT_CHOICE, self.OnBomconverterPanelValueChange)
        self.cldiscriminator_process_behaviour_loglevel_sizer.Add(self.cldiscriminator_process_behaviour_loglevel_choice)
        self.cldiscriminator_process_behaviour_grid_sizer.Add(self.cldiscriminator_process_behaviour_loglevel_sizer, pos = (0, 2), flag=wx.ALIGN_LEFT)
        #--- --- --- компоновка: Варианты -> Поведение
        self.cldiscriminator_process_behaviour_sbox_sizer.Add(self.cldiscriminator_process_behaviour_grid_sizer, flag = wx.EXPAND | wx.ALL, border = gbs_variants_border)
        #--- --- компоновка: Поведение -> Процесс
        self.cldiscriminator_process_sbox_sizer.Add(self.cldiscriminator_process_behaviour_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Процесс -> Компоновщик панели
        self.cldiscriminator_panel_sizer.Add(self.cldiscriminator_process_sbox_sizer, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #--- Выполнение
        self.cldiscriminator_execution_sbox = wx.StaticBox(self.cldiscriminator_panel, label="Выполнение")                      #контейнер (именная группа) для выполнения
        self.cldiscriminator_execution_sbox_sizer = wx.StaticBoxSizer(self.cldiscriminator_execution_sbox, wx.VERTICAL)         #компоновщик группы
        #--- --- Команда
        self.cldiscriminator_execution_command_text = wx.TextCtrl(self.cldiscriminator_execution_sbox, style = wx.TE_MULTILINE | wx.TE_READONLY)
        self.cldiscriminator_execution_sbox_sizer.Add(self.cldiscriminator_execution_command_text, proportion = 1, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- --- Кнопка запуска
        self.cldiscriminator_execution_start_button = wx.Button(self.cldiscriminator_execution_sbox, label = "Запуск")
        self.cldiscriminator_execution_start_button.Bind(wx.EVT_BUTTON, self.OnCldiscriminatorStartButtonPress)
        self.cldiscriminator_execution_sbox_sizer.Add(self.cldiscriminator_execution_start_button, flag = wx.EXPAND | wx.ALL, border = group_border_inner)
        #--- компоновка: Выполнение -> Компоновщик панели
        self.cldiscriminator_panel_sizer.Add(self.cldiscriminator_execution_sbox_sizer, proportion = 1, flag = wx.EXPAND | wx.ALL, border = group_border_outer)

        #компоновка: Компоновщик панели -> Панель
        self.cldiscriminator_panel.SetSizer(self.cldiscriminator_panel_sizer)

        #возвращаем ссылку на панель
        return self.cldiscriminator_panel

    # Log panel ---------------------------------------------------------------------------------------------------------------------------------------------------------------
    def layout_panel_log(self, parent):
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

    #Обработчик события: кнопка выбора файла
    def OnFileBrowse(self, event, text_ctrl, multiple = False, save = False, wildcard = "All files (*.*)|*.*"):
        """ Opens file dialog and sets selected file path in the text field """
        if save:
            message = 'Сохранить файл'
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        else:
            message = 'Открыть файл'
            style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            if multiple: style |= wx.FD_MULTIPLE
        with wx.FileDialog(self, message, style = style, wildcard = wildcard) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                files = file_dialog.GetPaths()
                text = "\n".join(files)
                text_ctrl.SetValue(text)

    #Обработчик события: кнопка выбора папки
    def OnDirBrowse(self, event, text_ctrl):
        """ Opens folder dialog and sets selected directory path in the text field """
        with wx.DirDialog(self, "Select a directory") as dir_dialog:
            if dir_dialog.ShowModal() == wx.ID_OK:
                text_ctrl.SetValue(dir_dialog.GetPath())

    #Обработчик события: вызов завершения программы
    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    #Обработчик события: вызов сохранения параметров GUI
    def OnParamsSave(self, event):
        params = self.params_get()
        style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        wildcard = "Configuration files (*.ini)|*.ini|All files (*.*)|*.*"
        with wx.FileDialog(self, "Сохранить параметры в файл", style = style, wildcard = wildcard) as file_dialog:
            file_dialog.SetDirectory(_module_dirname)
            file_dialog.SetFilename('gui.ini')
            if file_dialog.ShowModal() == wx.ID_OK:
                path = file_dialog.GetPath()
                path = os.path.join(_module_dirname, path)
                self.params_save(params, path)

    #Обработчик события: вызов загрузки параметров GUI
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

    #Обработчик события: вызов сброса параметров GUI
    def OnParamsDefaults(self, event):
        params = self.params_default()
        self.params_apply(params)

    #Обработчик события: вызов окна о программе
    def OnAbout(self, event):
        """Display an About Dialog"""
        message = f"Графический интерфейс пользователя для программы BoM converter.\nВерсия от {_module_date:%Y-%m-%d}"
        wx.MessageBox(message, "О программе", wx.OK|wx.ICON_INFORMATION)

    #Обработчик события: изменение значений на панели bomconverter
    def OnBomconverterPanelValueChange(self, event):
        """Changes on BoM converter panel were made"""
        #получаем параметры с интерфейса
        params = self.params_get_bomconverter()
        
        #изменения на интерфейсе
        #--- количество файлов данных
        datafiles = params['input']['datafiles']
        datafiles_num = 0
        if len(datafiles) > 0:
            datafiles = datafiles.split('\n')
            for file in datafiles:
                if len(file) > 0: datafiles_num += 1
        label = self.bomconverter_input_data_label.GetLabelText()
        label = label.split('\n')
        self.bomconverter_input_data_label.SetLabelText(f"{label[0]}\n[{datafiles_num}]")
        #--- кнопка запуска
        if datafiles_num > 0: self.bomconverter_execution_start_button.Enable()
        else:                 self.bomconverter_execution_start_button.Disable()
        #--- флаги оптимизации
        config_optimize_all  = Bomconverter_OptimizationID.ALL.value in params['config']['optimize']
        config_optimize_none = Bomconverter_OptimizationID.NONE.value in params['config']['optimize']
        config_optimize_global = config_optimize_all | config_optimize_none
        self.bomconverter_config_optimize_mfrname_chkbox.Enable(not config_optimize_global)
        self.bomconverter_config_optimize_restol_chkbox.Enable(not config_optimize_global)
        self.bomconverter_config_optimize_all_chkbox.Enable(not config_optimize_none)
        self.bomconverter_config_optimize_none_chkbox.Enable(not config_optimize_all)
        #--- флаги выходных форматов
        output_format_all  = Bomconverter_OutputID.ALL.value in params['output']['format']
        output_format_none = Bomconverter_OutputID.NONE.value in params['output']['format']
        output_format_global = output_format_all | output_format_none
        self.bomconverter_output_format_pe3docx_chkbox.Enable(not output_format_global)
        self.bomconverter_output_format_pe3pdf_chkbox.Enable(not output_format_global)
        self.bomconverter_output_format_pe3csv_chkbox.Enable(not output_format_global)
        self.bomconverter_output_format_clxlsx_chkbox.Enable(not output_format_global)
        self.bomconverter_output_format_spcsv_chkbox.Enable(not output_format_global)
        self.bomconverter_output_format_all_chkbox.Enable(not output_format_none)
        self.bomconverter_output_format_none_chkbox.Enable(not output_format_all)

        #получаем аргументы для вызова
        argv = self.argv_build_bomconverter(params)

        #собираем команду для отображения
        self.bomconverter_execution_command_text.SetValue(self.command_build(argv))

    #Обработчик события: изменение значений на панели bomdiscriminator
    def OnBomdiscriminatorPanelValueChange(self, event):
        """Changes on BoM discriminator panel were made"""
        #изменения на интерфейсе (до сбора параметров)
        #--- смена расширения выходного файла в зависимости от формата
        result_format_choices = [self.bomdiscriminator_result_format_choice.GetString(i) for i in range(self.bomdiscriminator_result_format_choice.GetCount())]
        result_file = self.bomdiscriminator_result_file_text.GetValue()
        for choice in result_format_choices:
            if choice:
                choice_ext = os.path.extsep + choice
                if result_file.endswith(choice_ext):
                    choice_ext_new = os.path.extsep + self.get_choice_string(self.bomdiscriminator_result_format_choice)
                    result_file_new = result_file[:-len(choice_ext)] + choice_ext_new
                    if result_file_new != result_file:
                        self.bomdiscriminator_result_file_text.SetValue(result_file_new)
                    break

        #получаем параметры с интерфейса
        params = self.params_get_bomdiscriminator()

        #изменения на интерфейсе (после сбора параметров)
        #--- кнопка запуска
        if len(params['reference']['bom']) > 0 and len(params['subject']['bom']) > 0 and len(params['result']['file']) > 0:
            self.bomdiscriminator_execution_start_button.Enable()
        else:
            self.bomdiscriminator_execution_start_button.Disable()

        #получаем аргументы для вызова
        argv = self.argv_build_bomdiscriminator(params)

        #собираем команду для отображения
        self.bomdiscriminator_execution_command_text.SetValue(self.command_build(argv))

    #Обработчик события: изменение значений на панели cldiscriminator
    def OnCldiscriminatorPanelValueChange(self, event):
        """Changes on CL discriminator panel were made"""
        #получаем параметры с интерфейса
        params = self.params_get_cldiscriminator()

        #изменения на интерфейсе
        #--- кнопка запуска
        if len(params['reference']['cl']) > 0 and len(params['subject']['cl']) > 0 and len(params['result']['cl']) > 0:
            self.cldiscriminator_execution_start_button.Enable()
        else:
            self.cldiscriminator_execution_start_button.Disable()

        #получаем аргументы для вызова
        argv = self.argv_build_cldiscriminator(params)

        #собираем команду для отображения
        self.cldiscriminator_execution_command_text.SetValue(self.command_build(argv))

    #Обработчик события: вызов запуска bomconverter
    def OnBomconverterStartButtonPress(self, event):
        """BoM converter start button press event handler"""
        params = self.params_get_bomconverter()
        argv = self.argv_build_bomconverter(params)
        self.notebook.SetSelection(self.get_notebook_page_index(self.notebook, self.log_panel))
        self.execution_lock(True)
        self.cli_execute(argv)

    #Обработчик события: вызов запуска bomconverter
    def OnBomdiscriminatorStartButtonPress(self, event):
        """BoM discriminator start button press event handler"""
        params = self.params_get_bomdiscriminator()
        argv = self.argv_build_bomdiscriminator(params)
        self.notebook.SetSelection(self.get_notebook_page_index(self.notebook, self.log_panel))
        self.execution_lock(True)
        self.cli_execute(argv)

    #Обработчик события: вызов запуска cldiscriminator
    def OnCldiscriminatorStartButtonPress(self, event):
        """CL discriminator start button press event handler"""
        params = self.params_get_cldiscriminator()
        argv = self.argv_build_cldiscriminator(params)
        self.notebook.SetSelection(self.get_notebook_page_index(self.notebook, self.log_panel))
        self.execution_lock(True)
        self.cli_execute(argv)

    #Обработчик события: вызов очистки лога
    def OnClearLogButtonPress(self, event):
        """Clear log button press event handler"""
        self.log_text.Clear()

    #Обработчик события: вызов копирования лога
    def OnCopyLogButtonPress(self, event):
        """Copy log button press event handler"""
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(self.log_text.GetValue()))
            wx.TheClipboard.Close()

    #Обработчик события: вызов поиска в логе
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

    #Обработчик события: изменение текста для поиска в логе
    def OnSearchLogTextChange(self, event):
        search_text = self.log_control_search_text.GetValue()
        if len(search_text) > 0: self.log_control_search_button.Enable()
        else: self.log_control_search_button.Disable()

    #Обработчик события: изменение лога
    def OnLogValueChange(self, event):
        text = self.log_text.GetValue()
        lines = text.count("\n") + 1
        chars = len(text)

        self.log_statusbar_length_label.SetLabelText(f"length: {chars:,}".replace(',', ' '))
        self.log_statusbar_linecount_label.SetLabelText(f"lines: {lines:,}".replace(',', ' '))
        self.OnLogCursorPositionChange(None)
        if event is not None: event.Skip()

    #Обработчик события: изменение позиции курсора в логе
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

    #Обработчик события: срабатываение таймера обновления лога
    def OnLogTimer(self, event):
        self.log_update("")

    #Блокирует кнопки запуска
    def execution_lock(self, state):
        if state:
            self.bomconverter_execution_start_button.Disable()
            self.bomdiscriminator_execution_start_button.Disable()
            self.cldiscriminator_execution_start_button.Disable()
        else:
            self.bomconverter_execution_start_button.Enable()
            self.bomdiscriminator_execution_start_button.Enable()
            self.cldiscriminator_execution_start_button.Enable()

    #Возвращает индекс вкладки блокнота по панели
    def get_notebook_page_index(self, notebook, panel):
        for i in range(notebook.GetPageCount()):
            if notebook.GetPage(i) is panel:
                return i
        return -1

    #Возвращает текстовое значение выбранное на Choice
    def get_choice_string(self, choice, default_index = 0):
        selected_index = choice.GetSelection()
        if selected_index < 0: selected_index = default_index
        return choice.GetString(selected_index)

    #Устанавливает значение выбранное на Choice по тексту, возвращает False если такого варианта текста нет
    def set_choice_string(self, choice, string, default_index = None, case_sensitive = False):
        result = True
        item_index = choice.FindString(string, case_sensitive)
        if item_index == wx.NOT_FOUND:
            result = False
            if default_index is not None:
                item_index = default_index
        choice.SetSelection(item_index)
        return result

    #Собирает все параметры со всех панелей
    def params_get(self):
        bomconverter_params = self.params_get_bomconverter()
        bomdiscriminator_params = self.params_get_bomdiscriminator()
        cldiscriminator_params = self.params_get_cldiscriminator()
        params = {
            'bomconverter': bomconverter_params,
            'bomdiscriminator': bomdiscriminator_params,
            'cldiscriminator': cldiscriminator_params
        }
        return params

    #Собирает параметры с панели bomconverter
    def params_get_bomconverter(self):
        """Get params from BoM converter panel"""
        config_optimize = []
        if self.bomconverter_config_optimize_none_chkbox.GetValue(): config_optimize.append(Bomconverter_OptimizationID.NONE.value)
        if self.bomconverter_config_optimize_all_chkbox.GetValue(): config_optimize.append(Bomconverter_OptimizationID.ALL.value)
        if self.bomconverter_config_optimize_mfrname_chkbox.GetValue(): config_optimize.append(Bomconverter_OptimizationID.MFR_NAME.value)
        if self.bomconverter_config_optimize_restol_chkbox.GetValue(): config_optimize.append(Bomconverter_OptimizationID.RES_TOL.value)
        config_optimize = ",".join(config_optimize)

        output_format = []
        if self.bomconverter_output_format_none_chkbox.GetValue(): output_format.append(Bomconverter_OutputID.NONE.value)
        if self.bomconverter_output_format_all_chkbox.GetValue(): output_format.append(Bomconverter_OutputID.ALL.value)
        if self.bomconverter_output_format_pe3docx_chkbox.GetValue(): output_format.append(Bomconverter_OutputID.PE3_DOCX.value)
        if self.bomconverter_output_format_pe3pdf_chkbox.GetValue(): output_format.append(Bomconverter_OutputID.PE3_PDF.value)
        if self.bomconverter_output_format_pe3csv_chkbox.GetValue(): output_format.append(Bomconverter_OutputID.PE3_CSV.value)
        if self.bomconverter_output_format_clxlsx_chkbox.GetValue(): output_format.append(Bomconverter_OutputID.CL_XLSX.value)
        if self.bomconverter_output_format_spcsv_chkbox.GetValue(): output_format.append(Bomconverter_OutputID.SP_CSV.value)
        output_format = ",".join(output_format)

        params = {
            'input': {
                'adproject'     : self.bomconverter_input_adproject_chkbox.GetValue(),
                'datafiles'     : self.bomconverter_input_data_text.GetValue(),
                'titleblock'    : self.bomconverter_input_titleblock_text.GetValue()
            },
            'config': {
                'settings'      : self.bomconverter_config_settings_text.GetValue(),
                'parser'        : self.bomconverter_config_parser_text.GetValue(),
                'optimize'      : config_optimize
            },
            'output': {
                'directory'     : self.bomconverter_output_directory_text.GetValue(),
                'format'        : output_format
            },
            'process': {
                'executable'    : self.bomconverter_process_exe_text.GetValue(),
                'noquestions'   : self.bomconverter_process_behaviour_noquestions_chkbox.GetValue(),
                'nohalt'        : self.bomconverter_process_behaviour_nohalt_chkbox.GetValue(),
                'loglevel'      : self.get_choice_string(self.bomconverter_process_behaviour_loglevel_choice)
            }
        }
        return params

    #Собирает параметры с панели bomdiscriminator
    def params_get_bomdiscriminator(self):
        """Get params from BoM discriminator panel"""
        config_fields_ignore = self.bomdiscriminator_config_fields_ignore_combobox.GetValue()
        if config_fields_ignore:
            config_fields_ignore = config_fields_ignore.split(',')
        else:
            config_fields_ignore = []
        for i, value in enumerate(config_fields_ignore):
            config_fields_ignore[i] = value.strip()
        config_fields_ignore_unpaired = self.bomdiscriminator_config_fields_ignore_unpaired_chkbox.GetValue()
        if config_fields_ignore_unpaired: config_fields_ignore.append('*')

        params = {
            'reference': {
                'bom'               : self.bomdiscriminator_reference_bom_text.GetValue(),
                'settings'          : self.bomdiscriminator_reference_settings_text.GetValue(),
            },
            'subject': {
                'bom'               : self.bomdiscriminator_subject_bom_text.GetValue(),
                'settings'          : self.bomdiscriminator_subject_settings_text.GetValue(),
            },
            'result': {
                'format'            : self.get_choice_string(self.bomdiscriminator_result_format_choice),
                'file'              : self.bomdiscriminator_result_file_text.GetValue(),
            },
            'config': {
                'settings'          : self.bomdiscriminator_config_settings_text.GetValue(),
                'fields': {
                    'key'               : self.bomdiscriminator_config_fields_key_combobox.GetValue(),
                    'key_list'          : [self.bomdiscriminator_config_fields_key_combobox.GetString(i) for i in range(self.bomdiscriminator_config_fields_key_combobox.GetCount())],
                    'ignore'            : ','.join(config_fields_ignore),
                    'ignore_list'       : [self.bomdiscriminator_config_fields_ignore_combobox.GetString(i) for i in range(self.bomdiscriminator_config_fields_ignore_combobox.GetCount())],
                },
                'xlsx_changes_mode' : self.get_choice_string(self.bomdiscriminator_config_xlsx_changes_mode_choice)
            },
            'process': {
                'executable'        : self.bomdiscriminator_process_exe_text.GetValue(),
                'noquestions'       : self.bomdiscriminator_process_behaviour_noquestions_chkbox.GetValue(),
                'nohalt'            : self.bomdiscriminator_process_behaviour_nohalt_chkbox.GetValue(),
                'loglevel'          : self.get_choice_string(self.bomdiscriminator_process_behaviour_loglevel_choice)
            }
        }
        return params

    #Собирает параметры с панели cldiscriminator
    def params_get_cldiscriminator(self):
        """Get params from CL discriminator panel"""
        params = {
            'reference': {
                'cl'            : self.cldiscriminator_reference_cl_text.GetValue(),
                'settings'      : self.cldiscriminator_reference_settings_text.GetValue(),
            },
            'subject': {
                'cl'            : self.cldiscriminator_subject_cl_text.GetValue(),
                'settings'      : self.cldiscriminator_subject_settings_text.GetValue(),
            },
            'result': {
                'cl'            : self.cldiscriminator_result_cl_text.GetValue(),
                'settings'      : self.cldiscriminator_result_settings_text.GetValue(),
            },
            'process': {
                'executable'    : self.cldiscriminator_process_exe_text.GetValue(),
                'noquestions'   : self.cldiscriminator_process_behaviour_noquestions_chkbox.GetValue(),
                'nohalt'        : self.cldiscriminator_process_behaviour_nohalt_chkbox.GetValue(),
                'loglevel'      : self.get_choice_string(self.cldiscriminator_process_behaviour_loglevel_choice)
            }
        }

        return params

    #Применяет параметры на интерфейс
    def params_apply(self, params):
        if 'bomconverter' in params: self.params_apply_bomconverter(params['bomconverter'])
        if 'bomdiscriminator' in params: self.params_apply_bomdiscriminator(params['bomdiscriminator'])
        if 'cldiscriminator' in params: self.params_apply_bomconverter(params['cldiscriminator'])

    #Применяет параметры на интерфейс для bomconverter
    def params_apply_bomconverter(self, params):
        if 'input' in params:
            block = params['input']
            if 'adproject' in block: self.bomconverter_input_adproject_chkbox.SetValue(block['adproject'])
            if 'datafiles' in block: self.bomconverter_input_data_text.SetValue(str(block['datafiles']))
            if 'titleblock' in block: self.bomconverter_input_titleblock_text.SetValue(str(block['titleblock']))
        if 'config' in params:
            block = params['config']
            if 'settings' in block: self.bomconverter_config_settings_text.SetValue(str(block['settings']))
            if 'parser' in block: self.bomconverter_config_parser_text.SetValue(str(block['parser']))
            if 'optimize' in block:
                self.bomconverter_config_optimize_none_chkbox.SetValue(Bomconverter_OptimizationID.NONE.value in block['optimize'])
                self.bomconverter_config_optimize_all_chkbox.SetValue(Bomconverter_OptimizationID.ALL.value in block['optimize'])
                self.bomconverter_config_optimize_mfrname_chkbox.SetValue(Bomconverter_OptimizationID.MFR_NAMES.value in block['optimize'])
                self.bomconverter_config_optimize_restol_chkbox.SetValue(Bomconverter_OptimizationID.RES_TOL.value in block['optimize'])
        if 'output' in params:
            block = params['output']
            if 'output' in block: self.bomconverter_output_directory_text.SetValue(str(block['directory']))
            if 'format' in block:
                self.bomconverter_output_format_none_chkbox.SetValue(Bomconverter_OutputID.NONE.value in block['format'])
                self.bomconverter_output_format_all_chkbox.SetValue(Bomconverter_OutputID.ALL.value in block['format'])
                self.bomconverter_output_format_pe3docx_chkbox.SetValue(Bomconverter_OutputID.PE3_DOCX.value in block['format'])
                self.bomconverter_output_format_pe3pdf_chkbox.SetValue(Bomconverter_OutputID.PE3_PDF.value in block['format'])
                self.bomconverter_output_format_pe3csv_chkbox.SetValue(Bomconverter_OutputID.PE3_CSV.value in block['format'])
                self.bomconverter_output_format_clxlsx_chkbox.SetValue(Bomconverter_OutputID.CL_XLSX.value in block['format'])
                self.bomconverter_output_format_spcsv_chkbox.SetValue(Bomconverter_OutputID.SP_CSV.value in block['format'])
        if 'process' in params:
            block = params['process']
            if 'executable' in block: self.bomconverter_process_exe_text.SetValue(str(block['executable']))
            if 'noquestions' in block: self.bomconverter_process_behaviour_noquestions_chkbox.SetValue(block['noquestions'])
            if 'nohalt' in block: self.bomconverter_process_behaviour_nohalt_chkbox.SetValue(block['nohalt'])
            if 'loglevel' in block: self.set_choice_string(self.bomconverter_process_behaviour_loglevel_choice, str(block['loglevel']), 0)
        self.OnBomconverterPanelValueChange(None)

    #Применяет параметры на интерфейс для bomdiscriminator
    def params_apply_bomdiscriminator(self, params):
        if 'reference' in params:
            block = params['reference']
            if 'bom' in block: self.bomdiscriminator_reference_bom_text.SetValue(str(block['bom']))
            if 'settings' in block: self.cldiscriminator_reference_settings_text.SetValue(str(block['settings']))
        if 'subject' in params:
            block = params['subject']
            if 'bom' in block: self.bomdiscriminator_subject_bom_text.SetValue(str(block['bom']))
            if 'settings' in block: self.bomdiscriminator_subject_settings_text.SetValue(str(block['settings']))
        if 'result' in params:
            block = params['result']
            if 'format' in block: self.set_choice_string(self.bomdiscriminator_result_format_choice, str(block['format']), 0)
            if 'file' in block: self.bomdiscriminator_result_file_text.SetValue(str(block['file']))
        if 'config' in params:
            block = params['config']
            if 'settings' in block: self.bomdiscriminator_config_settings_text.SetValue(str(block['settings']))
            if 'fields' in block:
                section = block['fields']
                if 'key' in section: self.bomdiscriminator_config_fields_key_combobox.SetValue(str(section['key']))
                if 'key_list' in section:
                    config_fields_key_value = self.bomdiscriminator_config_fields_key_combobox.GetValue()
                    self.bomdiscriminator_config_fields_key_combobox.Clear()
                    for choice in section['key_list']:
                        self.bomdiscriminator_config_fields_key_combobox.Append(choice)
                    self.bomdiscriminator_config_fields_key_combobox.SetValue(config_fields_key_value)
                if 'ignore' in section:
                    config_fields_ignore = str(section['ignore'])
                    config_fields_ignore_unpaired = False
                    if config_fields_ignore: config_fields_ignore = config_fields_ignore.split(',')
                    else:                    config_fields_ignore = []
                    for i in range(len(config_fields_ignore) - 1, -1, -1):
                        config_fields_ignore[i] = config_fields_ignore[i].strip()
                        if config_fields_ignore[i] == '*':
                            config_fields_ignore_unpaired = True
                            config_fields_ignore.pop(i)
                    self.bomdiscriminator_config_fields_ignore_combobox.SetValue(','.join(config_fields_ignore))
                    self.bomdiscriminator_config_fields_ignore_unpaired_chkbox.SetValue(config_fields_ignore_unpaired)
                if 'ignore_list' in section:
                    config_fields_ignore_value = self.bomdiscriminator_config_fields_ignore_combobox.GetValue()
                    self.bomdiscriminator_config_fields_ignore_combobox.Clear()
                    for choice in section['ignore_list']:
                        self.bomdiscriminator_config_fields_ignore_combobox.Append(choice)
                    self.bomdiscriminator_config_fields_ignore_combobox.SetValue(config_fields_ignore_value)
            if 'xlsx_changes_mode' in block: self.set_choice_string(self.bomdiscriminator_config_xlsx_changes_mode_choice, str(block['xlsx_changes_mode']), 0)
        if 'process' in params:
            block = params['process']
            if 'executable' in block: self.bomdiscriminator_process_exe_text.SetValue(str(block['executable']))
            if 'noquestions' in block: self.bomdiscriminator_process_behaviour_noquestions_chkbox.SetValue(block['noquestions'])
            if 'nohalt' in block: self.bomdiscriminator_process_behaviour_nohalt_chkbox.SetValue(block['nohalt'])
            if 'loglevel' in block: self.set_choice_string(self.bomdiscriminator_process_behaviour_loglevel_choice, str(block['loglevel']), 0)
        self.OnBomdiscriminatorPanelValueChange(None)

    #Применяет параметры на интерфейс для cldiscriminator
    def params_apply_cldiscriminator(self, params):
        if 'reference' in params:
            block = params['reference']
            if 'cl' in block: self.cldiscriminator_reference_cl_text.SetValue(str(block['cl']))
            if 'settings' in block: self.cldiscriminator_reference_settings_text.SetValue(str(block['settings']))
        if 'subject' in params:
            block = params['subject']
            if 'cl' in block: self.cldiscriminator_subject_cl_text.SetValue(str(block['cl']))
            if 'settings' in block: self.cldiscriminator_subject_settings_text.SetValue(str(block['settings']))
        if 'result' in params:
            block = params['result']
            if 'cl' in block: self.cldiscriminator_result_cl_text.SetValue(str(block['cl']))
            if 'settings' in block: self.cldiscriminator_result_settings_text.SetValue(str(block['settings']))
        if 'process' in params:
            block = params['process']
            if 'executable' in block: self.cldiscriminator_process_exe_text.SetValue(str(block['executable']))
            if 'noquestions' in block: self.cldiscriminator_process_behaviour_noquestions_chkbox.SetValue(block['noquestions'])
            if 'nohalt' in block: self.cldiscriminator_process_behaviour_nohalt_chkbox.SetValue(block['nohalt'])
            if 'loglevel' in block: self.set_choice_string(self.cldiscriminator_process_behaviour_loglevel_choice, str(block['loglevel']), 0)
        self.OnCldiscriminatorPanelValueChange(None)

    #Сохраняет параметры в конфигурационный файл
    def params_save(self, params, filename):
        config = configparser.ConfigParser()
        flat_params = nested_dict_flatten(params, '.', 1)

        for section, dictionary in flat_params.items():
            for option, value in dictionary.items():
                dictionary[option] = repr(value)
            config[section] = dictionary

        with open(filename, "w", encoding="utf-8") as configfile:
            config.write(configfile)

    #Загружает параметры из конфигурационного файла
    def params_load(self, filename):
        config = configparser.ConfigParser()

        try:
            config.read(filename, encoding="utf-8")
            params = {}
            for section in config.sections():
                section_dict = {}
                for key, value in config[section].items():
                    section_dict[key] = ast.literal_eval(value)
                params[section] = section_dict
            params = nested_dict_unflatten(params, '.', -1)
            return params

        except FileNotFoundError as e:
            self.statusbar.SetStatusText(f"Error: {e}")
        except (OSError, IOError) as e:
            self.statusbar.SetStatusText(f"File access error: {e}")
        except (configparser.Error, ValueError, KeyError) as e:
            self.statusbar.SetStatusText(f"Config parsing error: {e}")

        return None

    #Возвращает параметры по-умолчанию
    def params_default(self):
        params = {
            'bomconverter'     : self.params_default_bomconverter(),
            'bomdiscriminator' : self.params_default_bomdiscriminator(),
            'cldiscriminator'  : self.params_default_cldiscriminator()
        }
        return params

    #Возвращает параметры по-умолчанию для bomconverter
    def params_default_bomconverter(self):
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

    #Возвращает параметры по-умолчанию для bomdiscriminator
    def params_default_bomdiscriminator(self):
        params = {
            'reference': {
                'bom'               : "",
                'settings'          : "",
            },
            'subject': {
                'bom'               : "",
                'settings'          : "",
            },
            'result': {
                'format'            : Bomdiscriminator_OutputID.XLSX.value,
                'file'              : "",
            },
            'config': {
                'settings'          : "",
                'fields': {
                    'key'               : "Designator",
                    'key_list'          : ["Designator", "UniqueIdName,UniqueIdPath"],
                    'ignore'            : "",
                    'ignore_list'       : ["Footprint"]
                },
                'xlsx_changes_mode' : Bomdiscriminator_XlsxChangesModeID.COMMENT.value
            },
            'process': {
                'executable'        : "",
                'noquestions'       : False,
                'nohalt'            : True,
                'loglevel'          : ""
            }
        }
        return params

    #Возвращает параметры по-умолчанию для cldiscriminator
    def params_default_cldiscriminator(self):
        params = {
            'reference': {
                'cl'            : "",
                'settings'      : "",
            },
            'subject': {
                'cl'            : "",
                'settings'      : "",
            },
            'result': {
                'cl'            : "",
                'settings'      : "",
            },
            'process': {
                'executable'    : "",
                'noquestions'   : False,
                'nohalt'        : True,
                'loglevel'      : ""
            } 
        }
        return params

    #Собирает вектор аргументов для bomconverter
    def argv_build_bomconverter(self, params):
        """Build command line argument vector for bomconverter"""
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
            if Bomconverter_OptimizationID.NONE.value in optimize: argv.append(Bomconverter_OptimizationID.NONE.value)
            elif Bomconverter_OptimizationID.ALL.value in optimize: argv.append(Bomconverter_OptimizationID.ALL.value)
            else:
                for opt in optimize:
                    if any(opt == item.value for item in Bomconverter_OptimizationID):
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
            if Bomconverter_OutputID.NONE.value in format: argv.append(Bomconverter_OutputID.NONE.value)
            elif Bomconverter_OutputID.ALL.value in format: argv.append(Bomconverter_OutputID.ALL.value)
            else:
                for opt in format:
                    if any(opt == item.value for item in Bomconverter_OutputID):
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

    #Собирает вектор аргументов для bomdiscriminator
    def argv_build_bomdiscriminator(self, params):
        """Build command line argument vector for bomdiscriminator"""
        argv = []

        #исполняемый файл
        executable = params.get('process', {}).get('executable', '')
        if len(executable) == 0: executable = 'bomdiscriminator.py'
        if os.path.splitext(executable)[1].lstrip(os.extsep) == 'py':
            argv.append('python')
        argv.append(executable)

        #BoM
        bom_reference = params.get('reference', {}).get('bom', '')
        argv.append(bom_reference)
        bom_subject = params.get('subject', {}).get('bom', '')
        argv.append(bom_subject)
        bom_result = params.get('result', {}).get('file', '')
        argv.append(bom_result)

        #настройки
        settings_reference = params.get('reference', {}).get('settings', '')
        if settings_reference: argv.extend(['--settings-reference', settings_reference])
        settings_subject = params.get('subject', {}).get('settings', '')
        if settings_subject: argv.extend(['--settings-subject', settings_subject])
        settings_result = params.get('result', {}).get('settings', '')
        if settings_result: argv.extend(['--settings-result', settings_result])
        
        #конфигурация
        output = params.get('result', {}).get('format', '')
        if output: argv.extend(['--output', output])
        fields_key = params.get('config', {}).get('fields', {}).get('key', '')
        if fields_key: argv.extend(['--fields-key', fields_key])
        fields_ignore = params.get('config', {}).get('fields', {}).get('ignore', '')
        if fields_ignore: argv.extend(['--fields-ignore', fields_ignore])
        xlsx_changes_mode = params.get('config', {}).get('xlsx_changes_mode', '')
        if xlsx_changes_mode: argv.extend(['--xlsx-changes-mode', xlsx_changes_mode])

        #не задавать вопросов
        #noquestions = params.get('process', {}).get('noquestions', False)
        #if noquestions: argv.append('--noquestions')

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

    #Собирает вектор аргументов для cldiscriminator
    def argv_build_cldiscriminator(self, params):
        """Build command line argument vector for cldiscriminator"""
        argv = []

        #исполняемый файл
        executable = params.get('process', {}).get('executable', '')
        if len(executable) == 0: executable = 'cldiscriminator.py'
        if os.path.splitext(executable)[1].lstrip(os.extsep) == 'py':
            argv.append('python')
        argv.append(executable)

        #списки
        cl_reference = params.get('reference', {}).get('cl', '')
        argv.append(cl_reference)
        cl_subject = params.get('subject', {}).get('cl', '')
        argv.append(cl_subject)
        cl_result = params.get('result', {}).get('cl', '')
        argv.append(cl_result)

        #настройки
        settings_reference = params.get('reference', {}).get('settings', '')
        if settings_reference: argv.extend(['--settings-reference', settings_reference])
        settings_subject = params.get('subject', {}).get('settings', '')
        if settings_subject: argv.extend(['--settings-subject', settings_subject])
        settings_result = params.get('result', {}).get('settings', '')
        if settings_result: argv.extend(['--settings-result', settings_result])
        
        #не задавать вопросов
        #noquestions = params.get('process', {}).get('noquestions', False)
        #if noquestions: argv.append('--noquestions')

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

    #Собирает строку команды из вектора аргументов
    def command_build(self, argv):
        command = ""
        for arg in argv:
            if arg.find(" ") >= 0 or arg.find("\\") >= 0 or len(arg) == 0:
                command += ' "' + arg + '"'
            else:
                command += ' '  + arg
        return command[1:]

    #Запускает CLI-программу
    def cli_execute(self, argv):
        """Executes CLI program"""
        self.statusbar.SetStatusText("Процесс запущен...")
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

        self.log_lines_shown = len(self.cli_log)
        self.log_lines_last = self.cli_log[-1]
        self.log_last_update = time.monotonic()
        self.log_timer.Start(250)
    
    #Читает вывод CLI
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

    #Завершает работу с CLI-программой
    def cli_finished(self, code):
        self.log_timer.Stop()
        self.execution_lock(False)

        message = ""
        if code == 0:
            message = "Обработка успешно завершена"
        elif code == 3:
            message = "Операция отменена пользователем"
        else:
            message = "Программа завершилась с ошибкой"
        self.statusbar.SetStatusText(message)

    #Проверяет был ли запрос данных от CLI программы
    def cli_request(self):
        current_line = self.cli_log[-1]
        #определяем есть ли запрос
        if current_line.startswith("REQUEST") and (current_line.endswith(": ") or current_line.endswith("? ")):
            #в текущей строке есть запрос и он закончен -> определяем чего именно
            if "Choose which BoMs to process" in current_line:
                #запрос какие BoM-файлы обрабатывать -> надо получить список файлов
                self.bomconverter_select_bom()

    #Обновляет лог добавляя в него текст
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

    #Выбор BoM при запросе данных от bomconverter
    def bomconverter_select_bom(self):
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

class FileDropTarget(wx.FileDropTarget):
    def __init__(self, text_ctrl):
        super().__init__()
        self.text_ctrl = text_ctrl

    def OnDropFiles(self, x, y, filenames):
        """Handles the files dropped into the TextCtrl."""
        self.text_ctrl.SetValue("\n".join(filenames))
        return True

#Flattens a nested dictionary while preserving the top `preserve_levels` as nested dicts.
def nested_dict_flatten(nested_dict, sep = '.', preserve_levels = 0):
    """
    Flattens a nested dictionary while preserving the top `preserve_levels` as nested dicts.
    
    Args:
        nested_dict (dict): Arbitrary nested dictionary.
        sep (str): Separator to join keys.
        preserve_levels (int): How many top levels to keep as nested dicts.
        
    Returns:
        dict: Flattened dictionary with preserved outer structure.
    """
    def _flatten(d, prefix=(), level=0):
        result = {}
        for k, v in d.items():
            new_prefix = prefix + (str(k),)
            if isinstance(v, dict) and (preserve_levels == 0 or level < preserve_levels - 1):
                # Go deeper preserving outer layers
                sub_result = _flatten(v, new_prefix, level + 1)
                result.update(sub_result)
            elif isinstance(v, dict):
                # Stop preserving here — flatten this subdict
                flat = flatten_leaf_dict(v, sep=sep)
                for subkey, val in flat.items():
                    result[sep.join(new_prefix + (subkey,))] = val
            else:
                result[sep.join(new_prefix)] = v
        return result

    def flatten_leaf_dict(d, sep='.'):
        flat = {}
        for k, v in d.items():
            if isinstance(v, dict):
                sub_flat = flatten_leaf_dict(v, sep=sep)
                for subk, subv in sub_flat.items():
                    flat[f"{k}{sep}{subk}"] = subv
            else:
                flat[str(k)] = v
        return flat

    # Special handling if preserve_levels > 0
    if preserve_levels == 0:
        return _flatten(nested_dict, prefix=(), level=0)
    
    result = {}
    for k, v in nested_dict.items():
        if not isinstance(v, dict):
            result[str(k)] = v
        else:
            result[str(k)] = nested_dict_flatten(v, preserve_levels=preserve_levels - 1, sep=sep)
    return result

#Reconstructs a nested dictionary from flat keys
def nested_dict_unflatten(flat_dict, sep = '.', nested_levels = -1, *, current_level = 0):
    """
    Reconstructs a nested dictionary from flat keys.

    Args:
        flat_dict (dict): Dictionary with compound keys like 'a.b.c': value
        sep (str): Separator used in the keys
        nested_levels (int): Number of top-level nesting layers:
                             -1 = full depth
                              0 = flat
                              N = nest first N segments
    
    Returns:
        dict: Nested dictionary up to specified depth
    """
    result = {}

    for compound_key, value in flat_dict.items():
        # If value is dict, recursively unflatten it with incremented current_level
        if isinstance(value, dict):
            value = nested_dict_unflatten(
                value,
                nested_levels=nested_levels,
                sep=sep,
                current_level=current_level + 1,
            )

        parts = compound_key.split(sep)
        total_parts = len(parts)

        # Calculate how deep to nest here relative to overall level
        remaining_levels = nested_levels - current_level
        if remaining_levels < 0:
            # No nesting allowed, flatten all keys at this level
            remaining_levels = 0

        if nested_levels < 0:
            split_at = total_parts - 1
        else:
            split_at = min(remaining_levels, total_parts - 1)

        nesting_keys = parts[:split_at]
        remaining_key = sep.join(parts[split_at:])

        current = result
        for key in nesting_keys:
            current = current.setdefault(key, {})

        current[remaining_key] = value

    return result

if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the frame, show it, and start the event loop.
    app = App()
    frame = MainFrame()

    #загружаем параметры из файла 'gui.ini'
    params = None
    params_file = 'gui.ini'
    if os.path.isfile(params_file): params = frame.params_load(params_file)
    if params is None: params = frame.params_default()
    frame.params_apply(params)

    app.MainLoop()