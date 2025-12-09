import re
from copy import copy

class Designator():
    def __init__(self, full = "", prefix = None, index = None, number = 0, channel = None):
        self.full    = full     #полный
        self.name    = ""       #базовый (префикс + индекс)
        self.prefix  = prefix   #префикс
        self.index   = index    #индекс (строковой)
        self.number  = number   #номер (числовой)
        self.channel = channel  #канал
        if prefix is not None and index is not None:
            self.name = str(prefix) + str(index)

    def __eq__(self, other):
        if not isinstance(other, Designator):
            return NotImplemented
        return self.full == other.full

    def __str__(self):
        return self.full

    class Channel():
        def __init__(self, full = "", prefix = None, index = None, number = 0, enclosure = None):
            self.full       = full      #полное название канала
            self.name       = ""        #базовое название канала (префикс + индекс)
            self.prefix     = prefix    #префикс
            self.index      = index     #индекс (строковой)
            self.number     = number    #номер (числовой)
            self.enclosure  = ["", ""]  #обрамление канала
            if enclosure is not None: self.enclosure = copy(enclosure)
            if prefix is not None and index is not None: self.name = str(prefix) + str(index)

        #проверяет канал на целостность
        def check(self):
            if self.full != str(self.enclosure[0]) + str(self.prefix) + str(self.index) + str(self.enclosure[1]) or \
                self.name != str(self.prefix) + str(self.index) or \
                self.number <= 0:
                return False
            return True

        #ключ сортировки
        def _cmpkey(self):
            return (self.prefix, self.number)

    #разбирает десигнатор на составляющие
    def parse(str_des):
        #разделяем десигнатор на префикс (заглавные латинские буквы), индекс (число) и канал (всё остальное)
        match = re.match(r"^([A-Z]+)(\d+)(.*)$", str_des)
        if match: 
            prefix, index, channel = match.groups()
            #преобразуем индекс десигнатора в числовой
            if index.isdigit():
                number = int(index)
            else:
                number = 0
            if len(channel) > 0:
                #канал не пустой, разделяем его на индекс (либо 1 или 2 латинские заглавные буквы либо число), начальное обрамление (всё до индекса) и конечное обрамление (непрерывные не буквенно-цифровые символы в конце)
                match = re.match(r"^(.*?)([A-Z]{1,2}|\d+)([^A-Za-z\d]*)$", channel)
                if match:
                    channel_prefix, channel_index, channel_enclosure_end, = match.groups()
                    #выделяем из префикса начальное обрамление (непрерывные не буквенно-цифровые символы в начале) и оставляем в нём всё остальное
                    match = re.match(r"^([^A-Za-z\d]*)(.*)$", channel_prefix)
                    if match:
                        channel_enclosure_start, channel_prefix = match.groups()
                    else:
                        channel_enclosure_start = ""
                    #преобразуем индекс канала в числовой
                    if channel_index.isdigit():
                        channel_number = int(channel_index)
                    elif channel_index.isalpha() and channel_index.isupper() and len(channel_index) <= 2:
                        channel_number = 0
                        for char in channel_index:
                            channel_number = channel_number * 26 + (ord(char) - ord('A') + 1)
                    else:
                        channel_number = 0
                    #создаём канал
                    channel = Designator.Channel(channel, channel_prefix, channel_index, channel_number, [channel_enclosure_start, channel_enclosure_end])
                else:
                    channel = None
            else:
                channel = None
            return Designator(str_des, prefix, index, number, channel)
        else:
            return None

    #проверяет десигнатор на целостность
    def check(self):
        if self.name != str(self.prefix) + str(self.index): return False
        if self.index.isdigit():
            if int(self.index) != self.number: return False
        else:
            return False
        if self.channel is None:
            if self.full != self.name: return False
        else:
            if not self.channel.check(): return False
            if self.full != str(self.name) + str(self.channel.full): return False
        return True

    #ключ сортировки
    def _cmpkey(self):
        key = (self.prefix, self.number)
        if self.channel is not None: key += self.channel._cmpkey()
        return key