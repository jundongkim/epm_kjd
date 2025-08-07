ICP 폴더에 아래와 같이 가상의 데이터 normalized_data.csv를 생성.

normalized_data_1.csv : 1차 공정 
normalized_data_2.csv : 2차 공정
normalized_data_3.csv : 3차 공정

1차 공정: 
date, lot_id, mixer_start, mixer_end, hopper_start, hopper_end, auger_start, auger_end, rhk_input_start, rhk_input_end, rhk_output_start_end, roc_start, roc_end, target_icp1

2차 공정: 
date, lot_id, mixer_start, mixer_end, hopper_start, hopper_end, auger_start, auger_end, rhk_input_start, rhk_input_end, rhk_output_start_end, roc_start, roc_end, target_icp2

3차 공정:
date​, lot_id, washing_start, washing_end, filter_press_start_filter_press_end, dry_start, dry_end, cooler_start, cooler_end, shifter_start, shifter_end, ems_start, ems_end, packing_start, packing_end, target_icp3

date: 2022년 중 선택 일자로 부터 1주일

1차, 2차 공정 동일 순서
lot_id: 700kg/lot unique id
mixer_start ~ mixer_end: datetime 10분 내외 간격
hopper_start ~ hopper_end: datetime 100분 내외 간격
auger_start ~ auger_end: datetime 60분 내외 간격
rhk_input_start ~ rhk_input_end: datetime 30분 내외 간격
rhk_output_start ~ rhk_output_end: datetime 30분 내외 간격
roc_start ~ roc_end: datetime 40분 내외 간격

3차 공정
lot_id: 3500kg/lot unique id
washing_start ~ washing_end: datetime 240분 내외 간격
filter_press_start ~ filter_press_end: datetime 240분 내외 간격
dry_start ~ dry_end: datetime 24 시간 내외 간격
cooler_start ~ cooler_end: datetime 240분 내외 간격
shifter_start ~ shifter_end: datetime 240분 내외 간격
ems_start ~ ems_end: datetime 240분 내외 간격
packing_start ~ packing_end: datetime 240분 내외 간격


## target_icp1, targe_icp2, target_icp3 모두 0~1 사이 실수
## 각 공정의 설비 운전 시간은 순차적으로 진행 하되, 가장 긴 운영시간 설비를 고려하여 전후 휴유시간 존재함.
## Lot_id 는 yymmdd*** 으로 seq 하게 생성
