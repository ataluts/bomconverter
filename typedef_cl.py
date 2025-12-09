from enum import IntEnum
from dataclasses import dataclass

#CL class definition
@dataclass
class ComponentList():
    book_title  : str   = ''        #имя книги
    components  : list  = None      #список основных компонентов
    accessories : list  = None      #список сопутствующих компонентов
    substitutes : list  = None      #список допустимых замен

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
        def __init__(self, designator = None, kind = None, partnumber = None, parametric = None, description = None, package = None, manufacturer = None, quantity = 0, note = None, flag = None):
            self.designator   = []
            self.kind         = []
            self.partnumber   = []
            if parametric is None: self.parametric = False
            else:                  self.parametric = parametric
            self.description  = []
            self.package      = []
            self.manufacturer = []
            if quantity is None: self.quantity = 0
            else:                self.quantity = int(quantity)
            self.note         = []
            self.flag         = ComponentList.FlagType.NONE
            if isinstance(designator, (list, tuple)): self.designator.extend(designator)
            else: self.designator.append(designator)
            if isinstance(kind, (list, tuple)): self.kind.extend(kind)
            else: self.kind.append(kind)
            if isinstance(partnumber, (list, tuple)): self.partnumber.extend(partnumber)
            else: self.partnumber.append(partnumber)
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
        def add(self, designator, kind, partnumber, parametric, description, package, manufacturer, quantity = 1, note = '', flag = None):
            if flag == None: flag = ComponentList.FlagType.NONE
            if flag > self.flag: self.flag = flag

            if len(designator) > 0:
                if designator in self.designator:
                    #если десигнатор не пустой и такой уже есть то что-то пошло не так
                    if self.flag < ComponentList.FlagType.ERROR: self.flag = ComponentList.FlagType.ERROR
                self.designator.append(designator)

            if kind not in self.kind:
                if self.flag < ComponentList.FlagType.WARNING: self.flag = ComponentList.FlagType.WARNING     #если поля не совпадают то это подозрительно
                self.kind.append(kind)

            if partnumber not in self.partnumber:
                if self.flag < ComponentList.FlagType.WARNING: self.flag = ComponentList.FlagType.WARNING
                self.partnumber.append(partnumber)

            if parametric != self.parametric:
                #если флаг явного артикула не совпадает с уже существующим то что-то пошло не так
                if self.flag < ComponentList.FlagType.ERROR: self.flag = ComponentList.FlagType.ERROR

            if description not in self.description:
                if self.flag < ComponentList.FlagType.WARNING: self.flag = ComponentList.FlagType.WARNING
                self.description.append(description)

            if package not in self.package:
                if self.flag < ComponentList.FlagType.WARNING: self.flag = ComponentList.FlagType.WARNING
                self.package.append(package)

            if manufacturer not in self.manufacturer:
                if self.flag < ComponentList.FlagType.WARNING: self.flag = ComponentList.FlagType.WARNING
                self.manufacturer.append(manufacturer)

            self.quantity += quantity

            if note not in self.note:
                #if self.flag < ComponentList.FlagType.WARNING: self.flag = ComponentList.FlagType.WARNING
                self.note.append(note)

        #проверяет текущую запись на ошибки
        def check(self):
            #десигнатор
            if len(self.designator) != len(set(self.designator)):   #проверяем есть ли дубликаты
                if self.flag < ComponentList.FlagType.ERROR: self.flag = ComponentList.FlagType.ERROR
            #тип
            if len(self.kind) > 1:
                if self.flag < ComponentList.FlagType.WARNING: self.flag = ComponentList.FlagType.WARNING
            #номинал
            if len(self.partnumber) > 1:
                if self.flag < ComponentList.FlagType.ERROR: self.flag = ComponentList.FlagType.ERROR
            #описание
            if len(self.description) > 1:
                if self.flag < ComponentList.FlagType.WARNING: self.flag = ComponentList.FlagType.WARNING
            #корпус
            if len(self.package) > 1:
                if self.flag < ComponentList.FlagType.WARNING: self.flag = ComponentList.FlagType.WARNING
            #производитель
            if len(self.manufacturer) > 1:
                if self.flag < ComponentList.FlagType.WARNING: self.flag = ComponentList.FlagType.WARNING
            #количество
            if self.quantity < 0:
                if self.flag < ComponentList.FlagType.ERROR: self.flag = ComponentList.FlagType.ERROR
            #примечание
            if len(self.note) > 1:
                pass #if self.flag < ComponentList.FlagType.WARNING: self.flag = ComponentList.FlagType.WARNING

        #проверяет является ли запись пустой
        def isempty(self):
            attributes = [self.designator, self.kind, self.partnumber, self.description, self.package, self.manufacturer, self.note]
            for attribute in attributes:
                if attribute is not None and len(attribute) > 0:
                    for item in attribute:
                        if item is not None and len(item) > 0:
                            return False
            if self.quantity != 0:
                return False
            return True

    class SubstituteEntry():
        def __init__(self, primary_partnumber = None, primary_manufacturer = None, primary_quantity = 0, substitute_group = None, flag = None):
            self.primary_partnumber   = primary_partnumber
            self.primary_manufacturer = primary_manufacturer
            self.primary_quantity     = int(primary_quantity)
            self.substitute_group     = substitute_group
            self.flag                 = ComponentList.FlagType.NONE
            if flag is not None: self.flag = flag

        class SubstituteGroup():
            def __init__(self, designator = None, quantity = 0, substitute = None, flag = None):
                self.designator = designator
                self.quantity   = int(quantity)
                self.substitute = substitute
                self.flag       = ComponentList.FlagType.NONE
                if flag is not None: self.flag = flag

            class Substitute():
                def __init__(self, partnumber = None, manufacturer = None, note = None):
                    self.partnumber   = partnumber      #номинал
                    self.manufacturer = manufacturer    #производитель
                    self.note         = note            #примечание
                    self.flag         = ComponentList.FlagType.NONE
