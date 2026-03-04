# 코드 리뷰 (자동 점검)

## High
1. **`main.py`에서 한국 기사 0건일 때 런타임 에러 가능성**
   - `count` 변수가 한국 기사 루프 내부에서만 정의됩니다.
   - 한국 기사(`article_kor`)가 비어 있으면 `for i, article in enumerate(article_eng, count):` 에서 `UnboundLocalError`가 발생할 수 있습니다.
   - 권장: `count = 1`을 루프 전에 초기화하거나, 영어 기사 enumerate 시작값을 `len(article_kor) + 1`로 계산.

## Medium
2. **네트워크 요청 타임아웃/오류 처리 부족 (`main.py`, `sendMMS.py`)**
   - `requests.get`/`requests.post` 호출에 `timeout`과 `raise_for_status()`가 없습니다.
   - 외부 API 장애 시 스크립트가 무기한 대기하거나, 불완전한 JSON 응답을 정상 처리처럼 흘릴 수 있습니다.

3. **민감 정보가 로그로 출력될 위험 (`sendMMS.py`)**
   - `send_sms`에서 요청 payload 전체를 `print(data)`로 출력합니다.
   - API key/발신번호/수신번호 등 민감 데이터가 로그에 남을 수 있습니다.

4. **S3 업로드 Content-Type 고정 (`daily_upload_and_invalidate.py`)**
   - 모든 파일을 `text/html`로 업로드하고 있습니다.
   - CSS/JS/이미지 파일이 추가될 경우 브라우저 렌더링 문제를 유발할 수 있습니다.

## Low
5. **오타/가독성**
   - `newasapi` 변수명 오타 (`main.py`)는 기능에는 영향 없지만 유지보수성에 좋지 않습니다.

## Quick wins
- `main.py`의 `count` 초기화 버그 우선 수정.
- 모든 외부 HTTP 요청에 `timeout`, `raise_for_status()`, 예외 로깅 추가.
- 로그 마스킹(예: API key 뒤 4자리만 노출) 적용.
- 업로드 시 `mimetypes.guess_type`으로 `ContentType` 설정.
