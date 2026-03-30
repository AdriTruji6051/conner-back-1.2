import json
import socket
from datetime import datetime

from app.controlers.core_classes import ticket_info
from app.models.config import Config

class Printers:
    register_printers = dict()
    avaliable_printers = dict()

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
        except ConnectionRefusedError:
            raise ConnectionRefusedError(f'Server is not reacheable!. Server ip: {ipv4}:{port}')

    def __fetch_and_cache_printers(self, ipv4: str = '127.0.0.1') -> dict:
        printers = self.__query_service('print/dict', ipv4)
        self.avaliable_printers[ipv4] = printers
        return printers

    def list(self, ipv4: str = '127.0.0.1', refresh: bool = False) -> list:
        return list(self.dict(ipv4, refresh=refresh).keys())
    
    def dict(self, ipv4: str = '127.0.0.1', refresh: bool = False) -> dict:
        cached = self.avaliable_printers.get(ipv4)
        if refresh or cached is None or not cached:
            return self.__fetch_and_cache_printers(ipv4)
        return cached
    
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
    
    def print_ticket(self, ticket_info: ticket_info, ticket_id: int, notes: str, printer_name: str, ipv4: str = '127.0.0.1', print_many: int = 1):
        """
        Structure ticket data and send to printer multiple times.
        
        Args:
            ticket_info: Dictionary containing ticket products and totals
            ticket_id: The ticket identifier
            notes: Notes to include on ticket
            printer_name: Name of the printer to send to
            ipv4: IP address of the printer service
            print_many: Number of times to print the ticket
        """
        if print_many <= 0 or not printer_name:
            return
        
        # Verify printer exists
        if printer_name not in self.list(ipv4):
            raise ValueError(f'Printer "{printer_name}" not found in available printers on host {ipv4}')
        
        # Structure ticket content with headers, content, and footers
        printer_content = Printers.Tasks.struct_ticket(ticket_info, ticket_id, notes)
        
        # Send to printer multiple times
        for attempt in range(print_many):
            try:
                # Create print query with the structured content
                print_query = {
                    'action': 'printer/ticket',
                    'printContext': printer_content
                }
                print(print_query)
                self.__query_service(print_query, ipv4)
            except Exception as e:
                # Log warning but don't fail - ticket is already saved
                print(f'Warning: Failed to print ticket (attempt {attempt + 1}/{print_many}): {str(e)}')

    class Tasks:
        @staticmethod
        def struct_content(ticket_info: ticket_info, ticket_id: int, notes: str = '') -> list:
            """
            Format ticket information into printer-ready content structure.
            
            Args:
                ticket_info: Dictionary containing ticket products and totals
                ticket_id: The ticket identifier
                notes: Optional notes to include on ticket
            
            Returns:
                List of line objects formatted for printer with font, size, weight config
            """
            lines = []
            line_number = 0
            
            # Content font configuration
            CONTENT_FONT = 'Lucida Console'
            CONTENT_SIZE = 30
            CONTENT_WEIGHT = 1500
            CONTENT_CONFIG = 1
            
            # Header font configuration (larger)
            HEADER_FONT = 'Lucida Console'
            HEADER_SIZE = 36
            HEADER_WEIGHT = 2000
            HEADER_CONFIG = 2
            
            # Get current date and time
            now = datetime.now()
            fecha = now.strftime('%d-%m-%Y')
            hora = now.strftime('%H:%M')
            
            # Header line: FECHA and TICKET
            lines.append({
                'font': HEADER_FONT,
                'font_config': HEADER_CONFIG,
                'line': line_number,
                'size': HEADER_SIZE,
                'text': f'DATE: {fecha} {hora}',
                'weigh': HEADER_WEIGHT
            })
            line_number += 1
            
            lines.append({
                'font': HEADER_FONT,
                'font_config': HEADER_CONFIG,
                'line': line_number,
                'size': HEADER_SIZE,
                'text': f'TICKET º {ticket_id}',
                'weigh': HEADER_WEIGHT
            })
            line_number += 1
            
            # Empty line for spacing
            lines.append({
                'font': CONTENT_FONT,
                'font_config': CONTENT_CONFIG,
                'line': line_number,
                'size': CONTENT_SIZE,
                'text': '',
                'weigh': CONTENT_WEIGHT
            })
            line_number += 1
            
            # Column headers
            lines.append({
                'font': CONTENT_FONT,
                'font_config': CONTENT_CONFIG,
                'line': line_number,
                'size': CONTENT_SIZE,
                'text': 'CANTITY\t\PRICE\t\TOTAL',
                'weigh': CONTENT_WEIGHT
            })
            line_number += 1
            
            # Separator line
            lines.append({
                'font': CONTENT_FONT,
                'font_config': CONTENT_CONFIG,
                'line': line_number,
                'size': CONTENT_SIZE,
                'text': '---' * 20,
                'weigh': CONTENT_WEIGHT
            })
            line_number += 1
            
            # Product lines
            for product in ticket_info.get('products', []):
                # Product name/code and description
                code = product.get('code', '')
                description = product.get('description', '')
                product_name = f'{code} {description}'.strip()
                
                lines.append({
                    'font': CONTENT_FONT,
                    'font_config': CONTENT_CONFIG,
                    'line': line_number,
                    'size': CONTENT_SIZE,
                    'text': product_name,
                    'weigh': CONTENT_WEIGHT
                })
                line_number += 1
                
                # Product detail line: quantity, unit price, total price
                cantity = product.get('cantity', 0)
                sale_price = product.get('sale_price', 0)
                total_price = product.get('total_price', 0)
                
                detail_line = f'{cantity} PZ\t\t${sale_price}\t\t${total_price}'
                lines.append({
                    'font': CONTENT_FONT,
                    'font_config': CONTENT_CONFIG,
                    'line': line_number,
                    'size': CONTENT_SIZE,
                    'text': detail_line,
                    'weigh': CONTENT_WEIGHT
                })
                line_number += 1
            
            # Separator line before totals
            lines.append({
                'font': CONTENT_FONT,
                'font_config': CONTENT_CONFIG,
                'line': line_number,
                'size': CONTENT_SIZE,
                'text': '---' * 20,
                'weigh': CONTENT_WEIGHT
            })
            line_number += 1
            
            # Total line
            total = ticket_info.get('sub_total', 0)
            lines.append({
                'font': HEADER_FONT,
                'font_config': HEADER_CONFIG,
                'line': line_number,
                'size': HEADER_SIZE,
                'text': f'TOTAL: $ {total}',
                'weigh': HEADER_WEIGHT
            })
            line_number += 1
            
            # Products count
            articles_count = ticket_info.get('articles_count', 0)
            
            lines.append({
                'font': CONTENT_FONT,
                'font_config': CONTENT_CONFIG,
                'line': line_number,
                'size': CONTENT_SIZE,
                'text': f'PRODUCTOS: {articles_count}',
                'weigh': CONTENT_WEIGHT
            })
            line_number += 1
            
            # Notes if provided
            if notes:
                lines.append({
                    'font': CONTENT_FONT,
                    'font_config': CONTENT_CONFIG,
                    'line': line_number,
                    'size': CONTENT_SIZE,
                    'text': notes,
                    'weigh': CONTENT_WEIGHT
                })
                line_number += 1
            
            return lines
        
        @staticmethod
        def struct_ticket(ticket_info: ticket_info, ticket_id: int, notes: str = '') -> dict:
            """
            Format complete ticket structure with headers, content, and footers.
            
            Args:
                ticket_info: Dictionary containing ticket products and totals
                ticket_id: The ticket identifier
                notes: Optional notes to include on ticket
            
            Returns:
                Dictionary with 'header', 'content', and 'footer' sections
            """
            return {
                'header': Config.Ticket_text.get_headers(),
                'content': Printers.Tasks.struct_content(ticket_info, ticket_id, notes),
                'footer': Config.Ticket_text.get_footers()
            }