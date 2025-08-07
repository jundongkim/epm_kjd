import pandas as pd
import os
from datetime import datetime, timedelta
import glob

def extract_serialize_datasets(input_folder='data/iot'):
    """
    BAR00018.csv 형식의 파일에서 화살표와 셀 색상에 따라 10개의 serialize dataset을 추출
    """
    
    # iot 폴더에서 BAR로 시작하는 CSV 파일들 찾기 (대소문자 모두)
    pattern1 = os.path.join(input_folder, 'BAR*.csv')
    pattern2 = os.path.join(input_folder, 'BAR*.CSV')
    csv_files = glob.glob(pattern1) + glob.glob(pattern2)
    
    if not csv_files:
        print(f"No BAR*.csv or BAR*.CSV files found in {input_folder} folder")
        return
    
    print(f"Found {len(csv_files)} BAR files to process:")
    for file in csv_files:
        print(f"  - {file}")
    
    for csv_file in csv_files:
        print(f"Processing {csv_file}...")
        
        # CSV 파일 읽기 (첫 6줄은 메타데이터)
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 메타데이터 추출
        date_str = lines[0].split(',')[1].strip()  # 2018.02.21 12:51
        lot_no = lines[1].split(',')[1].strip()    # L820169
        bar_no = lines[2].split(',')[1].strip()    # 18
        
        # 날짜 문자열을 datetime 객체로 변환
        try:
            base_datetime = datetime.strptime(date_str, '%Y.%m.%d %H:%M')
        except ValueError:
            print(f"Error parsing date: {date_str}")
            continue
        
        # 헤더와 데이터 읽기 (7번째 줄부터)
        df = pd.read_csv(csv_file, skiprows=6)
        
        # 이미지의 색칠된 셀과 화살표 패턴에 따른 serialize 순서 정의
        # 각 행에서 색칠된 채널들의 패턴을 분석하여 serialize 순서 결정
        serialize_patterns = [
            # 패턴 1: CH-A1 중심 (첫 번째 색칠 패턴)
            {'channels': ['CH-A1'], 'name': '01'},
            # 패턴 2: CH-A2 중심 
            {'channels': ['CH-A2'], 'name': '02'},
            # 패턴 3: CH-A3 중심
            {'channels': ['CH-A3'], 'name': '03'},
            # 패턴 4: CH-A4 중심
            {'channels': ['CH-A4'], 'name': '04'},
            # 패턴 5: CH-A5 중심
            {'channels': ['CH-A5'], 'name': '05'},
            # 패턴 6: CH-B1 중심
            {'channels': ['CH-B1'], 'name': '06'},
            # 패턴 7: CH-B2 중심
            {'channels': ['CH-B2'], 'name': '07'},
            # 패턴 8: CH-B3 중심
            {'channels': ['CH-B3'], 'name': '08'},
            # 패턴 9: CH-B4 중심 (이미지에서 색칠된 패턴)
            {'channels': ['CH-B4'], 'name': '09'},
            # 패턴 10: CH-B5 중심 (이미지에서 색칠된 패턴)
            {'channels': ['CH-B5'], 'name': '10'}
        ]
        
        # 각 serialize 패턴별로 데이터 추출
        for pattern in serialize_patterns:
            print(f"Extracting pattern {pattern['name']}...")
            
            time_data = []
            actual_data = []
            
            for idx, row in df.iterrows():
                # Point 값을 밀리세컨드로 변환하여 시간 계산
                point_ms = int(row['Point'])
                timestamp = base_datetime + timedelta(milliseconds=point_ms)
                time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # 밀리세컨드까지
                
                # 해당 패턴의 채널 데이터 추출
                for channel in pattern['channels']:
                    if channel in df.columns:
                        time_data.append(time_str)
                        actual_data.append(row[channel])
            
            # 새로운 DataFrame 생성
            result_df = pd.DataFrame({
                'Time': time_data,
                'Actual Data': actual_data
            })
            
            # 파일명 생성: Lot No - Bar No - 패턴번호
            output_filename = f"{lot_no}-{bar_no}-{pattern['name']}.csv"
            output_path = os.path.join(input_folder, output_filename)
            
            # CSV 파일로 저장
            result_df.to_csv(output_path, index=False)
            print(f"Created: {output_filename} (Channels: {', '.join(pattern['channels'])})")
    
    print("All serialize datasets extracted successfully!")

def extract_colored_cell_patterns(input_folder='data/iot'):
    """
    이미지의 색칠된 셀 패턴을 기반으로 serialize 추출
    각 행에서 색칠된 셀들의 값을 시간 순서대로 나열
    """
    # iot 폴더에서 BAR로 시작하는 CSV 파일들 찾기 (대소문자 모두)
    pattern1 = os.path.join(input_folder, 'BAR*.csv')
    pattern2 = os.path.join(input_folder, 'BAR*.CSV')
    csv_files = glob.glob(pattern1) + glob.glob(pattern2)
    
    if not csv_files:
        print(f"No BAR*.csv or BAR*.CSV files found in {input_folder} folder")
        return
    
    print(f"Found {len(csv_files)} BAR files to process:")
    for file in csv_files:
        print(f"  - {file}")
    
    for csv_file in csv_files:
        print(f"Processing {csv_file} with colored cell patterns...")
        
        # CSV 파일 읽기
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 메타데이터 추출
        date_str = lines[0].split(',')[1].strip()
        lot_no = lines[1].split(',')[1].strip()
        bar_no = lines[2].split(',')[1].strip()
        
        try:
            base_datetime = datetime.strptime(date_str, '%Y.%m.%d %H:%M')
        except ValueError:
            print(f"Error parsing date: {date_str}")
            continue
        
        # 데이터 읽기
        df = pd.read_csv(csv_file, skiprows=6)
        
        # 이미지 패턴을 기반으로 한 각 행별 색칠된 채널 매핑
        # 각 serialize dataset별로 어떤 행에서 어떤 채널을 선택할지 정의
        row_channel_mapping = {
            # Serialize 01 (L820169-18-01.csv): 각 행별로 색칠된 채널
            1: [
                'CH-A1',  # row 1: CH-A1 색칠
                'B-OR',   # row 2: B-OR 색칠  
                'B-OR',   # row 3: B-OR 색칠
                'B-OR',   # row 4: B-OR 색칠
                'B-OR',   # row 5: B-OR 색칠
                'B-OR',   # row 6: B-OR 색칠
                'CH-A3',  # row 7: CH-A3 색칠
                'CH-A4',  # row 8: CH-A4 색칠
                'CH-A3',  # row 9: CH-A3 색칠
                'CH-A1',  # row 10: CH-A1 색칠
                'CH-A1',  # row 11: CH-A1 색칠 (계속...)
            ],
            # Serialize 02: 다른 색칠 패턴
            2: [
                'CH-A2',  # row 1: CH-A2 색칠
                'CH-A1',  # row 2: CH-A1 색칠
                'CH-A1',  # row 3: CH-A1 색칠
                'CH-A1',  # row 4: CH-A1 색칠
                'CH-A1',  # row 5: CH-A1 색칠
                'CH-A1',  # row 6: CH-A1 색칠
                'CH-A1',  # row 7: CH-A1 색칠
                'A-OR',   # row 8: A-OR 색칠
                'A-OR',   # row 9: A-OR 색칠
                'A-OR',   # row 10: A-OR 색칠
                'A-OR',   # row 11: A-OR 색칠
            ],
            # 나머지 serialize 패턴들도 이와 같이 정의...
        }
        
        # 간단한 방법: 각 채널별로 모든 행의 값을 추출
        channels = ['CH-A1', 'CH-A2', 'CH-A3', 'CH-A4', 'CH-A5', 
                   'CH-B1', 'CH-B2', 'CH-B3', 'CH-B4', 'CH-B5']
        
        # 사용자가 제공한 정확한 순환 패턴 정의
        # 기본 순환 순서: CH-A1, CH-B5, CH-B4, CH-B3, CH-B2, CH-B1, CH-A5, CH-A4, CH-A3, CH-A2
        base_cycle = ['CH-A1', 'CH-B5', 'CH-B4', 'CH-B3', 'CH-B2', 'CH-B1', 'CH-A5', 'CH-A4', 'CH-A3', 'CH-A2']
        
        # 각 serialize dataset별 시작 인덱스 정의
        start_indices = {
            1: 0,   # CH-A1에서 시작
            2: 9,   # CH-A2에서 시작  
            3: 8,   # CH-A3에서 시작
            4: 7,   # CH-A4에서 시작
            5: 6,   # CH-A5에서 시작
            6: 5,   # CH-B1에서 시작
            7: 4,   # CH-B2에서 시작
            8: 3,   # CH-B3에서 시작
            9: 2,   # CH-B4에서 시작
            10: 1,  # CH-B5에서 시작
        }
        
        # 각 serialize dataset의 패턴 생성
        serialize_patterns = {}
        for serialize_num in range(1, 11):
            pattern = []
            start_idx = start_indices[serialize_num]
            
            for row_idx in range(len(df)):
                # 순환 패턴에서 현재 위치 계산
                cycle_position = (start_idx + row_idx) % len(base_cycle)
                pattern.append(base_cycle[cycle_position])
            
            serialize_patterns[serialize_num] = pattern
        
        # 10개의 serialize dataset 생성
        for i in range(1, 11):
            time_data = []
            actual_data = []
            
            for idx, row in df.iterrows():
                # Point 값을 밀리세컨드로 변환하여 시간 계산
                point_ms = int(row['Point'])
                timestamp = base_datetime + timedelta(milliseconds=point_ms)
                time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                
                # 해당 serialize에 따른 채널 선택
                if i in serialize_patterns and idx < len(serialize_patterns[i]):
                    # 정의된 serialize 패턴 따름
                    selected_channel = serialize_patterns[i][idx]
                    channel_value = row[selected_channel]
                else:
                    # 기본값: 각 채널별 고정
                    target_channel = channels[i-1] if i-1 < len(channels) else channels[0]
                    channel_value = row[target_channel]
                
                time_data.append(time_str)
                actual_data.append(channel_value)
            
            # DataFrame 생성
            result_df = pd.DataFrame({
                'Time': time_data,
                'Actual Data': actual_data
            })
            
            # 파일명 생성
            output_filename = f"{lot_no}-{bar_no}-{i:02d}.csv"
            output_path = os.path.join(input_folder, output_filename)
            
            # CSV 파일로 저장
            result_df.to_csv(output_path, index=False)
            # 패턴 정보 출력
            pattern_channels = serialize_patterns[i][:14]  # 처음 14개 채널 순서
            print(f"Created: {output_filename}")
            print(f"Channel pattern: {' -> '.join(pattern_channels)}")
            print(f"First few values: {actual_data[:14]}")
            print()

def merge_serialize_datasets(input_folder='data/iot'):
    """
    BAR 파일 번호 순서로 각 serialize 패턴을 연결하여 전체 10개의 직렬화 파일 생성
    """
    print("\n=== 연결된 serialize 파일 생성 중 ===")
    
    # iot 폴더에서 생성된 serialize 파일들 찾기
    pattern = os.path.join(input_folder, 'L*-*-*.csv')
    serialize_files = glob.glob(pattern)
    
    if not serialize_files:
        print("No serialize files found to merge")
        return
    
    # 파일들을 lot_no, bar_no, serialize_num으로 그룹화
    file_groups = {}
    for file_path in serialize_files:
        filename = os.path.basename(file_path)
        # L820169-1-01.csv 형태에서 정보 추출
        parts = filename.replace('.csv', '').split('-')
        if len(parts) >= 3:
            lot_no = parts[0]
            bar_no = parts[1]
            serialize_num = parts[2]
            
            if serialize_num not in file_groups:
                file_groups[serialize_num] = []
            file_groups[serialize_num].append((int(bar_no), file_path))
    
    # 각 serialize 패턴별로 연결
    for serialize_num in sorted(file_groups.keys()):
        print(f"Creating merged file for serialize pattern {serialize_num}...")
        
        # bar_no 순서로 정렬
        sorted_files = sorted(file_groups[serialize_num], key=lambda x: x[0])
        
        merged_time_data = []
        merged_actual_data = []
        lot_no = None
        
        for bar_no, file_path in sorted_files:
            print(f"  - Adding {os.path.basename(file_path)}")
            
            # CSV 파일 읽기
            df = pd.read_csv(file_path)
            
            # lot_no 추출 (첫 번째 파일에서)
            if lot_no is None:
                filename = os.path.basename(file_path)
                lot_no = filename.split('-')[0]
            
            # 시간과 데이터 연결
            for _, row in df.iterrows():
                merged_time_data.append(row['Time'])
                merged_actual_data.append(row['Actual Data'])
        
        # 연결된 DataFrame 생성
        merged_df = pd.DataFrame({
            'Time': merged_time_data,
            'Actual Data': merged_actual_data
        })
        
        # 파일명 생성: L820169-01.csv
        output_filename = f"{lot_no}-{serialize_num}.csv"
        output_path = os.path.join(input_folder, output_filename)
        
        # CSV 파일로 저장
        merged_df.to_csv(output_path, index=False)
        print(f"Created merged file: {output_filename} ({len(merged_df)} rows)")
        print(f"First few values: {merged_actual_data[:10]}")
        print()
    
    print("All merged serialize datasets created successfully!")

def main():
    """
    메인 실행 함수
    """
    # data/iot 폴더가 존재하는지 확인
    if not os.path.exists('data/iot'):
        print("data/iot folder not found. Creating...")
        os.makedirs('data/iot')
    
    # 색칠된 셀 패턴을 기반으로 데이터 추출
    extract_colored_cell_patterns()
    
    # BAR 파일들을 번호 순서로 연결하여 전체 serialize 파일 생성
    merge_serialize_datasets()

if __name__ == "__main__":
    main() 