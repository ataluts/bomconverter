import copy

#Bill of materials
class BoM():
    def __init__(self, title = None, fields = None):
        #название
        self.title = title
        #названия полей
        if fields is not None:
            if isinstance(fields, list):
                self.fields = copy.deepcopy(fields)
            elif isinstance(fields, tuple):
                self.fields = list(fields)
            else:
                raise ValueError("Unsupported type for BoM field names")
        else:
            self.fields = []
        #записи
        self.entries = []

    class Entry():
        bom   = None
        value = None
        def __init__(self, bom, entry_value, strict = True, default_item_value = None):
            if isinstance(bom, BoM):
                self.bom = bom
            else:
                raise ValueError("Entry must be tied to a BoM.")

            if isinstance(entry_value, (list, tuple)):
                if len(entry_value) == len(self.bom.fields):
                    self.value = copy.deepcopy(entry_value)
                elif strict:
                    raise ValueError("BoM entry value length and fields length mismatch.")
                elif len(entry_value) > len(self.bom.fields):
                    self.value = entry_value[:len(self.bom.fields)]
                elif len(entry_value) < len(self.bom.fields):
                    self.value = copy.deepcopy(entry_value)
                    self.value.extend([default_item_value] * (len(self.bom.fields) - len(self.value)))
            elif isinstance(entry_value, dict):
                tmp_value = [default_item_value] * len(self.bom.fields)
                if strict and len(entry_value) != len(self.bom.fields):
                    raise ValueError("BoM entry value length and fields length mismatch.")
                else:
                    for key, item_value in entry_value.items():
                        if key in self.bom.fields:
                            field_index = self.bom.fields.index(key)
                            tmp_value[field_index] = item_value
                        elif strict:
                            raise ValueError("Dict key is not in field names.")
                    self.value = tmp_value
            else:
                raise ValueError("Unsupported type for BoM entry value.")

        #Возвращает значение записи в виде списка
        def to_list(self):
            return self.value

        #Возвращает значение записи в виде словаря
        def to_dict(self):
            dictionary = {}
            for index, field in enumerate(self.bom.fields):
                dictionary[field] = self.value[index]
            return dictionary
    
    #Возвращает значение поля для записи
    def get_entry_field_value(self, entry_index, field, value_in_not_exist = None):
        if field in self.fields:
            field_index = self.fields.index(field)
            return self.entries[entry_index].value[field_index]
        else:
            return value_in_not_exist

    #Вставляет запись в BoM
    def insert_entry(self, entry_value, index = -1,  strict = True, default_item_value = None):
        entry = self.Entry(self, entry_value, strict, default_item_value)
        if index > len(self.entries): index = len(self.entries)
        elif index < -len(self.entries): index = 0
        elif index < 0: index = len(self.entries) + index + 1
        self.entries.insert(index, entry)
        return entry
    
    #Вставляет поле в BoM
    def insert_field(self, field, index = -1, default_item_value = None):
        #нормализуем индекс
        if index > len(self.fields): index = len(self.fields)
        elif index < -len(self.fields): index = 0
        elif index < 0: index = len(self.fields) + index + 1
        #добавляем имя в список полей
        self.fields.insert(index, field)
        #добавляем поле в словари записей
        for entry in self.entries:
            entry.value.insert(index, default_item_value) 

    #Вставляет поля в BoM
    def insert_fields(self, fields, index = -1, default_item_value = None):
        if index > len(self.fields): index = len(self.fields)
        elif index < -len(self.fields): index = 0
        elif index < 0: index = len(self.fields) + index + 1
        for field in fields:
            self.insert_field(field, index, default_item_value)
            index += 1

    #Удаляет поле из BoM
    def remove_field(self, field):
        if field in self.fields:
            field_index = self.fields.index(field)
            self.fields.pop(field_index)
            for entry in self.entries:
                entry.value.pop(field_index)

    #Удаляет поля из BoM
    def remove_fields(self, fields):
        for field in fields:
            self.remove_field(field)

    #Переименовывает поле в BoM
    def rename_field(self, field, new_name):
        if field in self.fields:
            field_index = self.fields.index(field)
            self.fields[field_index] = new_name