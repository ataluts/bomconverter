from enum import IntEnum
import copy

#Класс перечня элементов
class PE3():
    def __init__(self):
        self.titleblock = {}
        self.elements   = []
        self.entries    = []
        self.groups     = []
        self.rows       = []

    #компонент в перечне
    class Element():
        def __init__(self, designator, value, quantity):
            self.designator = copy.deepcopy(designator) #десигнатор
            self.dominant   = None                      #основное значение (имеется если нет вариаций или есть доминирующая вариация, иначе пусто)
            self.variants   = []                        #вариации отличающиеся от основной (отсортированные по количеству каналов в них, сначала наибольшее)
            self.add_channel(self.designator.channel, value, quantity)
            self.designator.full = self.designator.name
            self.designator.channel = None

        class Variant():
            def __init__(self, channel, value, quantity):
                self.value      = value          #значение
                self.quantity   = int(quantity)  #общее количество
                self.quantities = []             #количество по каналам
                self.channels   = []             #список каналов
                self.channels.append(channel)
                self.quantities.append(self.quantity)

        class Value():
            def __init__(self, label, annotation):
                self.label      = label       #наименование
                self.annotation = annotation  #примечание

            def match(self, other):
                if not isinstance(other, self.__class__): return False
                if self.label != other.label or self.annotation != other.annotation: return False
                return True

        #добавляет канал в базовый компонент перечня
        def add_channel(self, channel, value, quantity):
            if self.dominant is None and len(self.variants) == 0:
                #компонент пустой и добавляется первое значение -> записываем значение как основное
                self.dominant = self.Variant(channel, value, quantity)                
            elif self.dominant is not None and value.match(self.dominant.value):
                #компонент имеет основное значение и добавляемое значение равно ему -> добавляем значение в основное
                self.dominant.channels.append(channel)
                self.dominant.quantities.append(int(quantity))
                self.dominant.quantity += self.dominant.quantities[-1]
            elif self.dominant is not None and len(self.variants) == 0:
                #вариаций нет и добавляемое значение не равно основному -> создаём новую вариацию
                if len(self.dominant.channels) == 1:
                    #в основном значении всего один канал -> перемещаем это значение в вариации
                    self.variants.append(self.dominant)
                    self.dominant = None
                self.variants.append(self.Variant(channel, value, quantity))
            else:
                #добавляемое значение не равно основному -> добавляем его в вариации
                for variant in self.variants:
                    if value.match(variant.value):
                        #добавляемое значение равно вариации -> добавляем его к найденной вариации
                        variant.channels.append(channel)
                        variant.quantities.append(int(quantity))
                        variant.quantity += variant.quantities[-1]
                        if self.dominant is None or len(variant.channels) > len(self.dominant.channels):
                            #основного значения либо нет либо вариация стала многочисленнее его -> перемещаем текущую вариацию в основное значение, а если основное значение было то ставим его в начало вариаций
                            if self.dominant is not None: self.variants.insert(0, self.dominant)
                            self.dominant = variant
                            self.variants.remove(variant)
                        break
                else:
                    #добавляемое значение новое -> создаём новую вариацию
                    self.variants.append(self.Variant(channel, value, quantity))

        #сортировка вариантов (по количеству каналов, наибольший в начале)
        def sort_variants(self):
            self.variants.sort(key=lambda variant: len(variant.channels), reverse=True)

        #ключ сортировки
        def _cmpkey(self):
            #сортируем по десигнатору, а если его нет (аксессуар) то по значению
            if self.designator.prefix is None:
                return ("\ufffd", self.dominant.value.label, self.dominant.value.annotation)
            return self.designator._cmpkey()

    #запись в перечне
    class Entry():
        def __init__(self, prefix, local_number, value = None):
            self.prefix        = prefix               #префикс
            self.local_numbers = [int(local_number)]  #список локальных номеров (числовых индексов для префикса)
            self.designators   = []                   #список десигнаторов (текстовых)
            self.baseline      = value                #базовое значение
            self.deviations    = []                   #список исключений
            if self.baseline is not None: self.designators.append(value.designator)

        class Value():
            def __init__(self, designator, label, quantity, annotation):
                self.designator = designator        #десигнатор (текстовый)
                self.label      = label             #наименование
                self.quantity   = int(quantity)     #количество (числовое)
                self.annotation = annotation        #примечание

            def match(self, other):
                if not isinstance(other, self.__class__): return False
                if self.label != other.label or self.annotation != other.annotation: return False
                return True

        class Deviation():
            def __init__(self, local_number, channel_number, value):
                self.local_number    = int(local_number)        #локальный номер основного элемента (числового индекса для префикса)
                self.channel_numbers = [int(channel_number)]    #список номеров каналов
                self.designators     = []                       #список десигнаторов (текстовых)
                self.value           = value                    #значение
                if self.value is not None: self.designators.append(value.designator)

            #добавляет значение в исключение
            def add_value(self, channel_number, value, delimiter):
                self._add_value(channel_number, value, self.value, self.channel_numbers, self.designators, delimiter)

            #добавляет значение к уже существующему
            @staticmethod
            def _add_value(number, value, target, numbers, designators, delimiter):
                if value is not None:
                    if value.label == target.label and value.annotation == target.annotation:
                        numbers.append(number)
                        designators.append(value.designator)
                        target.quantity += value.quantity
                        if len(designators) == 2:
                            target.designator = designators[0] + delimiter[0] + designators[1]
                            if target.designator == delimiter[0]: target.designator = ""
                        elif len(designators) >= 3:
                            target.designator = designators[0] + delimiter[1] + designators[-1]
                            if target.designator == delimiter[1]: target.designator = ""
                    else:
                        raise ValueError(f"{value.designator} label and/or annotation doesn't match target value!")

        #добавляет значение в базовое значение
        def add_value(self, local_number, value, delimiter):
            self.Deviation._add_value(local_number, value, self.baseline, self.local_numbers, self.designators, delimiter)

        #добавляет исключение
        def add_deviations(self, deviation):
            if isinstance(deviation, (tuple, list)):
                self.deviations.extend(deviation)
            else:
                self.deviations.append(deviation)

    #группа элементов
    class Group():
        def __init__(self, name = '', entry = None):
            self.name = name
            self.entries = []
            if entry is not  None: self.entries.append(entry)

        def add(self, entry):
            self.entries.append(entry)

    #строка таблицы перечня
    class Row():
        def __init__(self, designator = '', label = '', quantity = '', annotation = '', flag = None):
            self.designator = designator
            self.label      = label
            self.quantity   = quantity
            self.annotation = annotation
            if flag is None: self.flag = self.__class__.FlagType.SPACER
            else:            self.flag = flag

        class FlagType(IntEnum):
            SPACER = 0
            ITEM   = 1
            TITLE  = 2