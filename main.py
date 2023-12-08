import time

import autopy
import cv2
import numpy as np

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
detector = htm.handDetector(detectionCon=0.8, maxHands=1)
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


flag = calibration()
click = True
pos_count = 0
send_pos = False
mass = []
flag_delete_point = True
x1, x2, y1, y2, i, j = 0, 0, 0, 0, 0, 1
while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)
    fingers = detector.fingersUp()
    cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (255, 0, 255), 2)
    if len(lmList) != 0:
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]
        # print(str(x1) + " " + str(y1))
    if flag:
        # cli.sendString(str(x1) + ' ' + str(y1) + " " + str(x2) + " " + str(y2))
        if fingers[1] == 1 and fingers[2] == 1:
            length, img, lineInfo = detector.findDistance(8, 12, img)
            # print(length)
            if length < 45:
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
        for i in range(1, (len(mass) // 4) + 1):
            cv2.line(img, (mass[i * 4 - 4], mass[i * 4 - 3]),
                     (mass[i * 4 - 2], mass[i * 4 - 1]),
                     (255, 0, 255), 3)
            cv2.circle(img, (mass[i * 4 - 4], mass[i * 4 - 3]), 6, (0, 255, 0), cv2.FILLED)
            cv2.circle(img, (mass[i * 4 - 2], mass[i * 4 - 1]), 6, (0, 255, 0), cv2.FILLED)
        print(fingers)
        if (fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1
                and fingers[4] == 0 and len(mass) > 2):
            x1, y1 = lmList[4][1:]
            x2, y2 = lmList[17][1:]
            if flag_delete_point:
                print('вошёл')
                mass.pop()
                mass.pop()
                flag_delete_point = False
        else:
            flag_delete_point = True
        if not(0 in fingers):
            flag = False
    else:
        if fingers[1] == 1:
            x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
            y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))
            clocX = plocX + (x3 - plocX) / smoothening
            clocY = plocY + (y3 - plocY) / smoothening

            autopy.mouse.move(wScr - clocX, clocY)
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            plocX, plocY = clocX, clocY

        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, str(int(fps)), (20, 50), cv2.FONT_HERSHEY_PLAIN, 3,
                    (255, 0, 0), 3)

        cv2.imshow("Image", img)
        cv2.waitKey(1)
