# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from datetime import datetime

# extensions.py에서 db 객체를 임포트합니다.
from extensions import db
# models.py에서 Worker 모델과 초기 데이터 주입 함수를 임포트합니다.
from models import Worker, init_db_data

# 현재 파일의 디렉토리 경로를 설정합니다.
basedir = os.path.abspath(os.path.dirname(__file__))

# Flask 애플리케이션을 생성합니다.
app = Flask(__name__)

# 애플리케이션 설정을 로드합니다.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # 불필요한 경고 메시지 비활성화

# db 객체를 Flask 애플리케이션에 연결합니다.
db.init_app(app)

# 애플리케이션 컨텍스트 내에서 데이터베이스 초기화 (테이블 생성 및 초기 데이터 주입)
with app.app_context():
    db.create_all() # 모든 모델에 대해 테이블 생성
    init_db_data()  # 초기 근무자 데이터 주입

# --- 다음 근무 순번 관리 로직 ---
# 실제 서비스에서는 DB에 저장하여 서버가 재시작되어도 유지되도록 해야 합니다.
# 여기서는 예시를 위해 메모리 변수를 사용합니다.
# 주의: 이 current_duty_start_index는 앱이 재시작되면 초기화됩니다.
# 실제 배포 시에는 DB에 저장하거나, last_duty_date 등을 활용하여 순번을 계산해야 합니다.
current_duty_start_index = 0

def get_next_duty_workers_logic():
    global current_duty_start_index

    # 활성화된 (OFF가 아닌) 근무자들을 order_index 순으로 정렬하여 가져옵니다.
    # order_index는 드래그 앤 드롭으로 변경된 순서를 반영합니다.
    available_workers = Worker.query.filter_by(is_off=False).order_by(Worker.order_index).all()

    if not available_workers:
        return [] # 근무 가능한 사람이 없으면 빈 리스트 반환

    num_available = len(available_workers)
    next_two_workers_names = []

    # 현재 시작 인덱스부터 순환하며 다음 근무자 2명을 찾습니다.
    # 한 명만 근무할 경우도 드물게 있으므로 최대 2명으로 가정
    for i in range(2):
        if num_available == 0: # 혹시 모든 인원이 OFF 상태가 될 경우 대비
            break
        
        # 순환적으로 인덱스 계산
        worker_idx = (current_duty_start_index + i) % num_available
        next_two_workers_names.append(available_workers[worker_idx].name)

    return next_two_workers_names

def advance_duty_order_logic():
    global current_duty_start_index
    
    available_workers = Worker.query.filter_by(is_off=False).order_by(Worker.order_index).all()
    num_available = len(available_workers)

    if num_available > 0:
        # 현재 근무한 사람들의 last_duty_date 및 duty_count 업데이트 (선택 사항)
        with app.app_context(): # DB 트랜잭션을 위해 app_context 필요
            for i in range(2): # 최대 2명에 대해 업데이트
                if num_available > 0 and (current_duty_start_index + i) < num_available:
                    worker_to_update_idx = (current_duty_start_index + i) % num_available
                    worker_to_update = available_workers[worker_to_update_idx]
                    worker_to_update.last_duty_date = datetime.now()
                    worker_to_update.duty_count += 1
            db.session.commit()

        # 다음 순번으로 시작 인덱스를 이동시킵니다.
        # 여기서는 2명씩 근무한다고 가정하고 2칸 이동
        current_duty_start_index = (current_duty_start_index + 2) % num_available
        print(f"근무 순번이 다음으로 넘어갔습니다. 새 시작 인덱스: {current_duty_start_index}")
    else:
        print("근무 가능한 인원이 없어 순번을 넘길 수 없습니다.")


# --- 라우트 정의 ---

@app.route('/')
def index():
    # 다음 근무자 정보를 가져옵니다.
    next_workers = get_next_duty_workers_logic()
    return render_template('index.html', next_workers=next_workers)

@app.route('/workers', methods=['GET', 'POST'])
def workers():
    if request.method == 'POST':
        worker_name = request.form['name']
        if worker_name:
            # 새로운 근무자를 추가할 때 order_index를 마지막 순서로 부여
            max_order_index = db.session.query(db.func.max(Worker.order_index)).scalar()
            new_order_index = (max_order_index if max_order_index is not None else -1) + 1
            
            new_worker = Worker(name=worker_name, order_index=new_order_index)
            db.session.add(new_worker)
            db.session.commit()
        return redirect(url_for('workers'))
    
    # 모든 근무자를 order_index 순으로 정렬하여 가져옵니다.
    all_workers = Worker.query.order_by(Worker.order_index).all()
    return render_template('workers.html', workers=all_workers)

@app.route('/delete_worker/<int:id>')
def delete_worker(id):
    worker_to_delete = Worker.query.get_or_404(id)
    db.session.delete(worker_to_delete)
    db.session.commit()
    return redirect(url_for('workers'))

@app.route('/update_worker_order', methods=['POST'])
def update_worker_order():
    data = request.get_json()
    new_order_ids = data.get('order') # ['1', '3', '2', ...] 와 같은 형식의 ID 리스트 (문자열)

    if not new_order_ids:
        return jsonify({'success': False, 'message': '순서 데이터가 없습니다.'}), 400

    try:
        # 트랜잭션 시작: 모든 업데이트가 성공하거나, 하나라도 실패하면 모두 롤백
        with db.session.begin_nested(): # nested transaction for safety
            for index, worker_id_str in enumerate(new_order_ids):
                worker_id = int(worker_id_str) # 문자열 ID를 정수로 변환
                worker = Worker.query.get(worker_id)
                if worker:
                    worker.order_index = index # 새로운 순서 인덱스 업데이트
                else:
                    raise ValueError(f"ID {worker_id}를 가진 근무자를 찾을 수 없습니다.")
            db.session.commit() # 트랜잭션 커밋
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback() # 오류 발생 시 롤백
        print(f"순서 업데이트 중 오류 발생: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/toggle_off_worker/<int:worker_id>', methods=['POST'])
def toggle_off_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    data = request.get_json()
    
    if 'is_off' not in data or not isinstance(data['is_off'], bool):
        return jsonify({'success': False, 'message': '잘못된 is_off 값입니다.'}), 400

    worker.is_off = data['is_off']
    try:
        db.session.commit()
        return jsonify({'success': True, 'is_off': worker.is_off})
    except Exception as e:
        db.session.rollback()
        print(f"OFF 상태 토글 중 오류 발생: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/next_duty', methods=['POST'])
def next_duty():
    advance_duty_order_logic()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) # 개발 중에는 debug=True로 설정하여 코드 변경 시 자동 재시작