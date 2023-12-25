import math
from threading import Thread

# import time

import autopy
import cv2
import ast

import HandTrackingModule as htm
from tracking_client import TrackingClient

##########################
wCam, hCam = 1280, 720
frameR = 150  # Frame Reduction
smoothening = 7
#########################

pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
detector = htm.handDetector(detectionCon=0.7, maxHands=1)
wScr, hScr = autopy.screen.size()
print(wScr, hScr)

cli = TrackingClient()
cli.connect()
cli.sendString("Если вы видите это сообщение, значит клиент точно подключился к серверу")


def calibration():
    flag1 = cli.receiveString()
    if flag1 == 'true':
        return True
    else:
        return False


def readServer():
    global stop
    server_str = cli.receiveString()
    if len(server_str) > 0:
        if server_str == 'stop':
            print('stop')
            stop = True


th = Thread(target=readServer)
th.start()
stop = False
run = True
flag = False  # сразу в режим работы
done = True
click = True
pos_count = 0
send_pos = False
mass = []
flag_delete_point = True
x1, x2, y1, y2, i, j = 0, 0, 0, 0, 0, 1
findpoint = False
index_near_point = 0
flip = True
mode = 1
read = False
write = False

while run:
    try:
        if not read:
            with open('text.txt', 'r') as f:  # тут читаем файл
                mass = ast.literal_eval(f.read())
                read = True
        success, img = cap.read()
        img = cv2.flip(img, 1)
        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img)
        fingers = detector.fingersUp()
        cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (255, 0, 255), 2)
        cv2.putText(img, str(mode), (20, 50), cv2.FONT_HERSHEY_PLAIN, 3,
                    (255, 0, 0), 3)
        cv2.line(img, (450, 0), (450, hCam), (0, 255, 0), 10)
        # cv2.line(img, (wCam - 350, 150), (wCam, 150), (0, 255, 0), 10)
        # cv2.line(img, (wCam - 235, 0), (wCam - 235, 150), (0, 255, 0), 10)
        # cv2.line(img, (wCam - 120, 0), (wCam - 120, 150), (0, 255, 0), 10)
        if len(lmList) != 0:
            x1, y1 = lmList[8][1:]
            x2, y2 = lmList[12][1:]
            # print(str(x1) + " " + str(y1))
        if flag:
            mode = 1
            # cli.sendString(str(x1) + ' ' + str(y1) + " " + str(x2) + " " + str(y2))
            if fingers[1] == 1 and fingers[2] == 1:
                length, img, lineInfo = detector.findDistance(8, 12, img)
                # print(length)
                if length < 25:
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                    if not send_pos:
                        cli.sendString('Точка = ' + str(pos_count) + " " + str(x1) + " " + str(y1))
                        print('Точка = ' + str(pos_count) + " " + str(x1) + " " + str(y1))
                        pos_count += 1
                        send_pos = True
                        mass.append(x1)
                        mass.append(y1)
                        print(mass)
                if length > 45:
                    send_pos = False

            print(fingers)
            if fingers[1] == 1:
                x13, y13 = lmList[13][1:]  # координаты середины руки (примерно)
                if x13 < 450:
                    if (fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1
                            and fingers[4] == 1 and len(mass) >= 2):
                        # x1, y1 = lmList[4][1:]
                        # x2, y2 = lmList[17][1:]
                        if flag_delete_point:
                            print('вошёл')
                            mass.pop()
                            mass.pop()
                            flag_delete_point = False
                    else:
                        flag_delete_point = True
            if not (0 in fingers):
                flag = False
                write = False
        else:
            mode = 2
            if not write:
                with open("text.txt", "w") as output:  # при переходе в режим работы файл сохраняется с настройкой
                    output.write(str(mass))
                    write = True
            if len(mass) > 39:  # > 39
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
                            index_near_point = i  # нижний x (x1) ближайшей точки к пальцу
                            findpoint = True
                if (fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0
                        and fingers[4] == 0 and findpoint):
                    x1, y1 = lmList[8][1:]  # координаты пальца
                    length, img, lineInfo = detector.findDistance(8, 12, img)
                    len_of_line = math.sqrt(
                        (mass[index_near_point] - mass[index_near_point + 2]) ** 2 +
                        (mass[index_near_point + 1] - mass[index_near_point + 3]) ** 2)
                    if length < 45:
                        len_to_finger = math.sqrt(
                            (mass[index_near_point] - x1) ** 2 +
                            (mass[index_near_point + 1] - y1) ** 2)  # расстояние от верхней точки до пальца

                        number = len_to_finger / len_of_line * 100
                        print(number)
                        number = round(((len_to_finger / len_of_line) * 100), -1) / 10
                        print(str(number) + " test ")
                        if index_near_point > 35:
                            len_to_finger = math.sqrt(
                                (mass[index_near_point + 2] - x1) ** 2 +
                                (mass[index_near_point + 3] - y1) ** 2)  # расстояние от верхней точки до пальца
                            number = round(((len_to_finger / len_of_line) * 100), -1) / 10
                        if y1 < mass[index_near_point + 1] and index_near_point < 36:
                            number = 0
                        if x1 < mass[index_near_point] and index_near_point > 35:  # > 35
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
                        print(str(int(index_near_point / 4) + 1) + "" + str(int(number)))
                        cli.sendString(str(int(index_near_point / 4) + 1) + "" + str(int(number)))
                if len(lmList) > 0:
                    x13, y13 = lmList[13][1:]  # координаты середины руки (примерно)
                    if x13 < 450:

                        if (fingers[0] == 0 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0
                                and fingers[4] == 0 and flip):
                            flip = False
                            print('Прокрутили ручку вперед')
                            cli.sendString(str('Прокрутили ручку вперед'))
                        elif (fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0
                              and fingers[4] == 0 and flip):
                            flip = False
                            print('Прокрутили ручку назад')
                            cli.sendString(str('Прокрутили ручку назад'))
                        elif (fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0
                              and fingers[4] == 0 and flip):
                            flip = False
                            print('сбросил результаты')
                            cli.sendString(str('сбросил результаты'))
                        elif (fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0
                              and fingers[4] == 0 and flip):
                            print('сбросил обороты')
                            cli.sendString(str('сбросил обороты'))
                            flip = False
                    if (fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1
                            and not flip):
                        flip = True
                        cli.sendString('Сброс')
                        print('Сброс')
                    if (fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1
                            and fingers[4] == 0 and flip):
                        cli.sendString('Справка')
                        print('Справка')
                        flip = False
            if (fingers[0] == 0 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0
                    and fingers[4] == 1):
                flag = False
        if len(lmList) > 0:
            cli.sendString('Рука обнаружена')
        else:
            cli.sendString('Рука не обнаружена')
        for i in range(1, (len(mass) // 4) + 1):
            cv2.line(img, (mass[i * 4 - 4], mass[i * 4 - 3]),
                     (mass[i * 4 - 2], mass[i * 4 - 1]),
                     (255, 0, 255), 3)
        for i in range(1, (len(mass) // 2) + 1):
            cv2.circle(img, (mass[i * 2 - 2], mass[i * 2 - 1]), 6, (0, 255, 0), cv2.FILLED)

        # cTime = time.time()
        # fps = 1 / (cTime - pTime)
        # pTime = cTime
        cv2.imshow("Image", img)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        if stop:
            break
    finally:
        if not done:
            print('')

# Пофиксить баг с выходом за пределы рычажка
# каретка работает корректно, но нужно пофиксить баг выше
# создал линию, нужно проверять, находится ли 13 точка руки за пределами линии, возможно стоит изменить положение линии
# проверять, в каком направлении движется рука. Вариант... count = 0.
# Если координата 5 точки движется вперед с небольшой погрешностью (тестить),
# то count повышать до 5 (тестить). Если 5 набралось, совершать вращение. Затем делать сброс count
# не придумал, как проверять повторное кручение......
# Спокойной ночи..........


# идея для движения руки:
# Сделать 2 примитива или две линии перед ручкой и за ручкой
# Если какая-то точка руки сначала идёт через верхний примитив, затем через задний = движение назад
# Если наоборот, то это движение вперед
# Можно записывать в лист прохождения через эти линии и если последние 2 записи разные и их четное количество
# То считать это вращением
