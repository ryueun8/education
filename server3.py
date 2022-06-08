import socket
import sqlite3
import sys
import time
import os
import threading
conn = sqlite3.connect('iotai.db')
cur = conn.cursor()

client_sockets = []
clnt_cnt = 0 #클라이언트 들어올때마다 증가
lock = threading.Lock()

# 서버 IP 및 열어줄 포트
HOST = '127.0.0.1'
PORT = 9070
BUF_SIZE = 1024

def delete_imfor(clnt_sock):
    global clnt_cnt
    for i in range(0, clnt_cnt):
        if clnt_sock == client_sockets[i][0]:
            print('exit client')
            while i < clnt_cnt - 1:
                client_sockets[i] = client_sockets[i + 1]
                i += 1
            break
    clnt_cnt -= 1
    
def handle_clnt(clnt_sock):
    lock.acquire()
    for i in range(0, clnt_cnt):
        if client_sockets[i][0] == clnt_sock:
            clnt_num = i
            break
    lock.release()

    while True:
        clnt_msg = recv_clnt_msg(clnt_sock)
        if not clnt_msg:
            lock.acquire()
            delete_imfor(clnt_sock)
            lock.release()
            break

        if clnt_msg.startswith('@'): # 특정 기능 실행 시 @ 붙여서 받음
            clnt_msg = clnt_msg.replace('@', '')
            call_func(clnt_num, clnt_msg)
        else:
            continue

def call_func(clnt_num, instruction):
    a=loginlist()
    if instruction == 'sign':
        a.sign(clnt_num)
    elif instruction.startswith('login'):
        a.login(clnt_num, instruction)
    else:
        return
def recv_clnt_msg(clnt_sock):
    sys.stdout.flush()
    clnt_msg = clnt_sock.recv(BUF_SIZE)
    clnt_msg = clnt_msg.decode()


def send_clnt_msg(clnt_sock, msg):
    sys.stdin.flush()
    msg = msg.encode()
    clnt_sock.send(msg)

def Counseling(clnt_num):
    clnt_sock = client_sockets[clnt_num][0]
    type = client_sockets[clnt_num][1]
    if type == 'request':
        user_data = recv_clnt_msg(clnt_sock)
        accept=input("상담요청이 들어홧습니다 수락하시겠습니까?")
        if accept == 'y':
            cur.execute("SELECT * FROM Authority.M")
            row=cur.fetchone()
            for row in row:
                print(row)
            cur.execute("INSERT INTO Authority.M(memberID, TmemberID, authority) VALUES(?, ?, ?)", (user_data,'y',))
            conn.commit()
            conn.close()
            send_clnt_msg(clnt_sock, '@accept')
        elif accept == 'n':
            send_clnt_msg(clnt_sock, '@refuse')
            cur.execute("INSERT INTO Authority.M(memberID, TmemberID, authority) VALUES(?, ?, ?)", (user_data,'n',))
            conn.commit()
            conn.close()
            return
        else:
            send_clnt_msg(clnt_sock, '@fault')
            return
    else:
        print('error')
        conn.close()
        return

class loginlist:
    def sign(slef, clnt_num):
        clnt_sock = client_sockets[clnt_num][0]
        type = client_sockets[clnt_num][1] #에 저장된 정보에따라 아레 if문 결정
        check_id = recv_clnt_msg(clnt_sock)

        if check_id == "@exit":
            conn.close()
            return

        if type == 'student':
            user_data = recv_clnt_msg(clnt_sock)  # id포함 회원가입 데이터 받아옴(구분자 : /)
            user_data = user_data.split('/')
            lock.acquire()
            cur.execute("SELECT * FROM Member.M")
            row1=cur.fetchall()
            for row in row1:
                print(row)
            cur.executemany("INSERT INTO Member.M(memberID, memberPWD, memberName) VALUES(?, ?, ?)", (user_data,)) #회원 테이블에 저장
            conn.commit()
            conn.close()
        elif type == 'teaher':
            user_data = recv_clnt_msg(clnt_sock)  # id포함 회원가입 데이터 받아옴(구분자 : /)
            user_data = user_data.split('/')
            lock.acquire()
            cur.execute("SELECT * FROM Tmember.M")
            row2=cur.fetchall()
            for row in row2:
                print(row)
            cur.executemany("INSERT INTO Tmember.M(memberID, memberPWD, memberName) VALUES(?, ?, ?)", (user_data,)) #선생 테이블에 저장
            conn.commit()
            conn.close()
        else:
            print("error")
            conn.close()
            return
    def login(self, clnt_num, clnt_msg):
        global userIDPW
        clnt_sock = client_sockets[clnt_num][0]
        type = client_sockets[clnt_num][1] #에 저장된 정보에따라 아레 if문 결정
        clnt_msg = clnt_msg.split('/')  # log_in_data = 'log_in/ID/PW'
        check_id = clnt_msg[1]
        check_pw = clnt_msg[2]

        if check_id == "@exit":
            conn.close()
            return
        if type == 'student':
            cur.execute("SELECT * FROM Member.M")
            row1=cur.fetchall()
            for row in row1:
                print(row)
            for search in row1:
                if check_id == search[0] and check_pw == search[1]:#아이디,패스워드 일치하면
                    userIDPW=check_id
                    send_clnt_msg(clnt_sock, '@loginPerfect')
                    time.sleep(0.5)
                    os.system('clear') 
                else: #불일치시
                    send_clnt_msg(clnt_sock, '@loginError')
                    conn.close()
                return
        elif type == 'teaher':
            cur.execute("SELECT * FROM Tmember.M")
            row2=cur.fetchall()
            for row in row2:
                print(row)
            for search in row2:
                if check_id == search[0] and check_pw == search[1]:#아이디,패스워드 일치하면
                    userIDPW=check_id
                    send_clnt_msg(clnt_sock, '@perfect')
                    time.sleep(0.5)
                    os.system('clear') 
                else: #불일치시
                    send_clnt_msg(clnt_sock, '@loginError')
                    conn.close()
                return
        else:
            print("error")
            conn.close()
            return

def threaded(client_socket, addr): #함수의 내용을 바꿀 가능성이큼
    print('>> Connected by :', addr[0], ':', addr[1])

    # 클라이언트가 접속을 끊을 때 까지 반복합니다.
    while True:

        try:

            # 데이터가 수신되면 클라이언트에 다시 전송합니다.(에코)
            data = client_socket.recv(1024)

            if not data:
                print('>> Disconnected by ' + addr[0], ':', addr[1])
                break

            print('>> Received from ' + addr[0], ':', addr[1], data.decode())

            # 서버에 접속한 클라이언트들에게 채팅 보내기
            # 메세지를 보낸 본인을 제외한 서버에 접속한 클라이언트에게 메세지 보내기
            for client in client_sockets :
                if client != client_socket :
                    client.send(data)

        except ConnectionResetError as e:
            print('>> Disconnected by ' + addr[0], ':', addr[1])
            break

    if client_socket in client_sockets :
        client_sockets.remove(client_socket)
        print('remove client list : ',len(client_sockets))

    client_socket.close()

try:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    while True:
        print('>> Wait')

        client_socket, addr = server_socket.accept()
        clnt_msg = recv_clnt_msg(client_socket)
        #client_sockets.append(client_socket)

        lock.acquire()
        client_sockets.insert(clnt_cnt, [client_sockets, '!log_in', clnt_msg, 0])
        print("참가자 수 : ", len(client_sockets))
        clnt_cnt += 1 
        lock.release()

        t = threading.Thread(target=handle_clnt, args=(client_socket,))
        t1 = threading.Thread(target=threaded, args=(client_socket, addr,))
        t.start()
        t1.start()
        
        
except Exception as e :
    print ('에러는? : ',e)

finally:
    server_socket.close()
# 쓰레드에서 실행되는 코드입니다.
# 접속한 클라이언트마다 새로운 쓰레드가 생성되어 통신을 하게 됩니다.
#text123