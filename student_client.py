from PyQt5.QtWidgets import QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox, QApplication, QListWidget,QListWidgetItem
from PyQt5.QtCore import QThread, pyqtSlot
from PyQt5.QtGui import QColor, QIcon
from PyQt5 import QtCore
from PyQt5 import uic
import sys
from socket import *
import pandas as pd
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import random
import datetime


ui_form = uic.loadUiType("student.ui")[0]

class SocketClient(QThread):
    add_chat = QtCore.pyqtSignal(str)
    add_user = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.main = parent
        self.is_run = False #실행 플래그

    def connect_cle(self):
        self.cnn = socket(AF_INET, SOCK_STREAM)
        self.cnn.connect(('localhost', 8081))
        self.add_chat.emit("채팅 서버 접속완료")
        self.is_run = True

    def run(self):
        while True:
            data = self.cnn.recv(2048)
            data = data.decode()
            if not data:
                break
            self.add_chat.emit(data)

    def send(self, msg):
        self.cnn.send(f'{msg}'.encode())
        self.add_chat.emit(msg)



class student_client(QMainWindow, ui_form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.threading = SocketClient()

        self.n = 0

        self.name = [] #회원가입용 리스트 판다스로 묶어서 서버로 보낼 것
        self.ID = []
        self.PW = []

        self.qna= []

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

        self.btn_chat.clicked.connect(self.connect_server)


    def connect_server(self):
        #전송버튼 연결하고, 텍스트 가져오기

        self.threading.add_chat.connect(self.add_chat)
        self.threading.connect_cle()
        self.threading.start()


    def add_chat(self, msg):
        self.chat_window.appendPlainText(msg) #브라우저에 글자 추가



    def text_clear(self): #입력창 비우기
        self.input_id.clear()
        self.input_pw.clear()
    def btn_hide(self): #버튼 숨기기
        self.btn_main.hide()
        self.btn_info.hide()
        self.btn_counsel.hide()
        self.btn_qna.hide()
        self.btn_edustart.hide()
    def btn_show(self): #버튼 보이기
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

        self.qna_widget.setColumnCount(5)
        self.qna_widget.setHorizontalHeaderLabels(["제목", "작성자", "날짜", "내용보기", "답변상태"])
        self.qna_widget.setRowCount(50)

        # self.qna_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.qna_widget.cellDoubleClicked.connect(self.qna_contents) #더블 클릭하면 함수 연결
        self.qna_widget.setEditTriggers(QAbstractItemView.NoEditTriggers) #셀 수정 못하게
        self.run = False
        self.btn_q_ok.clicked.connect(self.qna_content)



    def qna_content(self):
        self.run = True
        self.qna_title = self.q_title.text()
        self.qna_name = self.q_name.text()
        self.qna_date = str(datetime.date.today())
        self.qna_text = self.q_text.toPlainText()
        if not self.qna_title:
            QMessageBox.about(self,'확인', '공백 ㄴㄴ')
            self.run = False
        elif not self.qna_name:
            QMessageBox.about(self,'확인', '공백 ㄴㄴ')
            self.run = False
        elif not self.qna_text:
            QMessageBox.about(self,'확인', '공백 ㄴㄴ')
            self.run = False


        while self.run:

            self.qna_widget.setItem(self.n, 0, QTableWidgetItem(self.qna_title))
            self.qna_widget.setItem(self.n, 1, QTableWidgetItem(self.qna_name))
            self.qna_widget.setItem(self.n, 2, QTableWidgetItem(self.qna_date))
            self.qna_widget.setItem(self.n, 3, QTableWidgetItem(self.qna_text))
            self.qna_widget.setItem(self.n, 4, QTableWidgetItem("답변없음"))

            self.n += 1
            self.q_title.clear()
            self.q_name.clear()
            self.q_text.clear()
            self.run = False


    @pyqtSlot()
    def qna_contents(self):
        self.label_title.clear()
        self.qna_browser.clear()

        loc_text = self.qna_widget.currentItem()
        title_c = self.qna_widget.currentColumn() - 3
        qna_text = loc_text.text()
        title_r = self.qna_widget.currentRow()
        loc_title = self.qna_widget.item(title_r, title_c)
        title_name = loc_title.text()

        self.qna_browser.append(qna_text) #여기서 self.qna_text는 리스트에서 가져오게끔
        self.label_title.setText(title_name)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = student_client()
    myWindow.setWindowTitle('학생 프로그램')
    myWindow.show()
    app.exec_()