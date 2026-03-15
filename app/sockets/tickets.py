from flask_socketio import emit, join_room, leave_room
from flask import request
import logging

from app.extensions import socketio

TICKET_MANAGER = None

def init_ticket_sockets(ticket_manager):
    """Initialize the socket handlers with a reference to the shared Tickets_manager instance."""
    global TICKET_MANAGER
    TICKET_MANAGER = ticket_manager


def broadcast_ticket_update(ticket_key: int):
    """Emit the latest ticket info to all clients in the ticket's room."""
    room = f'ticket_{ticket_key}'
    try:
        info = TICKET_MANAGER.get_ticket_info(ticket_key)
        socketio.emit('ticket_update', {'ticket_key': ticket_key, 'data': info}, to=room)
    except ValueError:
        socketio.emit('ticket_error', {'ticket_key': ticket_key, 'error': 'Ticket not found'}, to=room)


@socketio.on('join_ticket')
def handle_join_ticket(data):
    """Client requests to subscribe to real-time updates for a ticket.
    
    Expected payload: { "ticket_key": int }
    """
    ticket_key = data.get('ticket_key')
    if ticket_key is None:
        emit('ticket_error', {'error': 'ticket_key is required'})
        return

    try:
        ticket_key = int(ticket_key)
    except (TypeError, ValueError):
        emit('ticket_error', {'error': 'ticket_key must be an integer'})
        return

    room = f'ticket_{ticket_key}'
    join_room(room)

    try:
        info = TICKET_MANAGER.get_ticket_info(ticket_key)
        emit('ticket_update', {'ticket_key': ticket_key, 'data': info})
    except ValueError as e:
        emit('ticket_error', {'ticket_key': ticket_key, 'error': str(e)})

    logging.info(f'WebSocket: client {request.sid} joined room {room}')


@socketio.on('leave_ticket')
def handle_leave_ticket(data):
    """Client requests to unsubscribe from a ticket's room.
    
    Expected payload: { "ticket_key": int }
    """
    ticket_key = data.get('ticket_key')
    if ticket_key is None:
        emit('ticket_error', {'error': 'ticket_key is required'})
        return

    room = f'ticket_{ticket_key}'
    leave_room(room)
    emit('ticket_left', {'ticket_key': ticket_key})
    logging.info(f'WebSocket: client {request.sid} left room {room}')


@socketio.on('disconnect')
def handle_disconnect():
    logging.info(f'WebSocket: client {request.sid} disconnected')
