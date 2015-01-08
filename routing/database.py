import os
from sqlalchemy import create_engine

from routing.app_config import DB_CONN

engine = create_engine(DB_CONN, 
                       convert_unicode=True, 
                       server_side_cursors=True)

