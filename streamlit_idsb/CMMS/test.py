import json

with open("output/일일업무일지-old.json", "r", encoding="utf-8") as file:
    print("일일업무일지-old.json 로드 완료")
    old_data = json.load(file)

with open("output/일일업무일지-new.json", "r", encoding="utf-8") as file:
    print("일일업무일지-new.json 로드 완료")
    base_data = json.load(file)

old_entry_list = old_data["entries"]
base_entry_list = base_data["entries"]

for base_entry, old_entry in zip(base_entry_list, old_entry_list):
    if "이미지설명" not in old_entry:
        continue

    if base_entry["작업명"] == old_entry["작업명"]:
        base_entry["이미지설명"] = old_entry["이미지설명"]

base_data["entries"] = base_entry_list

with open("output/일일업무일지.json", "w", encoding="utf-8") as file:
    json.dump(base_data, file, ensure_ascii=False, indent=4)
