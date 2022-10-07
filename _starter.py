import os, subprocess
script_dirName = os.path.dirname(__file__)                      #адрес папки со скриптом

#добавляем в список аргументов скрипт который надо запустить
argv = ['python', os.path.join(script_dirName, 'bomconverter.py')]

#добавляем нужные аргументы
input_basepath = 'D:\\My Documents\\work'     #общий путь ко всем проектам
input_files = []
input_files.append(os.path.join(script_dirName, 'debug\\AD project\\BoM converter.PrjPcb'))
#input_files.append(os.path.join(input_basepath, '<project_dir>\\<project_name>.PrjPcb'))
argv.extend(input_files)

argv.append('--adproject')
#argv.extend(['--output', 'pe3-docx'])
#argv.append('--noquestions')
argv.append('--nohalt')

#запускаем основную программу как-будто из командной строки
subprocess.run(argv)


