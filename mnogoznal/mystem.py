import os
import platform
from subprocess import Popen, PIPE, STDOUT


def mystem(text):
    """Возвращает список, состоящий из списков вида [token, lemma, pos]"""

    coding = 'UTF-8'
    if platform.system() == 'Windows':
        coding = 'cp866'

    text = text.replace('—', '-')

    # Выполнение команды mystem
    # path = 'D:\Documents\Study\Projects\Python\mnogoznal\mystem'
    path = 'mystem'
    command = (path, '-e', coding, '-ndisc')
    p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    output = p.communicate(input=text.encode(coding))[0]

    # Обработка результата в считываемый вид (массив строк)
    string_output = str(output.decode(coding))
    string_output = string_output[:-2]  # В конце вывода стоит кавычка и перевод строки - не значащая информация

    string_output = string_output.replace("_", "")  # Убираем незначащий символ "_" в выводе
    string_output = string_output.replace('\\n\\n', '\s')
    sentences = string_output.split('\s')  # Деление вывода на предложения

    # Обработка каждого предложения по очереди
    # Результат каждого предложения - элемент списка sentences_array
    sentences_array = list()
    for sentence in sentences:
        if platform.system() == 'Windows':
            words = sentence.split(os.linesep)  # Деление предложений на слова
        else:
            words = sentence.split('\n')  # Деление предложений на слова
        words = [x for x in words if x != '']  # В некоторых местах появляются пустые элементы списка - удаляем

        # Обработка каждой строки так, чтобы получить для слова его токен, лемму и часть речи.
        # Результат для каждого слова записывается в список из трех элементов.
        # Все списки хранятся в списке words_array
        words_array = list()
        for word_line in words:
            start_index = word_line.find('{', )
            if start_index == -1:  # Случай, если попалось неизвестное слово
                token = word_line
                buf = [word_line, 'UNKNOWN']

            else:  # Случай, если попалось слово
                end_index = len(word_line) - 1
                token = word_line[:start_index]

                # Отбрасываем лишнюю информацию
                buf = word_line[start_index + 1:end_index].split(',')
                buf = buf[0].split('=')
                if len(buf) > 2:
                    del buf[2]

            # Оформляем результат в виде списка
            buf.insert(0, token)
            if len(buf) < 3:
                buf.insert(2, 'UNKNOWN')
            words_array.append(tuple(buf[:3]))

        sentences_array.append(words_array)
    return sentences_array


if __name__ == '__main__':
    sentences_array = mystem(input())

    for words_array in sentences_array:
        print(words_array)
