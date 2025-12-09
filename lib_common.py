import sys
import re
from pathlib import Path
import types
import collections.abc

_module_dirname   = Path(__file__).parent
_default_parser   = Path("parse_taluts.py")
_default_settings = Path("dict_settings.py")

#Ensures sys.stdout and sys.stderr use UTF-8 encoding with safe wrapping, avoiding double-wrapping or breaking the buffer.
def wrap_stdout_utf8():
    import io
    def wrap(stream):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
                return stream
            except Exception:
                pass
        if isinstance(stream, io.TextIOWrapper) and hasattr(stream, "buffer"):
            try:
                return io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace")
            except Exception:
                pass
        return stream  # fallback to original if all else fails

    sys.stdout = wrap(sys.stdout)
    sys.stderr = wrap(sys.stderr)

#Импортирует словарь
def import_dictionary(dictionary:str|Path|types.ModuleType|dict, verbose = False):
    if dictionary is None:
        if verbose: print("nothing to import.")
        return None
    if isinstance(dictionary, dict):
        #на входе сразу словарь -> его и возвращаем
        if verbose: print(f"ok, already in dictionary ({len(dictionary)} entries).")
        return dictionary 
    elif isinstance(dictionary, types.ModuleType):
        #на входе модуль -> возвращаем словарь из него
        if verbose: print("extracting data", end ="... ")
        if isinstance(dictionary.data, dict):
            if verbose: print("ok.")
            return dictionary.data
        else:
            if verbose: print("error! data is not a dictionary.")
            raise ValueError
    elif isinstance(dictionary, (str, Path)):
        #на входе строка или путь -> загружаем модуль по пути файла
        if isinstance(dictionary, str):
            dictionary = Path(dictionary)
        if verbose: print(f"from file '{dictionary.name}'", end ="... ")
        path = _module_dirname / dictionary
        if path.exists():
            name = path.stem
            import importlib.util
            spec = importlib.util.spec_from_file_location(name, path)
            dictionary = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(dictionary)
            if verbose: print("module loaded, extracting data", end ="... ")
            if isinstance(dictionary.data, dict):
                if verbose: print(f"done ({len(dictionary.data)} entries).")
                return dictionary.data
            else:
                if verbose: print("error! data is not a dictionary.")
                raise ValueError
        else:
            if verbose: print("error! file doesn't exist.")
            raise FileExistsError
    else:
        if verbose: print("error! invalid input.")
        raise ValueError

#Импортирует анализатор данных
def import_parser(parser:str|Path|types.ModuleType):
    print("INFO >> Importing designer's parser", end ="... ")
    if parser is None: parser = _default_parser
    if isinstance(parser, str): parser = Path(parser)
    if isinstance(parser, types.ModuleType):
        #на входе сразу модуль -> его и возвращаем
        print("ok, already imported.")
        return parser
    elif isinstance(parser, Path):
        ##на входе путь -> загружаем модуль по пути файла
        print(f"from file '{parser}'", end ="... ")
        path = _module_dirname / parser
        if path.exists():
            name = path.stem
            import importlib.util
            spec = importlib.util.spec_from_file_location(name, path)
            parser = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(parser)
            print("ok.")
            return parser
        else:
            print("error! file doesn't exist.")
            raise FileExistsError
    else:
        print("error! invalid input.")
        raise ValueError

#Импортирует данные основной надписи
def import_titleblock(titleblock:str|Path|dict):
    print("INFO >> Importing titleblock data", end ="... ")
    return import_dictionary(titleblock, True)

#Импортирует настройки
def import_settings(settings:str|Path|types.ModuleType|dict):
    if settings is None: settings = _default_settings
    print("INFO >> Importing settings", end ="... ")
    return import_dictionary(settings, True)
    
#Обновляет вложенные словари
def dict_nested_update(source:dict, update:dict):
    for key, value in update.items():
        if isinstance(value, collections.abc.Mapping):
            source[key] = dict_nested_update(source.get(key, {}), value)
        else:
            if source is None: source = {}
            source[key] = value
    return source

#Возвращает ключ словаря при совпадении значения
def dict_translate(value, dictionary:dict, case_sensitive:bool = True, reverse:bool = False, fallback = None):
    def match_value(value, item) -> bool:
        if isinstance(item, re.Pattern):
            if not case_sensitive:
                item = re.compile(item.pattern, re.IGNORECASE)
            if item.search(value) is not None: return True
            else: return False
        elif isinstance(value, str) and isinstance(item, str):
            if case_sensitive: return value == item
            else: return value.casefold() == item.casefold()
        else:
            return value == item

    if reverse: dictionary = dict(reversed(list(dictionary.items())))
    
    for key, entry in dictionary.items():
        if isinstance(entry, (list, tuple)):
            for item in entry:
                if match_value(value, item): return key
        else:
            if match_value(value, entry): return key

    return fallback