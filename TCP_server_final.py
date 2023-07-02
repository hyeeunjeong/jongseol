# Python Socket Communication - Threaded TCP Streaming Server
import socket
from _thread import *
import time
import threading

import re
import argparse
from luma.core import legacy
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, CP437_FONT, TINY_FONT, SINCLAIR_FONT, LCD_FONT
serial = spi(port=0, device=0, gpio=noop())
device = max7219(serial)
# from PIL import ImageFont
# font = ImageFont.truetype("examples/pixelmix.ttf", 8)

#import RPi_I2C_driver
from RPi_I2C_LCD_driver import RPi_I2C_driver
lcd=RPi_I2C_driver.lcd(0x27)
lcd.setCursor(0,0)
#lcd.clear()

LOCK = threading.Lock()

def thread_Rx(client_socket, addr):
    # repeats until the client disconnects
    while True:
        try:
            # when message is received from client, just echo the received message
            rx_msg = client_socket.recv(1024)
            if not rx_msg:
                print('Server:: disconnected by client ({}:{})\n'.format(addr[0], addr[1]))
                break
            print('Rx_msg = {}'.format(repr(rx_msg.decode('utf-8'))))
            number=repr(rx_msg.decode('utf-8')).translate(str.maketrans('','', r"'\x0'"))
            #test=str(1)
            #rx_msg.text(number)
            #legacy.text(number)
            with canvas(device) as draw:
                text(draw, (1,1), number, fill="white", font=proportional(CP437_FONT))
            #number_int = int(number)
            if(number >= '0' and number <= '1'):
                lcd.setCursor(0,0)
                lcd.print("have a nice day!")
            elif(number >= '2' and number <= '5'):
                lcd.setCursor(0,0)
                lcd.print("keep safe drive!")
            elif(number >= '6' and number <= '9'):
                lcd.setCursor(0,0)
                lcd.print("too many people")
                #lcd.setCursor(0, 1)
                #lcd.print("caution!!")
            #time.sleep(0.2)
            #lcd.clear()
            #show_message(device, number, fill="white", font=proportional(CP437_FONT), scroll_delay=0.05)
        except ConnectionResetError as e:
            print('Server:: disconnected by client ({}:{})'.format(addr[0],addr[1]))
            break
        #time.sleep(1) # for thread_switching

HOST = '' 
PORT = 8089

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()

LOCK.acquire()
print('Server:: TCP streaming server is started now')
LOCK.release()

# when a client requests connection, the server accepts and returns a new client socket
# communication is provided using the new client socket
while True:
    LOCK.acquire()
    print('Server:: waiting connection request from next client ....\n')
    LOCK.release()
    client_socket, addr = server_socket.accept()
    LOCK.acquire()
    print('Server:: connected to a client ({}:{})'.format(addr[0], addr[1]))
    print('Server:: client_socket = ', client_socket)
    LOCK.release()
    start_new_thread(thread_Rx, (client_socket, addr))

server_socket.close()
