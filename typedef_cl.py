import collections.abc
from enum import IntEnum

#CL class definition
class CL_typeDef():
    def __init__(self, book_title = ''):
        self.book_title  = book_title
        self.components  = None         #список основных компонентов
        self.accessories = None         #список сопутствующих компонентов
        self.substitutes = None         #список допустимых замен

    class Sublist():
        def __init__(self, title = '', entries = None):
            self.title   = title
            self.entries = [] if entries is None else entries

    class FlagType(IntEnum):
        NONE    = 0
        OK      = 1
        WARNING = 2
        ERROR   = 3

    class ComponentEntry():
        def __init__(self, designator = None, kind = None, value = None, description = None, package = None, manufacturer = None, quantity = 0, note = None, flag = None):
            self.designator   = []
            self.kind         = []
            self.value        = []
            self.description  = []
            self.package      = []
            self.manufacturer = []
            self.quantity     = int(quantity)
            self.note         = []
            self.flag         = CL_typeDef.FlagType.NONE
            if isinstance(designator, (list, tuple)): self.designator.extend(designator)
            else: self.designator.append(designator)
            if isinstance(kind, (list, tuple)): self.kind.extend(kind)
            else: self.kind.append(kind)
            if isinstance(value, (list, tuple)): self.value.extend(value)
            else: self.value.append(value)
            if isinstance(description, (list, tuple)): self.description.extend(description)
            else: self.description.append(description)
            if isinstance(package, (list, tuple)): self.package.extend(package)
            else: self.package.append(package)
            if isinstance(manufacturer, (list, tuple)): self.manufacturer.extend(manufacturer)
            else: self.manufacturer.append(manufacturer)
            if isinstance(note, (list, tuple)): self.note.extend(note)
            else: self.note.append(note)
            if flag is not None: self.flag = flag

        #добавляет компонент к текущей записи
        def add(self, designator, kind, value, description, package, manufacturer, quantity = 1, note = '', flag = None):
            if flag == None: flag = CL_typeDef.FlagType.NONE
            if flag > self.flag: self.flag = flag

            if len(designator) > 0:
                if designator in self.designator:
                    #если десигнатор не пустой и такой уже есть то что-то пошло не так
                    if self.flag < CL_typeDef.FlagType.ERROR: self.flag = CL_typeDef.FlagType.ERROR
                self.designator.append(designator)

            if kind not in self.kind:
                if self.flag < CL_typeDef.FlagType.WARNING: self.flag = CL_typeDef.FlagType.WARNING     #если поля не совпадают то это подозрительно
                self.kind.append(kind)

            if value not in self.value:
                if self.flag < CL_typeDef.FlagType.WARNING: self.flag = CL_typeDef.FlagType.WARNING
                self.value.append(value)

            if description not in self.description:
                if self.flag < CL_typeDef.FlagType.WARNING: self.flag = CL_typeDef.FlagType.WARNING
                self.description.append(description)

            if package not in self.package:
                if self.flag < CL_typeDef.FlagType.WARNING: self.flag = CL_typeDef.FlagType.WARNING
                self.package.append(package)

            if manufacturer not in self.manufacturer:
                if self.flag < CL_typeDef.FlagType.WARNING: self.flag = CL_typeDef.FlagType.WARNING
                self.manufacturer.append(manufacturer)

            self.quantity += quantity

            if note not in self.note:
                #if self.flag < CL_typeDef.FlagType.WARNING: self.flag = CL_typeDef.FlagType.WARNING
                self.note.append(note)

        #проверяет текущую запись на ошибки
        def check(self):
            #десигнатор
            if len(self.designator) != len(set(self.designator)):   #проверяем есть ли дубликаты
                if self.flag < CL_typeDef.FlagType.ERROR: self.flag = CL_typeDef.FlagType.ERROR
            #тип
            if len(self.kind) > 1:
                if self.flag < CL_typeDef.FlagType.WARNING: self.flag = CL_typeDef.FlagType.WARNING
            #номинал
            if len(self.value) > 1:
                if self.flag < CL_typeDef.FlagType.ERROR: self.flag = CL_typeDef.FlagType.ERROR
            #описание
            if len(self.description) > 1:
                if self.flag < CL_typeDef.FlagType.WARNING: self.flag = CL_typeDef.FlagType.WARNING
            #корпус
            if len(self.package) > 1:
                if self.flag < CL_typeDef.FlagType.WARNING: self.flag = CL_typeDef.FlagType.WARNING
            #производитель
            if len(self.manufacturer) > 1:
                if self.flag < CL_typeDef.FlagType.WARNING: self.flag = CL_typeDef.FlagType.WARNING
            #количество
            if self.quantity < 0:
                if self.flag < CL_typeDef.FlagType.ERROR: self.flag = CL_typeDef.FlagType.ERROR
            #примечание
            if len(self.note) > 1:
                pass #if self.flag < CL_typeDef.FlagType.WARNING: self.flag = CL_typeDef.FlagType.WARNING

    class SubstituteEntry():
        def __init__(self, primary_value = None, primary_manufacturer = None, primary_quantity = 0, substitute_group = None, flag = None):
            self.primary_value        = primary_value
            self.primary_manufacturer = primary_manufacturer
            self.primary_quantity     = int(primary_quantity)
            self.substitute_group     = substitute_group
            self.flag                 = CL_typeDef.FlagType.NONE
            if flag is not None: self.flag = flag

        class SubstituteGroup():
            def __init__(self, designator = None, quantity = 0, substitute = None, flag = None):
                self.designator = designator
                self.quantity   = int(quantity)
                self.substitute = substitute
                self.flag       = CL_typeDef.FlagType.NONE
                if flag is not None: self.flag = flag

            class Substitute():
                def __init__(self, value = None, manufacturer = None, note = None):
                    self.value        = value           #номинал
                    self.manufacturer = manufacturer    #производитель
                    self.note         = note            #примечание
                    self.flag         = CL_typeDef.FlagType.NONE
