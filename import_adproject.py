import os
import olefile
import configparser

script_dirName  = os.path.dirname(__file__)                                                     #адрес папки со скриптом
script_baseName = os.path.splitext(os.path.basename(__file__))[0]                               #базовое имя модуля

#Проект Altium Designer
class ADProject_typeDef():
    def __init__(self):
        self.address = ''
        self.directory = ''
        self.config = None      #configparcer object with all project file data

        self.sourceFiles = []
        self.generatedFiles = []
        self.SchDocs = []
        self.BoMs = []
        self.BoMVariantNames = []

        self.designator = ''
        self.name = ''
        self.author = ''
        self.titleblock = {}


#Схемный файл Altium Designer
class SchDoc_typeDef():
    def __init__(self, address = '', **kwargs):
        self.address = address
        self.lines = []

    #читает данные из файла
    def read(self, **kwargs):
        file_encoding = kwargs.get('encoding', 'cp1251')
        casefold_keys = kwargs.get('casefold_keys', False)   #с какой-то версии Altium после 17 имена полей стали в CamelCase вместо UPPERCASE, поэтому делаем возможность casefold для ключей

        #читаем данные из файла    
        if os.path.isfile(self.address) and olefile.isOleFile(self.address):
            with olefile.OleFileIO(self.address) as SchDocFile:
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

#Импортирует Altium Designer project
def importz(address, **kwargs):
    print('INFO >> ADProject importing module running with parameters:')
    print(' ' * 12 + 'input: ' +  os.path.basename(address))

    #создаём объект проекта
    ADProject = ADProject_typeDef()
    ADProject.address = address
    ADProject.directory = os.path.dirname(ADProject.address)

    #читаем данные из файла
    print('INFO >> Reading data from PrjPcb file', end ="... ", flush = True)
    if os.path.isfile(ADProject.address):
        #где-то после 17 версии Altium стали добавлять лишние символы перед основным содержимым файла проекта, поэтому просто так открыть его через configparser стало нельзя
        
        #открываем файл и читаем весь текст из него
        with open(ADProject.address) as file:
            contents = file.read()

        #проверяем нормальный файл или с приколюхами
        if contents[0:8] != '[Design]':
            #либо файл вообще левый либо с приколюхами, пытаемся убирать приколюхи пока не найдём начало конфигурации (до определённого предела)
            for i in range(8):
                contents = contents[1:]
                if contents[0:8] == '[Design]': break
            else:
                print("error: can't parse file")
                raise Exception

        #читаем конфиг
        ADProject.config = configparser.ConfigParser()
        ADProject.config.read_string(contents)
        config_sections = ADProject.config.sections()

        #получаем список документов
        docIndex = 1
        genIndex = 1
        for section in config_sections:
            if 'Document' + str(docIndex) in config_sections:
                ADProject.sourceFiles.append(ADProject.config['Document' + str(docIndex)]['DocumentPath'])
                docIndex += 1
                if os.path.splitext(ADProject.sourceFiles[-1])[1] == ".SchDoc":
                    ADProject.SchDocs.append(SchDoc_typeDef(os.path.join(ADProject.directory, ADProject.sourceFiles[-1])))
            elif 'GeneratedDocument' + str(genIndex) in config_sections:
                ADProject.generatedFiles.append(ADProject.config['GeneratedDocument' + str(genIndex)]['DocumentPath'])
                genIndex += 1

        print('done. (' + str(len(ADProject.sourceFiles)) + ' source files, ' + str(len(ADProject.generatedFiles)) + ' generated files)')
    else:
        print("error: file doesn't exist")
        raise Exception

    print('INFO >> ADProject import finished.')  
    return ADProject