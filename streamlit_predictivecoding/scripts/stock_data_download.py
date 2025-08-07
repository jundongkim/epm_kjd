# 1) FinanceDataReader 설치
#    pip install finance-datareader

import FinanceDataReader as fdr
import pandas as pd

def download_index_data(ticker: str,
                        start_date: str = None,
                        end_date: str = None,
                        output_filename: str = None):
    """
    FinanceDataReader로 인덱스 데이터를 가져와 CSV로 저장합니다.
    
    Parameters:
    - ticker: 인덱스 코드 ('KS11'=KOSPI, 'KQ11'=KOSDAQ 등)
    - start_date: 조회 시작일 (YYYY-MM-DD), None 이면 가능한 가장 오래된 데이터
    - end_date: 조회 종료일 (YYYY-MM-DD), None 이면 오늘까지
    - output_filename: 저장할 파일명. None 이면 자동 생성
    """
    # 데이터 로드
    df = fdr.DataReader(ticker, start_date, end_date)
    
    if df.empty:
        print(f"[오류] '{ticker}'에 대한 데이터를 찾을 수 없습니다.")
        return
    
    # 파일명 자동 생성
    if not output_filename:
        sd = start_date or "start"
        ed = end_date   or "end"
        output_filename = f"{ticker}_{sd}_{ed}.csv"
    
    # CSV로 저장
    df.to_csv(output_filename, encoding="utf-8-sig")
    print(f"✔️ '{output_filename}'에 데이터가 저장되었습니다.")

if __name__ == "__main__":
    print("한국 주식 인덱스 데이터 다운로드 (FinanceDataReader 사용)")
    print("예시 인덱스 코드: KS11 (KOSPI), KQ11 (KOSDAQ)\n")
    
    ticker   = input("▶ 인덱스 코드 입력: ").strip().upper()
    start    = input("▶ 시작일 (YYYY-MM-DD, 생략 가능): ").strip() or None
    end      = input("▶ 종료일 (YYYY-MM-DD, 생략 가능): ").strip() or None
    filename = input("▶ 저장할 파일명 (생략 시 자동 생성): ").strip() or None
    
    download_index_data(ticker, start, end, filename)
