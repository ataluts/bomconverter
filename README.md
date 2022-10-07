# BoM Converter

## Назначение
RU: Автоматизированное создание перечня элементов (ПЭ3), списка закупки компонентов (СК) и спецификации (СП) из проекта Altium Designer.<br/>
EN: Creating components database from Altium Designer project, schematics and BoM files and exporting it to different output formats.

## Описание:
Суть работы программы сводится к тому чтобы из проекта Altium Designer получить информацию о компонентах и о самом проекте, затем свести эту информацию в стандартизованную базу данных и уже из этой базы экспортировать данные в требуемый тип документа с требуемым форматированием. Проект сделан модульно чтобы импорт, парсинг, сборка и экспорт были максимально независимы друг от друга. Чтобы каждый схемотехник мог написать свой парсер под свой формат ведения схемы при этом экспорт задавался общепринятыми на предприятии стандартами и мог спокойно сопровождаться соответствующими сотрудниками без задалбывания схемотехника.

### Краткое описание работы
Всё крутится вокруг базы данных. Ключевым моментом является её заполнение, а каким именно образом уже возможны варианты.

Можно скармливать программе либо файл проекта в котором все данные подлинкованы (что предпочтительно), либо BoM-файлы и данные основной надписи по отдельности.
В случае работы с проектом AD достаточно указать только адрес самого файла. Программа запускает импортёр проекта AD, который берёт на себя все технические сложности чтения проекта и составляет из него соответсвующий объект. Далее созданный объект проекта перекидывается в парсер конкретного схемотехника который знает как правильно вытащить данные из проекта и выдаёт список BoM-файлов и данные об "основной надписи". (Особенность конкретно моего парсера проекта заключается в том что BoM файлы должны быть добавлены в проект, быть с расширением *"csv"* и иметь префикс *"bom"*, а именем конфигурации считается весь текст между *"BoM "* и *".csv"*).

Далее обрабатывается каждый BoM-файл из заданного списка. Вначале импортёр открывает BoM-файл и составляет из него соответствующий объект. Затем этот объект передаётся в парсер схемотехника который знает как из представленных данных правильно сформировать базу данных компонентов (попутно проверив всё на возможные ошибки). (Особенность конкретно моего парсера BoM заключается в том что при экспорте из AD не должно быть группировки компонентов - то есть каждый элемент должен находится в отдельной строке).

После получения базы данных компонентов происходит трансляция имён производителей по словарю, что позволяет привести разные вариации записи имён к единообразию (что также полезно в случаях изменения имён когда один производитель покупает другого).

Далее для каждого типа экспорта соответствующим модулем происходит сборка соответсвующего объекта после чего этот объект передаётся в требуемый экспортёр который производит запись данных в нужный формат. Для экспорта в PDF необходимо наличие установленного MiKTeX (писалось под версией 20.11).

В отдельный модуль выделена сборка строк для ПЭ3 и СП (по ЕСКД или по любому-другому формату) которая собирает поля из параметров компонентов в базе данных. Стиль форматирования при сборке строки передаётся в качестве параметров при вызове функции и также доступен при вызове сборщика. Стили заданы в основном файле программы перед вызовом каждого сборщика. Также имеется возможность локализации, словарь которой задаётся в отдельном файле. Группировка элементов в перечне происходит по префиксу в позиционном обозначении. Имена групп заданы в отдельном словаре соответствующего сборщика.

### Как запускать
Можно запускать *"bomconverter.py"* из командной строки с указанием параметров (*-h* для их описания), либо просто перетащив на него BoM-файлы в проводнике (но тогда все параметры будут в значениях по-умолчанию), либо из IDE через файл *"_starter.py"* в котором задать все нужные параметры и список всех проектов, что, имхо, самый удобный вариант.

Параметр *"--output"* задаёт что и в каком формате надо получить на выходе:
- *'all'* - экспорт всего возможного;
- *'cl-xlsx'* - список компонентов для закупки с группировкой по номиналам и отдельным листом со списком допустимых замен (если присутствуют) в формате Excel;
- *'pe3-docx'* - перечень элементов (ПЭ3) в формате MS Word;
- *'pe3-pdf'* - перечень элементов (ПЭ3) в формате PDF (должен быть установлен MiKTeX);
- *'sp-csv'* - файл для импорта данных (с полями заполненными как для ПЭ3) в *"КОМПАС-3D"* через прикладную библиотеку *"Конвертор eCAD-КОМПАС (текст)"* (для создания перечня или спецификации в Компасе).

## Отладочный проект
В папке *"debug/AD project"* лежит тестовый проект Altium Designer сделанный для работы с моим парсером (его адрес добавлен в *"_starter.py"*). На схеме представлены различные элементы с примерами заполнения полей. В папку *"debug/AD project/project outputs/Bill of Materials"* изначально экспортируются BoM-файлы из проекта. Туда же записывыаются и выходные файлы самой программы. Все эти файлы доступны там в качестве примера получаемого результата.

## Disclaimer
Программа разрабатывалась в перерывах между основной работой (а именно разработкой оборудования - я схемотехник, а не программист) и как первый проект на Python, поэтому не ждите вылизанного кода и нормальной обработки ошибок :) Хотя, справедливости ради, следует заметить, что код полностью переписывался с нуля уже 2 раза и это третья итерация данного программного решения.

Изначальная идея была взята из скрипта [Bombier 2.0](https://github.com/dngulin/bombier) с принципиальной разницей в прогоне компонентов через базу данных чтобы отвязать форматирование параметров в проекте Альтиума от форматирования параметров в перечне элементов. 
