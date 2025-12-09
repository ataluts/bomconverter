from dataclasses import dataclass, field
from enum import IntEnum
from datetime import datetime as dt
from typedef_designator import Designator

#Единицы измерения расстояния
class LengthUnits(IntEnum):
    MM  = 0         #миллиметры
    MIL = 1         #милы

#Слои печатной платы
class PCBlayer(IntEnum):
    TOP       = 0       #внешний верхний
    BOTTOM    = 255     #внешний нижний
    MIDDLE_1  = 1       #внутренний 1
    MIDDLE_2  = 2       #внутренний 2
    MIDDLE_3  = 3       #внутренний 3
    MIDDLE_4  = 4       #внутренний 4
    MIDDLE_5  = 5       #внутренний 5
    MIDDLE_6  = 6       #внутренний 6
    MIDDLE_7  = 7       #внутренний 7
    MIDDLE_8  = 8       #внутренний 8
    MIDDLE_9  = 9       #внутренний 9
    MIDDLE_10 = 10      #внутренний 10
    MIDDLE_11 = 11      #внутренний 11
    MIDDLE_12 = 12      #внутренний 12
    MIDDLE_13 = 13      #внутренний 13
    MIDDLE_14 = 14      #внутренний 14
    MIDDLE_15 = 15      #внутренний 15
    MIDDLE_16 = 16      #внутренний 16
    MIDDLE_17 = 17      #внутренний 17
    MIDDLE_18 = 18      #внутренний 18
    MIDDLE_19 = 19      #внутренний 19
    MIDDLE_20 = 20      #внутренний 20
    MIDDLE_21 = 21      #внутренний 21
    MIDDLE_22 = 22      #внутренний 22
    MIDDLE_23 = 23      #внутренний 23
    MIDDLE_24 = 24      #внутренний 24
    MIDDLE_25 = 25      #внутренний 25
    MIDDLE_26 = 26      #внутренний 26
    MIDDLE_27 = 27      #внутренний 27
    MIDDLE_28 = 28      #внутренний 28
    MIDDLE_29 = 29      #внутренний 29
    MIDDLE_30 = 30      #внутренний 30

#Тип монтажа
class MountType(IntEnum):
    UNDEFINED    = 0     #неизвестно
    SURFACE      = 1     #поверхностный
    SEMI_SURFACE = 2     #поверхностный, но с выводами для механики
    THROUGHHOLE  = 3     #выводной
    EDGE         = 4     #в край (торец) платы
    CHASSIS      = 5     #на корпус
    UNKNOWN      = 6     #неизвестный

#Pick and place
@dataclass
class PnP():
    @dataclass
    class Entry():
        @dataclass
        class State():
            enabled : bool  = True      #включено
            reason  : str   = None      #причина

            def disable(self, reason:str = None):
                self.enabled = False
                self.reason = reason

            def enable(self, reason:str = None):
                self.enabled = True
                self.reason = reason

        designator  : Designator                        #позиционное обозначение
        layer       : PCBlayer                          #слой
        location    : list[float, float]                #расположение [X, Y]
        rotation    : float                             #угол поворота
        footprint   : str                               #посадочное место
        mount       : MountType             = None      #тип монтажа
        partnumber  : str                   = None      #артикул
        description : str                   = None      #параметрическое описание
        comment     : str                   = None      #коментарий
        state       : State                 = None      #состояние

        #ключ сортировки по расположению
        def _cmpkey_location(self):
            raise NotImplementedError
        
        #ключ сортировки по состоянию
        def _cmpkey_state(self):
            return (self.state.enabled, self.state.reason)

    title       : str           = None                          #название
    variant     : str           = None                          #название конфигурации
    revision    : str           = None                          #название ревизии
    datetime    : dt            = None                          #дата и время
    units       : LengthUnits   = LengthUnits.MM                #единицы измерения длины
    entries     : list          = field(default_factory=list)   #записи
    
    #Вставляет запись в PnP
    def insert_entry(self, entry, index = -1):
        if index > len(self.entries): index = len(self.entries)
        elif index < -len(self.entries): index = 0
        elif index < 0: index = len(self.entries) + index + 1
        self.entries.insert(index, entry)
        return entry

    #Сортирует записи
    def sort(self, method = 'designator', reverse = False):
        if method == 'designator':
            self.entries.sort(key = lambda entry: entry.designator._cmpkey(), reverse = reverse)
        elif method == 'layer':
            self.entries.sort(key = lambda entry: entry.layer, reverse = reverse)
        elif method == 'location':
            self.entries.sort(key = lambda entry: entry._cmpkey_location(), reverse = reverse)
        elif method == 'rotation':
            self.entries.sort(key = lambda entry: entry.rotation, reverse = reverse)
        elif method == 'footprint':
            self.entries.sort(key = lambda entry: entry.footprint, reverse = reverse)
        elif method == 'mount':
            self.entries.sort(key = lambda entry: entry.mount, reverse = reverse)
        elif method == 'partnumber':
            self.entries.sort(key = lambda entry: entry.partnumber, reverse = reverse)
        elif method == 'description':
            self.entries.sort(key = lambda entry: entry.description, reverse = reverse)
        elif method == 'comment':
            self.entries.sort(key = lambda entry: entry.comment, reverse = reverse)
        elif method == 'state':
            self.entries.sort(key = lambda entry: entry._cmpkey_state(), reverse = reverse)
        else:
            raise NotImplementedError

