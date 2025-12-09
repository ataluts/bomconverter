import os
from pathlib import Path
import math

import dict_locale as lcl
import lib_common

_module_dirname  = Path(__file__).parent                                                                    #адрес папки со скриптом
_module_basename = Path(__file__).stem                                                                      #базовое имя модуля
dictionary_path = _module_dirname / Path(_module_basename.replace('optimize', 'dict') + os.extsep + 'py')   #адрес словаря

#Оптимизирует посадочные места для установщика компонентов
def optimize(data, **kwargs):
    print('INFO >> PnP footprints optimizer module running.')
    
    #локализация
    locale = kwargs.get('locale', lcl.Locale.EN)

    #параметры
    dictionary = kwargs.get('dictionary', dictionary_path)
    case_sensitive = kwargs.get('caseSensitive', False)
    none_group_disable = kwargs.get('NoneGroupDisable', True)

    #получаем данные из словаря
    print("INFO >> Importing dictionary", end ="... ")
    dictionary = lib_common.import_dictionary(dictionary, True)

    #разворачиваем данные
    pnp = data

    #заменяем название посадочных мест по словарю
    print('INFO >> Translating footprints', end ="... ", flush = True)
    stats_disabled = 0
    stats_replaced = 0
    NOTFOUND = object()
    for entry in pnp.entries:
        if entry.footprint is not None:
            result = lib_common.dict_translate(entry.footprint, dictionary, case_sensitive, False, NOTFOUND)
            if result is NOTFOUND:
                #посадочное не найдено в словаре -> оставляем как есть
                pass
            elif result is None and none_group_disable:
                #посадочное в группе None и есть флаг отключения -> отключаем запись
                entry.state.disable(locale.translate(lcl.optimize_pnp_fp.DISABLE_REASON))
                stats_disabled += 1
            else:
                #получили новое значение из словаря
                if isinstance(result, tuple):
                    #кортеж -> значит есть смещения которые надо применить
                    if 0 < len(result) <= 5:
                        entry.footprint = result[0]
                        if len(result) >= 2:
                            if len(result) >= 4:
                                offset_rotate = True
                                if len(result) >= 5: offset_rotate = bool(result[4])
                                if offset_rotate: angle = math.radians(entry.rotation)
                                else:             angle = 0
                                entry.location[0] += result[2] * math.cos(angle) - result[3] * math.sin(angle)
                                entry.location[1] += result[2] * math.sin(angle) + result[3] * math.cos(angle)
                            entry.rotation = (entry.rotation + result[1]) % 360
                            if entry.rotation < 0: entry.rotation += 360
                    else:
                        raise ValueError("Invalid dictionary key data size")
                else:
                    #простое значение -> просто заменяем значение
                    entry.footprint = result
                stats_replaced += 1

    print(f"done. ({stats_replaced} replaced, {stats_disabled} disabled)")

    print("INFO >> PnP footprints optimization completed.") 
    return True