# models.py
from extensions import db # extensions.py에서 db 객체를 임포트합니다.

class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    is_off = db.Column(db.Boolean, default=False)
    last_duty_date = db.Column(db.DateTime, nullable=True)
    duty_count = db.Column(db.Integer, default=0)
    order_index = db.Column(db.Integer, default=0, nullable=False) # 순서 저장을 위한 새로운 컬럼

    def __repr__(self):
        return f'<Worker {self.name}>'

def init_db_data():
    # 데이터베이스에 초기 데이터를 주입하는 함수
    if not Worker.query.first(): # 테이블에 데이터가 없는 경우만 추가
        initial_workers = ["김철수", "이영희", "박지민", "최현우", "정미나",
                           "윤성준", "오유리", "장승현", "조아라", "한동건"]
        for index, name in enumerate(initial_workers):
            db.session.add(Worker(name=name, order_index=index)) # 초기 데이터 주입 시 order_index도 설정
        db.session.commit()
        print("초기 근무자 데이터가 추가되었습니다.")