# init_db.py

from app import create_app, db
from models import init_db_data

# Flask 앱을 생성합니다.
app = create_app()

# 앱 컨텍스트 내에서 데이터베이스 초기화 작업을 수행합니다.
with app.app_context():
    print("데이터베이스 테이블을 생성합니다...")
    db.create_all()  # 모든 모델에 대해 테이블 생성
    print("초기 근무자 데이터를 주입합니다...")
    init_db_data()   # 초기 근무자 데이터 주입
    print("데이터베이스 초기화가 완료되었습니다.")
