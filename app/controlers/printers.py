import json
import socket
from datetime import datetime

from app.controlers.core_classes import ticket_info
from app.models.config import Config

DEFAULT_FONT = 'Lucida Console'
REPEAT_CHARS = 30

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
        # Ensure we have an up-to-date list of printers from the service before validating
        printers = self.list(ipv4, refresh=True)
        if printer not in printers:
            raise ValueError(f'Printer not in avaliable printers in host: {ipv4}')
        
        query = {
            'action': 'printer/put',
            'printer': printer,
        }

        result = self.__query_service(query, ipv4)

        # Invalidate cached printers so future reads reflect the updated default immediately
        if ipv4 in self.avaliable_printers:
            try:
                del self.avaliable_printers[ipv4]
            except Exception:
                self.avaliable_printers.pop(ipv4, None)

        return result
    
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
        def create_separator_line(line_number: int, font: str, font_config: int, size: int, weight: int, repeat_chars: int = REPEAT_CHARS) -> dict:
            """
            Create a separator line for ticket printing.
            
            Args:
                line_number: The line number in the ticket
                font: Font family to use
                font_config: Font configuration ID
                size: Font size
                weight: Font weight
                repeat_chars: Number of times to repeat the separator pattern
            
            Returns:
                Dictionary with separator line configuration
            """
            return {
                'font': font,
                'font_config': font_config,
                'line': line_number,
                'size': size,
                'text': '---' * repeat_chars,
                'weigh': weight,
                'cut_row': True,
                'jumpline': False
            }
        
        @staticmethod
        def _get_font_config(config_getter, defaults: dict) -> dict:
            """
            Helper method to retrieve font configuration with fallback defaults.
            
            Args:
                config_getter: Function to call for config retrieval
                defaults: Dictionary with default values (font, size, weigh, id)
            
            Returns:
                Dictionary with font configuration
            """
            try:
                config = config_getter()
                return {
                    'font': config.get('font') if config else defaults['font'],
                    'size': config.get('size') if config else defaults['size'],
                    'weigh': config.get('weigh') if config else defaults['weigh'],
                    'id': config.get('id') if config and 'id' in config else defaults['id']
                }
            except Exception:
                return defaults

        @staticmethod
        def _add_header_lines(lines: list, line_number: int, ticket_id: int, header_config: dict) -> int:
            """
            Add header lines (date, time, ticket ID) to the ticket.
            
            Args:
                lines: List to append lines to
                line_number: Current line number
                ticket_id: Ticket identifier
                header_config: Header font configuration
            
            Returns:
                Updated line number
            """
            now = datetime.now()
            fecha = now.strftime('%d-%m-%Y')
            hora = now.strftime('%H:%M')
            
            lines.append({
                'font': header_config['font'],
                'font_config': header_config['id'],
                'line': line_number,
                'size': header_config['size'],
                'text': f'DATE: {fecha} {hora}',
                'weigh': header_config['weigh'],
                'cut_row': False,
                'jumpline': False
            })
            line_number += 1
            
            lines.append({
                'font': header_config['font'],
                'font_config': header_config['id'],
                'line': line_number,
                'size': header_config['size'],
                'text': f'TICKET º {ticket_id}',
                'weigh': header_config['weigh'],
                'cut_row': False,
                'jumpline': False
            })
            return line_number + 1

        @staticmethod
        def _add_notes_lines(lines: list, line_number: int, notes: str, content_config: dict) -> int:
            """
            Add notes lines to the ticket if notes are provided.
            
            Args:
                lines: List to append lines to
                line_number: Current line number
                notes: Notes text (may contain newlines)
                content_config: Content font configuration
            
            Returns:
                Updated line number
            """
            if not notes:
                return line_number
            
            note_lines = notes.split('\n')
            for note_line in note_lines:
                lines.append({
                    'font': content_config['font'],
                    'font_config': content_config['id'],
                    'line': line_number,
                    'size': content_config['size'],
                    'text': note_line,
                    'weigh': content_config['weigh'],
                    'cut_row': False,
                    'jumpline': False
                })
                line_number += 1
            return line_number

        @staticmethod
        def _add_product_lines(lines: list, line_number: int, products: list, content_config: dict, print_full_row: bool) -> int:
            """
            Add product lines to the ticket.
            
            Args:
                lines: List to append lines to
                line_number: Current line number
                products: List of product dictionaries
                content_config: Content font configuration
                print_full_row: Whether to print full row or cut
            
            Returns:
                Updated line number
            """
            for product in products:
                description = f'{product.get('description', '')}'.strip()
                
                lines.append({
                    'font': content_config['font'],
                    'font_config': content_config['id'],
                    'line': line_number,
                    'size': content_config['size'],
                    'text': description,
                    'weigh': content_config['weigh'],
                    'cut_row': not print_full_row,
                    'jumpline': not print_full_row
                })
                line_number += 1
                
                cantity = product.get('cantity', 0)
                sale_price = product.get('sale_price', 0)
                total_price = product.get('total_price', 0)
                detail_line = f'{cantity} PZ\\${sale_price}\\${total_price}'
                
                lines.append({
                    'font': content_config['font'],
                    'font_config': content_config['id'],
                    'line': line_number,
                    'size': content_config['size'],
                    'text': detail_line,
                    'weigh': content_config['weigh'],
                    'cut_row': not print_full_row,
                    'jumpline': not print_full_row
                })
                line_number += 1
            return line_number

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
            
            # Get print_full_row setting from database
            try:
                print_full_row = Config.Ticket_text.get_print_full_row()
            except Exception:
                print_full_row = True
            
            # Get font configurations
            content_config = Printers.Tasks._get_font_config(
                Config.Ticket_text.get_body_font,
                {'font': DEFAULT_FONT, 'size': 30, 'weigh': 1500, 'id': 1}
            )
            header_config = Printers.Tasks._get_font_config(
                Config.Ticket_text.get_header_font,
                {'font': DEFAULT_FONT, 'size': 36, 'weigh': 2000, 'id': 2}
            )
            
            # Add header lines
            line_number = Printers.Tasks._add_header_lines(lines, line_number, ticket_id, header_config)
            
            # Add notes if provided
            line_number = Printers.Tasks._add_notes_lines(lines, line_number, notes, content_config)
            
            # Empty line for spacing
            lines.append({
                'font': content_config['font'],
                'font_config': content_config['id'],
                'line': line_number,
                'size': content_config['size'],
                'text': '',
                'weigh': content_config['weigh'],
                'cut_row': False,
                'jumpline': False
            })
            line_number += 1
            
            # Column headers
            lines.append({
                'font': content_config['font'],
                'font_config': content_config['id'],
                'line': line_number,
                'size': content_config['size'],
                'text': 'CANTITY\\PRICE\\TOTAL',
                'weigh': content_config['weigh'],
                'cut_row': False,
                'jumpline': False
            })
            line_number += 1
            
            # Separator line
            lines.append(Printers.Tasks.create_separator_line(
                line_number, content_config['font'], content_config['id'],
                content_config['size'], content_config['weigh']
            ))
            line_number += 1
            
            # Add product lines
            line_number = Printers.Tasks._add_product_lines(
                lines, line_number, ticket_info.get('products', []), content_config, print_full_row
            )
            
            # Separator line before totals
            lines.append(Printers.Tasks.create_separator_line(
                line_number, content_config['font'], content_config['id'],
                content_config['size'], content_config['weigh']
            ))
            line_number += 1
            
            # Total line
            total = ticket_info.get('sub_total', 0)
            lines.append({
                'font': header_config['font'],
                'font_config': header_config['id'],
                'line': line_number,
                'size': header_config['size'] * 1.2,
                'text': f'TOTAL: $ {total}',
                'weigh': header_config['weigh'],
                'cut_row': False,
                'jumpline': False
            })
            line_number += 1
            
            # Products count
            articles_count = ticket_info.get('articles_count', 0)
            lines.append({
                'font': content_config['font'],
                'font_config': content_config['id'],
                'line': line_number,
                'size': content_config['size'],
                'text': f'PRODUCTS: {articles_count}',
                'weigh': content_config['weigh'],
                'cut_row': False,
                'jumpline': False
            })
            
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