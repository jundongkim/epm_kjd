import pandas as pd
import os
import glob

def transform_bar_files(input_folder='data/iot'):
    """
    BAR00018.csv 형식의 파일들을 변환하여 BAR00018TR.csv 형식으로 생성
    칼럼 구성: No, Point, CH-A1, CH-A2, CH-A3, CH-A4, CH-A5, CH-B1, CH-B2, CH-B3, CH-B4, CH-B5
    
    패턴:
    1행: (1, CH-A1)
    2행: (2, CH-A1), (1, CH-A2)
    3행: (3, CH-A1), (2, CH-A2), (1, CH-A3)
    4행: (4, CH-A1), (3, CH-A2), (2, CH-A3), (1, CH-A4)
    ...
    마지막 데이터 이후에도 모든 채널이 참조될 때까지 연장
    """
    
    # iot 폴더에서 BAR로 시작하는 CSV 파일들 찾기 (대소문자 모두)
    pattern1 = os.path.join(input_folder, 'BAR*.csv')
    pattern2 = os.path.join(input_folder, 'BAR*.CSV')
    csv_files = glob.glob(pattern1) + glob.glob(pattern2)
    
    # TR.CSV 파일들은 제외
    csv_files = [f for f in csv_files if not f.upper().endswith('TR.CSV')]
    
    if not csv_files:
        print(f"No BAR*.csv or BAR*.CSV files found in {input_folder} folder")
        return
    
    print(f"Found {len(csv_files)} BAR files to transform:")
    for file in csv_files:
        print(f"  - {file}")
    
    for csv_file in csv_files:
        print(f"\nProcessing {csv_file}...")
        
        try:
            # CSV 파일 읽기 (첫 6줄은 메타데이터)
            with open(csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 메타데이터 추출
            date_str = lines[0].split(',')[1].strip()  # 2018.02.21 12:51
            lot_no = lines[1].split(',')[1].strip()    # L820169
            bar_no = lines[2].split(',')[1].strip()    # 18
            
            print(f"  Date: {date_str}")
            print(f"  Lot No: {lot_no}")
            print(f"  Bar No: {bar_no}")
            
            # 헤더와 데이터 읽기 (7번째 줄부터)
            df = pd.read_csv(csv_file, skiprows=6)
            original_rows = len(df)
            
            print(f"  Original columns: {list(df.columns)}")
            print(f"  Original data rows: {original_rows}")
            
            # 필요한 채널 컬럼들 정의 (순서대로)
            required_channels = ['CH-A1', 'CH-A2', 'CH-A3', 'CH-A4', 'CH-A5', 
                               'CH-B1', 'CH-B2', 'CH-B3', 'CH-B4', 'CH-B5']
            
            # 전체 필요한 행 수 계산: 원본 행 수 + 채널 수 - 1
            # 마지막 채널(CH-B5)까지 모든 데이터가 참조되려면 추가 행이 필요
            total_rows = original_rows + len(required_channels) - 1
            
            print(f"  Extended total rows: {total_rows} (original: {original_rows} + extension: {len(required_channels) - 1})")
            
            # 새로운 DataFrame 생성
            transformed_data = {
                'No': range(1, total_rows + 1),  # 1부터 시작하는 순번
                'Point': [None] * total_rows     # Point 컬럼 (원본 데이터 + 빈 값)
            }
            
            # Point 컬럼 채우기 (원본 데이터 + 확장된 부분)
            for i in range(original_rows):
                transformed_data['Point'][i] = df.iloc[i]['Point']
            
            # 확장된 부분에서 Point 값 연속 증가
            if original_rows >= 2:
                # Point 간격 계산 (마지막 두 점 사이의 간격)
                last_point = df.iloc[original_rows - 1]['Point']
                second_last_point = df.iloc[original_rows - 2]['Point']
                point_interval = last_point - second_last_point
                
                # 확장된 부분에서 Point 값 연속 증가
                for i in range(original_rows, total_rows):
                    next_point = last_point + point_interval * (i - original_rows + 1)
                    transformed_data['Point'][i] = next_point
            else:
                # 데이터가 부족한 경우 빈 값으로 유지
                for i in range(original_rows, total_rows):
                    transformed_data['Point'][i] = ''
            
            # 각 채널 컬럼 초기화 (모두 빈 값으로)
            for channel in required_channels:
                transformed_data[channel] = ['' for _ in range(total_rows)]
            
            # 각 행마다 채널별로 다른 행의 데이터 참조
            for current_row in range(total_rows):
                # 현재 행에서 채울 채널 수 결정 (1행: 1개, 2행: 2개, ...)
                num_channels_to_fill = min(current_row + 1, len(required_channels))
                
                # 각 채널별로 참조할 행 계산 및 데이터 설정
                for ch_idx in range(num_channels_to_fill):
                    channel = required_channels[ch_idx]
                    
                    # 참조할 행 계산: 현재 행에서 채널 인덱스만큼 뒤로
                    reference_row = current_row - ch_idx
                    
                    # 참조할 행이 원본 데이터 범위 내에 있는지 확인
                    if 0 <= reference_row < original_rows and channel in df.columns:
                        transformed_data[channel][current_row] = df.iloc[reference_row][channel]
            
            # 변환된 DataFrame 생성
            result_df = pd.DataFrame(transformed_data)
            
            # 빈 문자열을 NaN으로 변환한 후 다시 빈 문자열로 (CSV 저장시 깔끔하게)
            result_df = result_df.replace('', pd.NA).fillna('')
            
            # 출력 파일명 생성
            base_filename = os.path.basename(csv_file)
            if base_filename.upper().endswith('.CSV'):
                output_filename = base_filename[:-4] + 'TR.CSV'
            else:
                output_filename = base_filename[:-4] + 'TR.csv'
            
            output_path = os.path.join(input_folder, output_filename)
            
            # CSV 파일로 저장
            result_df.to_csv(output_path, index=False)
            
            print(f"  ✅ Created: {output_filename}")
            print(f"     Columns: {list(result_df.columns)}")
            print(f"     Total rows: {len(result_df)} (original: {original_rows}, extended: {len(result_df) - original_rows})")
            print(f"     Point range: {df['Point'].min():.1f} ~ {df['Point'].max():.1f} (original data only)")
            
            # 패턴 예시 출력 (처음 6행과 마지막 6행)
            print(f"  📋 Pattern examples (first 6 rows):")
            for i in range(min(6, len(result_df))):
                row = result_df.iloc[i]
                pattern_info = []
                for ch_idx, ch in enumerate(required_channels):
                    if row[ch] != '' and pd.notna(row[ch]):
                        ref_row = i - ch_idx + 1  # 1-based indexing for display
                        pattern_info.append(f"({ref_row}, {ch})")
                print(f"     Row {i+1}: {', '.join(pattern_info) if pattern_info else 'No channels'}")
            
            print(f"  📋 Pattern examples (last 6 rows):")
            start_idx = max(0, len(result_df) - 6)
            for i in range(start_idx, len(result_df)):
                row = result_df.iloc[i]
                pattern_info = []
                for ch_idx, ch in enumerate(required_channels):
                    if row[ch] != '' and pd.notna(row[ch]):
                        ref_row = i - ch_idx + 1  # 1-based indexing for display
                        pattern_info.append(f"({ref_row}, {ch})")
                print(f"     Row {i+1}: {', '.join(pattern_info) if pattern_info else 'No channels'}")
                
        except Exception as e:
            print(f"  ❌ Error processing {csv_file}: {str(e)}")
            continue
    
    print(f"\n=== Transformation Complete ===")
    
    # 생성된 TR 파일들 확인
    tr_pattern1 = os.path.join(input_folder, '*TR.csv')
    tr_pattern2 = os.path.join(input_folder, '*TR.CSV')
    tr_files = glob.glob(tr_pattern1) + glob.glob(tr_pattern2)
    
    print(f"Generated {len(tr_files)} TR files:")
    for tr_file in sorted(tr_files):
        tr_df = pd.read_csv(tr_file)
        print(f"  - {os.path.basename(tr_file)}: {len(tr_df)} rows, {len(tr_df.columns)} columns")

def verify_transformed_files(input_folder='data/iot'):
    """
    변환된 파일들의 구조와 데이터를 검증
    """
    print("\n=== Verifying Transformed Files ===")
    
    # TR 파일들 찾기
    tr_pattern1 = os.path.join(input_folder, '*TR.csv')
    tr_pattern2 = os.path.join(input_folder, '*TR.CSV')
    tr_files = glob.glob(tr_pattern1) + glob.glob(tr_pattern2)
    
    if not tr_files:
        print("No TR files found for verification")
        return
    
    expected_columns = ['No', 'Point', 'CH-A1', 'CH-A2', 'CH-A3', 'CH-A4', 'CH-A5', 
                       'CH-B1', 'CH-B2', 'CH-B3', 'CH-B4', 'CH-B5']
    
    for tr_file in sorted(tr_files):
        print(f"\nVerifying {os.path.basename(tr_file)}:")
        
        try:
            df = pd.read_csv(tr_file)
            
            # 컬럼 구조 확인
            if list(df.columns) == expected_columns:
                print("  ✅ Column structure: CORRECT")
            else:
                print("  ❌ Column structure: INCORRECT")
                print(f"     Expected: {expected_columns}")
                print(f"     Actual:   {list(df.columns)}")
            
            # 데이터 요약
            print(f"  📊 Data summary:")
            print(f"     Total rows: {len(df)}")
            print(f"     No range: {df['No'].min()} ~ {df['No'].max()}")
            
            # Point 컬럼에서 빈 값이 아닌 것들만 확인
            valid_points = df[df['Point'] != '']['Point']
            if len(valid_points) > 0:
                print(f"     Point range (valid data): {valid_points.min():.1f} ~ {valid_points.max():.1f}")
                print(f"     Valid Point rows: {len(valid_points)} / {len(df)}")
            
            # 참조 패턴 검증 (처음 10행과 마지막 10행)
            print(f"  🔄 Reference pattern verification:")
            
            # 마지막 행에서 CH-B5가 채워져 있는지 확인
            last_row = df.iloc[-1]
            if not (pd.isna(last_row['CH-B5']) or last_row['CH-B5'] == ''):
                print("     ✅ Extension pattern: CORRECT (CH-B5 reaches the end)")
            else:
                print("     ❌ Extension pattern: INCORRECT (CH-B5 does not reach the end)")
            
            # 첫 몇 행과 마지막 몇 행 참조 패턴 보기
            print(f"  👀 First 3 rows reference pattern:")
            for i in range(min(3, len(df))):
                row = df.iloc[i]
                pattern_info = []
                for ch_idx, ch in enumerate(expected_columns[2:]):  # CH-A1부터
                    if not (pd.isna(row[ch]) or row[ch] == ''):
                        ref_row = i - ch_idx + 1  # 1-based indexing
                        pattern_info.append(f"({ref_row}, {ch})")
                print(f"     Row {i+1}: {', '.join(pattern_info) if pattern_info else 'No channels'}")
            
            print(f"  👀 Last 3 rows reference pattern:")
            start_idx = max(0, len(df) - 3)
            for i in range(start_idx, len(df)):
                row = df.iloc[i]
                pattern_info = []
                for ch_idx, ch in enumerate(expected_columns[2:]):  # CH-A1부터
                    if not (pd.isna(row[ch]) or row[ch] == ''):
                        ref_row = i - ch_idx + 1  # 1-based indexing
                        pattern_info.append(f"({ref_row}, {ch})")
                print(f"     Row {i+1}: {', '.join(pattern_info) if pattern_info else 'No channels'}")
                
        except Exception as e:
            print(f"  ❌ Error reading {tr_file}: {str(e)}")

def main():
    """
    메인 실행 함수
    """
    print("=== BAR Files Transformation (Extended Reference Pattern) ===")
    
    # data/iot 폴더가 존재하는지 확인
    if not os.path.exists('data/iot'):
        print("data/iot folder not found. Creating...")
        os.makedirs('data/iot')
    
    # BAR 파일들을 변환
    transform_bar_files()
    
    # 변환된 파일들 검증
    verify_transformed_files()

if __name__ == "__main__":
    main() 