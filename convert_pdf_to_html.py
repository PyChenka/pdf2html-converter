import PyPDF2
import re
from datetime import datetime
from langdetect import detect
from translate import Translator
import fitz  # PyMuPDF


################################
# Редактирование инфо о законе #
################################

def remove_html_tags(lst):
    cleaned_list = []
    for string in lst:
        cleaned_string = re.sub('<.*?>', '', string)
        cleaned_list.append(cleaned_string)
    return cleaned_list


def remove_first_last_lines(lines, phrase, pages_count):
    """Удаляет ненужные строки"""
    for index, line in enumerate(lines):
        if phrase in line:  # Проверяем, содержит ли строка заданную фразу
            line = line.split()[1:]
            line = ' '.join(line)
            line = re.sub('/' + str(pages_count), '||', line).strip()
            line = line.split('||')[1:]
            line = ' '.join(line)
            lines[index] = line

        line = line.strip()  # Убираем лишние пробелы в начале и конце каждой строки
        lines[index] = line

    return lines[1:]


def remove_empty_lines(lines):
    """Удаляет пустые строки из списка строк"""
    return list(filter(lambda x: x.strip(), lines))


def get_doc_title(path):
    # Открываем файл для чтения
    pdf_file = open(path, 'rb')
    pdf_reader = PyPDF2.PdfReader(pdf_file)

    doc_title = []

    # Обходим первую страницу и достаёт заголовок
    page = pdf_reader.pages[0]
    lines = page.extract_text().split('\n')

    # print(lines)

    cleared_page = remove_first_last_lines(
        lines, 'https://', len(pdf_reader.pages))

    if len(pdf_reader.pages) == 1:
        doc_title = cleared_page[5:9]
    else:
        doc_title = cleared_page[:5]

    pdf_file.close()
    return doc_title


def translate_text(text):
    lang = detect(text)
    translator = Translator(from_lang=lang, to_lang='en')

    if lang != 'en':
        translation = translator.translate(text)
        return translation
    else:
        return None


def get_law_number(doc):
    law_number = [int(s) for s in str.split(doc[0]) if s.isdigit()]

    if law_number[0]:
        return law_number[0]
    else:
        return None


def get_law_create_date(doc):
    # Регулярное выражение для даты dd/dd/dddd
    pattern = r'\d{1,}/\d{1,}/\d{4}'
    match = re.search(pattern, doc[1])

    if match:
        date_str = match.group()
        law_date = datetime.strptime(date_str, '%d/%m/%Y').date()
        return law_date
    else:
        return None


def get_law_type(doc):
    doc_first_line = doc[0]

    # Удаляем цифры из строки
    law_type = re.sub("[0-9]", "", doc_first_line)

    # Удаляем заданные фразы из строки
    phrases = ["no", "№", "No."]
    for phrase in phrases:
        law_type = law_type.replace(phrase, '')

    return law_type.strip()


def get_law_name(doc):
    doc.pop(2)
    doc.pop(1)
    doc_first_line = doc[0]
    doc.pop(0)

    # Подстановка знака № и очистка строки от ненужных символов
    phrases = ["no", "No", "No."]
    for phrase in phrases:
        doc_first_line = doc_first_line.replace(phrase, '№')
    phrases = [",", "."]
    for phrase in phrases:
        doc_first_line = doc_first_line.replace(phrase, '')

    law_number = [int(s) for s in str.split(doc_first_line) if s.isdigit()]

    # Убираем из строки номер закона и знак №, если этот знак после перевода не в конце
    doc_first_line = re.sub(str(law_number[0]), '', doc_first_line).strip()
    doc_first_line = re.sub('№', '', doc_first_line).strip()

    number = ''.join(['№', str(law_number[0])])

    law_name = ' '.join([doc_first_line, number, doc[0]])

    return law_name.strip()


def get_law_data(path):
    doc_title_arr = get_doc_title(path)
    doc_title_arr = remove_empty_lines(doc_title_arr)

    # Переводим заголовок на английский
    text = translate_text('|'.join(doc_title_arr))
    if text is None:
        print('Ошибка перевода')
        return

    text = text.split('|')
    document_title = []

    for line in text:
        line = line.strip()  # Убираем лишние пробелы в начале и конце строки
        line = " ".join(line.split())  # Убираем лишние пробелы между словами
        document_title.append(line)

    law_number = get_law_number(document_title)
    law_date = get_law_create_date(document_title)
    law_type = get_law_type(document_title)
    law_name = get_law_name(document_title)

    # (!!!) РАСКОММЕНТИРОВАТЬ
    # processing_law_data(law_number, law_date, law_type, law_name)


def processing_law_data(law_number, law_date, law_type, law_name):
    # Обработчик информации о законе
    # (!!!) Тут будет запись в БД
    print('law_number:', law_number)
    print('law_date:', law_date)
    print('law_type:', law_type)
    print('law_name:', law_name)


########################
# Редактирование файла #
########################

def flatten_list(lst):
    """Преобразует двумерный массив в одномерный"""
    flattened_list = []
    for sublist in lst:
        for item in sublist:
            flattened_list.append(item)
    return flattened_list


def check_article(text, is_title):
    """Проверяет, является ли параграф заголовком раздела"""
    if is_title:
        text = remove_html_tags(text)
        text = " ".join(text)
        text = '<h3 class="law-title center">' + text + '</h3>'
    else:
        text = " ".join(text)
        text = '<p class="law-text">' + text + '</p>'

    return text


def set_left_side_paragraph(paragraph):
    """Задаёт классы параграфа, расположенного слева относительно страницы"""
    class_str = re.findall(r'class=\"(.*)\"', paragraph)
    classes = class_str[0].split()
    if 'law-title' in classes:
        classes[classes.index('law-title')] = 'law-text'
        classes.append('bold')
    if 'center' in classes:
        classes.remove('center')
    classes.append('left')

    pattern = r'class="(.+?)"'
    paragraph = re.sub(pattern, r'class="{}"'.format(
        ' '.join(classes)), paragraph)
    paragraph = re.sub('h3', 'p', paragraph)

    return paragraph


def wrap_doc_title(doc):
    """Редактирует заголовок документа и оборачивает в нужный тег"""
    law_title_number = 0
    title_end_index = 0
    paragraph_number = 0
    law_title = []

    for paragraph in doc:
        if 'h3' in paragraph:
            law_title_number += 1

        if law_title_number == 2:
            title_end_index = paragraph_number
            break

        paragraph_number += 1

    law_title = doc[:(title_end_index + 1)]  # получаем из документа заголовок
    doc = doc[(title_end_index + 1):]  # убираем из документа заголовок

    for i, item in enumerate(law_title):
        law_title[i] = re.sub('<br>', ';', item)

    for i, item in enumerate(law_title):
        if 'h3' in item:
            item = remove_html_tags([item])
            item = '<span class="bold">' + item[0] + '</span>'
            law_title[i] = item
        else:
            item = remove_html_tags([item])
            law_title[i] = item[0]

    for i, item in enumerate(law_title):
        law_title[i] = re.sub(';', '<br>', item)

    law_title = '<h2 class="law-title center main">' + \
        '<br>'.join(law_title) + '</h2>'

    return [law_title] + ['<div class="law-line"></div>'] + doc


def join_articles(doc):
    """Объединяет попарно идущие заголовки разделов"""
    first_article_index = 0
    last_article_index = 0
    is_multiple_article = False

    tag_to_find = 'h3'

    for index, item in enumerate(doc):
        if tag_to_find in item and tag_to_find not in doc[index - 1]:
            first_article_index = index

        if tag_to_find in item and tag_to_find in doc[index - 1]:
            last_article_index = index
            is_multiple_article = True

        if tag_to_find not in item and tag_to_find in doc[index - 1] and is_multiple_article:
            item = doc[first_article_index:(last_article_index + 1)]
            for article_part in item:
                doc.remove(article_part)
            item = remove_html_tags(item)
            item = '<h3 class="law-title center">' + \
                '<br>'.join(item) + '</h3>'
            doc.insert(first_article_index, item)

            is_multiple_article = False

    return doc


def reverse_text(text):
    result_text = text[::-1]

    # Отображаем зеркально все числа
    numbers = re.findall(r'\d+', result_text)
    if len(numbers):
        for number in numbers:
            result_text = result_text.replace(number, number[::-1])

    # Отображаем зеркально все даты
    dates = re.findall(r'\d{4}/\d{1,}/?\d{0,}', result_text)
    if len(dates):
        for date in dates:
            reversed_date = date.split('/')
            reversed_date = '/'.join(reversed_date[::-1])
            result_text = result_text.replace(date, reversed_date)
    
    # Отображаем зеркально все слова на английском
    english_words = re.findall(r'\b[a-zA-Z]+\b', result_text)
    if len(english_words):
        for word in english_words:
            result_text = result_text.replace(word, word[::-1])

    # Меняем местами скобки
    swapped_string = ""
    for char in result_text:
        if char == "(":
            swapped_string += ")"
        elif char == ")":
            swapped_string += "("
        else:
            swapped_string += char
    result_text = swapped_string

    return result_text


def extract_text_from_pdf(file_path):
    # Открываем файл для чтения
    doc = fitz.open(file_path)
    result_doc = []

    for page in doc:
        doc_page = []
        blocks = page.get_text("dict", flags=11, sort=True)
        page_width = blocks['width']

        for b in blocks["blocks"]:  # iterate through the text blocks
            paragraph = []
            x1 = b['bbox'][2]  # Позиция правого края параграфа
            is_title = True
            to_extract = True

            for l in b["lines"]:  # iterate through the text lines
                line = []

                for s in l["spans"]:  # iterate through the text spans
                    # Проверка, содержит ли параграф ссылку
                    if 'https://' in s["text"] or "Image" in s["text"] or "Table" in s["text"]:
                        to_extract = False

                    text = reverse_text(s["text"])

                    if s["flags"] == 20:
                        # Жирный шрифт оборачиваем в тег <span>
                        line.insert(0, '<span class="bold">' +
                                    text.strip() + '</span>')
                    else:
                        line.insert(0, text.strip())
                        is_title = False
                paragraph += line
                paragraph.append('<br>')

            if to_extract:
                # Удаляем последний <br>
                paragraph.pop()

                # Проверка, является ли параграф заголовком раздела
                paragraph = check_article(paragraph, is_title)

                # Проверка, расположен ли параграф слева
                if x1 < page_width / 2:
                    paragraph = set_left_side_paragraph(paragraph)

                doc_page.append(paragraph)

            to_extract = True

        doc_page.pop(0)
        result_doc.append(doc_page)

    doc.close()
    result_doc[-1].pop()
    return result_doc


#################
# Создание HTML #
#################

def create_html(doc, output_html_path):
    document_content = '\n'.join(doc)
    comments = '''
    <!--
        * * * Теги HTML * * *
        
        <h1>ТЕКСТ</h1>, <h2>ТЕКСТ</h2>, <h3>ТЕКСТ</h3> - Заголовки 1-го, 2-го и 3-го уровней
        
        <p>ТЕКСТ</p> - Абзац текста
        
        <span>ТЕКСТ</span> - Содержит небольшой текст или часть текста внутри абзаца
        
        <br> - Перенос строки(закрывающий тег не нужен!)
        
        <div>Здесь могут быть разные теги</div> - Структурный блок
        
        
        * * * Структура нашего документа * * *
        
        * Используемые классы:
        > Необходимы для задания стилей. Можно задавать несколько через пробел
        
        law-title                   : заголовок любого уровня, всегда жирным шрифтом
        law-title main              : заголовок 1-го уровня
        
        law-text                    : абзац текста
        
        center                      : выровнять блок по центру
        left                        : выровнять блок слева
        right                       : выровнять блок справа
        
        bold                        : жирный шрифт
        italic                      : курсив
        
        law-line                    : декоративная линия по центру
        
        * Структура файла:
        
        > Главный заголовок документа, расположен по центру
        <h1 class="law-title center main">
            <span class="bold">Жирный текст</span>
            <br>
            Обычный текст
            <br>
            Обычный текст
            <span class="bold">Жирный текст</span>
        </h1>
        
        -------------------------------------------------------------
        
        > Декоративная линия по центру
        <div class="law-line"></div>
        
        -------------------------------------------------------------
        
        > Заголовок раздела, расположен по центру
        <h2 class="law-title center">
            Текст
        <br>
            Текст
        </h2>
        
        > Заголовок раздела, расположен слева
        <h2 class="law-title left">
            Текст
        <br>
            Текст
        </h2>
        
        > Заголовок раздела, расположен справа
        <h2 class="law-title right">
            Текст
        <br>
            Текст
        </h2>
        
        -------------------------------------------------------------
        
        > Абзац текста
        <p class="law-text">
            Текст
        </p>
        
        > Абзац текста жирным шрифтом
        <p class="law-text bold">
            Текст
        </p>
        
        > Абзац текста, расположен слева
        <p class="law-text left">
            Текст
        </p>
        
        > Абзац текста, расположен по центру
        <p class="law-text center">
            Текст
        </p>
        
        > Абзац текста, расположен справа
        <p class="law-text right">
            Текст
        </p>
    -->
    '''
    
    html = f'''
    {comments}
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
    {document_content}
    </body>
    </html>
    '''

    with open(output_html_path, 'w', encoding='utf-8') as file:
        file.write(html)
        print("HTML file created successfully.")


###################
# Главная функция #
###################

def process_pdf_file(input_file_path, output_html_directory):
    """Обрабатывает файл PDF"""
    doc = extract_text_from_pdf(input_file_path)
    file_name = input_file_path.split('/')[-1].split('.')[0]
    output_html_path = output_html_directory + file_name + '.html'

    # print(doc)

    # Преобразование двухмерного списка в одномерный
    doc = flatten_list(doc)

    # Редактирование заголовка документа
    doc = wrap_doc_title(doc)

    # Объединение заголовков разделов, идущих друг за другом
    doc = join_articles(doc)

    # Запись в новый HTML
    create_html(doc, output_html_path)

    # Извлечение данных о законе
    # get_law_data(input_file_path)


# Пути к файлам
input_pdf = "Abu Dhabi/Direction 1/Federal_Decree_Law_№_32_of_2021_regarding_trading_companies.pdf"
output_html_directory = 'Result HTML/'

# Используем функцию process_pdf_file для обработки файла PDF
process_pdf_file(input_pdf, output_html_directory)

# Federal Law № 2 of 1971 Concerning the Union Flag
# Federal_Decree_Law_№_32_of_2021_regarding_trading_companies
# Federal_Law_№_10_of_1972_Concerning_the_emblem_of_the_United_Arab
# Federal_Law_№_47_of_2022_in_the_matter_of_corporate_and_business
# Ministerial_Resolution_№_71_of_1989_Regarding_the_procedures_for
# Resolution_of_the_Supreme_Council_of_the_Federation_№_3_of_1996
