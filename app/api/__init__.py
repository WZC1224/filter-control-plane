from app.api.auth import bp as auth_bp
from app.api.auth import users_bp
from app.api.tasks import bp as tasks_bp
from app.api.meta import bp as meta_bp
from app.api.orders import bp as orders_bp
from app.api.bills import bp as bills_bp
from app.api.notices import bp as notices_bp

bp_list = [auth_bp, users_bp, tasks_bp, meta_bp, orders_bp, bills_bp, notices_bp]
