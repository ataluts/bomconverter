#Класс спецификации
class SP():
    def __init__(self):
        self.titleblock = None
        self.entries    = []

    #запись элемента в спецификации
    class entry():
        def __init__(self, designator = '', label = '', quantity = 0):
            self.designator        = [designator]   #список десигнаторов
            self.label             = label
            self.quantity          = int(quantity)

        def add(self, designator, quantity = 1):
            self.designator.append(designator)
            self.quantity += quantity
