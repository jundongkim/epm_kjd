ICP/qcp 폴더에 아래와 같이 가상의 iot 데이터 qcp_process_1.csv, qcp_process_2.csv, qcp_process_3.csv를 생성.

qcp_process_1.csv : 1차 공정 
qcp_process_2.csv : 2차 공정
qcp_process_3.csv : 3차 공정

1차 공정: 
date, lot_id, mixer, hopper, auger, rhk_input, rhk_output, roc

2차 공정: 
date, lot_id, mixer, hopper, auger, rhk_input, rhk_output, roc

3차 공정:
date​, lot_id, washing, filter_press, dry, cooler, shifter, ems, packing

date: 2022년 1월 데이터

1차, 2차 공정 동일 순서
lot_id: 700kg/lot unique id
mixer: 10분 운영
hopper: 100분 운영
auger: 60분 운영
rhk: 30분 운영
rhk: 30분 운영
roc: 40분 운영

3차 공정
lot_id: 3500kg/lot unique id
washing: 240분 운영
filter_press: 240분 운영
dry: 24 시간 운영
cooler: 240분 운영
shifter: 240분 운영
ems: 240분 운영
packing: 240분 운영


## target_icp1, targe_icp2, target_icp3 모두 0~1 사이 실수
## 각 공정의 설비 운전 시간은 순차적으로 진행 하되, 가장 긴 운영시간 설비를 고려하여 전후 휴유시간 존재함.
## Lot_id 는 yymmdd*** 으로 seq 하게 생성
