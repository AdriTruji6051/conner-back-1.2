import json
import socket

from app.controlers.core_classes import ticket_info

class Printers:
    register_printers = dict()

    def __query_service(self, query: object, ipv4: str = '127.0.0.1', port: int = 9100) -> any:
        try:
            if not query:
                raise ValueError('Query must not be empty.')
            
            if isinstance(query, dict):
                query = json.dumps(query)
            
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((ipv4, port))

            client_socket.sendall(query.encode('utf-8'))
            data = client_socket.recv(1024)
            data = json.loads(data.decode('utf-8'))
            client_socket.close()

            return data
        except ConnectionRefusedError as e:
            raise ConnectionRefusedError(f'Server is not reacheable!. Server ip: {ipv4}:{port}')
        except Exception as e:
            raise e

    def list(self, ipv4: str = '127.0.0.1') -> list:
        return self.__query_service('print/list', ipv4)
    
    def dict(self, ipv4: str = '127.0.0.1') -> dict:
        return self.__query_service('print/dict', ipv4)
    
    def update_printer(self, printer: str, ipv4: str = '127.0.0.1') -> str:
        if printer not in self.list(ipv4):
            raise ValueError(f'Printer not in avaliable printers in host: {ipv4}')
        
        query = {
            'action': 'printer/put',
            'printer': printer,
        }

        return self.__query_service(query, ipv4)
    
    def open_drawer(self, ipv4: str = '127.0.0.1'):
        return self.__query_service('drawer/open', ipv4)

    def stop_service(self, ipv4: str = '127.0.0.1'):
        return self.__query_service('service/stop', ipv4)
    

    # TODO
    class Tasks:
        @staticmethod
        def struct_ticket():
            return
        
        def struct_tag():
            return