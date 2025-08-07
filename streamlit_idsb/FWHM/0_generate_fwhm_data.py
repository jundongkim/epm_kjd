import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os
import time
import sys
from tqdm import tqdm
from scipy import stats
from datetime import datetime # Added for lot_id generation

# 프로젝트 루트 디렉토리 경로 계산 (FWHM 폴더의 부모 폴더)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path에 프로젝트 루트 추가
if project_root not in sys.path:
    sys.path.append(project_root)

# ====================== 데이터 생성 설정 ======================
# 기본 설정
N_SAMPLES = 1000            # 생성할 데이터 레코드 수 (요청사항: 1000개)
RANDOM_SEED = 44            # 랜덤 시드 재설정
OUTPUT_DIR = '.'            # 현재 디렉토리 (FWHM 폴더)

# 특성(Feature) 생성 설정 - 모든 특성 영향도 균형있게 조정
LI_FEATURES_BASE_VARIANCE = 0.7      # Li 기본 특성의 분산
PRE_L_BASE_VARIANCE = 0.7           # Pre_L 기본 특성의 분산
PRE_S_BASE_VARIANCE = 0.7           # Pre_S 기본 특성의 분산
QCP_BASE_VARIANCE = 0.75            # Qcp 기본 특성의 분산 (신규 추가)

# 이상치(Outlier) 설정
LI_OUTLIER_RATIO = 0.015              # Li 특성 이상치 비율
LI_OUTLIER_SCALE = 0.4               # Li 특성 이상치 강도
PRE_L_OUTLIER_RATIO = 0.015           # Pre_L 특성 이상치 비율
PRE_L_OUTLIER_SCALE = 0.4            # Pre_L 특성 이상치 강도
PRE_S_OUTLIER_RATIO = 0.015          # Pre_S 특성 이상치 비율
PRE_S_OUTLIER_SCALE = 0.4            # Pre_S 특성 이상치 강도
QCP_OUTLIER_RATIO = 0.015           # Qcp 특성 이상치 비율 (신규 추가)
QCP_OUTLIER_SCALE = 0.4             # Qcp 특성 이상치 강도 (신규 추가)

# 노이즈 설정
NOISE_LEVEL_BASE = 0.1               # 기본 노이즈 레벨
NOISE_VARIANCE = 0.15                # 노이즈 분산

# 타겟 변수 생성 설정
TARGET_LINEAR_WEIGHT = 0.6           # 선형 성분 가중치
TARGET_NONLINEAR_WEIGHT = 0.25       # 비선형 성분 가중치
TARGET_INTERACTION_WEIGHT = 0.2      # 상호작용 성분 가중치
TARGET_NOISE_WEIGHT = 0.15           # 노이즈 성분 가중치
TARGET_OUTLIER_RATIO = 0.002         # 타겟 이상치 비율
TARGET_OUTLIER_SCALE = 0.4           # 타겟 이상치 강도

# R2 목표 값
TARGET_R2 = 0.85                     # 목표 R2 값

# 특성 간 관련성 설정
FEATURE_CORRELATION = 0.4            # 같은 그룹 내 특성 간 상관관계 강도
FEATURE_GROUP_CORRELATION = 0.1      # 다른 그룹 간 특성 상관관계 강도

# 다양성 설정
FEATURE_DIVERSITY = 0.2              # 특성 간 다양성을 위한 추가 랜덤 요소
MULTIMODAL_DIST = False              # 다중 모드 분포 활성화
PATTERN_COMPLEXITY = 0.4             # 비선형 패턴의 복잡성을 높이는 계수

# Li 분포를 unimodal로 만들기 위한 설정
LI_UNIMODAL = True                   # Li 특성을 단봉분포(unimodal)로 생성
LI_DIST_SKEW = 0.0                   # Li 분포의 왜도 (0은 대칭, 양수는 오른쪽 꼬리, 음수는 왼쪽 꼬리)
LI_SMOOTHING = 0.3                   # Li 특성 평활화 계수

# 특성 그룹별 중요도 조절 상수
LI_IMPORTANCE_FACTOR = 1.2           # Li 특성 중요도를 약간 높임
PRE_L_IMPORTANCE_FACTOR = 1.2        # Pre_L 특성 중요도 유지
PRE_S_IMPORTANCE_FACTOR = 1.0        # Pre_S 특성 중요도 유지
QCP_IMPORTANCE_FACTOR = 1.1         # Qcp 특성 중요도 설정 (신규 추가)

# ====================== 이하 코드 ======================

# 출력 디렉토리 생성
os.makedirs(f'{OUTPUT_DIR}', exist_ok=True)

# 랜덤 시드 설정
np.random.seed(RANDOM_SEED)

print(f"Generating dataset with {N_SAMPLES} samples...")
print(f"Data settings:")
print(f"- Li features variance: {LI_FEATURES_BASE_VARIANCE}")
print(f"- Pre_L/S features variance: {PRE_L_BASE_VARIANCE}/{PRE_S_BASE_VARIANCE}")
print(f"- Outlier ratios - Li:{LI_OUTLIER_RATIO*100}%, Pre_L:{PRE_L_OUTLIER_RATIO*100}%, Pre_S:{PRE_S_OUTLIER_RATIO*100}%")
print(f"- Noise level: {NOISE_LEVEL_BASE}")
print(f"- Feature correlations: Within group {FEATURE_CORRELATION}, Between groups {FEATURE_GROUP_CORRELATION}")
print(f"- Feature diversity: {FEATURE_DIVERSITY}, Pattern complexity: {PATTERN_COMPLEXITY}")


# Generate base features with increased variance and outliers
def generate_correlated_features():
    print("Generating base features...")
    
    # 다중 모드 분포 생성 함수 (더 다양한 값을 위해)
    def create_multimodal_distribution(size, n_modes=3):
        modes = np.random.uniform(-1, 1, n_modes)
        weights = np.random.dirichlet(np.ones(n_modes))
        spreads = np.random.uniform(0.2, 0.6, n_modes)
        result = np.zeros(size)
        start_idx = 0
        for i in range(n_modes):
            mode_size = int(size * weights[i]) if i < n_modes - 1 else size - start_idx # Ensure exact size
            if mode_size > 0:
                result_slice = np.random.normal(modes[i], spreads[i], mode_size)
                result[start_idx : start_idx + mode_size] = result_slice
                start_idx += mode_size
        np.random.shuffle(result) # Shuffle to mix modes
        return result
    
    # Li를 위한 단봉분포(unimodal) 생성 함수
    def create_unimodal_distribution(size, skew=LI_DIST_SKEW):
        if abs(skew) < 0.01:
            return np.random.normal(0, 1, size)
        else:
            return stats.skewnorm.rvs(skew, size=size)
    
    n_base_features = 5
    cov_matrix = np.eye(n_base_features)
    for i in range(n_base_features):
        for j in range(i + 1, n_base_features):
            distance = abs(i - j)
            correlation = FEATURE_CORRELATION * (0.8 ** distance)
            cov_matrix[i, j] = cov_matrix[j, i] = correlation
    
    base_features = np.random.multivariate_normal(
        mean=np.zeros(n_base_features), cov=cov_matrix, size=N_SAMPLES
    )
    
    if MULTIMODAL_DIST:
        for i in range(1, n_base_features, 2):
            multimodal_data = create_multimodal_distribution(N_SAMPLES)
            blend_factor = 0.7
            base_features[:, i] = blend_factor * base_features[:, i] + (1-blend_factor) * multimodal_data
    
    if LI_UNIMODAL:
        li_base = np.zeros((N_SAMPLES, n_base_features))
        for i in range(n_base_features):
            skew_variation = LI_DIST_SKEW + np.random.uniform(-0.2, 0.2)
            li_base[:, i] = create_unimodal_distribution(N_SAMPLES, skew_variation)
        blend_ratio = 0.3
        li_base = (1 - blend_ratio) * li_base + blend_ratio * base_features
        li_base = li_base * LI_FEATURES_BASE_VARIANCE
    else:
        li_base = base_features * LI_FEATURES_BASE_VARIANCE
    
    diversity_factor = FEATURE_DIVERSITY
    pre_l_base = (base_features + np.random.normal(0, 0.3, (N_SAMPLES, n_base_features))) * PRE_L_BASE_VARIANCE
    pre_s_base = (base_features + np.random.normal(0, 0.4, (N_SAMPLES, n_base_features))) * PRE_S_BASE_VARIANCE
    qcp_base = (base_features + np.random.normal(0, 0.35, (N_SAMPLES, n_base_features))) * QCP_BASE_VARIANCE

    for i in range(n_base_features):
        if LI_UNIMODAL:
            if i % 2 == 0:
                li_base[:, i] = li_base[:, i] + LI_SMOOTHING * np.tanh(li_base[:, i])
        else:
            if i % 2 == 0:
                li_base[:, i] = np.sign(li_base[:, i]) * np.abs(li_base[:, i])**0.7
        if i % 3 == 0:
            pre_l_base[:, i] += 0.2 * np.sin(pre_l_base[:, i] * 3.0) * diversity_factor
        if i % 3 == 1:
            pre_s_base[:, i] += 0.2 * (pre_s_base[:, i]**2) * diversity_factor
    
    pbar = tqdm(total=28+32+32+30, desc="Generating features")

    print("Generating Li features...")
    li_features = []
    for i in range(28):
        if i < n_base_features:
            feature = li_base[:, i]
            outlier_idx = np.random.choice(N_SAMPLES, size=int(N_SAMPLES * LI_OUTLIER_RATIO), replace=False)
            outlier_direction = np.random.choice([-1, 1], size=len(outlier_idx))
            feature[outlier_idx] += outlier_direction * np.abs(np.random.normal(0, LI_OUTLIER_SCALE, size=len(outlier_idx)))
        else:
            base_idx = i % n_base_features
            secondary_idx = (i + 2) % n_base_features
            tertiary_idx = (i + 4) % n_base_features
            if LI_UNIMODAL:
                if i % 8 == 0: feature = li_base[:, base_idx] * 0.7 + li_base[:, secondary_idx] * 0.3 + LI_SMOOTHING * np.tanh(li_base[:, base_idx] * 0.7 + li_base[:, secondary_idx] * 0.3)
                elif i % 8 == 1: feature = li_base[:, base_idx] * 0.8 + 0.2 * np.tanh(li_base[:, secondary_idx] * 0.5)
                elif i % 8 == 2: feature = li_base[:, base_idx] * 0.6 + li_base[:, secondary_idx] * 0.4
                elif i % 8 == 3: feature = li_base[:, base_idx] * 0.75 + 0.25 * (li_base[:, secondary_idx] * 0.5 + 0.5)
                elif i % 8 == 4: feature = li_base[:, base_idx] * 0.7 + 0.3 * np.tanh(li_base[:, secondary_idx])
                elif i % 8 == 5: feature = li_base[:, base_idx] * 0.5 + li_base[:, secondary_idx] * 0.3 + li_base[:, tertiary_idx] * 0.2
                elif i % 8 == 6: feature = li_base[:, base_idx] * 0.6 + li_base[:, secondary_idx] * 0.4
                else: feature = li_base[:, base_idx] * 0.7 + 0.3 * (li_base[:, secondary_idx] + 0.05 * li_base[:, secondary_idx]**2)
            else:
                if i % 8 == 0: feature = li_base[:, base_idx] * 0.8 + np.sin(li_base[:, secondary_idx] * PATTERN_COMPLEXITY * 3) * 0.4
                elif i % 8 == 1: feature = li_base[:, base_idx] * 0.7 + np.exp(li_base[:, secondary_idx] * 0.3) * 0.2
                elif i % 8 == 2: feature = li_base[:, base_idx] * 0.75 + np.tanh(li_base[:, secondary_idx] * PATTERN_COMPLEXITY * 2) * 0.5
                elif i % 8 == 3: feature = li_base[:, base_idx] * 0.6 + li_base[:, secondary_idx] ** 2 * 0.3
                elif i % 8 == 4: feature = li_base[:, base_idx] * 0.65 + np.log1p(np.abs(li_base[:, secondary_idx])) * 0.35
                elif i % 8 == 5: feature = li_base[:, base_idx] * 0.5 + (li_base[:, secondary_idx] * li_base[:, tertiary_idx]) * 0.4
                elif i % 8 == 6: feature = li_base[:, base_idx] * 0.7 + np.abs(li_base[:, secondary_idx] - li_base[:, tertiary_idx]) * 0.3
                else: feature = li_base[:, base_idx] * 0.6 + np.sqrt(np.abs(li_base[:, secondary_idx])) * 0.4
            noise_level = NOISE_LEVEL_BASE * (1 + 0.3 * (i % 4))
            feature += np.random.normal(0, noise_level, N_SAMPLES)
        li_features.append(feature)
        pbar.update(1)

    print("Generating Pre_L and Pre_S features...")
    pre_l_features = []
    pre_s_features = []
    for i in range(32):
        if i < n_base_features:
            pre_l = pre_l_base[:, i]
            pre_s = pre_s_base[:, i]
            if i % 2 == 0:
                outlier_idx_l = np.random.choice(N_SAMPLES, size=int(N_SAMPLES * PRE_L_OUTLIER_RATIO), replace=False)
                outlier_direction_l = np.random.choice([-1, 1], size=len(outlier_idx_l))
                pre_l[outlier_idx_l] += outlier_direction_l * np.abs(np.random.normal(0, PRE_L_OUTLIER_SCALE, size=len(outlier_idx_l)))
                outlier_idx_s = np.random.choice(N_SAMPLES, size=int(N_SAMPLES * PRE_S_OUTLIER_RATIO), replace=False)
                outlier_direction_s = np.random.choice([-1, 1], size=len(outlier_idx_s))
                pre_s[outlier_idx_s] += outlier_direction_s * np.abs(np.random.normal(0, PRE_S_OUTLIER_SCALE, size=len(outlier_idx_s)))
        else:
            base_idx = i % n_base_features
            li_idx = i % 28
            if i % 10 == 0:
                pre_l = pre_l_base[:, base_idx] * 0.65 + np.sin(li_features[li_idx] * PATTERN_COMPLEXITY * 3) * 0.25
                pre_s = pre_s_base[:, base_idx] * 0.6 + np.sin(li_features[(li_idx + 5) % 28] * PATTERN_COMPLEXITY * 3) * 0.3
            elif i % 10 == 1:
                pre_l = pre_l_base[:, base_idx] * 0.7 + np.log1p(np.abs(li_features[li_idx])) * 0.2
                pre_s = pre_s_base[:, base_idx] * 0.65 + np.log1p(np.abs(li_features[(li_idx + 7) % 28])) * 0.25
            elif i % 10 == 2:
                pre_l = pre_l_base[:, base_idx] * 0.6 + li_features[li_idx]**2 * 0.15
                pre_s = pre_s_base[:, base_idx] * 0.55 + li_features[(li_idx + 9) % 28]**2 * 0.2
            elif i % 10 == 3:
                pre_l = pre_l_base[:, base_idx] * 0.7 + np.tanh(li_features[li_idx] * PATTERN_COMPLEXITY * 2) * 0.3
                pre_s = pre_s_base[:, base_idx] * 0.65 + np.tanh(li_features[(li_idx + 11) % 28] * PATTERN_COMPLEXITY * 2) * 0.35
            elif i % 10 == 4:
                pre_l = pre_l_base[:, base_idx] * 0.6 + (li_features[li_idx] * li_features[(li_idx + 1) % 28]) * 0.2
                pre_s = pre_s_base[:, base_idx] * 0.55 + (li_features[(li_idx + 13) % 28] * li_features[(li_idx + 14) % 28]) * 0.25
            elif i % 10 == 5:
                pre_l = pre_l_base[:, base_idx] * 0.75 + li_features[li_idx] * 0.25
                pre_s = pre_s_base[:, base_idx] * 0.7 + li_features[(li_idx + 15) % 28] * 0.3
            elif i % 10 == 6:
                pre_l = pre_l_base[:, base_idx] * 0.6 + np.exp(li_features[li_idx] * 0.2) * 0.2
                pre_s = pre_s_base[:, base_idx] * 0.55 + np.exp(li_features[(li_idx + 17) % 28] * 0.15) * 0.25
            elif i % 10 == 7:
                pre_l = pre_l_base[:, base_idx] * 0.65 + np.sqrt(np.abs(li_features[li_idx])) * 0.25
                pre_s = pre_s_base[:, base_idx] * 0.6 + np.sqrt(np.abs(li_features[(li_idx + 19) % 28])) * 0.3
            elif i % 10 == 8:
                pre_l = pre_l_base[:, base_idx] * 0.7 + np.abs(li_features[li_idx] - li_features[(li_idx + 2) % 28]) * 0.2
                pre_s = pre_s_base[:, base_idx] * 0.65 + np.abs(li_features[(li_idx + 21) % 28] - li_features[(li_idx + 22) % 28]) * 0.25
            else:
                pre_l = pre_l_base[:, base_idx] * 0.6 + np.sin(li_features[li_idx]**2) * 0.3
                pre_s = pre_s_base[:, base_idx] * 0.55 + np.log1p(np.abs(li_features[(li_idx + 23) % 28]**2)) * 0.35
            if i % 4 == 0:
                pre_l += create_multimodal_distribution(N_SAMPLES) * FEATURE_DIVERSITY * 0.1
            if i % 5 == 0:
                pre_s += create_multimodal_distribution(N_SAMPLES) * FEATURE_DIVERSITY * 0.12
            pre_l += np.random.normal(0, NOISE_LEVEL_BASE * (0.9 + 0.2 * (i % 3)), N_SAMPLES)
            pre_s += np.random.normal(0, NOISE_LEVEL_BASE * (1.1 + 0.2 * (i % 4)), N_SAMPLES)
        pre_l_features.append(pre_l)
        pre_s_features.append(pre_s)
        pbar.update(2)

    print("Generating Qcp features...")
    qcp_features = []
    for i in range(30):
        if i < n_base_features:
            qcp = qcp_base[:, i]
            outlier_idx = np.random.choice(N_SAMPLES, size=int(N_SAMPLES * QCP_OUTLIER_RATIO), replace=False)
            outlier_direction = np.random.choice([-1, 1], size=len(outlier_idx))
            qcp[outlier_idx] += outlier_direction * np.abs(np.random.normal(0, QCP_OUTLIER_SCALE, size=len(outlier_idx)))
        else:
            base_idx = i % n_base_features
            li_idx = i % 28
            pre_l_idx = i % 32
            pre_s_idx = i % 32
            if i % 9 == 0: qcp = qcp_base[:, base_idx] * 0.5 + np.sin(li_features[li_idx] * PATTERN_COMPLEXITY * 2) * 0.3 + pre_l_features[pre_l_idx] * 0.2
            elif i % 9 == 1: qcp = qcp_base[:, base_idx] * 0.6 + np.log1p(np.abs(li_features[li_idx])) * 0.25 + pre_s_features[pre_s_idx] * 0.15
            elif i % 9 == 2: qcp = qcp_base[:, base_idx] * 0.55 + pre_l_features[pre_l_idx]**2 * 0.2 + pre_s_features[pre_s_idx] * 0.25
            elif i % 9 == 3: qcp = qcp_base[:, base_idx] * 0.7 + np.tanh(li_features[li_idx] * PATTERN_COMPLEXITY * 1.5) * 0.3
            elif i % 9 == 4: qcp = qcp_base[:, base_idx] * 0.65 + (pre_l_features[pre_l_idx] * pre_l_features[(pre_l_idx + 1) % 32]) * 0.2
            elif i % 9 == 5: qcp = qcp_base[:, base_idx] * 0.6 + np.exp(pre_s_features[pre_s_idx] * 0.15) * 0.25
            elif i % 9 == 6: qcp = qcp_base[:, base_idx] * 0.4 + li_features[li_idx] * 0.2 + pre_l_features[pre_l_idx] * 0.2 + pre_s_features[pre_s_idx] * 0.2
            elif i % 9 == 7: qcp = qcp_base[:, base_idx] * 0.5 + (li_features[li_idx] * pre_s_features[pre_s_idx]) * 0.3
            else: qcp = qcp_base[:, base_idx] * 0.45 + (pre_l_features[pre_l_idx] * pre_s_features[pre_s_idx]) * 0.35
            if i % 6 == 0:
                qcp += create_multimodal_distribution(N_SAMPLES) * FEATURE_DIVERSITY * 0.11
            qcp += np.random.normal(0, NOISE_LEVEL_BASE * (1.0 + 0.2 * (i % 5)), N_SAMPLES)
        qcp_features.append(qcp)
        pbar.update(1)

    pbar.close()
    return np.array(li_features).T, np.array(pre_l_features).T, np.array(pre_s_features).T, np.array(qcp_features).T

# Create target variable with controlled relationship to features
def generate_target(li_data, pre_l_data, pre_s_data, qcp_data):
    print("Generating target variable...")
    important_li_indices = [0, 3, 7, 14, 20, 9, 15, 21, 25]
    important_pre_l_indices = [1, 5, 8, 12, 16]
    important_pre_s_indices = [0, 4, 7, 10, 15, 18]
    important_qcp_indices = [2, 6, 11, 18, 25]

    print("  - Adding linear component...")
    li_weights = np.array([0.5, 0.48, 0.45, 0.42, 0.4, 0.38, 0.35, 0.32, 0.3]) * TARGET_LINEAR_WEIGHT * LI_IMPORTANCE_FACTOR
    pre_l_weights = np.array([0.6, 0.58, 0.55, 0.52, 0.5]) * TARGET_LINEAR_WEIGHT * PRE_L_IMPORTANCE_FACTOR
    pre_s_weights = np.array([0.65, 0.63, 0.6, 0.57, 0.55, 0.53]) * TARGET_LINEAR_WEIGHT * PRE_S_IMPORTANCE_FACTOR
    qcp_weights = np.array([0.5, 0.48, 0.45, 0.42, 0.4]) * TARGET_LINEAR_WEIGHT * QCP_IMPORTANCE_FACTOR

    linear_component = np.zeros(N_SAMPLES)
    for i, idx in enumerate(important_li_indices): linear_component += li_weights[i] * li_data[:, idx]
    for i, idx in enumerate(important_pre_l_indices): linear_component += pre_l_weights[i] * pre_l_data[:, idx]
    for i, idx in enumerate(important_pre_s_indices): linear_component += pre_s_weights[i] * pre_s_data[:, idx]
    for i, idx in enumerate(important_qcp_indices): linear_component += qcp_weights[i] * qcp_data[:, idx]

    print("  - Adding non-linear transformations...")
    nonlinear_component = np.zeros(N_SAMPLES)
    nonlinear_component += TARGET_NONLINEAR_WEIGHT * 0.4 * np.sin(li_data[:, important_li_indices[0]]) * LI_IMPORTANCE_FACTOR
    nonlinear_component += TARGET_NONLINEAR_WEIGHT * 0.35 * np.tanh(li_data[:, important_li_indices[2]]) * LI_IMPORTANCE_FACTOR
    nonlinear_component += TARGET_NONLINEAR_WEIGHT * 0.25 * np.sin(li_data[:, important_li_indices[4]] * 2.0) * LI_IMPORTANCE_FACTOR
    nonlinear_component += TARGET_NONLINEAR_WEIGHT * 0.2 * np.sin(li_data[:, important_li_indices[6]] * 2.0) * LI_IMPORTANCE_FACTOR
    nonlinear_component += TARGET_NONLINEAR_WEIGHT * 0.7 * np.log1p(np.abs(pre_l_data[:, important_pre_l_indices[1]])) * PRE_L_IMPORTANCE_FACTOR
    nonlinear_component += TARGET_NONLINEAR_WEIGHT * 0.65 * np.square(pre_l_data[:, important_pre_l_indices[3]]) * PRE_L_IMPORTANCE_FACTOR
    nonlinear_component += TARGET_NONLINEAR_WEIGHT * 0.75 * np.square(pre_s_data[:, important_pre_s_indices[2]]) * PRE_S_IMPORTANCE_FACTOR
    nonlinear_component += TARGET_NONLINEAR_WEIGHT * 0.7 * np.cos(pre_s_data[:, important_pre_s_indices[4]] * 1.5) * PRE_S_IMPORTANCE_FACTOR
    nonlinear_component += TARGET_NONLINEAR_WEIGHT * 0.5 * np.sin(qcp_data[:, important_qcp_indices[0]] * 2.0) * QCP_IMPORTANCE_FACTOR
    nonlinear_component += TARGET_NONLINEAR_WEIGHT * 0.45 * np.tanh(qcp_data[:, important_qcp_indices[3]]) * QCP_IMPORTANCE_FACTOR

    print("  - Adding interaction terms...")
    interaction_component = np.zeros(N_SAMPLES)
    interaction_component += TARGET_INTERACTION_WEIGHT * 0.4 * li_data[:, important_li_indices[0]] * li_data[:, important_li_indices[1]] * LI_IMPORTANCE_FACTOR
    interaction_component += TARGET_INTERACTION_WEIGHT * 0.35 * li_data[:, important_li_indices[2]] * li_data[:, important_li_indices[3]] * LI_IMPORTANCE_FACTOR
    interaction_component += TARGET_INTERACTION_WEIGHT * 0.3 * li_data[:, important_li_indices[4]] * pre_l_data[:, important_pre_l_indices[0]] * LI_IMPORTANCE_FACTOR
    interaction_component += TARGET_INTERACTION_WEIGHT * 0.25 * li_data[:, important_li_indices[5]] * pre_s_data[:, important_pre_s_indices[0]] * LI_IMPORTANCE_FACTOR
    interaction_component += TARGET_INTERACTION_WEIGHT * 0.7 * pre_l_data[:, important_pre_l_indices[1]] * pre_s_data[:, important_pre_s_indices[1]] * PRE_L_IMPORTANCE_FACTOR
    interaction_component += TARGET_INTERACTION_WEIGHT * 0.65 * pre_l_data[:, important_pre_l_indices[2]] * pre_s_data[:, important_pre_s_indices[2]] * PRE_S_IMPORTANCE_FACTOR
    interaction_component += TARGET_INTERACTION_WEIGHT * 0.4 * li_data[:, important_li_indices[8]] * qcp_data[:, important_qcp_indices[1]] * QCP_IMPORTANCE_FACTOR
    interaction_component += TARGET_INTERACTION_WEIGHT * 0.5 * pre_l_data[:, important_pre_l_indices[4]] * qcp_data[:, important_qcp_indices[2]] * QCP_IMPORTANCE_FACTOR
    interaction_component += TARGET_INTERACTION_WEIGHT * 0.45 * pre_s_data[:, important_pre_s_indices[5]] * qcp_data[:, important_qcp_indices[4]] * QCP_IMPORTANCE_FACTOR

    print("  - Adding quadratic terms...")
    quadratic_terms = np.zeros(N_SAMPLES)
    optimal_li_value = 0.5
    quadratic_terms += 0.25 * TARGET_NONLINEAR_WEIGHT * -(li_data[:, important_li_indices[4]] - optimal_li_value)**2 * LI_IMPORTANCE_FACTOR
    optimal_pre_l_value = 0.4
    quadratic_terms += 0.65 * TARGET_NONLINEAR_WEIGHT * -(pre_l_data[:, important_pre_l_indices[3]] - optimal_pre_l_value)**2 * PRE_L_IMPORTANCE_FACTOR
    optimal_pre_s_value = 0.6
    quadratic_terms += 0.7 * TARGET_NONLINEAR_WEIGHT * -(pre_s_data[:, important_pre_s_indices[1]] - optimal_pre_s_value)**2 * PRE_S_IMPORTANCE_FACTOR
    optimal_qcp_value = 0.55
    quadratic_terms += 0.5 * TARGET_NONLINEAR_WEIGHT * -(qcp_data[:, important_qcp_indices[2]] - optimal_qcp_value)**2 * QCP_IMPORTANCE_FACTOR

    print("  - Adding sigmoid terms...")
    sigmoid_term = 0.2 * TARGET_NONLINEAR_WEIGHT * (1 / (1 + np.exp(-8 * (li_data[:, important_li_indices[3]] - 0.5)))) * LI_IMPORTANCE_FACTOR
    sigmoid_term += 0.65 * TARGET_NONLINEAR_WEIGHT * (1 / (1 + np.exp(-8 * (pre_l_data[:, important_pre_l_indices[0]] - 0.5)))) * PRE_L_IMPORTANCE_FACTOR
    sigmoid_term += 0.7 * TARGET_NONLINEAR_WEIGHT * (1 / (1 + np.exp(-8 * (pre_s_data[:, important_pre_s_indices[0]] - 0.5)))) * PRE_S_IMPORTANCE_FACTOR
    sigmoid_term += 0.5 * TARGET_NONLINEAR_WEIGHT * (1 / (1 + np.exp(-8 * (qcp_data[:, important_qcp_indices[0]] - 0.6)))) * QCP_IMPORTANCE_FACTOR

    signal = (linear_component + nonlinear_component + interaction_component + quadratic_terms + sigmoid_term)
    
    def adjust_noise_for_target_r2(signal, target_r2=TARGET_R2):
        signal_var = np.var(signal)
        if signal_var == 0: return np.zeros_like(signal), 1.0 # Avoid division by zero
        if target_r2 >= 1.0: return np.zeros_like(signal), 1.0
        if target_r2 <= 0: target_r2 = 0.01 # Avoid invalid noise variance calculation
        
        required_noise_var = signal_var * (1/target_r2 - 1)
        if required_noise_var < 0: required_noise_var = 0 # Ensure non-negative variance
        required_noise_std = np.sqrt(required_noise_var)
        
        noise = np.random.normal(0, required_noise_std, N_SAMPLES)
        
        outlier_idx = np.random.choice(N_SAMPLES, size=int(N_SAMPLES * TARGET_OUTLIER_RATIO), replace=False)
        outlier_direction = np.random.choice([-1, 1], size=len(outlier_idx))
        noise[outlier_idx] += outlier_direction * np.abs(np.random.normal(0, TARGET_OUTLIER_SCALE * required_noise_std if required_noise_std > 0 else 0, size=len(outlier_idx)))
        
        target = signal + noise
        ss_total = np.sum((target - np.mean(target))**2)
        ss_residual = np.sum((target - signal)**2)
        
        if ss_total == 0: return noise, 1.0 # Avoid division by zero
        r2 = 1 - (ss_residual / ss_total)
        
        print(f"  - Target R2: {target_r2:.4f}, Achieved R2: {r2:.4f}")
        return noise, r2

    print("  - Adjusting noise to achieve target R2...")
    noise, achieved_r2 = adjust_noise_for_target_r2(signal)
    target = signal + noise

    print("  - Transforming target to normal distribution...")
    target_rank = stats.rankdata(target) / (len(target) + 1) # Add 1 to avoid exact 1.0
    target_normal = stats.norm.ppf(target_rank)
    target_normal = np.clip(target_normal, -4, 4)
    target_normal[~np.isfinite(target_normal)] = 0

    print("  - Scaling target to [0.1, 0.9] range...")
    target_min, target_max = np.min(target_normal), np.max(target_normal)
    if target_max == target_min: # Avoid division by zero if all values are the same
        target_scaled = np.full_like(target_normal, 0.5)
    else:
        target_scaled = 0.1 + 0.8 * (target_normal - target_min) / (target_max - target_min)

    median_value = np.median(target_scaled)
    print(f"  - Target median: {median_value:.4f} (목표: 0.5)")
    print(f"  - Target range: {np.min(target_scaled):.4f} to {np.max(target_scaled):.4f}")
    
    print("  - Verifying normal distribution (before scaling)...")
    _, p_value = stats.normaltest(target_normal)
    print(f"  - Normal distribution test p-value: {p_value:.4f}")
    
    # Final R2 calculation (approximation after scaling)
    signal_rank = stats.rankdata(signal) / (len(signal) + 1)
    signal_normal = stats.norm.ppf(signal_rank)
    signal_normal = np.clip(signal_normal, -4, 4)
    signal_min, signal_max = np.min(signal_normal), np.max(signal_normal)
    if signal_max == signal_min:
        signal_scaled = np.full_like(signal_normal, 0.5)
    else:
        signal_scaled = 0.1 + 0.8 * (signal_normal - signal_min) / (signal_max - signal_min)
        
    ss_total_scaled = np.sum((target_scaled - np.mean(target_scaled))**2)
    ss_residual_scaled = np.sum((target_scaled - signal_scaled)**2)
    if ss_total_scaled == 0:
        final_r2 = 1.0
    else:
        final_r2 = 1 - (ss_residual_scaled / ss_total_scaled)
    print(f"  - Final R2 after transformation (approx): {final_r2:.4f}")

    print(f"  - Target_F statistics: mean={np.mean(target_scaled):.4f}, std={np.std(target_scaled):.4f}")
    print(f"  - Target_F quantiles: 10%={np.quantile(target_scaled, 0.1):.4f}, 25%={np.quantile(target_scaled, 0.25):.4f}, 75%={np.quantile(target_scaled, 0.75):.4f}, 90%={np.quantile(target_scaled, 0.9):.4f}")

    return target_scaled

# --- Main Execution ---
if __name__ == "__main__":
    print("Generating feature data...")
    start_time = time.time()
    li_data, pre_l_data, pre_s_data, qcp_data = generate_correlated_features()
    feature_time = time.time() - start_time
    print(f"Feature generation completed in {feature_time:.2f} seconds")

    start_time = time.time()
    target = generate_target(li_data, pre_l_data, pre_s_data, qcp_data)
    target_time = time.time() - start_time
    print(f"Target generation completed in {target_time:.2f} seconds")

    # Create column names
    li_cols = [f'Li{i}' for i in range(1, 29)]
    pre_l_cols = [f'Pre_L{i}' for i in range(1, 33)]
    pre_s_cols = [f'Pre_S{i}' for i in range(1, 33)]
    qcp_cols = [f'Qcp{i}' for i in range(1, 31)]

    # Combine all features
    print("Combining features...")
    all_features = np.hstack([li_data, pre_l_data, pre_s_data, qcp_data])
    all_cols = li_cols + pre_l_cols + pre_s_cols + qcp_cols

    # Create unnormalized DataFrame
    print("Creating unnormalized dataframe...")
    df = pd.DataFrame(all_features, columns=all_cols)
    df['Target_F'] = target # Add the already scaled target

    # Generate and add lot_id column
    print("Generating lot_id...")
    today_str = datetime.now().strftime('%y%m%d')
    lot_ids = [f"{today_str}_{i+1:04d}" for i in range(N_SAMPLES)]
    df.insert(0, 'lot_id', lot_ids)

    # Save unnormalized data (with scaled Target_F)
    unnormalized_file = f'{OUTPUT_DIR}/unnormalized_data.csv'
    print(f"Saving unnormalized data to {unnormalized_file}...")
    df.to_csv(unnormalized_file, index=False)

    # Normalize all numeric columns (except target) to 0-1 range
    print("Normalizing numeric feature data...")
    scaler = MinMaxScaler()
    # Select only feature columns for scaling
    feature_cols_for_scaling = li_cols + pre_l_cols + pre_s_cols + qcp_cols
    df_normalized_features = pd.DataFrame(
        scaler.fit_transform(df[feature_cols_for_scaling]),
        columns=feature_cols_for_scaling
    )

    # Combine lot_id, normalized features, and the already-scaled target
    df_final = pd.concat([df[['lot_id']].reset_index(drop=True), df_normalized_features, df[['Target_F']].reset_index(drop=True)], axis=1)

    # Save normalized data
    normalized_file = f'{OUTPUT_DIR}/normalized_data.csv'
    print(f"Saving normalized data to {normalized_file}...")
    df_final.to_csv(normalized_file, index=False)

    print('Generated new dataset with controlled relationships and increased variance')
    print(f'Unnormalized data shape: {df.shape}')
    print(f'Normalized data shape: {df_final.shape}')
    print(f'Unnormalized data saved to: {unnormalized_file}')
    print(f'Normalized data saved to: {normalized_file}')
    print('Data generation complete!') 