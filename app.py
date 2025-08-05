import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

# Flask 애플리케이션 초기화
app = Flask(__name__)

# 데이터베이스 설정
# Heroku 환경에서는 DATABASE_URL 환경 변수를 사용하고,
# 로컬 환경에서는 SQLite 데이터베이스 파일을 사용합니다.
if 'DATABASE_URL' in os.environ:
    # Heroku PostgreSQL 연결을 위해 'postgresql://' 스키마를 'postgresql+psycopg2://'로 변경
    # Heroku의 DATABASE_URL은 'postgres://'로 시작할 수 있으므로, SQLAlchemy 1.4+ 호환을 위해 변경 필요
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL'].replace("://", "ql://", 1)
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # SQLAlchemy 이벤트 추적 비활성화 (권장)

# SQLAlchemy 객체 초기화
db = SQLAlchemy(app)

# ====================================================================
# 데이터베이스 모델 정의
# 'worker' 테이블에 해당하는 Worker 모델을 정의합니다.
# ====================================================================
class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_off = db.Column(db.Boolean, default=False)
    last_duty_date = db.Column(db.Date, nullable=True)
    duty_count = db.Column(db.Integer, default=0)
    order_index = db.Column(db.Integer, default=0) # 순서 유지를 위한 인덱스

    def __repr__(self):
        return f'<Worker {self.name}>'

# ====================================================================
# 데이터베이스 테이블 생성 및 초기 데이터 삽입
# 앱 컨텍스트 내에서 db.create_all()을 호출하여 테이블을 생성합니다.
# Heroku에 처음 배포할 때 테이블이 없으면 생성됩니다.
# 초기 데이터가 필요한 경우 여기에 추가할 수 있습니다.
# ====================================================================
with app.app_context():
    db.create_all()  # 초기 데이터 삽입 예시 (이 부분을 주석 해제하여 사용)
    if Worker.query.count() == 0: # Worker 테이블에 데이터가 없는 경우에만 삽입
        workers_data = [
            Worker(name='양성식', is_off=False, last_duty_date=date(2025, 7, 30), duty_count=5, order_index=1),
            Worker(name='조영은', is_off=False, last_duty_date=date(2025, 7, 29), duty_count=6, order_index=2),
            Worker(name='엄진석', is_off=False, last_duty_date=date(2025, 7, 28), duty_count=7, order_index=3),
            Worker(name='박성희', is_off=False, last_duty_date=date(2025, 7, 31), duty_count=4, order_index=4),
            Worker(name='이규환', is_off=False, last_duty_date=date(2025, 7, 31), duty_count=4, order_index=5),
            Worker(name='전소현', is_off=False, last_duty_date=date(2025, 7, 31), duty_count=4, order_index=6),
            Worker(name='박선영', is_off=False, last_duty_date=date(2025, 7, 31), duty_count=4, order_index=7),
            Worker(name='이하늘', is_off=False, last_duty_date=date(2025, 7, 31), duty_count=4, order_index=8),
            Worker(name='이광호', is_off=False, last_duty_date=date(2025, 7, 31), duty_count=4, order_index=9),
            Worker(name='김미란', is_off=False, last_duty_date=date(2025, 7, 31), duty_count=4, order_index=10),
        ]
        db.session.add_all(workers_data)
        db.session.commit()
  
# ====================================================================
# 핵심 로직 함수: 다음 근무자 선정 로직 (로그에서 오류가 발생했던 부분)
# ====================================================================
def get_next_duty_workers_logic():
    # 근무 가능한(is_off=False) 모든 작업자를 가져옵니다.
    # order_index 순서로 정렬합니다.
    available_workers = Worker.query.filter_by(is_off=False).order_by(Worker.order_index).all()

    if not available_workers:
        return [] # 근무 가능한 작업자가 없으면 빈 리스트 반환

    # 여기서는 가장 간단한 로직으로, order_index가 가장 낮은 작업자를 반환합니다.
    # 실제 앱의 "다음 근무자 선정 로직"에 따라 이 부분을 수정해야 합니다.
    # 예를 들어, last_duty_date, duty_count 등을 고려하여 복잡한 로직을 구현할 수 있습니다.
    
    # 예시: 가장 오래 쉬었거나, 근무 횟수가 가장 적은 사람을 선정하는 로직 (주석 처리됨)
    # available_workers.sort(key=lambda w: (w.last_duty_date if w.last_duty_date else date.min, w.duty_count))
    # next_worker = available_workers[0]
    # return [next_worker]

    # 현재는 단순히 order_index 순서대로 반환
    return available_workers


# ====================================================================
# 라우트 정의
# ====================================================================

@app.route('/')
def index():
    # get_next_duty_workers_logic 함수 호출
    next_workers = get_next_duty_workers_logic()
    # 'index.html' 템플릿을 렌더링하고, next_workers 데이터를 전달합니다.
    return render_template('index.html', next_workers=next_workers)

# 추가 라우트 (예시: 모든 작업자 목록 보기)
@app.route('/workers')
def list_workers():
    workers = Worker.query.order_by(Worker.order_index).all()
    # 'workers.html' 템플릿을 렌더링하고, workers 데이터를 전달합니다.
    return render_template('workers.html', workers=workers)

# ====================================================================
# 앱 실행
# ====================================================================
if __name__ == '__main__':
    app.run(debug=True) # 로컬 개발 시 디버그 모드 활성화
