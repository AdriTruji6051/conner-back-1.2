from app.extensions import db
from app.models.core_classes import User, TicketText, TicketFontConfig
from app.helpers.helpers import raise_exception_if_missing_keys, ValidationError, collect_missing_keys
from sqlalchemy import event

create_user_keys = ['user', 'user_name', 'password', 'role_type']
update_user_keys = ['user', 'user_name', 'password', 'role_type', 'id']
create_text_keys = ['text', 'line', 'is_header', 'font_config']
create_font_config_keys = ['font', 'weigh', 'size']

DEFAULT_FONT_NAME = 'Console'
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
        def get_all() -> list[User]:
            return User.query.all()

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


@event.listens_for(TicketFontConfig, 'before_update')
def _prevent_default_font_update(mapper, connection, target):
    if is_protected_font_config(target):
        raise ValueError('Default ticket font cannot be modified.')


@event.listens_for(TicketFontConfig, 'before_delete')
def _prevent_default_font_delete(mapper, connection, target):
    if is_protected_font_config(target):
        raise ValueError('Default ticket font cannot be deleted.')