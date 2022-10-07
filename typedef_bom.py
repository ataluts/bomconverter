#Bill of materials
class BoM_typeDef():
    def __init__(self, prefix = '', postfix = ''):
        self.prefix      = prefix
        self.postfix     = postfix
        self.fieldNames  = []
        self.entries     = []