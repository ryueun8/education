import pickle

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox, QApplication, QListWidget,QListWidgetItem,QWidget, QLabel
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QColor, QIcon, QPixmap, QImage
from PyQt5 import QtCore
from PyQt5 import uic
import sys
from socket import *
import pandas as pd
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import random
import time
import datetime
import sqlite3
import urllib.request
import requests

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt




ui_form = uic.loadUiType("student.ui")[0]

class student_client(QMainWindow, ui_form):
    def __init__(self):
        super().__init__()

        self.conn = sqlite3.connect('student_db.db', check_same_thread=False)
        self.cur = self.conn.cursor()

        # 서버 아이피
        self.server_ip = '127.0.0.1'
        # 서버 포트번호
        self.server_port = 9071
        # 서버에 소켓 연결
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.client_socket.connect((self.server_ip, self.server_port))
        self.setupUi(self)
        self.stackedWidget.setCurrentIndex(0)
        self.online_nickname_list = []
        self.role = '학생'
        self.name = ''
        self.id = ''
        self.pw = ''
        self.pw_re = ''
        self.partner_id = ''
        self.partner_name = ''
        self.ID = []
        self.PW = []

        self.qna_list = []

        self.from_db = [] #문제 목록
        self.bird_name = [] #새 이름
        self.quiz_ox = '' #퀴즈 정오표


        self.crc = ClientReceiveChat(self)
        self.crc.display_received_message.connect(self.display_received_message_on_textbrowser)
        self.crc.join_success.connect(self.join_success)
        self.crc.join_fail.connect(self.join_fail)
        self.crc.login_success.connect(self.login_success)
        self.crc.login_fail.connect(self.login_fail)
        self.crc.online_partner_list.connect(self.display_online_partner_list)
        self.crc.counsel_check.connect(self.counsel_check)
        self.crc.counsel_success.connect(self.counsel_success)
        self.crc.counsel_fail.connect(self.counsel_fail)
        self.crc.counsel_end.connect(self.counsel_end)

        self.crc.qna_receive_msg.connect(self.update_qna)
        # self.crc.exercise_info.conncet(self.exercise_quiz)
        self.crc.quiz_bird_name.connect(self.test_page)

        self.crc.start()


        self.now = time.strftime('%H:%M:%S')
        self.btn_chat.setDisabled(True)
        self.btn_counsel_end.setDisabled(True)

        # 버튼 연결
        # 회원가입 버튼
        self.btn_join.clicked.connect(self.join_event)
        self.btn_join_ok.clicked.connect(self.push_join_enter_button)

        # 로그인 버튼
        self.login_ok.clicked.connect(self.push_login_enter_button)
        self.btn_chat.clicked.connect(self.push_send_button)
        self.btn_hide()  # 로그인 전 불필요한 버튼 가리기
        self.join_widget.hide()  # 회원가입 창 가리기
        # self.tabWidget.hide()  # 학습/QNA용 탭 위젯 가리기
        self.stackedWidget_2.hide()

        self.btn_main.clicked.connect(self.main_page)
        self.btn_info.clicked.connect(self.my_page)
        self.btn_qna.clicked.connect(self.qna_page)
        self.btn_counsel.clicked.connect(self.counsel_page)
        self.btn_counsel_end.clicked.connect(self.exit_counsel)


        self.btn_counsel_request.clicked.connect(self.request_counsel_partner_list)

        self.bird_dic = {'나무발발이': 'bird1',
                         '가창오리': 'bird2',
                         '개꿩': 'bird3',
                         '멋쟁이새': 'bird4',
                         '긴꼬리딱새': 'bird5',
                         '긴점박이올빼미': 'bird6',
                         '까마귀': 'bird7',
                         '까막딱다구리': 'bird8',
                         '까치': 'bird9',
                         '깝작도요': 'bird10',
                         '꼬까참새': 'bird11',
                         '꾀꼬리': 'bird12',
                         '노랑딱새': 'bird13',
                         '논병아리': 'bird14',
                         '덤불해오라기': 'bird15',
                         '독수리': 'bird16',
                         '두루미': 'bird17',
                         '따오기': 'bird18',
                         '뜸부기': 'bird19',
                         '매': 'bird20',
                         '메추라기': 'bird21',
                         '멧비둘기': 'bird22',
                         '물수리': 'bird23',
                         '방울새': 'bird24',
                         '북방쇠박새': 'bird25',
                         '붉은발도요': 'bird26'}



    def join_event(self):
        self.join_widget.show()

    # 로그인 전 버튼 숨기는 메서드
    def btn_hide(self): #버튼 숨기기
        self.btn_main.hide()
        self.btn_info.hide()
        self.btn_counsel.hide()
        self.btn_qna.hide()


    # 로그인 후 버튼 보이게 하는 메서드
    def btn_show(self):
        self.btn_main.show()
        self.btn_info.show()
        self.btn_counsel.show()
        self.btn_qna.show()

    # 회원가입 확인버튼 눌렀을 때 메서드
    # 학생/교사 구분하는 값도 받아야됨
    def push_join_enter_button(self):
        # 입력한 성명
        self.name = self.join_name.text()
        # 입력한 아이디
        self.id = self.join_id.text()
        # 입력한 비밀번호
        self.pw = self.join_pw.text()
        # 입력한 비밀번호 확인
        self.pw_re = self.join_pw_re.text()
        if ' ' in self.name:
            QMessageBox.warning(self, '주의', '이름에 공백이 포함될 수 없습니다.', QMessageBox.Yes)
        elif len(self.name) < 2:
            QMessageBox.warning(self, '주의', '이름을 2자 이상 입력해주세요.', QMessageBox.Yes)
        elif self.id == '':
            QMessageBox.warning(self, '주의', '아이디를 입력해주세요.', QMessageBox.Yes)
        elif self.pw == '':
            QMessageBox.warning(self, '주의', '비밀번호를 입력해주세요.', QMessageBox.Yes)
        if self.pw != self.pw_re:
            QMessageBox.warning(self, '비밀번호 오류', '비밀번호가 일치하지 않습니다. 확인해주세요.', QMessageBox.Yes)
        try:
            info = 'student' + chr(1111) + self.id + chr(1111) + self.pw + chr(1111) + self.name
            self.client_socket.send(info.encode())
        except:
             QMessageBox.warning(self, '서버에 회원정보를 전송하지 못했습니다.', QMessageBox.Yes)

        self.cur.execute("insert into join_student(id) values(?)", (self.id,))
        self.conn.commit()



    # 로그인 확인버튼 눌렀을 때 메서드
    def push_login_enter_button(self):
        # 입력한 아이디
        self.id = self.input_id.text()
        # 입력한 비밀번호
        self.pw = self.input_pw.text()
        # 선택한 직업
        info = 'student' + chr(2222) + self.id + chr(2222) + self.pw
        self.client_socket.send(info.encode())

    def main_page(self): #메인페이지
        self.main_text.setText("메인페이지입니다")
        self.stackedWidget.setCurrentIndex(1)
        self.btn_exercise.clicked.connect(self.exercise)

        self.stackedWidget_2.show()
        self.btn_test.clicked.connect(self.quiz_start)


    def exercise(self): #학습하는 함수 / 얘가 두 번 돎
        self.cur.execute("select * from birdselect")
        self.bird_info = self.cur.fetchall()
        print("bird_info", self.bird_info[0][0]) #나무발발이

        self.cur.execute("select * from learning")
        self.learning_info = self.cur.fetchall()

        for j in range(len(self.learning_info)):
            if self.learning_info[j][0] == self.id:
                for i in range(len(self.bird_info)):
                    if self.bird_widget.item(25) == None:
                        if self.learning_info[0][i+1] == 1:
                            self.bird_widget.insertItem(i, self.bird_info[i][0] + " (학습완료)")
                        elif self.learning_info[0][i+1] == 0:
                            self.bird_widget.insertItem(i, self.bird_info[i][0])
                    elif self.bird_widget.item(25) != None:
                        pass
            elif self.learning_info[j][0] != self.id:
                continue

        self.bird_widget.itemClicked.connect(self.exercise_2)
        self.bird_widget.itemClicked.connect(self.send_learning_progress)

    def send_learning_progress(self):
        selected_bird = self.bird_widget.currentItem().text().strip(" (학습완료)")
        print(selected_bird)
        print('kbkb', self.bird_dic[selected_bird])
        progress_msg = self.id + chr(2020) + (self.bird_dic[selected_bird])
        self.client_socket.send(progress_msg.encode())

    def exercise_2(self): #리스트 클릭 되었을 때, 상호작용하는 함수
        a = self.bird_widget.currentRow() #선택된 열
        self.label_22.clear() #d이름
        self.label_23.clear() #과명
        self.label_17.clear() #이미지
        self.bird_explain.clear() #종특징
        bird_name = self.bird_info[a][0]
        bird_family = self.bird_info[a][1]
        bird_explain = self.bird_info[a][2]
        bird_image = self.bird_info[a][3]


        self.label_22.setText(bird_name)
        self.label_23.setText(bird_family)

        url_image = f"{bird_image}"
        image = QImage()
        image.loadFromData(requests.get(url_image).content)
        self.label_17.setPixmap(QPixmap(image))

        self.bird_explain.append(bird_explain)

        self.cur.execute("select id from join_student")
        name = self.cur.fetchall()
        std_id = []
        for i in range(len(name)):
            std_id.append(name[i][0])

        if self.id not in std_id:
            query = "insert into learning(userID, %s) values(?, ?)"%self.bird_dic[bird_name]
            self.cur.execute(query, (self.id, '1'))
            self.conn.commit()

        else:
            query1 = "update learning set %s = ? where userID = ?" %self.bird_dic[bird_name]
            self.cur.execute(query1, ('1', self.id))
            self.conn.commit()


    def quiz_start(self): #서버에 요청해서 디비에서 문제 받아오기
        self.stackedWidget_2.setCurrentIndex(1)
        self.btn_test.setDisabled(True)
        self.btn_exercise.hide()
        self.client_socket.send(chr(1818).encode())

    @pyqtSlot(str) #새 이름 서버에서 받음/ quiz 관련
    def test_page(self, a):
        bird_name = a[:-1].split(chr(1818))

        for i in range(len(bird_name)):
            self.cur.execute(f"select * from birdselect where birdName = '{bird_name[i]}'")
            a = self.cur.fetchall()
            #문제 정보가 self.from_db에 담아져있음
            self.from_db.append(a)

        for i in range(len(bird_name)):
            self.bird_name.append(self.from_db[i][0][0])
        self.bird_call()

    def bird_call(self):
       # 여기부터는 문제 띄울 값 가져오는 부분
        self.bird_name_1 = self.from_db[0][0][0]
        bird_family_1 = self.from_db[0][0][1]
        bird_explain_1 = self.from_db[0][0][2]
        bird_image_1 = self.from_db[0][0][3]
        # 여기부터는 문제 띄우는 부분
        self.label_26.setText(bird_family_1)
        self.study_bird_2.append(bird_explain_1)
        url_image = f"{bird_image_1}"
        image = QImage()
        image.loadFromData(requests.get(url_image).content)
        self.label_25.setPixmap(QPixmap(image))

        self.Q_pushButton.clicked.connect(self.q_answer)


    def q_answer(self):

        a = self.lineEdit.text()

        try:
            if a.rstrip() == self.from_db[0][0][0]:
                print("정답")
                self.quiz_ox += '1,'

            elif a.rstrip() != self.from_db[0][0][0]:
                print("오답")
                self.quiz_ox += '0,'

            del self.from_db[0]
            self.label_26.clear()
            self.study_bird_2.clear()
            self.label_25.clear()
            self.lineEdit.clear()

            bird_family_1 = self.from_db[0][0][1]

            bird_explain_1 = self.from_db[0][0][2]
            bird_image_1 = self.from_db[0][0][3]
            # 여기부터는 문제 띄우는 부분
            self.label_26.setText(bird_family_1)
            self.study_bird_2.append(bird_explain_1)
            url_image = f"{bird_image_1}"
            image = QImage()
            image.loadFromData(requests.get(url_image).content)
            self.label_25.setPixmap(QPixmap(image))
        except:
            QMessageBox.about(self, '시험 끝', f'결과보기 {self.quiz_ox}')
            print("결과", self.quiz_ox)
            self.study_bird_2.append("시험이 종료되었습니다.")
            self.client_socket.send((self.id + chr(5323) + self.quiz_ox).encode())
            self.btn_exercise.show()
            #학생 점수 통계 및 포인트
            self.std_score.display(int((self.quiz_ox.count('1') / (self.quiz_ox.count('1') + self.quiz_ox.count('0'))) * 100))

    def my_page(self):
        self.std_id.setText(self.id)
        self.main_text.setText("마이페이지입니다")
        self.stackedWidget.setCurrentIndex(2)

    def counsel_page(self):
        self.main_text.setText("상담페이지입니다")
        self.stackedWidget.setCurrentIndex(3)

    def qna_page(self):

        self.q_name.setText(self.id)
        self.q_name.setDisabled(True)

        self.main_text.setText("Q&A 페이지입니다")
        self.stackedWidget.setCurrentIndex(4)

        self.qna_widget.setColumnCount(5)
        self.qna_widget.setHorizontalHeaderLabels(["제목", "아이디", "날짜", "내용보기", "답변상태"])
        self.qna_widget.setRowCount(50)
        self.qna_widget.setColumnWidth(0, 200)

        self.qna_widget.cellClicked.connect(self.qna_contents) #더블 클릭하면 함수 연결
        self.qna_widget.setEditTriggers(QAbstractItemView.NoEditTriggers) #셀 수정 못하게
        self.run = False
        self.btn_q_ok.clicked.connect(self.qna_content)
        self.F5.clicked.connect(self.refresh) #디비에서 qna글 가져오는 버튼



    def qna_content(self):
        self.run = True
        self.qna_title = self.q_title.text()
        self.qna_name = self.id
        self.qna_date = str(datetime.date.today())
        self.qna_text = self.q_text.toPlainText()
        self.answer_state = '답변없음'

        self.send_qna = self.qna_title + chr(0000) + self.qna_name + chr(0000) + self.qna_date + chr(0000) + self.qna_text + chr(0000) + self.answer_state
        self.client_socket.send(self.send_qna.encode())


        if not self.qna_title:
            QMessageBox.about(self,'확인', '공백 ㄴㄴ')
            self.run = False
        elif not self.qna_text:
            QMessageBox.about(self,'확인', '공백 ㄴㄴ')
            self.run = False
        QMessageBox.about(self, "확인", "등록된 글은 수정/삭제가 불가능합니다. 등록하시겠습니까?")
        self.q_title.clear()
        self.q_name.clear()
        self.q_text.clear()

    def refresh(self): #db에서 가져오는 것
        self.qna_widget.clearContents()
        self.client_socket.send("qna글요청".encode())
        print("self.id", self.id)


    @pyqtSlot(str) #db에서 학생 qna을 가져오기
    # qna 글 업데이트, receieve 메세지에서 값 받기
    def update_qna(self, a):
        b = a[:-1].split(chr(1003))
        for i in range(len(b)):
            aa = b[i].split(chr(1001))
            self.qna_widget.setItem(i, 0, QTableWidgetItem(aa[0]))
            self.qna_widget.setItem(i, 1, QTableWidgetItem(aa[1]))
            self.qna_widget.setItem(i, 2, QTableWidgetItem(aa[2]))
            self.qna_widget.setItem(i, 3, QTableWidgetItem(aa[3]))
            self.qna_widget.setItem(i, 4, QTableWidgetItem(aa[4]))


    # 상담 요청 버튼 눌렀을 때 -> 서버에 온라인 상태의 선생님 리스트 데이터 요청함
    def request_counsel_partner_list(self):
        request = 'teacher' + chr(5555)
        self.client_socket.send(request.encode())
        select_partner_popup.show()

    # 상담페이지에서 보내기 버튼 눌렀을 때 입력한 메세지 보내는 메서드
    def push_send_button(self):
        # 유저가 입력한 메세지
        writed_message = self.std_text.toPlainText()
        print(writed_message)
        # 실제 채팅창에 입력될 메세지 (입력 시간 + 닉네임 + 메세지)
        final_message_to_send = f'[{self.now}] {self.name}({self.role}) : \n{writed_message}' + chr(
            8888) + self.partner_id
        # 서버로 메세지 보냄
        self.client_socket.send(final_message_to_send.encode())
        # 전송한 메세지를 텍스트에딧에서 지움
        self.std_text.clear()
        self.textBrowser_1.append(final_message_to_send.split(chr(8888))[0])

    # 상담페이지에서 나갔을 때 상담 종료 알림 메서드
    def exit_counsel(self):
        message = '상대방이 나갔습니다. 상담이 종료됩니다.' + chr(8999) + self.partner_id
        print(message)
        self.client_socket.send(message.encode())
        QMessageBox.information(self, '상담 종료', '상담이 종료되었습니다.', QMessageBox.Yes)
        self.label_teacher.setText('')
        self.label_student.setText('')
        self.btn_chat.setDisabled(True)
        self.btn_counsel_end.setDisabled(True)

    # 회원가입 성공했을 때
    @pyqtSlot()
    def join_success(self):
        QMessageBox.information(self, '회원가입 성공', '회원정보가 저장되었습니다.', QMessageBox.Yes)

    # 회원가입 실패했을 때
    @pyqtSlot()
    def join_fail(self):
        QMessageBox.information(self, '회원가입 실패', '아이디가 중복됩니다. 다른 아이디를 사용해주세요.', QMessageBox.Yes)

    # 로그인 성공했을 때
    @pyqtSlot(str)
    def login_success(self, received_message):
        self.name = received_message.split(chr(3333))[0]
        QMessageBox.information(self, '로그인 성공', '메인페이지로 넘어갑니다.', QMessageBox.Yes)
        self.main_page()
        self.btn_show()  # 로그인 후 버튼 보이기
        # self.tabWidget.show()  # 학습/QNA용 탭 위젯 보이기

    # 로그인 실패했을 때
    @pyqtSlot()
    def login_fail(self):
        QMessageBox.warning(self, '로그인 실패', 'ID/PW를 확인해주세요.', QMessageBox.Yes)

    # 서버로부터 받은 상담메세지를 채팅창에 띄우는 슬롯
    @pyqtSlot(str)
    def display_received_message_on_textbrowser(self, received_message):
        # print('received_message: ', received_message)
        self.textBrowser_1.append(received_message)


    # 서버로부터 받은 온라인 클라이언트 리스트를 띄우는 슬롯
    @pyqtSlot(str)
    def display_online_partner_list(self, received_message):
        select_partner_popup.list_partner.clear()
        partners = received_message.split(chr(5555))
        for i in range(0, len(partners)):
            select_partner_popup.list_partner.addItem(partners[i])

    # 상담 요청 들어왔을 때 수락의사 묻는 팝업 띄우는 슬롯
    @pyqtSlot(str)
    def counsel_check(self, received_message):
        counsel_check_popup.show()
        msg_to_display = received_message.split(chr(6666))[0]
        counsel_check_popup.display.setText(msg_to_display)


    @pyqtSlot()
    def counsel_success(self):
        QMessageBox.information(self, '요청 결과', '상대방이 상담 요청을 수락했습니다.\n 상담방으로 이동합니다.', QMessageBox.Yes)
        self.stackedWidget.setCurrentIndex(3)
        self.label_teacher.setText(f'{self.partner_name} ({self.partner_id})')
        self.label_student.setText(f'{self.name} ({self.id})')
        self.btn_chat.setDisabled(False)

    @pyqtSlot()
    def counsel_fail(self):
        QMessageBox.information(self, '요청 결과', '상대방이 상담 요청을 거절했습니다.\n 나중에 다시 시도해주세요.', QMessageBox.Yes)

    @pyqtSlot(str)
    def counsel_end(self, received_message):
        QMessageBox.information(self, '상담 종료', received_message, QMessageBox.Yes)
        self.btn_chat.setDisabled(False)
        self.btn_counsel_end.setDisabled(False)

    @pyqtSlot(int, int) #qna글 가져오기
    def qna_contents(self, row, col):
        try:
            if col != 3:  # 답변 보기가 아닌 다른 것을 선택했을 때, 오류 나지 않도록
                pass
            else:
                self.label_title.clear()
                self.qna_browser.clear()
                select_cell = self.qna_widget.item(row, col)  # 선택된 셀
                text_call = self.qna_widget.item(row, col - 3)
                qna_text = select_cell.text()  # 내용의 텍스트를 가져오는 것
                title_text = text_call.text()
                self.qna_browser.append(qna_text)
                self.label_title.setText("[제목]" + title_text)
        except AttributeError:
            pass


# 상담요청할 때 원하는 선생님 픽하는 창
class SelectPartner(QWidget):
    def __init__(self):
        super().__init__()

        self.okButton = QPushButton('OK')
        self.cancelButton = QPushButton('Cancel')
        self.list_partner = QComboBox()
        self.hbox = QHBoxLayout()
        self.vbox = QVBoxLayout()

        self.okButton.clicked.connect(self.okbutton_function)
        self.cancelButton.clicked.connect(self.cancelbutton_function)

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 300, 300)
        self.setWindowTitle('상담을 원하는 선생님을 선택하세요.')

        self.hbox.addWidget(self.okButton)
        self.hbox.addWidget(self.cancelButton)

        self.vbox.addWidget(self.list_partner)
        self.vbox.addLayout(self.hbox)

        self.setLayout(self.vbox)

    def okbutton_function(self):
        raw_data = self.list_partner.currentText()
        selected_partner_name = raw_data.split(' ')[0]
        myWindow.partner_name = raw_data.split(' ')[0]
        selected_partner_id = raw_data.split(' ')[1]
        myWindow.partner_id = raw_data.split(' ')[1]
        ask_msg = f'{myWindow.name} ({myWindow.id}) 학생이 상담을 요청했습니다.' + chr(6666) + selected_partner_id + chr(6666) + selected_partner_name + chr(6666) + myWindow.id + chr(6666) + myWindow.name
        myWindow.client_socket.send(ask_msg.encode())
        QMessageBox.information(self, '상담 요청', '상담 요청 메세지를 보냈습니다.', QMessageBox.Yes)
        self.close()

    def cancelbutton_function(self):
        self.close()

# 상담 요청 받았을 때 의사 묻는 팝업
class CounselCheck(QWidget):
    def __init__(self):
        super().__init__()

        self.okButton = QPushButton('수락')
        self.cancelButton = QPushButton('거절')
        self.display = QLabel()
        self.hbox = QHBoxLayout()
        self.vbox = QVBoxLayout()

        self.okButton.clicked.connect(self.okbutton_function)
        self.cancelButton.clicked.connect(self.cancelbutton_function)

    def initUI(self):
        self.setGeometry(300, 300, 200, 300)
        self.setWindowTitle('상담 요청이 들어왔습니다.')
        self.hbox.addWidget(self.okButton)
        self.hbox.addWidget(self.cancelButton)

        self.vbox.addWidget(self.display)
        self.vbox.addLayout(self.hbox)

        self.setLayout(self.vbox)

    # 수락
    def okbutton_function(self):
        msg = myWindow.partner_id + chr(7777) + '수락'
        myWindow.client_socket.send(msg.encode())
        QMessageBox.information(self, '상담 수락', '상담 채팅방으로 이동합니다.', QMessageBox.Yes)
        myWindow.label_teacher.setText(f'{myWindow.partner_name} ({myWindow.partner_id})')
        myWindow.label_student.setText(f'{myWindow.name} ({myWindow.id})')
        myWindow.btn_chat.setDisabled(False)
        myWindow.btn_counsel_request.setDisabled(True)
        myWindow.btn_counsel_end.setDisabled(False)
        self.stackedWidget.setCurrentIndex(3)
        self.close()

    # 거절
    def cancelbutton_function(self):
        msg = myWindow.partner_id + chr(7777) + '거절'
        myWindow.client_socket.send(chr(7777).encode())
        QMessageBox.information(self, '상담 거절', '상담 거절 메세지를 보냈습니다.', QMessageBox.Yes)
        self.close()


class ClientReceiveChat(QThread):
    display_received_message = pyqtSignal(str)
    display_online = pyqtSignal(str)
    join_success = pyqtSignal()
    join_fail = pyqtSignal()
    login_success = pyqtSignal(str)
    login_fail = pyqtSignal()
    online_partner_list = pyqtSignal(str)
    counsel_check = pyqtSignal(str)
    counsel_success = pyqtSignal()
    counsel_fail = pyqtSignal()
    counsel_end = pyqtSignal(str)

    qna_receive_msg = pyqtSignal(str)
    quiz_bird_name = pyqtSignal(str)



    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        while True:
            self.client_socket = self.parent.client_socket
            received_message = self.client_socket.recv(4096).decode()
            if not received_message:
                break
            # 회원가입 성공 메세지 받았을 때
            if chr(1111) in received_message:
                self.join_success.emit()
            # 회원가입 실패 메세지 받았을 때
            elif chr(2222) in received_message:
                self.join_fail.emit()
            # 로그인 성공 메세지 받았을 때
            elif chr(3333) in received_message:
                self.login_success.emit(received_message)
            # 로그인 실패 메세지 받았을 때
            elif chr(4444) in received_message:
                self.login_fail.emit()
            # 온라인 상태인 선생님 리스트 받았을 때
            elif chr(5555) in received_message:
                self.online_partner_list.emit(received_message)

            # 상담요청 메세지 받았을 때
            elif chr(6666) in received_message:
                a = received_message.split(chr(6666))
                print('a[0] :', a[0])
                print('a[1] :', a[1])
                print('a[2] :', a[2])
                print('a[3] :', a[3])
                print('a[4] :', a[4])
                # 상담요청 보낸 사람의 아이디 저장
                # 상대방이 지목한 아이디(a[2])가 내 아이디(myWindow.id)와 같다면
                if a[3] == myWindow.id:
                    self.counsel_check.emit(received_message)

            # 상담요청에 대한 답변 받았을 때
            elif chr(7777) in received_message:
                a = received_message.split(chr(7777))
                print('a[0] :', a[0])
                print('a[1] :', a[1])
                if a[0] == myWindow.id and a[1] == '수락':
                    self.counsel_success.emit()
                elif a[0] == myWindow.id and a[1] == '거절':
                    self.counsel_fail.emit()
                else:
                    pass
            elif chr(8888) in received_message:
                a = received_message.split(chr(8888))
                print('a[0] :', a[0])
                print('a[1] :', a[1])
                if a[1] == self.parent.id:
                    self.display_received_message.emit(a[0])
            elif chr(8999) in received_message:
                a = received_message.split(chr(8999))
                print('a[0] :', a[0])
                print('a[1] :', a[1])
                if a[1] == myWindow.id:
                    self.counsel_end.emit(a[0])

            elif chr(1001) in received_message:
                self.qna_receive_msg.emit(received_message)

            elif chr(1818) in received_message:
                print("1818", received_message)
                self.quiz_bird_name.emit(received_message)

            else:
                # 상담메세지 받았을 때
                self.display_received_message.emit(received_message)

        print('서버 연결 종료')
        self.client_socket.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = student_client()
    myWindow.setWindowTitle('학생 프로그램')
    myWindow.show()
    select_partner_popup = SelectPartner()
    counsel_check_popup = CounselCheck()
    app.exec_()






