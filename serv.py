import socket

server = socket.socket()
print("소켓 생성완료")
s_name = socket.gethostname()

print('서버 컴퓨터이름: ', s_name)
server.bind((s_name, 9060))

server.listen(3)
print('서버 리슨닝...')

while 1:
    client, address = server.accept()
    name = client.recv(1024).decode()
    print("클라이언트와 연결되었습니다.", name)

    client.send(bytes('서버에 연결되었습니다', 'utf-8'))
    client.close()