from app.extensions import db
from app.models.core_classes import User, TicketText, TicketFontConfig, TicketSettings
from app.helpers.helpers import raise_exception_if_missing_keys, ValidationError, collect_missing_keys
from sqlalchemy import event
import uuid

create_user_keys = ['user', 'user_name', 'password', 'role_type']
update_user_keys = ['user', 'user_name', 'password', 'role_type', 'id']
create_text_keys = ['text', 'line', 'is_header', 'font_config']
create_font_config_keys = ['font', 'weigh', 'size']

DEFAULT_FONT_NAME = 'Consolas'
DEFAULT_FONT_SIZE = 12
DEFAULT_FONT_WEIGHT = 500

_DEFAULT_FONT_CONFIG_ID: int | None = None


def ensure_default_font_config() -> TicketFontConfig:
    """Ensure the default ticket font exists and cache its id."""
    global _DEFAULT_FONT_CONFIG_ID

    font_cfg = TicketFontConfig.query.filter_by(
        font=DEFAULT_FONT_NAME,
        size=DEFAULT_FONT_SIZE,
        weigh=DEFAULT_FONT_WEIGHT,
    ).first()

    if not font_cfg:
        font_cfg = TicketFontConfig(
            font=DEFAULT_FONT_NAME,
            size=DEFAULT_FONT_SIZE,
            weigh=DEFAULT_FONT_WEIGHT,
        )
        db.session.add(font_cfg)
        db.session.commit()

    _DEFAULT_FONT_CONFIG_ID = font_cfg.id
    return font_cfg


def ensure_at_least_one_user() -> User:
    """Ensure at least one user exists in the database.
    
    Creates a default admin user if no users are found.
    This prevents the system from being locked out on first run.
    """
    user_count = User.query.count()
    if user_count > 0:
        return User.query.first()
    
    admin_user = User(
        user='admin',
        user_name='admin',
        password='admin',
        role_type='admin'
    )
    db.session.add(admin_user)
    db.session.commit()
    return admin_user


def is_protected_font_config(candidate: TicketFontConfig | int | None) -> bool:
    """Return True if the provided font configuration is the default one."""
    if candidate is None:
        return False

    default_id = _DEFAULT_FONT_CONFIG_ID
    candidate_id = candidate if isinstance(candidate, int) else candidate.id

    if default_id is not None:
        return candidate_id == default_id

    if isinstance(candidate, TicketFontConfig):
        return (
            candidate.font == DEFAULT_FONT_NAME and
            candidate.size == DEFAULT_FONT_SIZE and
            candidate.weigh == DEFAULT_FONT_WEIGHT
        )

    return False


class Config:
    class Users:
        @staticmethod
        def get_all(page: int | None = None, page_size: int | None = None):
            query = User.query
            if page is not None and page_size is not None:
                pagination = query.paginate(page=page, per_page=page_size, error_out=False)
                return {
                    'items': [u.to_dict() for u in pagination.items],
                    'page': page,
                    'page_size': page_size,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            return query.all()

        @staticmethod
        def login(user: str, password: str) -> dict:
            user_obj = User.query.filter_by(user=user).first()

            if not user_obj:
                raise ValueError('User or password are incorrect!')

            if password != user_obj.password:
                raise ValueError('User or password are incorrect!')

            return {
                'id': user_obj.id,
                'user': user_obj.user,
                'user_name': user_obj.user_name,
                'role_type': user_obj.role_type,
            }

        @staticmethod
        def create(data: dict):
            v = ValidationError()
            v.errors.extend(collect_missing_keys(data, create_user_keys, 'create user'))
            if v.has_errors:
                raise v

            user = User(
                user=data['user'],
                user_name=data['user_name'],
                password=data['password'],
                role_type=data['role_type'],
            )
            db.session.add(user)
            db.session.commit()

        @staticmethod
        def update(data: dict):
            v = ValidationError()
            v.errors.extend(collect_missing_keys(data, update_user_keys, 'update user'))
            if v.has_errors:
                raise v

            user = User.query.get(data['id'])
            if not user:
                raise ValueError(f'User with id {data["id"]} not found')

            user.user = data['user']
            user.user_name = data['user_name']
            user.password = data['password']
            user.role_type = data['role_type']
            db.session.commit()

        @staticmethod
        def delete(id: int):
            user = User.query.get(id)
            if not user:
                raise ValueError(f'User with id {id} not found')
            db.session.delete(user)
            db.session.commit()

        @staticmethod
        def update_language_preference(user_id: int, language: str) -> None:
            """Update user's language preference.
            
            Args:
                user_id: User ID
                language: Language code ('es-MX' or 'en-US')
                
            Raises:
                ValueError: If user not found or invalid language
                ValidationError: If validation fails
            """
            # Validate language
            valid_languages = ['es-MX', 'en-US']
            if language not in valid_languages:
                raise ValidationError().add('language_preference', 
                    f'Invalid language. Must be one of: {", ".join(valid_languages)}')
            
            # Find user
            user = User.query.get(user_id)
            if not user:
                raise ValueError(f'User with id {user_id} not found')
            
            # Update language preference
            user.language_preference = language
            db.session.commit()

    class Ticket_text:
        @staticmethod
        def raise_exception_if_text_not_valid(data: list[dict], is_header: bool = False):
            if not data:
                raise ValidationError([{'text': 'Text array must have values, not be empty'}])

            v = ValidationError()
            for idx, row in enumerate(data):
                row = dict(row)
                prefix = f'text[{idx}].'
                v.errors.extend(
                    {prefix + k: msg for k, msg in err.items()}
                    for err in collect_missing_keys(
                        row, create_text_keys,
                        'text_headers array' if is_header else 'text_footers array'
                    )
                )

                if 'text' in row and not len(row['text']):
                    v.add(f'{prefix}text', 'Must not be empty')
                if 'line' in row and row['line'] < 0:
                    v.add(f'{prefix}line', 'Must be greater than or equal to zero')
                if 'is_header' in row:
                    if is_header and row['is_header'] != 1:
                        v.add(f'{prefix}is_header', 'Must be 1 for header rows')
                    if not is_header and row['is_header'] != 0:
                        v.add(f'{prefix}is_header', 'Must be 0 for footer rows')
                    if row['is_header'] not in [0, 1]:
                        v.add(f'{prefix}is_header', 'Must be 0 or 1')

            v.raise_if_errors()

        @staticmethod
        def get_headers() -> list[dict]:
            entries = TicketText.query.filter_by(is_header=1).order_by(TicketText.line).all()
            result = []
            for entry in entries:
                result.append(entry.to_display_dict())
            return result

        @staticmethod
        def get_footers() -> list[dict]:
            entries = TicketText.query.filter_by(is_header=0).order_by(TicketText.line).all()
            result = []
            for entry in entries:
                result.append(entry.to_display_dict())
            return result

        @staticmethod
        def update_headers(data: list[dict]):
            Config.Ticket_text.raise_exception_if_text_not_valid(data, True)
            Config.Ticket_text.drop_headers()

            for row in data:
                entry = TicketText(
                    text=row['text'],
                    line=row['line'],
                    is_header=row['is_header'],
                    font_config=row.get('font_config'),
                )
                db.session.add(entry)
            db.session.commit()

        @staticmethod
        def update_footers(data: list[dict]):
            Config.Ticket_text.raise_exception_if_text_not_valid(data, False)
            Config.Ticket_text.drop_footers()

            for row in data:
                entry = TicketText(
                    text=row['text'],
                    line=row['line'],
                    is_header=row['is_header'],
                    font_config=row.get('font_config'),
                )
                db.session.add(entry)
            db.session.commit()

        @staticmethod
        def drop_headers():
            TicketText.query.filter_by(is_header=1).delete()
            db.session.commit()

        @staticmethod
        def drop_footers():
            TicketText.query.filter_by(is_header=0).delete()
            db.session.commit()

        @staticmethod
        def getFonts() -> list[TicketFontConfig]:
            return TicketFontConfig.query.all()

        @staticmethod
        def createFont(font: str, weigh: int, size: int):
            v = ValidationError()
            if not font:
                v.add('font', 'Is required')
            if weigh is None or weigh < 0:
                v.add('weigh', 'Is required and must be >= 0')
            if size is None or size < 0:
                v.add('size', 'Is required and must be >= 0')
            v.raise_if_errors()

            fc = TicketFontConfig(font=font, weigh=weigh, size=size)
            db.session.add(fc)
            db.session.commit()

        @staticmethod
        def deleteFont(id: int):
            if is_protected_font_config(id):
                raise ValueError('Default ticket font cannot be deleted')
            fc = TicketFontConfig.query.get(id)
            if not fc:
                raise ValueError(f'Font config with id {id} not found')
            db.session.delete(fc)
            db.session.commit()

        @staticmethod
        def get_body_font() -> dict:
            """Return the currently configured body font as a dict.

            If no explicit setting exists, ensure the default font config exists and return it.
            Also create the settings row if missing.
            """
            settings = TicketSettings.query.first()
            if settings and settings.body_font_config:
                fc = TicketFontConfig.query.get(settings.body_font_config)
                if fc:
                    return fc.to_dict()

            # Fallback: ensure default font config exists and persist to settings
            fc = ensure_default_font_config()
            if not settings:
                settings = TicketSettings(body_font_config=fc.id)
                db.session.add(settings)
                db.session.commit()
            return fc.to_dict()

        @staticmethod
        def set_body_font(font_config_id: int):
            fc = TicketFontConfig.query.get(font_config_id)
            if not fc:
                raise ValueError(f'Font config with id {font_config_id} not found')
            settings = TicketSettings.query.first()
            if not settings:
                settings = TicketSettings(body_font_config=fc.id)
                db.session.add(settings)
            else:
                settings.body_font_config = fc.id
            db.session.commit()

        @staticmethod
        def get_header_font() -> dict:
            """Return the currently configured header font as a dict.

            If no explicit setting exists, ensure the default font config exists and return it.
            Also create the settings row if missing.
            """
            settings = TicketSettings.query.first()
            if settings and settings.header_font_config:
                fc = TicketFontConfig.query.get(settings.header_font_config)
                if fc:
                    return fc.to_dict()

            # Fallback: ensure default font config exists and persist to settings
            fc = ensure_default_font_config()
            if not settings:
                settings = TicketSettings(header_font_config=fc.id)
                db.session.add(settings)
                db.session.commit()
            return fc.to_dict()

        @staticmethod
        def set_header_font(font_config_id: int):
            fc = TicketFontConfig.query.get(font_config_id)
            if not fc:
                raise ValueError(f'Font config with id {font_config_id} not found')
            settings = TicketSettings.query.first()
            if not settings:
                settings = TicketSettings(header_font_config=fc.id)
                db.session.add(settings)
            else:
                settings.header_font_config = fc.id
            db.session.commit()

        @staticmethod
        def get_print_full_row() -> bool:
            """Return the current print_full_row setting.
            
            If no settings exist, create default with print_full_row=True.
            """
            settings = TicketSettings.query.first()
            if not settings:
                # Create default settings
                fc = ensure_default_font_config()
                settings = TicketSettings(
                    body_font_config=fc.id,
                    header_font_config=fc.id,
                    print_full_row=True
                )
                db.session.add(settings)
                db.session.commit()
            return settings.print_full_row

        @staticmethod
        def set_print_full_row(value: bool):
            """Update the print_full_row setting.
            
            Args:
                value: Boolean indicating whether to print full rows
            """
            if not isinstance(value, bool):
                raise ValueError('print_full_row must be a boolean value')
            
            settings = TicketSettings.query.first()
            if not settings:
                fc = ensure_default_font_config()
                settings = TicketSettings(
                    body_font_config=fc.id,
                    header_font_config=fc.id,
                    print_full_row=value
                )
                db.session.add(settings)
            else:
                settings.print_full_row = value
            db.session.commit()

        @staticmethod
        def upload_photo(photo_data: bytes, position: str = 'header', height: int | None = None, width: int = 640):
            """Upload and process a photo for ticket printing.
            
            Args:
                photo_data: Raw image bytes
                position: 'header' or 'footer' - where to print the photo
                height: Optional custom height in pixels (50-1000)
                width: Width in pixels (100-640). Default 640 for 80mm thermal printer
            """
            from PIL import Image
            import io
            
            v = ValidationError()
            if not photo_data:
                v.add('photo_data', 'Photo data is required')
            if position not in ['header', 'footer']:
                v.add('position', 'Position must be "header" or "footer"')
            if height is not None and (height < 50 or height > 1000):
                v.add('height', 'Height must be between 50 and 1000 pixels')
            if width < 100 or width > 640:
                v.add('width', 'Width must be between 100 and 640 pixels')
            v.raise_if_errors()
            
            # Process image: convert to grayscale and resize to specified width
            img = Image.open(io.BytesIO(photo_data))
            
            # Convert to grayscale
            img = img.convert('L')
            
            # Calculate aspect ratio
            aspect_ratio = img.height / img.width
            
            if height is None:
                # Auto-calculate height based on aspect ratio and width
                new_height = int(width * aspect_ratio)
            else:
                new_height = height
            
            # Resize image
            img = img.resize((width, new_height), Image.Resampling.LANCZOS)
            
            # Convert back to bytes
            output = io.BytesIO()
            img.save(output, format='PNG')
            processed_data = output.getvalue()
            
            # Generate unique photo ID
            photo_id = str(uuid.uuid4())
            
            # Save to database
            settings = TicketSettings.query.first()
            if not settings:
                fc = ensure_default_font_config()
                settings = TicketSettings(
                    body_font_config=fc.id,
                    header_font_config=fc.id,
                    photo_id=photo_id,
                    photo_data=processed_data,
                    photo_position=position,
                    photo_height=new_height,
                    photo_width=width,
                    photo_enabled=True
                )
                db.session.add(settings)
            else:
                settings.photo_id = photo_id
                settings.photo_data = processed_data
                settings.photo_position = position
                settings.photo_height = new_height
                settings.photo_width = width
                settings.photo_enabled = True
            
            db.session.commit()
            
            # Push photo to all printer services
            from app.helpers.helpers import push_photo_to_all_services
            push_results = push_photo_to_all_services(photo_id, processed_data)
            
            return {
                'photo_id': photo_id,
                'height': new_height, 
                'width': width,
                'distributed_to': push_results
            }

        @staticmethod
        def get_photo_config() -> dict:
            """Get current photo configuration."""
            settings = TicketSettings.query.first()
            if not settings:
                return {
                    'photo_enabled': False,
                    'photo_position': 'header',
                    'photo_height': None,
                    'photo_width': 640,
                    'has_photo': False
                }
            
            return {
                'photo_enabled': settings.photo_enabled,
                'photo_position': settings.photo_position,
                'photo_height': settings.photo_height,
                'photo_width': settings.photo_width or 640,
                'has_photo': settings.photo_data is not None
            }

        @staticmethod
        def get_photo_data() -> bytes | None:
            """Get the raw photo data for printing."""
            settings = TicketSettings.query.first()
            if not settings or not settings.photo_data:
                return None
            return settings.photo_data

        @staticmethod
        def update_photo_config(enabled: bool | None = None, position: str | None = None, height: int | None = None, width: int | None = None):
            """Update photo configuration without changing the photo itself."""
            v = ValidationError()
            if position is not None and position not in ['header', 'footer']:
                v.add('position', 'Position must be "header" or "footer"')
            if height is not None and (height < 50 or height > 1000):
                v.add('height', 'Height must be between 50 and 1000 pixels')
            if width is not None and (width < 100 or width > 640):
                v.add('width', 'Width must be between 100 and 640 pixels')
            v.raise_if_errors()
            
            settings = TicketSettings.query.first()
            if not settings:
                fc = ensure_default_font_config()
                settings = TicketSettings(
                    body_font_config=fc.id,
                    header_font_config=fc.id
                )
                db.session.add(settings)
            
            if enabled is not None:
                settings.photo_enabled = enabled
            if position is not None:
                settings.photo_position = position
            if height is not None:
                settings.photo_height = height
            if width is not None:
                settings.photo_width = width
            
            db.session.commit()

        @staticmethod
        def delete_photo():
            """Remove the photo from ticket configuration and all printer services."""
            settings = TicketSettings.query.first()
            if settings and settings.photo_id:
                photo_id = settings.photo_id
                
                # Delete from all printer services
                from app.helpers.helpers import delete_photo_from_all_services
                delete_results = delete_photo_from_all_services(photo_id)
                
                # Delete from database
                settings.photo_id = None
                settings.photo_data = None
                settings.photo_enabled = False
                settings.photo_height = None
                db.session.commit()
                
                return delete_results
            return {}


@event.listens_for(TicketFontConfig, 'before_update')
def _prevent_default_font_update(mapper, connection, target):
    if is_protected_font_config(target):
        raise ValueError('Default ticket font cannot be modified.')


@event.listens_for(TicketFontConfig, 'before_delete')
def _prevent_default_font_delete(mapper, connection, target):
    if is_protected_font_config(target):
        raise ValueError('Default ticket font cannot be deleted.')