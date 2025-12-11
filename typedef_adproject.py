import olefile
import locale
import configparser
from pathlib import Path

script_dirName  = Path(__file__).parent     #адрес папки со скриптом
script_baseName = Path(__file__).stem       #базовое имя модуля

#Проект Altium Designer
class ADProject():
    def __init__(self, address:Path = None):
        self.address = address
        if self.address is not None: self.directory = self.address.parent
        else: self.directory = None
        self.config = None      #configparcer object with all project file data

        self.sourceFiles = []
        self.generatedFiles = []
        self.variants = []
        self.SchDoc = []
        self.PcbDoc = []
        self.BoMDoc = []
        self.PnPDoc = []

        self.designator = None
        self.name = None
        self.author = None
        self.titleblock = None

    #читает файл проекта Altium Designer
    def read(self, **kwargs) -> None:
        #параметры
        max_data_offset = kwargs.get('maxDataOffset',  8)
        file_encoding   = kwargs.get('encoding',  ('utf-8-sig', locale.getpreferredencoding(False)))
        if not isinstance(file_encoding, (list, tuple)): file_encoding = (file_encoding)

        #читаем данные из файла
        if self.address.is_file():
            #открываем файл и читаем весь текст из него перебирая кодировки (в старых версиях AD системная кодировка, в новых UTF-8 с сигнатурой)
            for encoding in file_encoding:
                try:
                    with open(self.address, 'r', encoding=encoding) as file:
                        contents = file.read()
                except UnicodeDecodeError:
                    continue
                break
            else:
                raise Exception("Can't read AD project file - unknown encoding")
            
            #читаем конфиг
            self.config = configparser.ConfigParser()
            self.config.read_string(contents)
            config_sections = self.config.sections()

            #получаем список документов
            document_index = 1
            variant_index = 1
            generated_index = 1
            for section in config_sections:
                if f"Document{document_index}" in config_sections:
                    self.sourceFiles.append(Path(self.config[f"Document{document_index}"]['DocumentPath']))
                    document_index += 1
                    if self.sourceFiles[-1].suffix == ".SchDoc":
                        self.SchDoc.append(SchDoc(self.sourceFiles[-1], self))
                    elif self.sourceFiles[-1].suffix == ".PcbDoc":
                        self.PcbDoc.append(PcbDoc(self.sourceFiles[-1], self))
                elif f"ProjectVariant{variant_index}" in config_sections:
                    self.variants.append(self.config[f"ProjectVariant{variant_index}"]['Description'])
                    variant_index += 1
                elif f"GeneratedDocument{generated_index}" in config_sections:
                    self.generatedFiles.append(Path(self.config[f"GeneratedDocument{generated_index}"]['DocumentPath']))
                    generated_index += 1
        else:
            raise Exception("File doesn't exist")

#Схемный файл Altium Designer
class SchDoc():
    def __init__(self, address:Path = None, project:ADProject = None, **kwargs):
        self.address = address
        self.project = project
        self.lines = []

    #читает данные из файла
    def read(self, **kwargs) -> None:
        file_encoding = kwargs.get('encoding', 'cp1251')
        casefold_keys = kwargs.get('casefold_keys', False)   #с какой-то версии Altium после 17 имена полей стали в CamelCase вместо UPPERCASE, поэтому делаем возможность casefold для ключей

        #определяем абсолютный путь к файлу
        if self.project is not None:
            fullpath = self.project.directory / self.address
        else:
            fullpath = self.address

        #читаем данные из файла    
        if fullpath.is_file() and olefile.isOleFile(fullpath):
            with olefile.OleFileIO(fullpath) as SchDocFile:
                if SchDocFile.exists('FileHeader'):
                    schematic = SchDocFile.openstream('FileHeader')
                    data = schematic.read()
                    i = 0
                    while i < len(data):
                        #читаем строку из файла схемы
                        lineLength = int.from_bytes(data[i:i+3], byteorder='little', signed=False)
                        line = data[i+4:i+4+lineLength-1].decode(file_encoding, 'backslashreplace')

                        #преобразуем строку в словарь параметров
                        dictionary = {}
                        params = line.split('|')
                        for param in params:
                            if len(param) > 0:
                                values = param.split('=', 1)
                                if len(values) == 2:
                                    key = values[0]
                                    if casefold_keys: key = key.casefold()
                                    dictionary[key] = values[1]

                        #добавляем словарь в массив
                        self.lines.append(dictionary)
                        
                        i += lineLength + 4
                SchDocFile.close()

#Файл печатной платы Altium Designer
class PcbDoc():
    def __init__(self, address:Path = None, project:ADProject = None):
        self.address = address
        self.project = project

#Файл Bill of Materials
class BoMDoc():
    def __init__(self, address:Path = None, project:ADProject = None, variant:str = None, variant_enclosure:list[str, str] = None):
        self.address = address
        self.project = project
        self.variant = variant
        self.variant_enclosure = variant_enclosure

#Файл Pick and Place
class PnPDoc():
    def __init__(self, address:Path = None, project:ADProject = None, pcb:PcbDoc = None, variant:str = None, variant_enclosure:list[str, str] = None):
        self.address = address
        self.project = project
        self.PcbDoc  = pcb
        self.variant = variant
        self.variant_enclosure = variant_enclosure