// static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    const workerList = document.getElementById('worker-list');

    if (workerList) {
        new Sortable(workerList, {
            animation: 150, // 드래그 시 애니메이션 속도
            onEnd: function (evt) {
                // 드래그가 끝났을 때 실행되는 함수
                const newOrder = Array.from(workerList.children).map(item => item.dataset.id);
                console.log("새로운 순서:", newOrder);

                // 변경된 순서를 백엔드로 전송
                fetch('/update_worker_order', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ order: newOrder })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('순서 업데이트 성공!');
                        // 성공 시 UI 업데이트가 필요하면 여기에 추가 (예: 메시지 표시)
                    } else {
                        console.error('순서 업데이트 실패:', data.message);
                        alert('순서 업데이트에 실패했습니다.');
                    }
                })
                .catch(error => {
                    console.error('AJAX 오류:', error);
                    alert('서버와 통신 중 오류가 발생했습니다.');
                });
            }
        });
    }

    // OFF/OFF 해제 버튼 이벤트 리스너 추가 (아래 2번 항목과 관련)
    const toggleOffButtons = document.querySelectorAll('.toggle-off-btn');
    toggleOffButtons.forEach(button => {
        button.addEventListener('click', function() {
            const workerId = this.dataset.id;
            const currentIsOff = this.dataset.isOff === 'true'; // 문자열 'true'/'false'를 boolean으로 변환

            fetch(`/toggle_off_worker/${workerId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ is_off: !currentIsOff }) // 현재 상태의 반대를 보냄
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('OFF 상태 업데이트 성공!');
                    // UI 즉시 업데이트 (페이지 새로고침 없이)
                    const listItem = this.closest('.worker-item');
                    if (listItem) {
                        if (!currentIsOff) { // OFF 설정으로 변경된 경우
                            listItem.classList.add('off-duty');
                            this.textContent = 'OFF 해제';
                            this.dataset.isOff = 'true';
                        } else { // OFF 해제로 변경된 경우
                            listItem.classList.remove('off-duty');
                            this.textContent = 'OFF 설정';
                            this.dataset.isOff = 'false';
                        }
                    }
                } else {
                    console.error('OFF 상태 업데이트 실패:', data.message);
                    alert('OFF 상태 업데이트에 실패했습니다.');
                }
            })
            .catch(error => {
                console.error('AJAX 오류:', error);
                alert('서버와 통신 중 오류가 발생했습니다.');
            });
        });
    });
});