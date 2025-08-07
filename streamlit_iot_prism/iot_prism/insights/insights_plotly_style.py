import plotly.graph_objects as go
import numpy as np

def apply_insights_plotly_style(fig):
    """인사이트 모듈의 Plotly 차트에 공통 스타일을 적용합니다."""
    fig.update_layout(
        font=dict(family='Paperlogy, Noto Sans KR, sans-serif'),
        plot_bgcolor='rgba(240, 249, 255, 0.5)',
        paper_bgcolor='rgba(255, 255, 255, 1)',
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(200, 200, 200, 0.5)',
            borderwidth=1
        ),
        xaxis=dict(
            gridcolor='rgba(200, 200, 200, 0.2)',
            showline=True,
            linewidth=1,
            linecolor='rgba(200, 200, 200, 0.8)',
            mirror=True
        ),
        yaxis=dict(
            gridcolor='rgba(200, 200, 200, 0.2)',
            showline=True,
            linewidth=1,
            linecolor='rgba(200, 200, 200, 0.8)',
            mirror=True
        ),
        title=dict(
            font=dict(
                size=20,
                color='#0D47A1',
                family='Paperlogy, Noto Sans KR, sans-serif'
            ),
            x=0.5,
            xanchor='center'
        )
    )
    
    # 테마 색상 적용
    update_trace_colors(fig)
    
    return fig

def update_trace_colors(fig):
    """차트의 트레이스에 테마 색상을 적용합니다."""
    # 테마 색상 팔레트
    colors = [
        '#1976D2',  # 주요 색상 (파란색)
        '#FF5722',  # 보조 색상 (주황색)
        '#4CAF50',  # 녹색
        '#9C27B0',  # 보라색
        '#FFC107',  # 노란색
        '#795548',  # 갈색
        '#607D8B',  # 파란 회색
        '#E91E63',  # 핑크
        '#00BCD4',  # 청록색
        '#8BC34A'   # 연한 녹색
    ]
    
    trace_count = 0
    for trace in fig.data:
        if hasattr(trace, 'marker') and trace.marker:
            # 산점도, 막대 그래프 등 마커가 있는 그래프
            if trace.marker.color is None or isinstance(trace.marker.color, str):
                trace.marker.color = colors[trace_count % len(colors)]
        
        if hasattr(trace, 'line') and trace.line:
            # 선 그래프
            if trace.line.color is None or isinstance(trace.line.color, str):
                trace.line.color = colors[trace_count % len(colors)]
        
        # 특별한 트레이스 유형 처리
        if trace.type == 'bar':
            if not hasattr(trace, 'marker') or trace.marker is None:
                trace.marker = dict(color=colors[trace_count % len(colors)])
            else:
                trace.marker.color = colors[trace_count % len(colors)]
        
        trace_count += 1
    
    return fig

def create_insights_line_chart(df, x_col, y_col, title, show_markers=False, marker_size=5, line_width=2, include_trend=False):
    """인사이트 모듈용 선 차트를 생성합니다."""
    fig = go.Figure()
    
    # 메인 데이터 트레이스 추가
    mode = 'lines+markers' if show_markers else 'lines'
    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode=mode,
            name=y_col,
            line=dict(width=line_width),
            marker=dict(size=marker_size) if show_markers else None,
        )
    )
    
    # 추세선 추가 (선택 사항)
    if include_trend and len(df) > 1:
        x_numeric = np.arange(len(df))
        y_values = df[y_col].values
        model = np.polyfit(x_numeric, y_values, 1)
        trend_values = np.poly1d(model)(x_numeric)
        
        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=trend_values,
                mode='lines',
                name='추세선',
                line=dict(width=line_width, dash='dash')
            )
        )
    
    # 레이아웃 설정
    fig.update_layout(
        title=title,
        xaxis_title=x_col,
        yaxis_title=y_col,
        height=400
    )
    
    # 공통 스타일 적용
    apply_insights_plotly_style(fig)
    
    return fig

def create_insights_bar_chart(df, x_col, y_col, title, color=None, barmode='group'):
    """인사이트 모듈용 막대 차트를 생성합니다."""
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=df[x_col],
            y=df[y_col],
            name=y_col,
            marker_color=color
        )
    )
    
    # 레이아웃 설정
    fig.update_layout(
        title=title,
        xaxis_title=x_col,
        yaxis_title=y_col,
        height=400,
        barmode=barmode
    )
    
    # 공통 스타일 적용
    apply_insights_plotly_style(fig)
    
    return fig

def create_insights_pie_chart(labels, values, title):
    """인사이트 모듈용 파이 차트를 생성합니다."""
    fig = go.Figure()
    
    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            textinfo='percent+label',
            insidetextorientation='radial'
        )
    )
    
    # 레이아웃 설정
    fig.update_layout(
        title=title,
        height=400
    )
    
    # 공통 스타일 적용
    apply_insights_plotly_style(fig)
    
    return fig

def create_insights_histogram(df, column, nbins, title, show_kde=True):
    """인사이트 모듈용 히스토그램을 생성합니다."""
    fig = go.Figure()
    
    fig.add_trace(
        go.Histogram(
            x=df[column],
            nbinsx=nbins,
            name=column
        )
    )
    
    # KDE 추가 (선택 사항)
    if show_kde:
        from scipy import stats
        x_kde = np.linspace(df[column].min(), df[column].max(), 1000)
        kde = stats.gaussian_kde(df[column].dropna())
        y_kde = kde(x_kde)
        
        # 히스토그램에 맞게 KDE 스케일링
        hist_values, bin_edges = np.histogram(df[column], bins=nbins)
        scaling_factor = max(hist_values) / max(y_kde) if max(y_kde) > 0 else 1
        
        fig.add_trace(
            go.Scatter(
                x=x_kde,
                y=y_kde * scaling_factor,
                mode='lines',
                name='KDE',
                line=dict(width=2)
            )
        )
    
    # 레이아웃 설정
    fig.update_layout(
        title=title,
        xaxis_title=column,
        yaxis_title='빈도',
        height=400
    )
    
    # 공통 스타일 적용
    apply_insights_plotly_style(fig)
    
    return fig 