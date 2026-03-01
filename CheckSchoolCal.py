import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime
import os
import io

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="학사일정 점검 시스템",
    page_icon="📋",
    layout="wide"
)

st.title("📋 2026학년도 고등학교 학사일정 점검 시스템")
st.markdown("---")

# ============================================================
# 2026학년도 공휴일 (학사일정 범위: 2026.3.1 ~ 2027.2.28)
# 토/일은 평일 계산 시 자동 제외되므로, 평일에 해당하는 공휴일만 정의
# ============================================================
HOLIDAYS_2026 = {
    # 3월
    date(2026, 3, 2),   # 삼일절 대체공휴일 (월)
    # 5월
    date(2026, 5, 5),   # 어린이날 (화)
    date(2026, 5, 25),  # 부처님오신날 대체공휴일 (월)
    # 6월
    date(2026, 6, 3),   # 지방선거일 (수)
    # 8월
    date(2026, 8, 17),  # 광복절 대체공휴일 (월)
    # 9월
    date(2026, 9, 24),  # 추석 연휴 (목)
    date(2026, 9, 25),  # 추석 (금)
    # 10월
    date(2026, 10, 5),  # 개천절 대체공휴일 (월)
    date(2026, 10, 9),  # 한글날 (금)
    # 12월
    date(2026, 12, 25), # 기독탄신일 (금)
    # 2027년
    date(2027, 1, 1),   # 신정 (금)
    date(2027, 2, 8),   # 설날 연휴 (월)
    date(2027, 2, 9),   # 설날 대체공휴일 (화)
}

# ============================================================
# 유틸리티 함수
# ============================================================
def count_weekdays(start_date, end_date):
    """start_date ~ end_date(양쪽 포함) 평일 수"""
    if not start_date or not end_date or start_date > end_date:
        return 0
    count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count

def count_holidays_in_range(start_date, end_date, holidays):
    """범위 내 평일 공휴일 수"""
    return sum(1 for h in holidays if start_date <= h <= end_date and h.weekday() < 5)

def to_date(val):
    """다양한 타입 → date 변환"""
    if val is None:
        return None
    # NaN/NaT 체크
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    # datetime.datetime
    if isinstance(val, datetime):
        return val.date()
    # pd.Timestamp
    if isinstance(val, pd.Timestamp):
        return val.date()
    # date
    if isinstance(val, date):
        return val
    # 문자열
    if isinstance(val, str):
        val = val.strip()
        if val == '' or val.lower() == 'nat':
            return None
        try:
            return pd.to_datetime(val).date()
        except:
            return None
    return None

def to_int(val):
    """숫자 변환 (NaN → 0)"""
    if val is None:
        return 0
    try:
        if pd.isna(val):
            return 0
    except (TypeError, ValueError):
        pass
    try:
        return int(float(val))
    except:
        return 0

# ============================================================
# 핵심 점검 함수
# ============================================================
def check_school(file_name, df, holidays=HOLIDAYS_2026):
    """학교 1개 파일 점검 → (errors, details) 반환"""

    school_name = os.path.basename(file_name).split('_')[0]
    errors = []
    details = []

    # 데이터 행 탐색: col[12]가 '1~2' 또는 '3', col[0]이 '예시'가 아닌 행
    rows_12, rows_3 = [], []
    for idx in range(df.shape[0]):
        row = df.iloc[idx]
        grade = str(row.iloc[12]).strip() if pd.notna(row.iloc[12]) else ''
        serial = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
        if serial == '예시':
            continue
        if grade == '1~2':
            rows_12.append(row)
        elif grade == '3':
            rows_3.append(row)

    if not rows_12 or not rows_3:
        errors.append(f"[{school_name}] 데이터 행(1~2학년/3학년)을 찾을 수 없습니다.")
        return errors, details

    for r12, r3 in zip(rows_12, rows_3):
        sname = str(r12.iloc[6]) if pd.notna(r12.iloc[6]) else school_name

        # --- 날짜 추출 ---
        open_12       = to_date(r12.iloc[16])
        open_3        = to_date(r3.iloc[16])
        s_close_12    = to_date(r12.iloc[17])  # 여름방학식
        s_open_12     = to_date(r12.iloc[18])  # 여름개학식
        w_close_12    = to_date(r12.iloc[19])  # 겨울방학식
        w_open_12     = to_date(r12.iloc[20])  # 겨울개학식
        end_12        = to_date(r12.iloc[21])  # 종업식

        s_close_3     = to_date(r3.iloc[17])
        s_open_3      = to_date(r3.iloc[18])
        w_close_3     = to_date(r3.iloc[19])
        w_open_3      = to_date(r3.iloc[20])
        grad_3        = to_date(r3.iloc[22])   # 졸업식 (col22)
        if grad_3 is None:
            grad_3    = to_date(r3.iloc[21])

        # 수업일수 & 재량휴업일
        sem1_12, sem2_12 = to_int(r12.iloc[13]), to_int(r12.iloc[14])
        sem1_3,  sem2_3  = to_int(r3.iloc[13]),  to_int(r3.iloc[14])
        disc1_12, disc2_12 = to_int(r12.iloc[51]), to_int(r12.iloc[52])
        disc1_3,  disc2_3  = to_int(r3.iloc[51]),  to_int(r3.iloc[52])

        details.append(f"\n### 🏫 {sname}")

        # ===== 점검 1: 개학일 비교 =====
        details.append("\n**[점검1] 개학일 비교**")
        if open_12 and open_3:
            if open_12 == open_3:
                details.append(f"- ✅ 개학일 동일 ({open_12})")
            else:
                msg = f"❌ 개학일 불일치: 1~2학년({open_12}) vs 3학년({open_3})"
                details.append(f"- {msg}")
                errors.append(f"[{sname}] {msg}")
        else:
            msg = f"⚠️ 개학일 데이터 누락 (1~2학년={open_12}, 3학년={open_3})"
            details.append(f"- {msg}")
            errors.append(f"[{sname}] {msg}")

        # ===== 점검 2: 1학기 수업일수 =====
        for label, od, sc, s1d, d1 in [
            ("1~2학년", open_12, s_close_12, sem1_12, disc1_12),
            ("3학년",   open_3,  s_close_3,  sem1_3,  disc1_3),
        ]:
            details.append(f"\n**[점검2] {label} 1학기 수업일수**")
            if od and sc:
                wd = count_weekdays(od, sc)
                hol = count_holidays_in_range(od, sc, holidays)
                calc = wd - hol - d1
                details.append(f"- 개학일({od}) → 여름방학식({sc})")
                details.append(f"- 평일 {wd}일 − 공휴일 {hol}일 − 재량휴업 {d1}일 = **{calc}일**")
                details.append(f"- 기재 수업일수: **{s1d}일**")
                if calc == s1d:
                    details.append(f"- ✅ 일치")
                else:
                    msg = f"❌ {label} 1학기 불일치: 계산 {calc}일 vs 기재 {s1d}일 (차이 {calc - s1d:+d}일)"
                    details.append(f"- {msg}")
                    errors.append(f"[{sname}] {msg}")
            else:
                msg = f"⚠️ {label} 1학기 날짜 누락"
                details.append(f"- {msg}")
                errors.append(f"[{sname}] {msg}")

        # ===== 점검 3: 2학기 수업일수 =====
        for label, so, wc, wo, ed, s2d, d2 in [
            ("1~2학년", s_open_12, w_close_12, w_open_12, end_12,  sem2_12, disc2_12),
            ("3학년",   s_open_3,  w_close_3,  w_open_3,  grad_3, sem2_3,  disc2_3),
        ]:
            details.append(f"\n**[점검3] {label} 2학기 수업일수**")
            if so and wc:
                wd_main = count_weekdays(so, wc)
                hol_main = count_holidays_in_range(so, wc, holidays)
                calc = wd_main - hol_main - d2
                details.append(f"- 여름개학식({so}) → 겨울방학식({wc})")
                details.append(f"- 기본구간: 평일 {wd_main}일 − 공휴일 {hol_main}일 − 재량휴업 {d2}일 = {calc}일")

                if wo is not None and ed is not None:
                    wd_ex = count_weekdays(wo, ed)
                    hol_ex = count_holidays_in_range(wo, ed, holidays)
                    extra = wd_ex - hol_ex
                    calc += extra
                    end_label = '종업식' if label == '1~2학년' else '졸업식'
                    details.append(f"- 겨울개학식({wo}) → {end_label}({ed}): +{extra}일")
                    details.append(f"- 총 계산: **{calc}일**")
                else:
                    details.append(f"- 겨울개학식: 공란 → 추가 계산 없음")
                    details.append(f"- 총 계산: **{calc}일**")

                details.append(f"- 기재 수업일수: **{s2d}일**")
                if calc == s2d:
                    details.append(f"- ✅ 일치")
                else:
                    msg = f"❌ {label} 2학기 불일치: 계산 {calc}일 vs 기재 {s2d}일 (차이 {calc - s2d:+d}일)"
                    details.append(f"- {msg}")
                    errors.append(f"[{sname}] {msg}")
            else:
                msg = f"⚠️ {label} 2학기 날짜 누락"
                details.append(f"- {msg}")
                errors.append(f"[{sname}] {msg}")

    return errors, details

# ============================================================
# Streamlit UI
# ============================================================

# 사이드바 - 공휴일 표시
with st.sidebar:
    st.header("📅 적용 공휴일 목록")
    st.caption("2026학년도 (2026.3 ~ 2027.2)")
    holiday_names = {
        date(2026, 3, 2):  "삼일절 대체공휴일",
        date(2026, 5, 5):  "어린이날",
        date(2026, 5, 25): "부처님오신날 대체공휴일",
        date(2026, 6, 3):  "지방선거일",
        date(2026, 8, 17): "광복절 대체공휴일",
        date(2026, 9, 24): "추석 연휴",
        date(2026, 9, 25): "추석",
        date(2026, 10, 5): "개천절 대체공휴일",
        date(2026, 10, 9): "한글날",
        date(2026, 12, 25):"기독탄신일",
        date(2027, 1, 1):  "신정",
        date(2027, 2, 8):  "설날 연휴",
        date(2027, 2, 9):  "설날 대체공휴일",
    }
    for d in sorted(HOLIDAYS_2026):
        dow = ["월","화","수","목","금","토","일"][d.weekday()]
        st.write(f"- {d.strftime('%Y-%m-%d')} ({dow}) {holiday_names.get(d, '')}")

    st.markdown("---")
    st.header("📖 점검 기준")
    st.markdown("""
    **1. 개학일 비교**
    - 1~2학년과 3학년의 개학일 동일 여부

    **2. 1학기 수업일수**
    - (여름방학식 − 개학일 평일) − 공휴일 − 재량휴업일

    **3. 2학기 수업일수**
    - (겨울방학식 − 여름개학식 평일) − 공휴일 − 재량휴업일
    - 겨울개학식 있으면: + (종업/졸업식 − 겨울개학식)
    """)

# 파일 업로드
st.header("📂 파일 업로드")
st.info("💡 여러 학교의 엑셀 파일을 동시에 업로드할 수 있습니다. (파일명: **학교명_2026학년도 고등학교 학사일정 현황.xlsx**)")

uploaded_files = st.file_uploader(
    "학사일정 엑셀 파일을 선택하세요",
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

if uploaded_files:
    st.markdown("---")
    st.header("🔍 점검 결과")

    total_errors = 0
    all_results = {}

    for uf in uploaded_files:
        try:
            df = pd.read_excel(uf, sheet_name=0, header=None)
            errs, details = check_school(uf.name, df)
            all_results[uf.name] = {"errors": errs, "details": details}
            total_errors += len(errs)
        except Exception as e:
            all_results[uf.name] = {
                "errors": [f"파일 처리 오류: {str(e)}"],
                "details": [f"\n❌ 파일을 읽는 중 오류가 발생했습니다: {str(e)}"]
            }
            total_errors += 1

    # --- 요약 ---
    st.subheader("📊 전체 요약")

    col1, col2, col3 = st.columns(3)
    col1.metric("점검 학교 수", f"{len(all_results)}개")
    col2.metric("총 오류 건수", f"{total_errors}건",
                delta=None if total_errors == 0 else f"{total_errors}건 발견",
                delta_color="off" if total_errors == 0 else "inverse")
    col3.metric("정상 학교 수",
                f"{sum(1 for v in all_results.values() if not v['errors'])}개")

    # 오류 요약 테이블
    if total_errors > 0:
        st.subheader("🔴 오류 요약")
        err_data = []
        for fname, res in all_results.items():
            school = fname.split('_')[0]
            for e in res["errors"]:
                err_data.append({"학교": school, "오류 내용": e})
        if err_data:
            st.dataframe(pd.DataFrame(err_data), use_container_width=True, hide_index=True)
    else:
        st.success("🎉 모든 학교가 점검을 통과했습니다!")

    # --- 학교별 상세 ---
    st.markdown("---")
    st.subheader("📝 학교별 상세 결과")

    for fname, res in all_results.items():
        school = fname.split('_')[0]
        icon = "🟢" if not res["errors"] else "🔴"
        with st.expander(f"{icon} {school} ({len(res['errors'])}건 오류)", expanded=bool(res["errors"])):
            for line in res["details"]:
                st.markdown(line)

else:
    st.markdown("\n")
    st.warning("👆 위에서 학사일정 엑셀 파일을 업로드해 주세요.")

    # 사용법 안내
    with st.expander("📖 사용 방법 안내", expanded=True):
        st.markdown("""
        ### 파일 형식
        - **파일명**: `학교명_2026학년도 고등학교 학사일정 현황.xlsx`
        - **시트 구조**: 교육청 배포 양식 그대로 사용
        - 1~2학년과 3학년이 각각 한 행씩 구성

        ### 점검 항목
        | 번호 | 점검 내용 | 설명 |
        |:---:|:---|:---|
        | 1 | 개학일 비교 | 1~2학년과 3학년의 개학일 동일 여부 |
        | 2 | 1학기 수업일수 | 개학일~여름방학식 평일 - 공휴일 - 재량휴업일 |
        | 3 | 2학기 수업일수 | 여름개학식~겨울방학식 평일 - 공휴일 - 재량휴업일 + (겨울개학식~종업/졸업식) |
        """)
