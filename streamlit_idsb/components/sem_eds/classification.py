# 스테인리스 강종 분류 ================================================
stainless_standard_composition = [
    {
        "grade": "SUS304",
        "series": "오스테나이트계",
        "Cr": (18.0, 20.0), "Ni": (8.0, 10.5),
        "Mo": (0, 0.75), "C": (0, 0.08), "Mn": (0, 2.0), "N": (0, 0.10)
    },
    {
        "grade": "SUS304L",
        "series": "오스테나이트계",
        "Cr": (18.0, 20.0), "Ni": (8.0, 12.0),
        "Mo": (0, 0.75), "C": (0, 0.03), "Mn": (0, 2.0), "N": (0, 0.10)
    },
    {
        "grade": "SUS316",
        "series": "오스테나이트계",
        "Cr": (16.0, 18.0), "Ni": (10.0, 14.0),
        "Mo": (2.0, 3.0), "C": (0, 0.08), "Mn": (0, 2.0), "N": (0, 0.10)
    },
    {
        "grade": "SUS316L",
        "series": "오스테나이트계",
        "Cr": (16.0, 18.0), "Ni": (10.0, 14.0),
        "Mo": (2.0, 3.0), "C": (0, 0.03), "Mn": (0, 2.0), "N": (0, 0.10)
    },
    {
        "grade": "SUS310S",
        "series": "오스테나이트계",
        "Cr": (24.0, 26.0), "Ni": (19.0, 22.0),
        "Mo": (0.0, 0.75), "C": (0, 0.25), "Mn": (0, 2.0), "N": (0, 0.10)
    },
    {
        "grade": "SUS321",
        "series": "오스테나이트계",
        "Cr": (17.0, 19.0), "Ni": (9.0, 12.0),
        "Mo": (0.0, 0.75), "C": (0, 0.08), "Mn": (0, 2.0), "N": (0, 0.10)
    },
    {
        "grade": "SUS430",
        "series": "페라이트계",
        "Cr": (16.0, 18.0), "Ni": (0.0, 0.75),
        "Mo": (0, 0.75), "C": (0, 0.12), "Mn": (0, 1.0)
    },
    {
        "grade": "SUS409",
        "series": "페라이트계",
        "Cr": (10.5, 11.75), "Ni": (0.0, 0.5),
        "Mo": (0, 0.75), "C": (0, 0.08), "Mn": (0, 1.0)
    },
    {
        "grade": "SUS410",
        "series": "마르텐사이트계",
        "Cr": (11.5, 13.5), "Ni": (0.0, 0.75),
        "C": (0, 0.15), "Mn": (0, 1.0)
    },
    {
        "grade": "SUS420",
        "series": "마르텐사이트계",
        "Cr": (12.0, 14.0), "Ni": (0.0, 0.75),
        "C": (0.15, 0.40), "Mn": (0, 1.0)
    },
    {
        "grade": "SUS440C",
        "series": "마르텐사이트계",
        "Cr": (16.0, 18.0), "Ni": (0.0, 0.75),
        "C": (0.95, 1.20), "Mn": (0, 1.0)
    },
    {
        "grade": "SUS329J3L",
        "series": "듀플렉스계",
        "Cr": (21.0, 23.0), "Ni": (4.5, 6.5),
        "Mo": (2.5, 3.5), "C": (0, 0.03), "Mn": (0, 2.0), "N": (0.14, 0.20)
    },
    {
        "grade": "SUS329J4L",
        "series": "듀플렉스계",
        "Cr": (24.0, 26.0), "Ni": (6.0, 8.0),
        "Mo": (3.0, 5.0), "C": (0, 0.03), "Mn": (0, 1.2), "N": (0.24, 0.32)
    },
    {
        "grade": "SUS630",
        "series": "석출경화계",
        "Cr": (15.0, 17.5), "Ni": (3.0, 5.0),
        "C": (0, 0.07), "Mn": (0, 1.0), "Cu": (3.0, 5.0)
    },
]

def get_stainless_standard_composition_df():
    # 데이터프레임으로 변환하기 위한 리스트 생성
    table_data = []
    for steel in stainless_standard_composition:
        row_data = {
            "강종": steel["grade"],
            "계열": steel["series"],
            "Cr (%)": steel.get("Cr", "-"),
            "Ni (%)": steel.get("Ni", "-"),
            "Mo (%)": steel.get("Mo", "-"),
            "C (%)": steel.get("C", "-"),
            "Mn (%)": steel.get("Mn", "-"),
            "N (%)": steel.get("N", "-"),
            "Cu (%)": steel.get("Cu", "-")
        }
        # 원소별 범위를 문자열로 변환하여 추가
        for element, range_values in row_data.items():
            if element not in ["강종", "계열"]:
                if isinstance(range_values, tuple) and len(range_values) == 2:
                    row_data[element] = f"{range_values[0]}-{range_values[1]}%"

        table_data.append(row_data)

    # 데이터프레임으로 변환하여 반환
    import pandas as pd
    df = pd.DataFrame(table_data)
    return df

def _classify_stainless_steel(composition: dict) -> list:
    elements = ['Cr', 'Ni', 'Mo', 'C', 'Mn', 'N', 'Cu']
    comp = {el: float(composition.get(el, 0.0)) for el in elements}

    def in_range(val, r):
        if r == (0, 0):
            return val == 0
        return r[0] <= val <= r[1]

    def range_str(el, r):
        return f"{el}: {r[0]}–{r[1]}%"

    def range_center(r):
        return (r[0] + r[1]) / 2 if r[1] > 0 else 0

    def similarity_score(input_val, ref_range):
        center = range_center(ref_range)
        if center == 0 and input_val == 0:
            return 1.0
        elif center == 0:
            return 0.0
        return max(0.0, 1.0 - abs(input_val - center) / center)

    # 1️⃣ 정확 일치
    for alloy in stainless_standard_composition:
        if all(in_range(comp.get(el, 0.0), alloy.get(el, (0, 0))) for el in alloy if el not in ["grade", "series"]):
            reason_lines = [range_str(el, alloy[el]) for el in alloy if el not in ["grade", "series"]]
            return [{
                "grade": alloy["grade"],
                "series": alloy["series"],
                "reason": "스테인리스 강종 표준 조성과 일치 (" + ", ".join(reason_lines) + ")"
            }]

    # 원본 데이터 사용 시 로직 -------------------------------------
    # # 2️⃣ 유사도 기반 후보 추출
    # candidates = []
    # for alloy in stainless_standard_composition:
    #     total_score = 0
    #     count = 0
    #     for el in elements:
    #         input_val = comp.get(el, 0.0)
    #         ref_range = alloy.get(el, (0, 0))
    #         score = similarity_score(input_val, ref_range)
    #         total_score += score
    #         count += 1
    #     avg_score = total_score / count
    #     if avg_score >= 0.6:
    #         candidates.append({
    #             "grade": alloy["grade"],
    #             "series": alloy["series"],
    #             "reason": f"스테인리스 강종 표준 조성과의 평균 유사도 {avg_score:.2%}",
    #             "score": avg_score
    #         })

    # if candidates:
    #     # 유사도 기준 내림차순 정렬
    #     candidates.sort(key=lambda x: x["score"], reverse=True)
    #     for c in candidates:
    #         del c["score"]
    #     return candidates

    # # 3️⃣ 모두 불일치
    # return [{
    #     "grade": "Unknown",
    #     "series": "Unknown",
    #     "reason": "스테인리스 강종 표준 조성 기준 불일치"
    # }]

    # 샘플 데이터 사용 시 로직 -------------------------------------
    # 2️⃣ 유사도 기반 후보 추출
    candidates = []
    for alloy in stainless_standard_composition:
        total_score = 0
        count = 0
        for el in elements:
            input_val = comp.get(el, 0.0)
            ref_range = alloy.get(el, (0, 0))
            score = similarity_score(input_val, ref_range)
            total_score += score
            count += 1
        avg_score = total_score / count
        candidates.append({
            "grade": alloy["grade"],
            "series": alloy["series"],
            "reason": f"스테인리스 강종 표준 조성과의 평균 유사도 {avg_score:.2%}",
            "score": avg_score
        })

    if candidates:
        # 유사도 기준 내림차순 정렬
        candidates.sort(key=lambda x: x["score"], reverse=True)
        for c in candidates:
            del c["score"]
    return candidates[:5]

def classify_stainless_steel(composition: dict):
    """시료의 화학 성분 조성을 기반으로 스테인리스 스틸 강종(grade)과 계열(series)을 분류합니다.

    Args:
        composition: 시료의 화학 성분 조성(Cr, Ni, Mo, C, Mn, N, Cu 등의 함량을 %로 표현)

    Returns:
        스테인리스 스틸 강종 분류 결과 목록 (정확 일치, 유사도 기반 후보, 또는 Unknown)
    """
    return _classify_stainless_steel(composition)

# LangChain Tool 정의
from langchain_core.tools import BaseTool
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class StainlessCompositionInput(BaseModel):
    """시료 성분 조성 입력 스키마"""
    composition: Dict[str, float] = Field(..., description="시료의 성분 조성('함량_비율' 키값의 딕셔너리)")

class StainlessSteelClassificationTool(BaseTool):
    """스테인리스 스틸 분류 도구"""
    name: str = "stainless_steel_classification"
    description: str = "시료의 화학 성분 조성을 기반으로 스테인리스 스틸 강종(grade)과 계열(series)을 분류합니다"
    args_schema: type[BaseModel] = StainlessCompositionInput

    def _run(self, composition: Dict[str, float]) -> List[Dict[str, Any]]:
        """동기적으로 스테인리스 스틸을 분류합니다."""
        return _classify_stainless_steel(composition)

    async def _arun(self, composition: Dict[str, float]) -> List[Dict[str, Any]]:
        """비동기적으로 스테인리스 스틸을 분류합니다."""
        return _classify_stainless_steel(composition)