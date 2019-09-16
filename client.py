import time
import timeit
import threading
import socket as sock
import math

HOST = "45.55.62.128"
MAX_SIZE = 50000
MAX_COUNT = 10000

def input_number(message, max_number):
    while True:
        try:
            number = int(input(message))
            if number > 0 and number <= max_number:
                return number
            print("Valor fora do intervalo 1-{}".format(max_number))
        except ValueError:
            print("Entrada inválida!")

def create_packets(concat_packets, packet_count, packet_size, max_buffer_size):
    packets = ["x" * packet_size] * packet_count
    if concat_packets:
        whole_message = "".join(packets)
        packets = [ whole_message[i*max_buffer_size:(i+1)*max_buffer_size] for i in range(int(math.ceil(float(len(whole_message))/max_buffer_size)))]
    return packets, len(packets[0]) * (len(packets) - 1) + len(packets[-1])

def tcp_sender(tcp_socket, packets):
    packet_size = len(packets[0])
    try:
        time.sleep(0.001)
        tcp_socket.send("TAMANHO:{}".format(packet_size).encode())
        for packet in packets:
            time.sleep(0.00001)
            ti = ((timeit.default_timer())*1000)
            tcp_socket.send(packet.encode())
            data = tcp_socket.recv(packet_size)
            tf = ((timeit.default_timer())*1000)
            print("[tcp]Servidor respondeu")
            print("[tcp]Tempo: ",tf-ti,"ms")
        tcp_socket.send("BEM".encode())
        tcp_socket.shutdown(sock.SHUT_RDWR)
        tcp_socket.close()
        print("Concluído, pressione q para sair ou qualquer outra coisa para enviar novamente: ")
    except sock.error as e:
        print(e)
        return

def send_udp(udp_socket, data, address):
    time.sleep(0.00001)
    udp_socket.sendto(data.encode(), address)

def udp_sender(udp_socket, packets, address, total_size):
    packet_size = len(packets[0])
    try:
        send_udp(udp_socket, "TAMANHO:{}".format(packet_size), address)
        time.sleep(0.0001)
        send_udp(udp_socket, "TOTAL:{}".format(total_size), address)
        time.sleep(0.0001)
        for packet in packets:
            ti = ((timeit.default_timer())*1000)
            send_udp(udp_socket, packet, address)
            data = udp_socket.recvfrom(packet_size)
            tf = ((timeit.default_timer())*1000)
            print("[udp]Tempo: ",tf-ti,"ms")
        time.sleep(0.0001)
        send_udp(udp_socket, "BEM", address)
        print("[udp]udp enviado")
    except sock.error as e:
        print(e)
        return

def send_both(tcp_socket, udp_socket, max_buffer_size, address):
    concat_packets = input("Concatenar pacotes? [y]:") == 'y'
    packet_size = input_number("Tamanho do Pacote: ", max_buffer_size)
    packet_count = input_number("Quantos pacotes: ", MAX_COUNT)

    try:
        tcp_socket.connect(address)
        message = tcp_socket.recv(10).decode()
        if message == "OCUPADO":
            print("Servidor ocupado.")
            return None, None
        elif message != "OK":
            print("Resposta Desconhecida do Servidor.")
            return None, None
    except sock.error as e:
        print("Falha ao conectar ao servidor. Erro: " + e.strerror)
        return None, None

    packets, total_size = create_packets(concat_packets, packet_count, packet_size, max_buffer_size)
    tcp_thread = threading.Thread(target=tcp_sender, args=(tcp_socket, packets))
    udp_thread = threading.Thread(target=udp_sender, args=(udp_socket, packets, address, total_size))

    tcp_thread.start()
    udp_thread.start()
    return  tcp_thread, udp_thread


def configure_tcp(port):
    tcp_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    tcp_socket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
    return tcp_socket

def main():
    port = input_number("Insira a porta: ", 65535)
    max_buffer_size = input_number("Insira o tamanho máximo do buffer: ", MAX_SIZE)

    udp_socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
    tcp_thread, udp_thread = None, None
    while True:
        if input("Insira q para sair ou qualquer outra coisa para começar a enviar: ") == "q":
            if (tcp_thread and tcp_thread.is_alive()) or (udp_thread and udp_thread.is_alive()):
                tcp_socket.shutdown(sock.SHUT_RDWR)
                udp_socket.close()
                udp_socket = None
                tcp_socket.close()
                if (tcp_thread and tcp_thread.is_alive()): tcp_thread.join()
                if (udp_thread and udp_thread.is_alive()): udp_thread.join()
            break
        elif not tcp_thread or not tcp_thread.is_alive():
            tcp_socket = configure_tcp(port)
            tcp_thread, udp_thread = send_both(tcp_socket, udp_socket, max_buffer_size, (HOST, port))
    if udp_socket: udp_socket.close()


if __name__ == "__main__":
    main()
