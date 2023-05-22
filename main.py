"""
Жиляев Антон ИУ7-14Б
"""


import struct
from typing import List, Any, Callable
from check_path import is_path_exists_or_creatable


field_width = 35
my_sep = '|'
LINE_FORMAT = 's'
COLUMNS_COUNT_FORMAT = 'i'
SIZE_INT_BYTES = struct.calcsize(COLUMNS_COUNT_FORMAT)


def get_number(convert_function: Callable, prompt='') -> Any:
    value = None
    while value is None:
        input_string = input(prompt)
        try:
            value = convert_function(input_string)
        except ValueError:
            print('Полученная строка не является валидным числом')

    return value


def get_separetor() -> str:
    return my_sep


def db_str_length(columns_len: int) -> int:
    return columns_len * field_width


def fields_repr_sep(fields: List[Any]) -> str | None:
    try:
        str = get_separetor().join([f'{field:{field_width}}' for field in fields])
    except:
        return None
    return str


def line_parse_sep(line: str) -> List[any] | None:
    try:
        fields = line.strip().split(my_sep)
    except:
        return None
    return fields


def read_byte_line(f, columns_len: int) -> bytearray:
    byte_line = None
    try:
        byte_line = f.read(db_str_length(columns_len))
    except MemoryError:
        print('Битая бд :/')
    return byte_line


def bytes_to_line(byte_line: bytearray, columns_len: int) -> str:
    return struct.unpack(f'{db_str_length(columns_len)}{LINE_FORMAT}', byte_line)[0].decode('UTF-8')


def line_to_bytes(line: str, columns_len: int) -> bytes:
    line = line.encode('UTF-8')
    return struct.pack(f'{db_str_length(columns_len)}{LINE_FORMAT}', line)


def read_columns(f) -> int:
    try:
        columns_len = struct.unpack(COLUMNS_COUNT_FORMAT, f.read(SIZE_INT_BYTES))[0]
    except:
        columns_len = 0
    return columns_len


def jump_to_nline_bytes(columns_len: int, n: int) -> int:
    return SIZE_INT_BYTES + db_str_length(columns_len) * (n + 1)


def choose_file(path: str) -> str:
    while True:
        path = input('Введите путь: ')
        if is_path_exists_or_creatable(path) and len(path) > 4 and path[-4:] == '.bin':
            break
        print('Введенный путь является некорректным')

    return path


def is_current_path_correct(path: str):
    return not (is_path_exists_or_creatable(path) and len(path) > 4 and path[-4:] == '.bin') or path == ''


def init_db(path: str) -> str:
    if is_current_path_correct(path):
        print('Некорректный путь')
        return path
    f = open(path, 'wb')

    while 2 >= (columns_len := get_number(int, 'Введите количество полей: ')):
        print('Некорректное значение')

    headers = []
    columns_types = []
    for i in range(columns_len):
        while len((header := input(f'Введите {i+1}-й заголовок базы данных: '))) > field_width:
            print(f'Заголовок длиннее ширины поля({field_width})')
        while (column_type := input(f'Введите тип данных {i+1}-го столбца: ')) \
                and column_type != 'str' and column_type != 'int':
            print('Введён неподдержанный тип данных')
        headers += [header]
        columns_types += [column_type]

    if headers:
        f.write(struct.pack(COLUMNS_COUNT_FORMAT, columns_len))
        f.write(line_to_bytes(fields_repr_sep(columns_types), columns_len))
        f.write(line_to_bytes(fields_repr_sep(headers), columns_len))

    print()
    while 0 > (lines_count := get_number(int, 'Введите количество записей для инициализации: ')):
        print('Некорректное значение')

    for i in range(lines_count):
        fields = []
        for j in range(columns_len):
            field = None
            while field is None:
                input_string = input(f'Введите {j + 1}-е поле {i + 1}-й строки: ')
                while columns_types[j].strip() == 'str' and len(input_string) > field_width:
                    print(f'Поле длиннее ширины поля({field_width})')
                    input_string = input(f'Введите {j + 1}-е поле {i + 1}-й строки: ')

                if columns_types[j].strip() == 'int':
                    try:
                        field = int(float(input_string))
                    except ValueError:
                        print('Полученная строка не является валидным числом')
                else:
                    field = input_string

            fields += [str(field)]
        f.write(line_to_bytes(fields_repr_sep(fields), columns_len))

    f.close()
    return path


def print_db(path: str) -> str:
    if is_current_path_correct(path):
        print('Некорректный путь')
        return path

    try:
        with open(path, 'rb') as f:
            if f.seek(0, 2) <= SIZE_INT_BYTES:
                print('\nБитый файл базы данных\n')
                return path
            f.seek(0)

            inp_str_columns = read_columns(f)
            f.seek(SIZE_INT_BYTES)
            try:
                inp_str_columns = int(inp_str_columns)
            except ValueError:
                print('\nБитый файл базы данных\n')
                return path
            columns_len = inp_str_columns
            if columns_len < 2:
                print('\nБитый файл базы данных\n')
                return path

            if f.seek(0, 2) < jump_to_nline_bytes(columns_len, 0):
                print('\nБитый файл базы данных\n')
                return path
            f.seek(SIZE_INT_BYTES)

            byte_line = read_byte_line(f, columns_len)
            if not byte_line:
                print('\nБитый файл базы данных\n')
                return path
            columns_types = line_parse_sep(bytes_to_line(byte_line, columns_len))
            f.seek(jump_to_nline_bytes(columns_len, 0))

            if not columns_types or len(columns_types) != columns_len:
                print('\nБитый файл базы данных\n')
                return path

            is_headers = 1
            current_pos = f.tell()
            file_length = (f.seek(0, 2) - current_pos) // db_str_length(columns_len)
            for i in range(file_length):
                f.seek(jump_to_nline_bytes(columns_len, i))

                byte_line = read_byte_line(f, columns_len)
                if not byte_line:
                    print('\nБитый файл базы данных\n')
                    return path
                parsed = line_parse_sep(bytes_to_line(byte_line, columns_len))
                if not parsed or len(parsed) != columns_len:
                    print('\nБитый файл базы данных\n')
                    return path

                if is_headers:
                    print(*[f'{item:{field_width}}' for item in parsed], sep=' | ')
                    is_headers = 0
                    continue
                for j in range(columns_len):
                    if columns_types[j].strip() == 'int':
                        try:
                            value = int(parsed[j])
                        except ValueError:
                            print('\nБитый файл базы данных\n')
                            return path
                        print(f'{value:<{field_width}.5g}', sep='', end='')
                    elif columns_types[j].strip() == 'str':
                        print(f'{parsed[j]:{field_width}}', sep='', end='')
                    if j != columns_len - 1:
                        print(f' {my_sep} ', sep='', end='')
                    elif j == columns_len - 1:
                        print(f' {my_sep} {i}')
    except PermissionError:
        print('Нет необходимого доступа')
    return path


def insert_line(path: str) -> str:
    if is_current_path_correct(path):
        print('Некорректный путь')
        return path
    try:
        while True:
            k = get_number(int, 'Введите позицию вставки: ')
            with open(path, 'rb') as f:
                if f.seek(0, 2) <= SIZE_INT_BYTES:
                    print('\nБитый файл базы данных\n')
                    return path
                f.seek(0)

                inp_str_columns = read_columns(f)
                f.seek(SIZE_INT_BYTES)
                try:
                    inp_str_columns = int(inp_str_columns)
                except ValueError:
                    print('\nБитый файл базы данных\n')
                    return path
                columns_len = inp_str_columns
                if columns_len < 2:
                    print('\nБитый файл базы данных\n')
                    return path

                if f.seek(0, 2) < jump_to_nline_bytes(columns_len, 1):
                    print('\nБитый файл базы данных\n')
                    return path
                f.seek(SIZE_INT_BYTES)

                byte_line = read_byte_line(f, columns_len)
                if not byte_line:
                    print('\nБитый файл базы данных\n')
                    return path
                columns_types = line_parse_sep(bytes_to_line(byte_line, columns_len))
                f.seek(SIZE_INT_BYTES + db_str_length(columns_len))

                if not columns_types or len(columns_types) != columns_len:
                    print('\nБитый файл базы данных\n')
                    return path

                lines_count = (f.seek(0, 2) - f.seek(0) - SIZE_INT_BYTES) // db_str_length(columns_len) - 2
                if 0 < k < lines_count + 2:
                    break
                print('Введите корректную позицию для вставки')

        with open(path, 'r+b') as f:
            fields = []
            for j in range(columns_len):
                field = None
                while field is None:
                    input_string = input(f'Введите {j + 1}-е поле: ')
                    while columns_types[j].strip() == 'str' and len(input_string) > field_width:
                        print(f'Поле длиннее ширины поля({field_width})')
                        input_string = input(f'Введите {j + 1}-е поле: ')

                    if columns_types[j].strip() == 'int':
                        try:
                            field = int(float(input_string))
                        except ValueError:
                            print('Полученная строка не является валидным числом')
                    elif columns_types[j].strip() == 'str':
                        field = input_string

                fields += [str(field)]

            f.seek(0, 2)
            byte_line_to_insert = line_to_bytes(fields_repr_sep(fields), columns_len)
            f.write(byte_line_to_insert)

            for i in range(lines_count, k - 1, -1):
                f.seek(jump_to_nline_bytes(columns_len, i))

                byte_line = read_byte_line(f, columns_len)
                if not byte_line:
                    print('\nБитый файл базы данных\n')
                    return path
                f.seek(jump_to_nline_bytes(columns_len, i))
                f.write(byte_line)
            f.seek(jump_to_nline_bytes(columns_len, k))
            f.write(byte_line_to_insert)

    except PermissionError:
        print('Нет необходимого доступа')
    return path


def delete_line(path: str) -> str:
    if is_current_path_correct(path):
        print('Некорректный путь')
        return path
    try:
        while True:
            with open(path, 'rb') as f:
                if f.seek(0, 2) <= SIZE_INT_BYTES:
                    print('\nБитый файл базы данных\n')
                    return path
                f.seek(0)

                inp_str_columns = read_columns(f)
                f.seek(SIZE_INT_BYTES)
                try:
                    inp_str_columns = int(inp_str_columns)
                except ValueError:
                    print('\nБитый файл базы данных\n')
                    return path
                columns_len = inp_str_columns
                if columns_len < 2:
                    print('\nБитый файл базы данных\n')
                    return path

                if f.seek(0, 2) < jump_to_nline_bytes(columns_len, 1):
                    print('\nБитый файл базы данных\n')
                    return path
                elif f.seek(0, 2) == jump_to_nline_bytes(columns_len, 1):
                    print('\nПустая бд')
                    return path
                f.seek(SIZE_INT_BYTES)

                k = get_number(int, 'Введите позицию удаления записи: ')

                byte_line = read_byte_line(f, columns_len)
                if not byte_line:
                    print('\nБитый файл базы данных\n')
                    return path
                columns_types = line_parse_sep(bytes_to_line(byte_line, columns_len))
                f.seek(SIZE_INT_BYTES + db_str_length(columns_len))

                if not columns_types or len(columns_types) != columns_len:
                    print('\nБитый файл базы данных\n')
                    return path

                lines_count = (f.seek(0, 2) - f.seek(0) - SIZE_INT_BYTES) // db_str_length(columns_len) - 2
                if 0 < k <= lines_count:
                    break
                print('Введите корректную позицию удаления записи')

        with open(path, 'r+b') as f:
            for i in range(k, lines_count):
                f.seek(jump_to_nline_bytes(columns_len, i + 1))
                byte_line = read_byte_line(f, columns_len)
                if not byte_line:
                    print('\nБитый файл базы данных\n')
                    return path
                f.seek(jump_to_nline_bytes(columns_len, i))
                f.write(byte_line)

            f.seek(jump_to_nline_bytes(columns_len, k))
            f.truncate(jump_to_nline_bytes(columns_len, lines_count))

    except PermissionError:
        print('Нет необходимого доступа')
    return path


def search_one_field(path: str) -> str:
    if is_current_path_correct(path):
        print('Некорректный путь')
        return path

    try:
        with open(path, 'rb') as f:
            if f.seek(0, 2) <= SIZE_INT_BYTES:
                print('\nБитый файл базы данных\n')
                return path
            f.seek(0)

            inp_str_columns = read_columns(f)
            f.seek(SIZE_INT_BYTES)
            try:
                inp_str_columns = int(inp_str_columns)
            except ValueError:
                print('\nБитый файл базы данных\n')
                return path
            columns_len = inp_str_columns
            if columns_len < 2:
                print('\nБитый файл базы данных\n')
                return path

            if f.seek(0, 2) < jump_to_nline_bytes(columns_len, 1):
                print('\nБитый файл базы данных\n')
                return path
            f.seek(SIZE_INT_BYTES)

            byte_line = read_byte_line(f, columns_len)
            if not byte_line:
                print('\nБитый файл базы данных\n')
                return path
            columns_types = line_parse_sep(bytes_to_line(byte_line, columns_len))
            f.seek(SIZE_INT_BYTES + db_str_length(columns_len))

            if not columns_types or len(columns_types) != columns_len:
                print('\nБитый файл базы данных\n')
                return path

            while not(0 < (column_1 := get_number(int, 'Выберете столбец для поиска: ')) <= columns_len):
                print('Некорректный столбец')
            column_1 -= 1
            search_value_1 = None
            while search_value_1 is None:
                inp_str_value = input('Введите значение для поиска: ')
                if columns_types[column_1].strip() == 'int':
                    try:
                        search_value_1 = int(inp_str_value)
                    except ValueError:
                        print('Значение не соответствует типу данных столбца')
                elif columns_types[column_1].strip() == 'str':
                    search_value_1 = inp_str_value

            print('\nНайденные записи в базе данных:')
            is_headers = 1
            current_pos = f.tell()
            file_length = (f.seek(0, 2) - current_pos) // db_str_length(columns_len)
            for i in range(file_length):
                f.seek(jump_to_nline_bytes(columns_len, i))

                byte_line = read_byte_line(f, columns_len)
                if not byte_line:
                    print('\nБитый файл базы данных\n')
                    return path
                parsed = line_parse_sep(bytes_to_line(byte_line, columns_len))
                if not parsed or len(parsed) != columns_len:
                    print('\nБитый файл базы данных\n')
                    return path

                if is_headers:
                    print(*[f'{item:{field_width}}' for item in parsed], sep=' | ')
                    is_headers = 0
                    continue

                found = 1
                if columns_types[column_1].strip() == 'int':
                    try:
                        value = int(parsed[column_1].strip())
                    except ValueError:
                        print('\nБитый файл базы данных\n')
                        return path
                elif columns_types[column_1].strip() == 'str':
                    value = parsed[column_1].strip()
                found *= search_value_1 == value

                if found:
                    for j in range(columns_len):
                        if columns_types[j].strip() == 'int':
                            try:
                                value = int(parsed[j])
                            except ValueError:
                                print('\nБитый файл базы данных\n')
                                return path

                            print(f'{value:<{field_width}.5g}', sep='', end='')
                        elif columns_types[j].strip() == 'str':
                            print(f'{parsed[j]:{field_width}}', sep='', end='')
                        if j != columns_len - 1:
                            print(f' {my_sep} ', sep='', end='')
                        elif j == columns_len - 1:
                            print(f' {my_sep} {i}')
    except PermissionError:
        print('Нет необходимого доступа')
    return path


def search_two_field(path: str) -> str:
    if is_current_path_correct(path):
        print('Некорректный путь')
        return path

    try:
        with open(path, 'rb') as f:
            if f.seek(0, 2) <= SIZE_INT_BYTES:
                print('\nБитый файл базы данных\n')
                return path
            f.seek(0)

            inp_str_columns = read_columns(f)
            f.seek(SIZE_INT_BYTES)
            try:
                inp_str_columns = int(inp_str_columns)
            except ValueError:
                print('\nБитый файл базы данных\n')
                return path
            columns_len = inp_str_columns
            if columns_len < 2:
                print('\nБитый файл базы данных\n')
                return path

            print(f.seek(0, 2), jump_to_nline_bytes(columns_len, 1))
            if f.seek(0, 2) < jump_to_nline_bytes(columns_len, 1):
                print('\nБитый файл базы данных\n')
                return path
            f.seek(SIZE_INT_BYTES)

            byte_line = read_byte_line(f, columns_len)
            if not byte_line:
                print('\nБитый файл базы данных\n')
                return path
            columns_types = line_parse_sep(bytes_to_line(byte_line, columns_len))
            f.seek(SIZE_INT_BYTES + db_str_length(columns_len))

            if not columns_types or len(columns_types) != columns_len:
                print('\nБитый файл базы данных\n')
                return path

            while not(0 < (column_1 := get_number(int, 'Выберете столбец для поиска: ')) <= columns_len):
                print('Некорректный столбец')
            column_1 -= 1
            search_value_1 = None
            while search_value_1 is None:
                inp_str_value = input('Введите значение для поиска: ')
                if columns_types[column_1].strip() == 'int':
                    try:
                        search_value_1 = int(inp_str_value)
                    except ValueError:
                        print('Значение не соответствует типу данных столбца')
                elif columns_types[column_1].strip() == 'str':
                    search_value_1 = inp_str_value

            while not(0 < (column_2 := get_number(int, 'Выберете столбец для поиска: ')) <= columns_len):
                print('Некорректный столбец')
            column_2 -= 1
            search_value_2 = None
            while search_value_2 is None:
                inp_str_value = input('Введите значение для поиска: ')
                if columns_types[column_2].strip() == 'int':
                    try:
                        search_value_2 = int(inp_str_value)
                    except ValueError:
                        print('Значение не соответствует типу данных столбца')
                elif columns_types[column_2].strip() == 'str':
                    search_value_2 = inp_str_value

            print('\nНайденные записи в базе данных:')
            is_headers = 1
            current_pos = f.tell()
            file_length = (f.seek(0, 2) - current_pos) // db_str_length(columns_len)
            for i in range(file_length):
                f.seek(jump_to_nline_bytes(columns_len, i))

                byte_line = read_byte_line(f, columns_len)
                if not byte_line:
                    print('\nБитый файл базы данных\n')
                    return path
                parsed = line_parse_sep(bytes_to_line(byte_line, columns_len))
                if not parsed or len(parsed) != columns_len:
                    print('\nБитый файл базы данных\n')
                    return path

                if is_headers:
                    print(*[f'{item:{field_width}}' for item in parsed], sep=' | ')
                    is_headers = 0
                    continue

                found = 1
                if columns_types[column_1].strip() == 'int':
                    try:
                        value = int(parsed[column_1].strip())
                    except ValueError:
                        print('\nБитый файл базы данных\n')
                        return path
                elif columns_types[column_1].strip() == 'str':
                    value = parsed[column_1].strip()
                found *= search_value_1 == value

                if columns_types[column_2].strip() == 'int':
                    try:
                        value = int(parsed[column_2].strip())
                    except ValueError:
                        print('\nБитый файл базы данных\n')
                        return path
                elif columns_types[column_2].strip() == 'str':
                    value = parsed[column_2].strip()
                found *= search_value_2 == value

                if found:
                    for j in range(columns_len):
                        if columns_types[j].strip() == 'int':
                            try:
                                value = int(parsed[j])
                            except ValueError:
                                print('\nБитый файл базы данных\n')
                                return path

                            print(f'{value:<{field_width}.5g}', sep='', end='')
                        elif columns_types[j].strip() == 'str':
                            print(f'{parsed[j]:{field_width}}', sep='', end='')
                        if j != columns_len - 1:
                            print(f' {my_sep} ', sep='', end='')
                        elif j == columns_len - 1:
                            print(f' {my_sep} {i}')
    except PermissionError:
        print('Нет необходимого доступа')
    return path


def loop(menu_str: str) -> None:
    actions = {
        1: choose_file,
        2: init_db,
        3: print_db,
        4: insert_line,
        5: delete_line,
        6: search_one_field,
        7: search_two_field,
    }

    path = ''
    while True:
        print(menu_str)
        prompt = 'Введите номер действия: '
        action = get_number(int, prompt=prompt)

        if action == 0:
            break

        if actions.get(action, -1) != -1:
            path = actions[action](path)
            print()
        else:
            print('Такого действия не существует')


def main():
    menu_str = '''Меню:
0. Завершить работу программы
1. Выбрать файл для работы
2. Инициализировать базу данных (создать либо перезаписать файл и заполнить его записями)
3. Вывести содержимое базы данных
4. Добавить запись в произвольную позицию
5. Удалить произвольную запись
6. Поиск по одному полю
7. Поиск по двум полям
'''
    loop(menu_str)


if __name__ == '__main__':
    main()
