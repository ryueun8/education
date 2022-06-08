from PyQt5.QtWidgets import QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox, QApplication, QListWidget,QListWidgetItem
from PyQt5.QtCore import QThread, pyqtSlot
from PyQt5.QtGui import QColor, QIcon
from PyQt5 import QtCore
from PyQt5 import uic
import sys
from socket import *
import pandas as pd


ui_form = uic.loadUiType("현진.ui")[0]

class SocketClient(QThread):
    add_chat = QtCore.pyqtSignal(str)
    add_user = QtCore.pyqtSignal(str) #->단일 채팅방이라서 필요 없을 것 같기도 하고, 선생님 클라이언트는 필요할 것 같기도하고


    def __init__(self, parent=None):
        super().__init__()
        self.main = parent
        self.is_run = False

    def connect_cle(self):
        self.cnn = socket(AF_INET, SOCK_STREAM)
        self.cnn.connect(('127.0.0.1', 9070))
        self.cnn.send('student'.encode())
        self.add_chat.emit('선생님과 연결되었습니다.')
        self.is_run = True

    def run(self):
        while True:
            data = self.cnn.recv(2048)

            if data.decode().split(",")[0] == '/teacher':
                self.add_user.emit(data.decode())
            else:
                self.add_chat.emit(data.decode())
    def send_msg(self, msg):
        self.cnn.send(f'{msg}'.encode())
        self.add_chat.emit(msg)


class student_client(QMainWindow, ui_form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.start_sock = SocketClient() #소켓 연결

        self.name = [] #회원가입용 리스트 판다스로 묶어서 서버로 보낼 것
        self.ID = []
        self.PW = []

        self.stackedWidget.setCurrentIndex(0) #시작 페이지
        self.btn_hide() #로그인 전 불필요한 버튼 가리기
        self.join_widget.hide() #회원가입 창 가리기
        self.tabWidget.hide() #학습/QNA용 탭 위젯 가리기
        self.login_ok.clicked.connect(self.login_event) #로그인 하면 로그인 이벤트로
        self.main_text.setText("로그인하십셔") #디폴트 텍스트 나중에는 프로그램 이름으로 변경

        self.btn_main.clicked.connect(self.main_page)
        self.btn_info.clicked.connect(self.my_page)
        self.btn_qna.clicked.connect(self.qna_page)
        self.btn_counsel.clicked.connect(self.counsel_page)
        self.btn_join.clicked.connect(self.join_event)


    def text_clear(self): #입력창 비우기
        self.input_id.clear()
        self.input_pw.clear()
    def btn_hide(self):
        self.btn_main.hide()
        self.btn_info.hide()
        self.btn_counsel.hide()
        self.btn_qna.hide()
        self.btn_edustart.hide()
    def btn_show(self):
        self.btn_main.show()
        self.btn_info.show()
        self.btn_counsel.show()
        self.btn_qna.show()
        self.btn_edustart.show()

    def login_event(self): #공백일 때 확인창 추가해야함, db랑 연결도 해야함
        id = self.input_id.text()
        pw = self.input_pw.text()

        if id == '1234' and pw == '1234': #나중에 디비랑 연결해야함
            QMessageBox.about(self, '로그인 성공', '메인페이지로 이동합니다.')
            self.main_page()
            self.text_clear()
            self.btn_show()
        elif pw != '1234':
            QMessageBox.about(self, '확인', '비밀번호 잘못. 확인부탁')
            self.text_clear()
        elif id != '1234':
            QMessageBox.about(self,'확인', '없는 아이디입니다. 확인부탁')
            self.text_clear()

    def join_event(self): #이거 다시 만들어야함
        self.join_widget.show()

        plag = True

        while plag:

            a = self.join_name.text()
            b = self.join_id.text()
            c = self.join_pw.text()
            d = self.join_pw_re.text()

            if c == d:
                self.name.append(a)
                self.ID.append(b)
                self.PW.append(c)
                plag = False


            elif c != d:
                QMessageBox.about(self, '확인', '패스워드 다름. 확인부탁')
                self.join_pw.clear()
                self.join_pw_re.clear()
        print(self.name)
        print(self.ID)
        print(self.PW)


    def main_page(self): #메인페이지
        self.main_text.setText("메인페이지입니다")
        self.stackedWidget.setCurrentIndex(1)
        self.btn_edustart.clicked.connect(self.exercise)

    def exercise(self): #학습하는 함수
        self.tabWidget.show()
        self.btn_edustart.hide()


    def my_page(self):
        self.main_text.setText("마이페이지입니다")
        self.stackedWidget.setCurrentIndex(2)
    def counsel_page(self):
        self.main_text.setText("상담페이지입니다")
        self.stackedWidget.setCurrentIndex(3)
    def qna_page(self):
        self.main_text.setText("Q&A 페이지입니다")
        self.stackedWidget.setCurrentIndex(4)






if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = student_client()
    myWindow.setWindowTitle('서버 관리 프로그램')
    myWindow.show()
    app.exec_()