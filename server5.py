from socket import *
from threading import *
import time
import sqlite3

class Server:
    def __init__(self):
        # 연결된 클라이언트 소켓 리스트
        self.clients = []
        # 데이터 수신 쓰레드 리스트
        self.clients_thread = []
        # sqlite3 연동
        self.conn = sqlite3.connect('iotai.db', check_same_thread=False)
        # cursor 생성
        self.cur = self.conn.cursor()

        # 소켓생성
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.now = time.strftime('%Y-%m-%d %H:%M:%S')

        # 서버 아이피
        self.server_ip = '127.0.0.1'
        # 서버 포트
        self.server_port = 9071
        # 소켓 바인드
        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(10)
        print(f'서버 주소 : {self.server_ip}, 포트 번호 : {self.server_port}')
        print('서버 생성 완료. 클라이언트의 연결 요청을 기다립니다.')

        #초기 문제 수
        #디비에서 퀴즈 컬럼값 -1 을 초기 셋팅을 한다.
        self.cur.execute("select * from quiz")
        abcde = self.cur.fetchone()  # a는 칼럼 수
        print("abcde", abcde)
        self.count = len(abcde) - 1
        self.t_quiz_num = self.count #현재 db에 있는 문제 수
        print(self.count)

        self.accept_client()


    # 클라이언트의 연결 요청을 받음
    def accept_client(self):
        while True:
            (client_socket, client_address) = self.server_socket.accept()
            # clients 리스트에 소켓이름 추가
            self.clients.append(client_socket)

            self.clients_thread.append(Thread(target=self.receive_message, args=(client_socket,)))
            self.clients_thread[-1].start()
            print(f'{client_address}님과 연결되었습니다.')

    # 접속한 클라이언트들로부터 메세지를 받는 메서드
    def receive_message(self, client_socket):
        while True:
            msg = client_socket.recv(1024)
            # 만약 연결이 종료(데이터가 없다)되었다면 그 소켓은 닫음
            if not msg:
                self.clients.remove(client_socket)
                break
            received_message = msg.decode()

            # 메세지별로 상황 구분
            # chr(1111) -> 회원가입 정보 받았을 때
            if chr(1111) in received_message:
                self.join_fail = False
                # 학생일 때
                if 'student' in received_message:
                    data = received_message.split(chr(1111))
                    self.cur.execute("SELECT * FROM Member")
                    row1 = self.cur.fetchall()
                    # 중복여부 확인
                    for search in row1:
                        # 일치하는 데이터가 있다면
                        if data[1] == search[0]:
                            # 회원가입 실패 메세지 보냄 chr(2222)로 구분
                            print("회원가입 실패, 중복된 아이디 존재함")
                            self.join_fail = True
                            break

                    if self.join_fail:
                        pass
                    else:
                        # 학생테이블에서 중복 아이디 없었다면 교사 테이블에서도 아이디 중복 확인
                        self.cur.execute("SELECT * FROM TMember")
                        row1 = self.cur.fetchall()
                        # 중복여부 확인
                        for search in row1:
                            # 일치하는 데이터가 있다면
                            if data[1] == search[0]:
                                # 회원가입 실패 메세지 보냄 chr(2222)로 구분
                                print("회원가입 실패, 중복된 아이디 존재함")
                                self.join_fail = True
                                break
                    # 중복된 아이디 존재해서 회원가입 실패했다면
                    if self.join_fail:
                        join_fail = chr(2222)
                        client_socket.send(join_fail.encode())
                    # 회원가입 성공했다면 DB에 등록하고 성공메세지 보냄
                    else:
                        self.cur.execute(
                            "INSERT INTO Member(memberID, memberPWD, memberName, online) VALUES(?, ?, ?, ?)",
                            (data[1], data[2], data[3], '0'))  # 회원 테이블에 저장
                        self.conn.commit()
                        # self.conn.close()
                        # 회원가입 성공 메세지 보냄
                        client_socket.send(chr(1111).encode())

                # 교사일 때 (학생일 때와 동일한 방식)
                elif 'teacher' in received_message:
                    # <role + chr(1111) + id + chr(1111) + pw + chr(1111) + 이름> 형태로 데이터 받았기 떄문에 chr(1111)로 쪼갬
                    data = received_message.split(chr(1111))  # 받아온 정보를 쪼갬
                    # data[1] id, data[2] pw, data[3] 이름
                    # 선생님 회원정보 테이블에서 데이터 불러옴
                    self.cur.execute("SELECT * FROM TMember")
                    row1 = self.cur.fetchall()
                    # 회원가입 실패여부를 저장할 변수
                    # 중복여부 확인
                    for search in row1:
                        # 일치하는 데이터가 있다면
                        if data[1] == search[0]:
                            # 회원가입 실패 메세지 보냄 chr(2222)로 구분
                            print("회원가입 실패, 중복된 아이디 존재함")
                            # 중복된 아이디가 존재해서 회원가입 실패했다면
                            # join_fail 변수를 True로 바꾸고
                            self.join_fail = True
                            # for loop에서 나옴
                            break
                    # 교사 테이블에서 중복아이디 발견됐다면 pass
                    if self.join_fail:
                        pass
                    # 교사 테이블에서 중복 아이디 발견되지 않았다면 학생테이블에서도 중복확인
                    else:
                        self.cur.execute("SELECT * FROM Member")
                        row1 = self.cur.fetchall()
                        # 중복여부 확인
                        for search in row1:
                            # 일치하는 데이터가 있다면
                            if data[1] == search[0]:
                                # 회원가입 실패 메세지 보냄 chr(2222)로 구분
                                print("회원가입 실패, 중복된 아이디 존재함")
                                self.join_fail = True
                                break
                    # 중복된 아이디 존재해서 회원가입 실패했다면
                    if self.join_fail:
                        # 클라이언트에 실패메세지 전송
                        join_fail = chr(2222)
                        client_socket.send(join_fail.encode())
                    # 회원가입 성공했다면 DB에 등록하고 성공메세지 보냄
                    else:
                        # DB에 회원정보 등록하고
                        self.cur.execute(
                            "INSERT INTO TMember(memberID, memberPWD, memberName, online) VALUES(?, ?, ?, ?)",
                            (data[1], data[2], data[3], '0'))  # 회원 테이블에 저장
                        self.conn.commit()
                        # self.conn.close()
                        # 회원가입 성공 메세지 보냄
                        client_socket.send(chr(1111).encode())

            # chr(2222) -> 로그인 요청 받았을 때
            elif chr(2222) in received_message:
                # 학생일 때 학생 DB에서 일치여부 확인
                if 'student' in received_message:
                    data = received_message.split(chr(2222))
                    # 데이터베이스에 저장된 학생 회원정보 불러옴
                    self.cur.execute("SELECT * FROM Member")
                    row1 = self.cur.fetchall()
                    # 로그인 성공 여부를 저장할 변수
                    self.login_success = False
                    # 일치여부 확인
                    for search in row1:
                        # 일치하는 데이터가 있다면
                        if data[1] == search[0] and data[2] == search[1]:
                            # 로그인 성공 메세지 보냄 chr(2222)로 구분
                            # 해당 회원의 이름 + chr(2222)
                            login_success = search[2] + chr(3333)
                            client_socket.send(login_success.encode())
                            print(data[1], "로그인 성공")
                            self.cur.execute('UPDATE member SET online = ? WHERE memberID = ?', ('1', data[1]))  # 회원 테이블에 저장
                            self.conn.commit()
                            self.login_success = True
                            break
                    # 위에서 회원정보 일치해서 로그인 성공 메세지 보냈다면
                    # 로그인 실패 메세지 안보냄
                    if self.login_success:
                        pass
                    # 아니라면 로그인 실패 메세지 보냄
                    else:
                        login_fail = chr(4444)
                        client_socket.send(login_fail.encode())
                # 교사일 때 교사 DB에서 일치여부 확인
                elif 'teacher' in received_message:
                    # 받은 데이터 스플릿으로 쪼갬
                    data = received_message.split(chr(2222))
                    # 데이터 베이스에 저장된 교사 회원정보 불러옴
                    self.cur.execute("SELECT * FROM TMember")
                    row1 = self.cur.fetchall()
                    # 로그인 성공여부를 저장할 변수
                    self.login_success = False
                    # 일치여부 확인
                    for search in row1:
                        # 일치하는 데이터 있다면
                        if data[1] == search[0] and data[2] == search[1]:
                            # 로그인 성공 메세지 보냄 chr(2222)로 구분
                            # 해당 회원의 이름 + chr(2222)
                            login_success = search[2] + chr(3333)
                            client_socket.send(login_success.encode())
                            print(data[1], "로그인 성공")
                            # 해당 교사의 온라인 접속상태 True로 변경
                            self.cur.execute('UPDATE Tmember SET online = ? WHERE memberID = ?', ('1', data[1]))  # 회원 테이블에 저장
                            self.conn.commit()
                            # 로그인 성공했으므로 True로 바꿈
                            self.login_success = True
                            break
                    # 위에서 회원정보 일치해서 로그인 성공 메세지 보냈다면
                    # 로그인 실패 메세지 안보냄
                    if self.login_success:
                        pass
                    # 아니라면 로그인 실패 메세지 보냄 chr(4444)으로 구분
                    else:
                        login_fail = chr(4444)
                        client_socket.send(login_fail.encode())

            # 상담 가능한 상대의 이름 + 아이디 보내기
            elif chr(5555) in received_message:
                # 학생이 온라인 상태의 선생님 리스트를 요구했을 때
                if 'teacher' in received_message:
                    self.cur.execute("SELECT memberName, memberID FROM TMember WHERE online = ?", ('1'))
                    # 데이터 담을 스트링변수 생성
                    teacher_list = ''
                    row = self.cur.fetchall()
                    for i in row:
                        # 스트링으로 추출한 데이터 ( 이름 + 아이디) 이어 붙임
                        # chr(5555)로 구분 및 스플릿
                        teacher_list += i[0] + ' ' + i[1] + chr(5555)
                    client_socket.send(teacher_list.encode())

                # 선생님이 온라인 상태의 학생 리스트를 요구했을 때
                elif 'student' in received_message:
                    self.cur.execute("SELECT memberName, memberID FROM Member WHERE online = ?", ('1'))
                    # 데이터 담을 스트링 변수 생성
                    student_list = ''
                    row = self.cur.fetchall()
                    for i in row:
                        # 스트링에 추출한 데이터 (선생님 이름 + 아이디) 이어붙임
                        student_list += i[0] + ' ' + i[1] + chr(5555)
                    client_socket.send(student_list.encode())

            # 상담 대상을 선택해서 보냈을 때
            # 이름 (아이디) 학생(or 교사)이/가 상담을 요청했습니다 + chr(6666) + 상대 id + chr(6666) + 본인 id
            # 그대로 클라이언트에 전달함
            elif chr(6666) in received_message:
                print('6666 들어옴')
                # msg1 = received_message.split(chr(6666))
                # # 해당 교사의 아이디
                # msg2 = msg1[0].split(' ')[1].encode()
                print('6666 : ', received_message)
                self.send_to_other_clients(client_socket, received_message)

            # 상대가 상담여부 메세지 보냈을 때
            # 대상 id + chr(7777) + '수락or거절'
            # 그대로 클라이언트에 전달함
            elif chr(7777) in received_message:
                print('7777 : ', received_message)
                self.send_to_other_clients(client_socket, received_message)

            # 상담 메세지 받았을 때
            # 그대로 클라이언트에 전달함
            elif chr(8888) in received_message:
                print('8888 : ', received_message)
                self.send_to_other_clients(client_socket, received_message)

            elif chr(8999) in received_message:
                print('8999 : ', received_message)
                self.send_to_other_clients(client_socket, received_message)


            # 교사가 접속 종료했을 때 해당 교사 온라인 컬럼 0으로 바꿈
            # 아직 클라이언트에서 구현 못했음
            elif chr(9999) in received_message:
                data = received_message.split(chr(9999))
                self.cur.execute('UPDATE Tmember SET online = ? WHERE memberID = ?', ('0', data[0]))  # 회원 테이블에 저장
                self.conn.commit()

            #추가부분 - 시작
            elif chr(0000) in received_message:
                data = received_message.split(chr(0000))
                self.cur.execute("insert into std_qna(Title, Name, WDate, content, Anstate) values (?,?,?,?,?)", (data[0], data[1],data[2], data[3],data[4]))
                self.conn.commit()

            elif "qna글요청" == received_message:
                self.cur.execute("select Title, Name, WDate, content, Anstate from std_qna")
                qna_msg = self.cur.fetchall()
                self.total = ''
                for i in qna_msg:
                    self.total += i[0] + chr(1001) + i[1] + chr(1001) + i[2] + chr(1001) + i[3] + chr(1001) + i[4] + chr(1003)

                client_socket.send(self.total.encode())

            elif chr(1002) in received_message:
                #교사 클라이언트에서 보내준 qna 답글 (1줄씩 전송)
                data = received_message.split(chr(1002))
                self.cur.execute("UPDATE std_qna SET Content = ? WHERE Title = ?",
                                 (data[1], data[0]))
                self.cur.execute("UPDATE std_qna SET Anstate = ? WHERE Title = ?",
                                 (data[2], data[0]))
                self.conn.commit()
                print(data)

            #학생클라이언트 문제 풀이 정보 서버 디비에 저장
            elif chr(1212) in received_message:
                data = received_message.split(chr(1212))
                self.cur.execute("INSERT INTO problemSelect VALUES(?, ?, ?, ?)", (data[0],data[1],data[2],data[3]))
                self.conn.commit()

            #디비에 저장된 학생 문제풀이 정보를 선생님에게 전송 -> 그래프 만들 때 사용
            elif chr(1313) in received_message:
                self.cur.execute("SELECT * FROM problemSelect")
                row = self.cur.fetchall()
                for i in row:
                    problem_list = i[0] + chr(1313) + i[1] + chr(1313) + i[2] + chr(1313) + i[3] + chr(1313)
                client_socket.send(problem_list.encode())

            #선생님 클라에서 문제 업데이트 / 새로운문제
            elif chr(1414) in received_message:
                data = received_message.split(chr(1414))
                self.cur.execute("INSERT INTO Problem VALUES(?, ?, ?)", (data[0],data[1],data[2]))
                self.conn.commit()

            #디비에 저장된 새로운 문제를 학생클라에게 전송
            elif chr(1515) in received_message:
                self.cur.execute("SELECT * FROM Problem")
                row = self.cur.fetchall()
                for i in row:
                    problem_list = i[0] + chr(1515) + i[1] + chr(1515) + i[2] + chr(1515)
                client_socket.send(problem_list.encode())

            #문제 풀이 정보에서 정답인 문제 골라서 점수 계산후 클라에 전송
            elif chr(1616) in received_message:
                score =0
                self.cur.execute("SELECT * FROM problemSelect")
                row = self.cur.fetchall()
                self.cur.execute("SELECT * FROM problem")
                row1 = self.cur.fetchall()
                for i in row:
                    for j in row1:
                        if i[1]==j[1]: #답이 같다면
                           score + i[3]
                print("총점수 : ", score)
                client_socket.send((row[0], score).encode())
            
            #포인트
            #클라이언트에서 유저아이디 / 추가된 포인트 
            elif chr(1717) in received_message:
                data = received_message.split(chr(1717))
                self.cur.execute("select * from Member where memberID = ?", (data[0]))
                user_point = self.cur.fetchall()
                for i in user_point:
                    if i[0] == data[0]:
                        self.cur.execute("update point memberPoint= ? where memberID = ?", (data[1], data[0]))
                        self.conn.commit()

            #디비에서 원하는 조류 데이터 전송
            elif chr(1818) in received_message:
                self.cur.execute("select birdName from birdSelect limit %d" %self.t_quiz_num)
                print("학생이 푸는 문제 개수", self.t_quiz_num)
                row = self.cur.fetchall()
                self.q_row = ''
                for i in range(len(row)):
                    self.q_row += row[i][0] + chr(1818)
                client_socket.send(self.q_row.encode())
                print("self.q_row", self.q_row)

            elif chr(1918) in received_message:
                self.cur.execute("select * from quiz")
                a = self.cur.fetchone() #a는 칼럼 수
                print("a", a )
                self.count = len(a)- 1  #문제 수
                client_socket.send((chr(1918) + str(self.count)).encode())
                print("count", self.count)

                # 칼럼 ,학생 정오표저장 userID 보내줘야함
            elif chr(5323) in received_message:
                data = received_message.split(chr(5323))
                print(data)

                self.cur.execute("select userID from quiz")
                name = self.cur.fetchall()

                if (data[0],) not in name:
                    print(name)
                    self.cur.execute("insert into quiz(userID) values(?)", (data[0],))
                    self.conn.commit()
                a = data[1].split(',')
                b = a[:-1]
                self.cur.execute('select * from quiz')
                column = self.cur.fetchone()

                for i in range(len(column) - 1):
                    query = "update quiz set q{0} = ? where userID = ?".format(i + 1)
                    # print(query)
                    self.cur.execute(query, (b[i], data[0]))
                    print("b[i+1]", b[i])
                    self.conn.commit()

                self.cur.execute('select * from quiz')
                ohno = self.cur.fetchall()
                print("학생 시험 결과", ohno )


            # #문제별 정오답
            elif chr(5355) in received_message:
                plus = []
                self.cur.execute('select * from quiz')
                quiz_num = self.cur.fetchall()

                for row in quiz_num:
                    if len(plus) == 0:
                        plus = [0 for i in range(len(row) - 1)]
                        row = list(row)

                    for i in range(1, len(row)):
                        plus[i - 1] += row[i]

                plus = chr(5355).join(map(str, plus))
                print(plus)
                client_socket.send(plus.encode())

                # 학생별 퀴즈 결과
            elif chr(4949) in received_message:
                print('received_message : ', received_message)
                target_id = received_message.split(chr(4949))[0]
                print('target_id : ', target_id)
                self.cur.execute('select * from quiz')
                quiz_result = self.cur.fetchall()
                print('quiz_result : ', quiz_result)
                # 행의 개수
                row_count = len(quiz_result)
                print('row_count : ', row_count)
                # 열의 개수
                column_count = len(quiz_result[0])
                print('column_count : ', column_count)

                # quiz_result는 리스트 타입
                # quiz_result의 원소는 튜플 타입
                data = ''
                for i in range(row_count):
                    for j in range(column_count):
                        if j == 0:
                            data += quiz_result[i][j] + chr(4949)
                        else:
                            if j == column_count - 1:
                                data += str(quiz_result[i][j])
                            else:
                                data += str(quiz_result[i][j]) + chr(4949)
                    if i == row_count - 1:
                        pass
                    else:
                        data += chr(4848)

                data = target_id + chr(4747) + data
                print('data : ', data)
                client_socket.send(data.encode())

            #칼럼
            elif chr(1919) in received_message:
                self.t_quiz_num = int(received_message.split(chr(1919))[1])
                if self.t_quiz_num != 5:
                    query = 'alter table quiz add column q%d integer' % self.t_quiz_num
                    self.cur.execute(query)
                    self.conn.commit()
                else:
                    print("1919 원인 모를 예외 상황 발생")

            #학습 진행상황 
            if chr(2020) in received_message:
                print('2020' + received_message)
                data = received_message.split(chr(2020))
                self.cur.execute("select userID from learning")
                name = self.cur.fetchall()

                if (data[0], ) not in name:

                    self.cur.execute("insert into learning(userID) values(?)", (data[0], ))
                    self.conn.commit()
        
                query = "update learning set %s = ? where userID = ?"%data[1]
                print("data[1]", data[1])
                self.cur.execute(query, ('1', data[0]))
                self.conn.commit()

            if chr(7776) in received_message: #정오표
                print("hi", received_message)
                data = received_message.split(chr(7776))


    # 송신 클라이언트를 제외한 다른 클라이언트에게 메세지 전송
    def send_to_clients(self, received_message):
        for client in self.clients:
            client.send(received_message.encode())

    # 송신자 제외한 모든 클라이언트에 메세지 전송
    def send_to_other_clients(self, client_socket, received_message):
        for client in self.clients:
            if client == client_socket:
                pass
            else:
                client.send(received_message.encode())


if __name__ == '__main__':
    Server()