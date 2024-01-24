import math
import os
import sys
from threading import Thread

import cv2
import ast

import HandTrackingModule as htm
from tracking_client import TrackingClient

wCam, hCam = 1280, 720   # Характеристики камеры (ширина и высота в пикселях)
frameR = 150  # отступ от границ камеры

# Код для считывания видео с камеры
cap = cv2.VideoCapture(0) # Если камер несколько, изменить цифру в аргументе
cap.set(3, wCam)
cap.set(4, hCam)
detector = htm.handDetector(detectionCon=0.7, maxHands=1) # объект для считывания ОДНОЙ руки

cli = TrackingClient()   # создаём объект-клиент
cli.connect() # стучимся на сервер
cli.sendString("Если вы видите это сообщение, значит клиент точно подключился к серверу")


# def calibration():
#     flag1 = cli.receiveString()
#     if flag1 == 'true':
#         return True
#     else:
#         return False

# метод для чтений сообщений с сервера
def readServer():
    global stop
    server_str = cli.receiveString()
    if len(server_str) > 0:
        if server_str == 'stop':
            print('stop')
            stop = True


th = Thread(target=readServer) # читаем в отдельном потоке
th.start()
stop = False  # флаг для остановки python приложения
flag = False  # True - отладка, False - режим работы
create_pos = False # Переключатель для режима отладки (используется при создании точки)
mass = [] # Массив точек
flag_delete_point = True # Переключатель удаления точек
x1, x2, y1, y2, i, j = 0, 0, 0, 0, 0, 1
findpoint = False # Включается, если выбран рычажок в режиме работы
index_near_point = 0 # Индекс в массиве ближайшей точки (x координата)
flip = True  # Переключатель разных жестов
mode = 1 # Режим работы для вывода на экран. 1 = Отладка, 2 - Работа
read = False # Флаг для чтения файла
write = False # Флаг для записи файла

while True:
    # Читаем файл с координатами точек 1 раз
    if not read:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        with open('text.txt', 'r') as f:
            mass = ast.literal_eval(f.read())
            read = True
    # Записываем в переменные пальцы, координаты точек руки, изображение
    success, img = cap.read()
    img = cv2.flip(img, 1)
    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)
    fingers = detector.fingersUp()
    # Выводим на экран прямоугольник (примерная область видимости руки), режим работы и разграничительную линию
    cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (255, 0, 255), 2)
    cv2.putText(img, str(mode), (20, 50), cv2.FONT_HERSHEY_PLAIN, 3,
                (255, 0, 0), 3)
    cv2.line(img, (450, 0), (450, hCam), (0, 255, 0), 10)

    # Берем координаты 8 и 12 точки руки
    if len(lmList) != 0:
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]
    # для режима отладки
    if flag:
        mode = 1

        # Если подняты указательный и средний палец, то вычисляем расстояние между их концами
        if fingers[1] == 1 and fingers[2] == 1:
            length, img, lineInfo = detector.findDistance(8, 12, img)
            if length < 25: # Если расстояние маленькое, то создаем точку 1 раз
                cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                if not create_pos:
                    create_pos = True
                    mass.append(x1)
                    mass.append(y1)
                    print(mass)
            if length > 45: # Если расстояние большое, то сбрасываем флаг создания точки
                create_pos = False

        # Если поднят указательный палец
        if fingers[1] == 1:
            x13, y13 = lmList[13][1:]  # координаты середины руки (примерно)
            # Если рука находится в правой части арифмометра
            if x13 < 450:
                if (fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1
                        and fingers[4] == 1 and len(mass) >= 2): # подняты все пальцы, кроме большого и есть точки
                    if flag_delete_point: # удаляем последнюю точку
                        mass.pop()
                        mass.pop()
                        flag_delete_point = False
                else:
                    flag_delete_point = True # сбрасываем флаг удаления
        if not (0 in fingers): # Если поднять все 5 пальцев, то переходим в режим работы
            flag = False
            write = False
    else: # Для режима работы
        mode = 2
        if not write:
            with open('text.txt', 'w') as output:  # при переходе в
                # режим работы файл сохраняется с настройкой
                output.write(str(mass))
                write = True
        if len(mass) > 39:  # Если выставили как минимум 10 точек
            # Если поднят только указательный палец, то ищем ближайший рычажок
            if (fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0
                    and fingers[4] == 0):
                minlen = 100000
                for i in range(0, len(mass) - 1, 4):
                    x1 = mass[i]  # x точки
                    y1 = mass[i + 1]  # y точки
                    x2, y2 = lmList[8][1:]  # координаты пальца
                    len_to_point = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)  # расстояние до точки
                    if len_to_point < minlen:
                        minlen = len_to_point
                        index_near_point = i  # верхний x (x1) ближайшей точки к пальцу
                        findpoint = True
            # Если подняты указательный и средний палец и ближайший рычажок найден
            if (fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0
                    and fingers[4] == 0 and findpoint):
                x1, y1 = lmList[8][1:]  # координаты пальца
                length, img, lineInfo = detector.findDistance(8, 12, img)
                # вычисляем длинну линии (борозды для рычажка)
                len_of_line = math.sqrt(
                    (mass[index_near_point] - mass[index_near_point + 2]) ** 2 +
                    (mass[index_near_point + 1] - mass[index_near_point + 3]) ** 2)
                # если указательный и средний палец сдвинуты вместе
                if length < 45:
                    len_to_finger = math.sqrt(
                        (mass[index_near_point] - x1) ** 2 +
                        (mass[index_near_point + 1] - y1) ** 2)  # расстояние от верхней точки до пальца

                    # вычисляем текущую цифру на арифмометре
                    number = round(((len_to_finger / len_of_line) * 100), -1) / 10
                    if index_near_point > 35: # для каретки (последней точки) другие вычисления
                        len_to_finger = math.sqrt(
                            (mass[index_near_point + 2] - x1) ** 2 +
                            (mass[index_near_point + 3] - y1) ** 2)  # расстояние от левой точки до пальца
                        number = round(((len_to_finger / len_of_line) * 100), -1) / 10 # значение каретки
                    # Условия для того, чтобы не отправить невозможных значений на сервер
                    if y1 < mass[index_near_point + 1] and index_near_point < 36:
                        number = 0
                    if x1 < mass[index_near_point] and index_near_point > 35:
                        number = 0
                    if number > 9:
                        number = 9
                    if number < 1:
                        number = 0
                    if index_near_point > 35:
                        if number < 1:
                            number = 1
                        if number > 8:
                            number = 8
                    # отправляем данные на сервер в виде строки формата "номер рычажка+цифра на рычажке" пример: "21"
                    cli.sendString(str(int(index_near_point / 4) + 1) + "" + str(int(number)))
            if len(lmList) > 0: # Если рука найдена камерой
                x13, y13 = lmList[13][1:]  # координаты середины руки (примерно)
                if x13 < 450: # если рука справа (за разграничительной линией)
                    if (fingers[0] == 0 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0
                            and fingers[4] == 0 and flip): # кулак = вращение ручки вперед
                        flip = False
                        cli.sendString(str('Прокрутили ручку вперед'))
                    elif (fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0
                          and fingers[4] == 0 and flip): # кулак + выставленный большой палец = вращение ручки назад
                        flip = False
                        cli.sendString(str('Прокрутили ручку назад'))
                    elif (fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0
                          and fingers[4] == 0 and flip): # большой и указательный палец сбрасывают показатель результата
                        flip = False
                        cli.sendString(str('сбросил результаты'))
                    elif (fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0
                          and fingers[4] == 0 and flip): # большой, указательный и средний палец сбрасывают обороты
                        cli.sendString(str('сбросил обороты'))
                        flip = False
                if (fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1
                        and not flip): # 5 пальцев сбрасывают флаг последнего жеста (сделано для того, чтобы на сервер
                    # не поступало множество жестов сразу, а только 1
                    flip = True
                    cli.sendString('Сброс')
                if (fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1
                        and fingers[4] == 0 and flip): # если показать средний, указательный и безымянный палец
                    # Появится справка. Для скрытия сбросить и повторить жест
                    cli.sendString('Справка')
                    flip = False
        if (fingers[0] == 0 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0
                and fingers[4] == 1): # показать один мизинец для перехода в режим отладки
            flag = True
    if len(lmList) > 0: # если есть координаты точек руки, то рука обнаружена
        cli.sendString('Рука обнаружена')
    else: # иначе отправляем данные, что рука не обнаружена
        cli.sendString('Рука не обнаружена')
    # 2 массива для прохождения по координатам в массиве и отрисовки точек и линий примитивов (рычажков)
    for i in range(1, (len(mass) // 4) + 1):
        cv2.line(img, (mass[i * 4 - 4], mass[i * 4 - 3]),
                 (mass[i * 4 - 2], mass[i * 4 - 1]),
                 (255, 0, 255), 3)
    for i in range(1, (len(mass) // 2) + 1):
        cv2.circle(img, (mass[i * 2 - 2], mass[i * 2 - 1]), 6, (0, 255, 0), cv2.FILLED)

    # выводим изображение на экран
    cv2.imshow("Image", img)
    key = cv2.waitKey(1)
    if key == ord('q'): # остановка по нажатию на q
        break
    if stop: # остановка при получении сигнала с сервера
        break
