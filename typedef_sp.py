#Класс спецификации
class SP_typeDef():
    def __init__(self):
        self.titleBlock = None
        self.entries    = []

    #запись элемента в спецификации
    class entry():
        def __init__(self, designator = '', label = '', quantity = 0, annotation = ''):
            self.designator        = [designator]   #список десигнаторов
            self.label             = label
            self.quantity          = int(quantity)
            self.annotation        = annotation

        def add(self, designator, quantity = 1):
            self.designator.append(designator)
            self.quantity += quantity
