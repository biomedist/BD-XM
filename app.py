import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
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
    last_duty_date = db.Column(db.Date, nullable=True) # 마지막 근무일
    duty_count = db.Column(db.Integer, default=0) # 총 근무 횟수
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
    db.create_all()
    # 초기 데이터 삽입 예시: Worker 테이블에 데이터가 없는 경우에만 삽입
    if Worker.query.count() == 0:
        print("Inserting initial worker data...")
        workers_data = [
            Worker(name='양성식', is_off=False, last_duty_date=None, duty_count=0, order_index=1),
            Worker(name='조영은', is_off=False, last_duty_date=None, duty_count=0, order_index=2),
            Worker(name='엄진석', is_off=False, last_duty_date=None, duty_count=0, order_index=3),
            Worker(name='박성희', is_off=False, last_duty_date=None, duty_count=0, order_index=4),
            Worker(name='김철수', is_off=False, last_duty_date=None, duty_count=0, order_index=5),
            Worker(name='이영희', is_off=False, last_duty_date=None, duty_count=0, order_index=6),
            Worker(name='박민수', is_off=False, last_duty_date=None, duty_count=0, order_index=7),
            Worker(name='최유리', is_off=False, last_duty_date=None, duty_count=0, order_index=8),
            Worker(name='정대웅', is_off=False, last_duty_date=None, duty_count=0, order_index=9),
            Worker(name='하정민', is_off=False, last_duty_date=None, duty_count=0, order_index=10),
        ]
        db.session.add_all(workers_data)
        db.session.commit()
        print("Initial worker data inserted successfully.")
    else:
        print("Workers already exist, skipping initial data insertion.")

# ====================================================================
# 핵심 로직 함수: 다음 근무자 선정 로직
# - 근무 가능한(is_off=False) 작업자 중 순번(order_index)이 가장 낮은 2명을 선정합니다.
# - 1명만 필요한 경우에도 유연하게 처리합니다.
# ====================================================================
def get_next_duty_workers_logic():
    # 근무 가능한(is_off=False) 모든 작업자를 order_index 순서로 가져옵니다.
    available_workers = Worker.query.filter_by(is_off=False).order_by(Worker.order_index).all()

    if not available_workers:
        return []

    # order_index가 가장 낮은 상위 2명만 반환합니다.
    # available_workers 리스트에 2명 미만이면 있는 만큼만 반환됩니다.
    return available_workers[:2]

# ====================================================================
# 라우트 정의
# ====================================================================

@app.route('/')
def index():
    next_workers = get_next_duty_workers_logic()
    return render_template('index.html', next_workers=next_workers)

@app.route('/workers', methods=['GET', 'POST'])
def workers():
    if request.method == 'POST':
        worker_name = request.form.get('name')
        if worker_name:
            # 새로운 근무자 추가 시 가장 높은 order_index 다음으로 설정
            max_order_index = db.session.query(db.func.max(Worker.order_index)).scalar()
            new_order_index = (max_order_index if max_order_index is not None else 0) + 1
            
            new_worker = Worker(name=worker_name, order_index=new_order_index)
            db.session.add(new_worker)
            db.session.commit()
        return redirect(url_for('workers'))
    
    # GET 요청 시 모든 근무자 목록을 order_index 순서로 가져옵니다.
    all_workers = Worker.query.order_by(Worker.order_index).all()
    return render_template('workers.html', workers=all_workers)

@app.route('/toggle_off/<int:worker_id>', methods=['POST'])
def toggle_off_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    worker.is_off = not worker.is_off
    
    # OFF 설정 시 last_duty_date를 업데이트하지 않습니다.
    # last_duty_date는 실제로 근무를 수행했을 때만 업데이트됩니다.
    db.session.commit()
    return jsonify(success=True, is_off=worker.is_off)

@app.route('/delete_worker/<int:worker_id>')
def delete_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    db.session.delete(worker)
    db.session.commit()
    return redirect(url_for('workers'))

@app.route('/update_order', methods=['POST'])
def update_order():
    # 클라이언트에서 전송된 새로운 순서의 worker ID 목록을 받습니다.
    # 예: {'order': [1, 3, 2, 4]}
    new_order_ids = request.json.get('order', [])
    
    if not new_order_ids:
        return jsonify(success=False, message="No order data provided"), 400

    # 각 worker의 order_index를 새로운 순서에 맞게 업데이트합니다.
    for index, worker_id in enumerate(new_order_ids):
        worker = Worker.query.get(worker_id)
        if worker:
            worker.order_index = index + 1 # 1부터 시작하는 인덱스로 설정
            db.session.add(worker) # 변경사항을 세션에 추가
    
    db.session.commit() # 모든 변경사항을 한 번에 커밋
    return jsonify(success=True)

@app.route('/record_duty', methods=['POST'])
def record_duty():
    # index.html에서 전송된 '다음 근무자'들의 ID를 받습니다.
    worker_ids = request.json.get('worker_ids', [])

    if not worker_ids:
        return jsonify(success=False, message="근무 기록할 근무자 ID가 제공되지 않았습니다."), 400

    # 근무를 수행한 근무자들의 정보 업데이트
    workers_on_duty = []
    for worker_id in worker_ids:
        worker = Worker.query.get(worker_id)
        if worker:
            workers_on_duty.append(worker)
            worker.last_duty_date = date.today() # 마지막 근무일 오늘 날짜로 업데이트
            worker.duty_count += 1 # 근무 횟수 증가
            db.session.add(worker) # 변경사항 스테이징

    # 모든 근무자들을 현재 order_index 순서로 가져옵니다.
    all_workers = Worker.query.order_by(Worker.order_index).all()

    # 새로운 순서 리스트를 만듭니다.
    # 근무를 수행한 근무자들은 리스트의 가장 뒤로 보냅니다.
    # 나머지 근무자들은 기존의 상대적인 순서를 유지합니다.
    remaining_workers = [w for w in all_workers if w.id not in worker_ids]
    new_ordered_list = remaining_workers + workers_on_duty

    # 새로운 순서에 따라 모든 근무자의 order_index를 재할당합니다.
    for index, worker in enumerate(new_ordered_list):
        worker.order_index = index + 1 # 1부터 시작하는 인덱스
        db.session.add(worker) # 변경사항 스테이징

    db.session.commit() # 모든 변경사항을 한 번에 커밋

    return jsonify(success=True, message="근무가 기록되었고 순번이 업데이트되었습니다.")

# ====================================================================
# 앱 실행
# ====================================================================
if __name__ == '__main__':
    app.run(debug=True) # 로컬 개발 시 디버그 모드 활성화
