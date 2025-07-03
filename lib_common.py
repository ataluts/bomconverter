import sys
import os
import types
import collections.abc

_module_dirname = os.path.dirname(__file__)                     #адрес папки со скриптом
_default_parser   = "parse_taluts.py"
_default_settings = "dict_settings.py"

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

#Импортирует анализатор данных
def import_parser(parser):
    print("INFO >> Importing designer's parser", end ="... ")
    if parser is None: parser = _default_parser
    if isinstance(parser, types.ModuleType):
        #на входе сразу модуль -> его и возвращаем
        print("ok, already imported.")
        return parser
    elif isinstance(parser, str):
        #на входе строка -> загружаем модуль по адресу в ней
        print(f"from file '{parser}'", end ="... ")
        path = os.path.join(_module_dirname, parser)
        if os.path.exists(path):
            name = os.path.splitext(os.path.basename(path))[0]
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
def import_titleblock(titleblock):
    print("INFO >> Importing titleblock data", end ="... ")
    if titleblock is None:
        print("nothing to import.")
        return None
    if isinstance(titleblock, dict):
        #на входе сразу словарь -> его и возвращаем
        print(f"ok, already in dictionary ({len(titleblock)} entries).")
        return titleblock
    elif isinstance(titleblock, str):
        #на входе строка -> загружаем модуль по адресу в ней
        print(f"from file '{titleblock}'", end ="... ")
        path = os.path.join(_module_dirname, titleblock)
        if os.path.exists(path):
            name = os.path.splitext(os.path.basename(path))[0]
            import importlib.util
            spec = importlib.util.spec_from_file_location(name, path)
            titleblock = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(titleblock)
            dictionary = titleblock.data
            print(f"done ({len(dictionary)} entries).")
            return dictionary
        else:
            print("error! file doesn't exist.")
            raise FileExistsError
    else:
        print("error! invalid input.")
        raise ValueError

#Импортирует настройки
def import_settings(settings):
    print("INFO >> Importing settings", end ="... ")
    if settings is None: settings = _default_settings
    if isinstance(settings, dict):
        #на входе сразу словарь -> его и возвращаем
        print("ok, already imported.")
        return settings
    elif isinstance(settings, types.ModuleType):
        #на входе модуль -> возвращаем словарь из него
        print("extracting data", end ="... ")
        if isinstance(settings.data, dict):
            print("ok.")
            return settings.data
        else:
            print("error! data is not a dictionary.")
            raise ValueError
    elif isinstance(settings, str):
        #на входе строка -> загружаем модуль по адресу в ней
        print(f"from file '{settings}'", end ="... ")
        path = os.path.join(_module_dirname, settings)
        if os.path.exists(path):
            name = os.path.splitext(os.path.basename(path))[0]
            import importlib.util
            spec = importlib.util.spec_from_file_location(name, path)
            settings = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(settings)
            print("module loaded, extracting data", end ="... ")
            if isinstance(settings.data, dict):
                print("ok.")
                return settings.data
            else:
                print("error! data is not a dictionary.")
                raise ValueError
        else:
            print("error! file doesn't exist.")
            raise FileExistsError
    else:
        print("error! invalid input.")
        raise ValueError
    
#Обновляет вложенные словари
def dict_nested_update(source, update):
    for key, value in update.items():
        if isinstance(value, collections.abc.Mapping):
            source[key] = dict_nested_update(source.get(key, {}), value)
        else:
            if source is None: source = {}
            source[key] = value
    return source