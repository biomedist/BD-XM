document.addEventListener('DOMContentLoaded', function() {
    // ================================================================
    // 근무자 OFF/ON 토글 기능
    // ================================================================
    document.querySelectorAll('.toggle-off-btn').forEach(button => {
        button.addEventListener('click', function() {
            const workerId = this.dataset.id;
            const isOff = JSON.parse(this.dataset.isOff); // HTML에서 문자열로 넘어오므로 JSON.parse
            const newIsOff = !isOff; // 현재 상태의 반대로 토글

            fetch(`/toggle_off/${workerId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                // body: JSON.stringify({ is_off: newIsOff }) // 현재는 URL로 ID만 전달하므로 body는 필요 없음
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const listItem = this.closest('.worker-item');
                    if (data.is_off) {
                        listItem.classList.add('off-duty');
                        this.textContent = 'OFF 해제';
                    } else {
                        listItem.classList.remove('off-duty');
                        this.textContent = 'OFF 설정';
                    }
                    // data-is-off 속성 업데이트
                    this.dataset.isOff = data.is_off;

                    console.log(`Worker ${workerId} status toggled to ${data.is_off}.`);
                } else {
                    alert('상태 변경 실패: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('상태 변경 중 오류가 발생했습니다.');
            });
        });
    });

    // ================================================================
    // 근무자 순서 변경 (드래그 앤 드롭) 기능 - SortableJS 사용
    // ================================================================
    const workerList = document.getElementById('worker-list');
    if (workerList) {
        new Sortable(workerList, {
            animation: 150, // 애니메이션 속도 (ms)
            onEnd: function (evt) {
                // 드래그 앤 드롭이 끝났을 때 호출됩니다.
                const newOrder = [];
                // 모든 li 요소의 data-id 속성(worker.id)을 가져와 새로운 순서를 만듭니다.
                Array.from(workerList.children).forEach(item => {
                    newOrder.push(parseInt(item.dataset.id));
                });

                console.log('New order:', newOrder);

                // 서버에 새로운 순서를 전송합니다.
                fetch('/update_order', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ order: newOrder }),
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('Worker order updated successfully.');
                    } else {
                        alert('순서 업데이트 실패: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error updating order:', error);
                    alert('순서 업데이트 중 오류가 발생했습니다.');
                });
            },
        });
    }
});
