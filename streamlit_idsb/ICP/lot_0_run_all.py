import os
import subprocess
import time

def run_script(script_name, description):
    """
    스크립트를 실행하고 결과를 출력합니다.
    
    Args:
        script_name (str): 실행할 스크립트 파일명
        description (str): 스크립트 실행 설명
    """
    print(f"\n{'='*50}")
    print(f"실행: {description}")
    print(f"{'='*50}")
    
    start_time = time.time()
    
    # 현재 디렉토리 기준 스크립트 실행
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    result = subprocess.run(['python', script_path], capture_output=True, text=True)
    
    # 실행 결과 출력
    if result.returncode == 0:
        print(f"\n✅ {description} 성공!")
        print(result.stdout)
    else:
        print(f"\n❌ {description} 실패!")
        print(f"에러 메시지: {result.stderr}")
    
    end_time = time.time()
    print(f"소요 시간: {end_time - start_time:.2f}초")

def main():
    # 1. 데이터 생성
    run_script('lot_1_data_generator.py', '가상 데이터 생성')
    
    # 2. 데이터 시각화
    run_script('lot_2_visualization.py', '데이터 시각화')
    
    # 3. 데이터 분석
    run_script('lot_3_analysis.py', '데이터 분석')
    
    print("\n\n모든 작업이 완료되었습니다!")
    print(f"결과물은 다음 위치에서 확인할 수 있습니다:")
    print(f"- 데이터 파일: lot_normalized_data_*.csv")
    print(f"- 시각화 결과: lot_visualization/")
    print(f"- 분석 결과: lot_analysis/")

if __name__ == "__main__":
    main() 