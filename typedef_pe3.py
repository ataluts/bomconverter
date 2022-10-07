from enum import IntEnum

#Класс перечня элементов
class PE3_typeDef():
    def __init__(self):
        self.titleBlock = None
        self.entries    = []
        self.groups     = []
        self.rows       = []

    #запись элемента в перечне
    class entry():
        def __init__(self, designator = '', prefix = '', index = '', label = '', quantity = 0, annotation = ''):
            self.designators       = [designator]   #список десигнаторов
            self.prefix            = prefix         #префикс элементов
            self.indexes           = [index]        #список индексов элементов
            self.designatorsRange  = designator
            self.label             = label
            self.quantity          = int(quantity)
            self.annotation        = annotation


        def add(self, designator, index, delimiter, quantity = 1):
            self.designators.append(designator)
            self.indexes.append(index)
            self.quantity += quantity
            if len(self.designators) == 1:
                self.designatorsRange = self.designators[0]
            elif len(self.designators) == 2:
                self.designatorsRange = self.designators[0] + delimiter[0] + self.designators[1]
            elif len(self.designators) >= 3:
                self.designatorsRange = self.designators[0] + delimiter[1] + self.designators[-1]

    #группа элементов
    class group():
        def __init__(self, name = '', entry = None):
            self.name = name
            if entry == None: self.entries = []
            else:  self.entries = [entry]

        def add(self, entry):
            self.entries.append(entry)

    #строка таблицы перечня
    class row():
        def __init__(self, designator = '', label = '', quantity = '', annotation = '', flag = None):
            self.designator = designator
            self.label      = label
            self.quantity   = quantity
            self.annotation = annotation
            if flag == None: self.flag = self.__class__.FlagType.SPACER
            else:            self.flag = flag

        class FlagType(IntEnum):
            SPACER = 0
            ITEM   = 1
            TITLE  = 2