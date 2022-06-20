from PyQt5.QtWidgets import  QTableWidgetItem, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal

from PyQt5 import uic
import sys
from socket import *
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import *
import time

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


ui_form = uic.loadUiType("student.ui")[0]

class teacher_client(QMainWindow, ui_form):
    def __init__(self):
        super().__init__()

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
        self.role = '교사'
        self.name = ''
        self.id = ''
        self.pw = ''
        self.pw_re = ''
        self.partner_id = ''
        self.partner_name = ''

        self.name = []  # 회원가입용 리스트 판다스로 묶어서 서버로 보낼 것
        self.ID = []
        self.PW = []

        self.qna_list = []

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
        self.crc.view_grade_table.connect(self.view_grade_table)

        self.crc.graph.connect(self.receive_graph)

        #리스트 형식으로 받은 부분
        self.crc.qna_receive_msg.connect(self.update_qna)
        self.crc.quiz_receive_count.connect(self.update_quiz)

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
        self.btn_counsel.clicked.connect(self.counsel_page)
        self.btn_hide()  # 로그인 전 불필요한 버튼 가리기
        # self.btn_edustart.hide()
        self.join_widget.hide()  # 회원가입 창 가리기
        # self.tabWidget.hide()  # 학습/QNA용 탭 위젯 가리기


        self.btn_main.clicked.connect(self.main_page)
        self.btn_info.clicked.connect(self.my_page)
        self.btn_qna.clicked.connect(self.qna_page)
        self.btn_counsel.clicked.connect(self.counsel_page)
        self.btn_counsel_end.clicked.connect(self.exit_counsel)

        self.btn_counsel_request.clicked.connect(self.request_counsel_partner_list)

        self.pushButton.clicked.connect(self.request_grade_table_by_student)
        self.pushButton.clicked.connect(self.graph_sts)


    def join_event(self): #이거 다시 만들어야함
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
            info = 'teacher' + chr(1111) + self.id + chr(1111) + self.pw + chr(1111) + self.name
            self.client_socket.send(info.encode())
        except:
             QMessageBox.warning(self, '서버에 회원정보를 전송하지 못했습니다.', QMessageBox.Yes)

    # 로그인 확인버튼 눌렀을 때 메서드
    # 학생/교사 구분하는 값도 받아야됨
    def push_login_enter_button(self):
        # 입력한 아이디
        self.id = self.input_id.text()
        # 입력한 비밀번호
        self.pw = self.input_pw.text()
        # 선택한 직업
        info = 'teacher' + chr(2222) + self.id + chr(2222) + self.pw
        self.client_socket.send(info.encode())

    def main_page(self): #메인페이지
        self.main_text.setText("메인페이지입니다")
        self.stackedWidget.setCurrentIndex(5)

        self.quiz_mum = 0 #이 값은 db에서 받아와야함 (퀴즈 테이블 컬럼 - 1)
        self.quiz_setnum.setValue(self.quiz_mum)
        self.quiz_setnum.setDisabled(True)

        self.quiz_F5.clicked.connect(self.F5_quiz)

    #학생별 통계 함수
    def add_sts_widget(self, student, value):
        for i in range(0, len(value)):
            for j in range(0, len(student)):
                self.sts_per_quiz.item(i, j, QTableWidgetItem(value))

    def draw_graph(self, quiz_num, value):
        for i in range(1, len(quiz_num) + 1):
            plt.text(i-1, value[i-1], value[i-1])

    # 학생별 퀴즈 결과 보기 버튼 눌렀을 때 메서드
    def request_grade_table_by_student(self):
        msg = self.id + chr(4949)
        self.client_socket.send(msg.encode())
        print("msg" , msg)

    def graph_sts(self):
        self.client_socket.send(chr(5355).encode())

    def F5_quiz(self):
        print("되나")
        self.quiz_setnum.setDisabled(False)
        self.client_socket.send(chr(1918).encode())

    @pyqtSlot(int)
    def update_quiz(self, a):
        print("a", a)
        self.quiz_mum = a
        self.quiz_setnum.setValue(self.quiz_mum)

        self.quiz_num_ok.clicked.connect(self.t_quiz)

    def t_quiz(self):
        b = self.quiz_setnum.value()

        if b == self.quiz_mum + 1:
            self.quiz_setnum.setDisabled(True)
            self.client_socket.send((chr(1919) + str(b)).encode()) #선생님 문제 추가
            self.quiz_num_ok.setDisabled(True)
            QMessageBox.about(self, '확인', f'문제가 추가되었습니다. 현재 문제개수 {self.quiz_mum + 1}')
        elif b == self.quiz_mum:
            QMessageBox.about(self, '확인', '추가 된 문제가 없습니다.')
        elif b > 26:
            QMessageBox.about(self, '확인', '26개 초과 문제 출제 불가')
        else:
            QMessageBox.about(self, '확인', '문제는 1문제씩만 추가 가능하고 줄일 수 없습니다. db관계자에게 문의부탁')

    def exercise(self): #학습하는 함수
        self.tabWidget.show()

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
        self.qna_widget.setHorizontalHeaderLabels(["제목", "아이디", "날짜", "내용보기", "답변상태"])
        self.qna_widget.setRowCount(50)
        self.qna_widget.setColumnWidth(0, 200)
        self.qna_widget.cellClicked.connect(self.qna_contents) #더블 클릭하면 함수 연결
        self.qna_widget.setEditTriggers(QAbstractItemView.NoEditTriggers) #셀 수정 못하게
        self.run = False
        self.btn_q_ok.clicked.connect(self.qna_content)
        self.F5.clicked.connect(self.refresh)

        self.label_13.hide()
        self.q_name.hide()

    def qna_content(self):
        self.qna_title = self.q_title.text()

        self.qna_text = self.q_text.toPlainText()
        self.answer_state = '답변완료★'
        answer_qna = self.qna_title + chr(1002) + self.qna_text + chr(1002) + self.answer_state
        self.client_socket.send(answer_qna.encode())

        self.q_title.clear()
        self.q_text.clear()

    def refresh(self):
        self.qna_widget.clearContents()
        # self.client_socket.send((chr(1001) + "qna글요청").encode())
        self.client_socket.send("qna글요청".encode())

    @pyqtSlot(str) #db에서 학생 qna을 가져오기
    # qna 글 업데이트, receieve 메세지에서 값 받기
    def update_qna(self, a):
        b = a[:-1].split(chr(1003))
        print("b", b)
        print("b", type(b))
        for i in range(len(b)):
            aa = b[i].split(chr(1001))
            self.qna_widget.setItem(i, 0, QTableWidgetItem(aa[0]))
            self.qna_widget.setItem(i, 1, QTableWidgetItem(aa[1]))
            self.qna_widget.setItem(i, 2, QTableWidgetItem(aa[2]))
            self.qna_widget.setItem(i, 3, QTableWidgetItem(aa[3]))
            self.qna_widget.setItem(i, 4, QTableWidgetItem(aa[4]))

    @pyqtSlot(int, int)
    def qna_contents(self, row, col):
        try:
            if col != 3: #답변 보기가 아닌 다른 것을 선택했을 때, 오류 나지 않도록
                pass
            else:
                self.label_title.clear()
                self.qna_browser.clear()
                select_cell = self.qna_widget.item(row, col) #선택된 셀
                text_call = self.qna_widget.item(row, col - 3)
                self.qna_text = select_cell.text() # 학생의 질문글
                self.title_text = text_call.text()
                self.qna_browser.append(self.qna_text)
                self.label_title.setText("[제목]" + self.title_text)
                self.q_title.setText(self.title_text)
                self.q_title.setDisabled(True)  # 비활성화
                self.q_text.setPlainText(self.qna_text + "\n\n\n[선생님 답변]") #학생의 질문을 textedit창에 띄움

        except AttributeError:
            pass

    # 상담 요청 버튼 눌렀을 때 -> 서버에 온라인 상태의 선생님 리스트 데이터 요청함
    def request_counsel_partner_list(self):
        request = 'student' + chr(5555)
        self.client_socket.send(request.encode())
        select_partner_popup.show()

    # 상담페이지에서 보내기 버튼 눌렀을 때 입력한 메세지 보내는 메서드
    def push_send_button(self):
        # 유저가 입력한 메세지
        writed_message = self.std_text.toPlainText()
        print(writed_message)
        # 실제 채팅창에 입력될 메세지 (입력 시간 + 닉네임 + 메세지)
        final_message_to_send = f'[{self.now}] {self.name}({self.role}) : \n{writed_message}' +chr(8888) + self.partner_id
        # 서버로 메세지 보냄
        self.client_socket.send(final_message_to_send.encode())
        # 전송한 메세지를 텍스트에딧에서 지움
        self.std_text.clear()
        self.textBrowser_1.append(final_message_to_send.split(chr(8888))[0])

    # 상담페이지에서 나갔을 때 채팅방에서 나가는 메서드
    def exit_counsel(self):
        message = '상대방이 나갔습니다. 상담이 종료됩니다.' + chr(8999) + self.partner_id
        print(message)
        self.client_socket.send(message.encode())
        QMessageBox.information(self, '상담 종료', '상담이 종료되었습니다.', QMessageBox.Yes)
        self.label_teacher.setText('')
        self.label_student.setText('')
        self.btn_chat.setDisabled(True)
        self.btn_counsel_end.setDisabled(True)

    # 그래프 값 받아오는 슬롯
    @pyqtSlot(str)
    def receive_graph(self, aa):
        print("aa 그래프에 넣을 값", aa)
        value_list = aa.split(chr(5355))
        q_value = []
        for i in value_list:
            q_value.append(int(i))
        print("q_value",q_value)
        print("q_value",type(q_value[0]))
        quiz_num = []
        for i in range(len(value_list)):
            a = f'q{i+1}'
            quiz_num.append(a)
        print("quiz_num",quiz_num)
        print("value_list", value_list)

        self.b = plt.figure()
        self.b.tight_layout(pad=3, w_pad=1.5, h_pad=1.5)
        self.a = FigureCanvas(self.b)
        self.ax = self.a.figure.subplots()
        self.std_sts.addWidget(self.a)
        plt.bar(quiz_num , q_value, color='steelblue')
        self.draw_graph(quiz_num , q_value)
        plt.title("Quiz Result")
        plt.ylabel("Score Per Quiz")
        self.a.draw()

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
        # self.refresh()
        # self.main_text.setText(f'{self.name} ({self.role})')  # 페이지 제목
        self.btn_show()  # 로그인 후 버튼 보이기
        # self.tabWidget.show()  # 학습/QNA용 탭 위젯 보이기

    # 로그인 실패했을 때
    @pyqtSlot()
    def login_fail(self):
        QMessageBox.warning(self, '로그인 실패', 'ID/PW를 확인해주세요.', QMessageBox.Yes)

    # 서버로부터 받은 상담메세지를 채팅창에 띄우는 슬롯
    @pyqtSlot(str)
    def display_received_message_on_textbrowser(self, received_message):
        msg_to_display = received_message.split(chr(7777))[0]
        self.textBrowser_1.append(msg_to_display)

    # 서버로부터 받은 온라인 클라이언트 리스트를 띄우는 슬롯
    @pyqtSlot(str)
    def display_online_partner_list(self, received_message):
        select_partner_popup.list_partner.clear()
        partners = received_message.split(chr(5555))
        for i in range(0, len(partners) - 1):
            select_partner_popup.list_partner.addItem(partners[i])

    # 상담 요청 들어왔을 때 수락의사 묻는 팝업 띄우는 슬롯
    @pyqtSlot(str)
    def counsel_check(self, received_message):
        print('counsel_check 메서드 : ', received_message)
        counsel_check_popup.show()
        msg_to_display = received_message.split(chr(6666))[0]
        counsel_check_popup.display.setText(msg_to_display)

    @pyqtSlot()
    def counsel_success(self):
        QMessageBox.information(self, '요청 결과', '상대방이 상담 요청을 수락했습니다.\n 상담방으로 이동합니다.', QMessageBox.Yes)
        self.stackedWidget.setCurrentIndex(3)
        self.label_teacher.setText(f'{self.name} ({self.id})')
        self.label_student.setText(f'{self.partner_name} ({self.partner_id})')
        self.btn_chat.setDisabled(False)
        self.btn_counsel_request.setDisabled(True)
        self.btn_counsel_end.setDisabled(False)

    @pyqtSlot()
    def counsel_fail(self):
        QMessageBox.information(self, '요청 결과', '상대방이 상담 요청을 거절했습니다.\n 나중에 다시 시도해주세요.', QMessageBox.Yes)

    @pyqtSlot()
    def counsel_end(self):
        print('counsel_end')
        QMessageBox.information(self, '상담 종료', '상대방이 상담을 종료했습니다.', QMessageBox.Yes)
        self.btn_chat.setDisabled(False)
        self.btn_counsel_end.setDisabled(False)

    @pyqtSlot(str) ##학생별통계
    def view_grade_table(self, raw_data):
        grade_result = []
        data_by_row = raw_data.split(chr(4848))
        for row_data in data_by_row:
            student_data = row_data.split(chr(4949))
            total = 0
            for i in range(len(student_data)):
                if i == 0:
                    pass
                else:
                    total += int(student_data[i])
            student_data.append(str(total))
            grade_result.append(student_data)
        print("테이블위젯에 넣을값 ", grade_result[0][7])
        print("테이블위젯에 넣을값 ", type(grade_result[0][7]))
        print("grade_result[0][0]",grade_result[0][0])

        quiz_col = len(grade_result[0])
        quiz_row = len(grade_result)

        self.sts_per_quiz.setColumnCount(quiz_col)
        self.sts_per_quiz.setRowCount(quiz_row)

        aa = []
        aa.append("아이디")
        for i in range(1, quiz_col - 1):
            col_name = f"q{i}"
            aa.append(col_name)

        aa.append("총점")
        # print(col_name)
        print("aa", aa)
        self.sts_per_quiz.setHorizontalHeaderLabels(aa)

        for i in range(quiz_row):
            for j in range(quiz_col):
                self.sts_per_quiz.setItem(i, j, QTableWidgetItem(grade_result[i][j]))


# 상담요청할 때 원하는 학생 픽하는 창
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
        self.setWindowTitle('상담을 원하는 학생을 선택하세요.')

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
        ask_msg = f'{myWindow.name} ({myWindow.id}) 선생님이 상담을 요청했습니다.' + chr(6666) + selected_partner_id + chr(6666) + selected_partner_name + chr(6666) + myWindow.id + chr(6666) + myWindow.name
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
        self.initUI()

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
        myWindow.stackedWidget.setCurrentIndex(3)
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
    relay_counsel_request = pyqtSignal()
    qna_receive_msg = pyqtSignal(str)
    row_count_1 = pyqtSignal(int)
    counsel_end = pyqtSignal()
    counsel_check = pyqtSignal(str)
    counsel_success = pyqtSignal()
    counsel_fail = pyqtSignal()

    quiz_receive_count = pyqtSignal(int)
    view_grade_table = pyqtSignal(str)

    graph = pyqtSignal(str)




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
            # 이름 (아이디) 학생(or 선생님)이 상담을 요청했습니다 + chr(6666) + selected_partner_id + chr(6666)
            # + selected_partner_name + chr(6666) + myWindow.id + chr(6666) + myWindow.name
            elif chr(6666) in received_message:
                a = received_message.split(chr(6666))
                # 상담요청 보낸 사람의 아이디 저장
                myWindow.partner_id = a[3]
                # print(myWindow.partner_id)
                myWindow.partner_name = a[4]
                # print(myWindow.partner_name)
                # 상대방이 지목한 아이디(a[1])가 내 아이디(myWindow.id)와 같다면
                if a[1] == myWindow.id:
                    self.counsel_check.emit(received_message)
            # 상담요청에 대한 답변 받았을 때
            elif chr(7777) in received_message:
                a = received_message.split(chr(7777))
                if a[0] == myWindow.id and a[1] == '수락':
                    self.counsel_success.emit()
                elif a[0] == myWindow.id and a[1] == '거절':
                    self.counsel_fail.emit()
                else:
                    pass
            # 상담 메세지 받았을 때
            elif chr(8888) in received_message:
                a = received_message.split(chr(8888))
                if a[1] == self.parent.id:
                    self.display_received_message.emit(a[0])
            elif chr(8999) in received_message:
                a = received_message.split(chr(8999))
                print('a[0] :', a[0])
                print('a[1] :', a[1])
                if a[1] == myWindow.id:
                    self.counsel_end.emit()
            elif chr(1001) in received_message:
                print("1001", received_message)
                self.qna_receive_msg.emit(received_message)
            elif chr(1918) in received_message:
                # print("1918", received_message)
                print(received_message.split(chr(1918))[1])
                quiz_count = int(received_message.split(chr(1918))[1])
                print("퀴즈개수", quiz_count)
                self.quiz_receive_count.emit(quiz_count)


            elif chr(4747) in received_message:
                print('4747')
                received_id = received_message.split(chr(4747))[0]
                print('id :',received_id)
                received_data = received_message.split(chr(4747))[1]
                print('data : ', received_data)
                if received_id == self.parent.id:
                    row_data = received_message.replace(received_id, '')
                    row_data = row_data.replace(chr(4747), '')
                    print('row_data : ', row_data)
                    self.view_grade_table.emit(row_data) #학생별통계

            elif chr(5355) in received_message:
                print("5355", received_message)
                self.graph.emit(received_message)



            else:
                # 상담메세지 받았을 때
                self.display_received_message.emit(received_message)

        print('서버 연결 종료')
        self.client_socket.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = teacher_client()
    myWindow.setWindowTitle('교사 프로그램')
    myWindow.show()
    select_partner_popup = SelectPartner()
    counsel_check_popup = CounselCheck()
    app.exec_()
