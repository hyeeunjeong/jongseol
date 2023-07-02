#횡단보도 위의 보행자 인식하여 전달 (하는 중)
import socket 
import time
import threading

import cv2
import numpy as np

#-- global 변수 선언
#인식 된 사람 수
n = 0
#횡단보도 좌표
crs_x = 0; crs_y = 0; crs_w = 0; crs_h = 0
check = -1

#-- 소켓을 위한 선언

HOST = "192.168.137.223" #<<<<< ip 주소 192.168.137.223
PORT = 8089
serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
serv_sock.connect((HOST, PORT))


#-- 인식된 사람수 전달 스레드

def thread_Tx(): 
        while True:
            global n
            try:
                #print("tx",n)
                tx_data = bytes([n]) 
                serv_sock.send(tx_data) 
            except Exception as e: 
                print("Client:: exception in thread_Tx - {}".format(e)) 
                serv_sock.close() 
                break
            time.sleep(1) # for thread_switching


video_path = 'CCTV영상21616다시.mp4' #<<<<< CCTV 영상
min_confidence = 0.3 #일치도 30% 이상일 때 같은 이미지로 인식

#################
# file_path = 'record.m4v'
# fps = 20
# fourcc = cv2.VideoWriter_fourcc(*'mp4v')         # 인코딩 포맷 문자
# size = (700, 400)                                # 프레임 크기
# out_frame = cv2.VideoWriter(file_path, fourcc, fps, size)
##################
#   

#-- yolo 포맷 및 클래스명 불러오기
model_file = './yolov3.weights' 
config_file = './yolov3.cfg' 
net = cv2.dnn.readNet(model_file, config_file)

classes = []
with open("./coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()] #i[0]
colors = np.random.uniform(0, 255, size=(len(classes), 3))

#-- 영상의 보행자 인식
def detectAndDisplay(frame):
    totalframe = 0
    img = cv2.resize(frame, (700, 400), fx=0.3, fy=0.2, interpolation=cv2.INTER_AREA) #확대할 때 cv2.INTER_LINEAR
    height, width, channels = img.shape #, channels

    #-- 창 크기 설정
    totalframe = totalframe + 1
    if totalframe % 5 == 1:

         blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False) #하나의 이미지를 전달

         net.setInput(blob)
         outs = net.forward(output_layers)

         #-- 탐지한 객체의 클래스 예측 
         class_ids = []
         confidences = []
         boxes = []


    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            
            if class_id == 0 and confidence > min_confidence: #yolo3에 사람 인식인 person은 1인데 -1해서 0한다
                #-- 탐지한 객체 박싱
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
               
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, min_confidence, 0.4)
    font = cv2.FONT_HERSHEY_DUPLEX

    #-- 횡단보도 영역 검출
    global crs_x, crs_y, crs_w, crs_h
    global check

    if (check == -1):

        blurred = cv2.GaussianBlur(img, (5, 5), 6)

        #횡단보도의 샐깔 영역
        lower = (160,155,155)
        upper = (200,220,220)
        thresh = cv2.inRange(blurred, lower, upper)

        #검출된 횡단보도 모핑
        kernel = np.ones((3,3), np.uint8)
        morph = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        kernel = np.ones((5,5), np.uint8)
        morph = cv2.morphologyEx(morph, cv2.MORPH_CLOSE, kernel)

        #모핑된 사진의 경계 표시
        cntrs = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cntrs = cntrs[0] if len(cntrs) == 2 else cntrs[1]

        #영역 필터
        good_contours = []
        for c in cntrs:
            area = cv2.contourArea(c)
            if area > 100:
                good_contours.append(c)

        #좋은 경계만 합성
        contours_combined = np.vstack(good_contours)

        #테두리 묶어 사각형으로
        crs_x, crs_y, crs_w, crs_h = cv2.boundingRect(contours_combined)

        check = 1

    #-- 인식된 정보들을 통하여 영상 처리 및 보행자 카운트
    count = 0
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]

            base_x = x + w/2; base_y = y + h #박스 하단 중점 좌표

            #영역 안의 보행자 카운트
            if (((base_x >= crs_x) and (base_x <= (crs_x + crs_w))) and ((base_y >= crs_y) and (base_y <= (crs_y + crs_h)))):
                #사람 표시
                color_2 = (0,255,0) #사람인식 상자 / 순서대로 b,g,r colors[i]
                cv2.rectangle(img, (x, y), (x + w, y + h), color_2, 2)
                
                count += 1
    
    #횡단보도 표시
    color_1 = (255,0,0)
    cv2.rectangle(img, (crs_x, crs_y), ((crs_x + crs_w), (crs_y + crs_h)), color_1, 2) #임시 확인용

    #탐지된 객체의 수를 출력
    txt = "DETECTED : " + str(count)
    color_txt = (255, 255, 255) #255 128 0
    cv2.putText(img, txt, (10, 30), font, 1, color_txt, 1)

    cv2.imshow("test_result", img)
    #out_frame.write(img) 

    print (count)
    global n
    n = count

#-- 영상 인식 스레드
def thread():
    cap = cv2.VideoCapture(video_path) #웹캠 사용시 video_path 0 으로 변경
    if not cap.isOpened:
        print('--(!)Error opening video capture')
        exit(0)
    while True:
        ret, frame = cap.read()
        if frame is None:
            print('--(!) No captured frame -- Break!')
            break
        detectAndDisplay(frame)

        if cv2.waitKey(1) & 0xFF == 27: #esc버튼 누를 때 종료한다
            break

    cap.release()
    #out_frame.release()
    cv2.destroyAllWindows()

#-- 작성한 스레드 돌리기
threading._start_new_thread(thread,()) 
threading._start_new_thread(thread_Tx,()) #<<<<잠깐만 임시로 꺼두고 실향허는거

while True:
    pass