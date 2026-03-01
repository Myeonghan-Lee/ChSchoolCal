# 📋 2026학년도 고등학교 학사일정 점검 시스템

고등학교 학사일정 엑셀 파일을 업로드하면 자동으로 오류를 점검합니다.

## 점검 항목
1. **개학일 비교** - 1~2학년과 3학년의 개학일 동일 여부
2. **1학기 수업일수** - (여름방학식 - 개학일 평일) - 공휴일 - 재량휴업일
3. **2학기 수업일수** - (겨울방학식 - 여름개학식 평일) - 공휴일 - 재량휴업일 + 겨울방학 후 추가구간

## 실행 방법

### 로컬 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Streamlit Cloud 배포
1. 이 저장소를 GitHub에 push
2. [share.streamlit.io](https://share.streamlit.io) 에서 배포

## 파일 구조
```
├── app.py                # Streamlit 앱
├── requirements.txt      # 의존성
└── README.md
```
