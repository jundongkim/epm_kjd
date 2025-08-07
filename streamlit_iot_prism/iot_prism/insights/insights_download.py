import streamlit as st
import base64
import os
import tempfile
import markdown
import pdfkit
from datetime import datetime


def download_button_for_text(text, filename, button_text):
    """텍스트 데이터에 대한 다운로드 버튼을 생성하는 함수"""
    b64 = base64.b64encode(text.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{button_text}</a>'
    st.markdown(href, unsafe_allow_html=True)


def convert_markdown_to_pdf(markdown_content, filename):
    """마크다운 내용을 PDF로 변환하는 함수"""
    try:
        # base64 이미지 추출 및 처리
        import re
        import uuid
        
        # 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp()
        img_pattern = r'!\[.*?\]\(data:image\/png;base64,(.*?)\)'
        
        # 이미지 찾아서 저장하고 경로 대체
        def replace_image(match):
            img_data = match.group(1)
            img_binary = base64.b64decode(img_data)
            img_filename = f"img_{uuid.uuid4().hex}.png"
            img_path = os.path.join(temp_dir, img_filename)
            
            with open(img_path, 'wb') as f:
                f.write(img_binary)
                
            return f'<img src="{img_path}" alt="Chart Image">'
        
        # 이미지 경로 대체
        html_content = re.sub(img_pattern, replace_image, markdown_content)
        
        # 마크다운을 HTML로 변환
        html_content = markdown.markdown(html_content)
        
        # 스타일 추가
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 20px;
                    color: #333;
                }}
                h1 {{
                    color: #0D47A1;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #1976D2;
                }}
                h2 {{
                    color: #1976D2;
                    padding-bottom: 5px;
                    border-bottom: 1px solid #BBDEFB;
                    margin-top: 30px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #E3F2FD;
                    color: #0D47A1;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
                img {{
                    max-width: 100%;
                    display: block;
                    margin: 20px auto;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
                code {{
                    background-color: #f5f5f5;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: monospace;
                }}
                blockquote {{
                    border-left: 4px solid #1976D2;
                    margin: 20px 0;
                    padding: 10px 20px;
                    background-color: #E3F2FD;
                }}
                hr {{
                    border: 0;
                    height: 1px;
                    background-color: #ddd;
                    margin: 30px 0;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # 임시 HTML 파일 생성
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            f.write(styled_html.encode('utf-8'))
            html_temp = f.name
        
        # 임시 PDF 파일 경로
        pdf_temp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
        
        # HTML을 PDF로 변환 (옵션 추가)
        pdfkit_options = {
            'encoding': 'UTF-8',
            'page-size': 'A4',
            'margin-top': '1cm',
            'margin-right': '1cm',
            'margin-bottom': '1cm',
            'margin-left': '1cm',
            'enable-local-file-access': None  # 로컬 파일 접근 허용
        }
        pdfkit.from_file(html_temp, pdf_temp, options=pdfkit_options)
        
        # 임시 HTML 파일 제거
        os.unlink(html_temp)
        
        # PDF 파일 읽기
        with open(pdf_temp, 'rb') as f:
            pdf_data = f.read()
        
        # 임시 PDF 파일과 디렉토리 제거
        os.unlink(pdf_temp)
        
        # 이미지 파일 제거
        import shutil
        shutil.rmtree(temp_dir)
        
        return pdf_data
    except Exception as e:
        st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
        return None


def download_button_for_pdf(markdown_content, filename, button_text):
    """PDF 다운로드 버튼을 생성하는 함수"""
    if not markdown_content:
        st.warning("PDF로 변환할 내용이 없습니다.")
        return
    
    try:
        # 마크다운을 PDF로 바로 변환하지 않고, 버튼 클릭 시 변환
        if st.button(button_text):
            with st.spinner("PDF 파일 생성 중... 잠시만 기다려주세요."):
                try:
                    # 마크다운을 PDF로 변환
                    pdf_data = convert_markdown_to_pdf(markdown_content, filename)
                    
                    if pdf_data:
                        # Streamlit의 download_button 사용
                        st.download_button(
                            label="PDF 다운로드",
                            data=pdf_data,
                            file_name=filename,
                            mime="application/pdf"
                        )
                        st.success("PDF 생성 완료! 위 버튼을 클릭하여 다운로드하세요.")
                    else:
                        st.error("PDF 생성에 실패했습니다. 다시 시도해주세요.")
                        st.write("오류 상세 정보: PDF 데이터를 생성할 수 없습니다.")
                except Exception as e:
                    st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc(), language="python")
    except Exception as e:
        st.error(f"PDF 다운로드 버튼 생성 중 오류가 발생했습니다: {str(e)}")
        st.info("대안으로 마크다운 파일을 다운로드하여 외부 도구를 이용해 PDF로 변환할 수 있습니다.") 