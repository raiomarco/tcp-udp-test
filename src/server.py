#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import threading
import socket as sock

FINISH = "BEM"


def input_number(message, max_number):
    while True:
        try:
            number = int(input(message))
            if number > 0 and number < max_number:
                return number
            print("Valor fora do intervalo 1-{}".format(max_number))
        except ValueError:
            print("Entrada inválida!")


def get_buffer(s, packet_name):
    data = s.recv(1000).decode()
    return int(data[len(packet_name)+1:])


def print_udp(interval, received, expected):
    time_passed = interval[1] - interval[0]
    received_kb = len(received) * 8 / 1000.0
    packet_loss = 100 - received.count("x") * 100.0 / expected
    if time_passed:
        print("Thread UDP: recebido {} kb no tempo de {} s com velocidade de {} kb/s. Perda de pacotes: {} %".format(
            received_kb,
            time_passed,
            received_kb / time_passed,
            packet_loss
        ))
    else:
        print("Tempo medido muito curto.")


def print_tcp(interval, received):
    time_passed = interval[1] - interval[0]
    received_kb = len(received) * 8 / 1000.0
    if time_passed:
        print("Thread TCP: recebido {} kb no tempo de {} s com velocidade de {} kb/s".format(
            received_kb,
            time_passed,
            received_kb / time_passed
        ))
    else:
        print("Tempo medido muito curto.")


def accept_clients(tcp_socket, udp_socket):
    tcp_t = None
    udp_t = None
    conn = None

    while True:
        try:
            conn = tcp_socket.accept()[0]
            if (tcp_t and tcp_t.is_alive()) or (udp_t and udp_t.is_alive()):
                conn.send("OCUPADO".encode())
                conn.close()
            else:
                conn.send("OK".encode())
                print("Cliente Conectado.")
                tcp_t = threading.Thread(target=receive_tcp, args=(conn, ))
                udp_t = threading.Thread(target=receive_udp, args=(udp_socket, ))
                tcp_t.start()
                udp_t.start()
        except sock.error as e:
            print(e.strerror)
            break

    if tcp_t and tcp_t.is_alive():
        if conn:
            conn.shutdown(sock.SHUT_RDWR)
            conn.close()
        tcp_t.join()

    if udp_t and udp_t.is_alive():
        udp_t.join()


def receive_udp(udp_socket):
    try:
        max_buffer_size = get_buffer(udp_socket, 'TAMANHO')
        expected = get_buffer(udp_socket, 'TOTAL')
    except ValueError:
        print("Mensagem incorreta do cliente![udp]")
        return
    except sock.error as e:
        print("[udp]" + e)
        return
    received = ""
    start = time.time()

    while True:
        stop = time.time()
        try:
            data = udp_socket.recv(max_buffer_size)
            if data.decode() == FINISH:
                break
            else:
                received += data.decode()

        except sock.error as e:
            print(e)
            break
    print_udp((start, stop), received, expected)


def receive_tcp(conn):
    try:
        max_buffer_size = get_buffer(conn, 'TAMANHO')
    except ValueError as e:
        print("Mensagem incorreta do cliente![tcp]")
        print(e)
        conn.close()
        return
    except sock.error as e:
        print(e.strerror)
        conn.close()
        return

    received = ""
    start = time.time()
    while True:
        stop = time.time()
        try:
            data = conn.recv(max_buffer_size)
            if not data:
                print("Conexão Terminou Prematuramente![tcp]")
                break

            if data.decode() == FINISH:
                break
            else:
                received += data.decode()
        except sock.error:
            break
    print_tcp((start, stop), received)
    conn.close()


def configure_tcp(port):
    tcp_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    tcp_socket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
    tcp_socket.bind(('', port))
    tcp_socket.listen(10)
    print('Servidor TCP pronto...')
    return tcp_socket


def configure_udp(port):
    udp_socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
    udp_socket.bind(('', port))
    # timeout é necessário para não ficar travado na udp_thread
    udp_socket.settimeout(10)
    print('Servidor UDP pronto...')
    return udp_socket


def main():
    port = input_number("Insira a porta: ", 65535)

    tcp_socket = configure_tcp(port)
    udp_socket = configure_udp(port)

    accepting_thread = threading.Thread(target=accept_clients, args=(tcp_socket, udp_socket))
    accepting_thread.start()

    while True:
        c = input("Insira q para sair:\n")
        if c == "q":
            tcp_socket.shutdown(sock.SHUT_RDWR)
            tcp_socket.close()
            udp_socket.close()
            break

    accepting_thread.join()


if __name__ == "__main__":
    main()
