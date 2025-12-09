from copy import deepcopy
from pathlib import Path

import dict_locale as lcl
import typedef_components as Components                             #класс базы данных компонентов
import typedef_pnp as PickPlace
import assemble                                                     #сборка ЕСКД значений

_module_dirname  = Path(__file__).parent     #адрес папки со скриптом
_module_basename = Path(__file__).stem       #базовое имя модуля

#Создаёт перечень элементов
def build(data, **kwargs):
    print('INFO >> pnp building module running.')

    #локализация
    locale = kwargs.get('locale', lcl.Locale.EN)

    #параметры
    sorting_method      = kwargs.get('sorting_method', None)
    sorting_reverse     = kwargs.get('sorting_reverse', False)
    disable_notbom      = kwargs.get('disable_notbom', False)
    disable_notfitted   = kwargs.get('disable_notfitted', True)
    disable_mount_smd         = kwargs.get('disable_mount_smd', False)
    disable_mount_semismd     = kwargs.get('disable_mount_semismd', False)
    disable_mount_throughhole = kwargs.get('disable_mount_throughhole', True)
    disable_mount_edge        = kwargs.get('disable_mount_edge', True)
    disable_mount_chassis     = kwargs.get('disable_mount_chassis', True)
    disable_mount_unknown     = kwargs.get('disable_mount_unknown', True)
    format_partnumber         = kwargs.get('format_partnumber', {})
    format_description        = kwargs.get('format_description', {})
    format_comment            = kwargs.get('format_comment', {})

    #разворачиваем данные
    if isinstance(data, (tuple, list)):
        #в данных компоненты и базовый файл установщика
        components = data[0]
        base_pnp   = data[1]
    else:
        #в данных непонятно что
        raise ValueError("Invalid input data")

    #создаём объект файла установщика
    new_pnp = deepcopy(base_pnp)

    print('INFO >> Processing base PnP entries', end ="... ", flush = True)
    if len(new_pnp.entries) > 0:
        #перебираем записи установщика
        for entry in new_pnp.entries:
            #перебираем компоненты
            for component in components.entries:
                #сравниваем десигнаторы
                if component.GNRC_designator == entry.designator:
                    #добавляем в запись установщика дополнительные данные о компоненте
                    if component.GNRC_mount is not None:
                        if   component.GNRC_mount == Components.MountType.SURFACE:      entry.mount = PickPlace.MountType.SURFACE
                        elif component.GNRC_mount == Components.MountType.SEMI_SURFACE: entry.mount = PickPlace.MountType.SEMI_SURFACE
                        elif component.GNRC_mount == Components.MountType.THROUGHHOLE:  entry.mount = PickPlace.MountType.THROUGHHOLE
                        elif component.GNRC_mount == Components.MountType.EDGE:         entry.mount = PickPlace.MountType.EDGE
                        elif component.GNRC_mount == Components.MountType.CHASSIS:      entry.mount = PickPlace.MountType.CHASSIS
                        else:                                                           entry.mount = PickPlace.MountType.UNKNOWN
                    entry.partnumber = assemble.assemble_pnp_partnumber(component, **format_partnumber)
                    entry.description = assemble.assemble_pnp_description(component, **format_description)
                    entry.comment = assemble.assemble_pnp_comment(component, **format_comment)
                    #отключаем ненужные записи, пропуская уже отключёные записи
                    if entry.state.enabled:
                        if not component.GNRC_fitted and disable_notfitted:
                            entry.state.disable(locale.translate(lcl.build_pnp.DISABLE_REASON_NOTFITTED))
                        elif entry.mount == PickPlace.MountType.SURFACE and disable_mount_smd:
                            entry.state.disable(locale.translate(lcl.build_pnp.DISABLE_REASON_MOUNT_SMD))
                        elif entry.mount == PickPlace.MountType.SEMI_SURFACE and disable_mount_semismd:
                            entry.state.disable(locale.translate(lcl.build_pnp.DISABLE_REASON_MOUNT_SEMISMD))
                        elif entry.mount == PickPlace.MountType.THROUGHHOLE and disable_mount_throughhole:
                            entry.state.disable(locale.translate(lcl.build_pnp.DISABLE_REASON_MOUNT_THROUGHHOLE))
                        elif entry.mount == PickPlace.MountType.EDGE and disable_mount_edge:
                            entry.state.disable(locale.translate(lcl.build_pnp.DISABLE_REASON_MOUNT_EDGE))
                        elif entry.mount == PickPlace.MountType.CHASSIS and disable_mount_chassis:
                            entry.state.disable(locale.translate(lcl.build_pnp.DISABLE_REASON_MOUNT_CHASSIS))
                        elif entry.mount == PickPlace.MountType.UNKNOWN and disable_mount_unknown:
                            entry.state.disable(locale.translate(lcl.build_pnp.DISABLE_REASON_MOUNT_UNKNOWN))
                    break
            else:
                #запись не найдена среди компонентов
                if disable_notbom:
                    entry.state.disable(locale.translate(lcl.build_pnp.DISABLE_REASON_NOTBOM))

        #сортируем записи нужным образом
        if sorting_method is not None:
            new_pnp.sort(sorting_method, sorting_reverse)

        print(f"done. ({len(new_pnp.entries)} entries)")
    else:
        print("0 base entries provided.")
    
    print("INFO >> pnp building completed.") 
    return new_pnp