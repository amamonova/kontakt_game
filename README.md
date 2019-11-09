# kontakt-game
There is a project of CSC - Kontakt Game.

## Data downloading
Скрипт main.py в папке data отвечает за скачивание и обработку данных  с википедии и викисловаря

#### Входные данные 
1) Скрипт спросит что вы хотите скачать 1 - википедию 2 - викисловарь
2) Скрипт спросит путь к директории, куда вы хотите сохранить dump файлы 
(промежуточные файлы, после завершения работы скрипта можете их удалить)
###### Замечание: Не на Linux OS могут возникнуть проблемы из-за другого формата пути, в этом случае напишите pavlov200912

#### Выходные данные
Скрипт сохраняет в директории запуска несколько файлов 'wikipedia_data{i}.csv',
которые содержат csv таблицы обработанных данных. Во всех файлах разделителем является \\  (backslash)
#### Формат данных
##### Wikipedia csv file
1) Заголовок
2) Текст статьи
##### Wiktionary json file
Пример использования файла: https://colab.research.google.com/drive/1hheCmPLU7i6ybMFMkrDMb05fN-OmKmw1
1) Заголовок
2) Часть речи (пока noun/other)
3) Значение и примеры в формате [(meaning, [examples]), ...]
4) Синонимы, Антонимы, Гипонимы, Гиперонимы в формате словаря {'synonyms':[...], ...}
5) Фразеологизмы (список строк)

###### Всего данные после обработки занимают около 5-6 Гб, выделите место заранее. Загрузка и обработка файлов может занять значительное время.
