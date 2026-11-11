# depgraph-apt

Инструмент визуализации графа зависимостей пакетов Ubuntu (apt).
Зависимости получаются собственным кодом из индекса `Packages`
репозитория, без `apt`, `dpkg` и сторонних библиотек.

## Состояние

Этап 1: параметры из командной строки и их проверка.
На этом этапе инструмент выводит все параметры в формате
`ключ=значение`.

## Параметры командной строки

| Опция | Описание | По умолчанию |
|-------|----------|--------------|
| `-p`, `--package` | имя анализируемого пакета | обязательна |
| `-r`, `--repo` | URL индекса репозитория или путь к файлу тестового репозитория | обязательна |
| `-t`, `--test-mode` | режим тестового репозитория: `--repo` — путь к файлу | выключен |
| `-o`, `--output` | имя файла с изображением графа (`.png`) | `graph.png` |
| `-d`, `--max-depth` | максимальная глубина анализа (целое, >= 0) | `3` |

Ошибки в параметрах приводят к сообщению `error: ...` в stderr и коду
возврата `1`.

## Сборка и тесты

Сборка не требуется (чистый Python 3.9+, только стандартная библиотека).

```
make test
```

## Примеры

```
make run ARGS="-p curl -r https://archive.ubuntu.com/ubuntu/dists/jammy/main/binary-amd64/Packages.gz -d 2"
```

Вывод:

```
package=curl
repo=https://archive.ubuntu.com/ubuntu/dists/jammy/main/binary-amd64/Packages.gz
test_mode=False
output=graph.png
max_depth=2
```

Примеры ошибок:

```
make run ARGS="-p curl -r http://x -d -1"      # error: максимальная глубина должна быть >= 0
make run ARGS="-p curl -r ftp://x"             # error: репозиторий должен быть http(s) или file URL
make run ARGS="-p 'Bad Name' -r http://x"      # error: недопустимое имя пакета
make run ARGS="-t -p A -r missing.txt"         # error: файл тестового репозитория не найден
make run ARGS="-p curl -r http://x -o g.txt"   # error: выходной файл должен заканчиваться на .png
```
