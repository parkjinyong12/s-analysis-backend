# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_executor import Executor
 
db = SQLAlchemy()
cors = CORS()
executor = Executor() 