import socket
import threading
import os
import hashlib
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
import time  # Import time module

def calcular_hash(arquivo):
    sha256 = hashlib.sha256()
    with open(arquivo, 'rb') as f:
        for bloco in iter(lambda: f.read(4096), b''):
            sha256.update(bloco)
    return sha256.hexdigest()

def handle_client(client_socket, client_address):
    print(f"Conexão de {client_address} estabelecida.")
    chat_window = None

    while True:
        try:
            request = client_socket.recv(1024).decode('utf-8')

            if not request:
                break

            if request.startswith("Sair"):
                print(f"Cliente {client_address} desconectado.")
                break

            elif request.startswith("Arquivo"):
                parts = request.split(' ', 1)
                threading.Thread(target=send_archive(parts,client_socket, client_address)).start()
                            
            elif request.startswith("Chat"):
                if not chat_window:
                    chat_window = ChatWindow(server_root, client_socket, client_address)
                chat_window.display_message(f"Cliente {client_address}: {request[5:]}\n")
                    
        except ConnectionResetError:
            print(f"Conexão com {client_address} foi perdida.")
            break

    client_socket.close()
    clients.remove(client_socket)
    if chat_window:
        chat_window.close_window()
def send_archive(parts, client_socket, client_address):
    if len(parts) == 2:
        nome_arquivo = parts[1]
        if os.path.exists(nome_arquivo):
            tamanho_arquivo = os.path.getsize(nome_arquivo)
            hash_arquivo = calcular_hash(nome_arquivo)

            metadados = f"Nome: {nome_arquivo}\nTamanho: {tamanho_arquivo}\nHash: {hash_arquivo}\nStatus: ok\n"
            client_socket.send(metadados.encode('utf-8'))

            confirmacao = client_socket.recv(1024).decode('utf-8')
            if confirmacao == "Pronto para receber":
                with open(nome_arquivo, 'rb') as f:
                    parte_numero = 1
                    while True:
                        dados = f.read(4096)
                        if not dados:
                            break
                        client_socket.sendall(dados)
                        print(f"Enviando parte {parte_numero} para {client_address}: {dados[:10]}... ({len(dados)} bytes)")
                        parte_numero += 1
                client_socket.send("EOF".encode('utf-8'))
                print(f"Envio do arquivo {nome_arquivo} completo para {client_address}")
        else:
            client_socket.send("Status: arquivo inexistente\n".encode('utf-8'))
                
class ChatWindow:
    def __init__(self, root, client_socket, client_address):
        self.client_socket = client_socket
        self.client_address = client_address

        self.window = tk.Toplevel(root)
        self.window.title(f"Chat com {client_address}")

        self.chat_log = scrolledtext.ScrolledText(self.window, state='disabled', width=50, height=20)
        self.chat_log.pack()

        self.chat_entry = tk.Entry(self.window, width=50)
        self.chat_entry.pack()
        self.chat_entry.bind("<Return>", self.send_message)

    def display_message(self, message):
        self.chat_log.config(state='normal')
        self.chat_log.insert(tk.END, message)
        self.chat_log.config(state='disabled')

    def send_message(self, event):
        mensagem = self.chat_entry.get()
        self.client_socket.send(f"Chat {mensagem}".encode('utf-8'))
        self.display_message(f"Você: {mensagem}\n")
        if mensagem.lower() == 'sair':
            self.client_socket.send("Sair".encode('utf-8'))
            self.window.destroy()

    def close_window(self):
        self.window.destroy()

def broadcast_message(message):
    for client in clients:
        try:
            client.send(f"Broadcast: {message}\n".encode('utf-8'))
        except:
            client.close()
            clients.remove(client)

def start_server():
    global clients, server_root
    clients = []

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))
    server.listen(5)
    print("Servidor escutando na porta 9999...")

    while True:
        client_socket, client_address = server.accept()
        clients.append(client_socket)
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

def enviar_broadcast(event=None):
    mensagem = broadcast_entry.get()
    broadcast_entry.delete(0, tk.END)
    broadcast_message(mensagem)
    broadcast_log.config(state='normal')
    broadcast_log.insert(tk.END, f"Você: {mensagem}\n")
    broadcast_log.config(state='disabled')

if __name__ == "__main__":
    server_root = tk.Tk()
    server_root.title("Servidor TCP")

    broadcast_frame = tk.Frame(server_root)
    broadcast_frame.pack()

    broadcast_log = scrolledtext.ScrolledText(broadcast_frame, state='disabled', width=50, height=20)
    broadcast_log.pack()

    broadcast_entry = tk.Entry(broadcast_frame, width=50)
    broadcast_entry.pack()
    broadcast_entry.bind("<Return>", enviar_broadcast)

    threading.Thread(target=start_server).start()
    server_root.mainloop()
