"""
애플리케이션 스타일시트 상수 정의
"""

# 색상 상수
COLOR_WAITING = "#D1D3D4"    # 다운로드 대기 / 메타데이터 로딩 중
COLOR_DOWNLOADING = "#DBC4F0" # 다운로드 중
COLOR_FINISHED = "#B8E8FC"    # 완료
COLOR_ERROR = "#FF0000"       # 실패
COLOR_PAUSED = "#FFE0B2"      # 일시정지 (살구색)

# 메인 윈도우 스타일
MAIN_WINDOW_STYLE = """
QMainWindow {
    background-color: transparent;
}
QWidget {
    color: #333333;
    font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
}
/* QScrollArea 스타일링 */
QScrollArea {
    background: transparent;
    border: none;
}
/* 스크롤바 스타일링 */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #D1D1D1;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { 
    background: #A8A8A8; 
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { 
    height: 0px; 
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { 
    background: none; 
}
"""

# 중앙 위젯 스타일
CENTRAL_WIDGET_STYLE = """
QWidget#CentralWidget {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 15px;
}
"""

# 타이틀 바 스타일
TITLE_BAR_STYLE = "background: transparent; border: none;"

# 최소화 버튼 스타일
MINIMIZE_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    color: #999999;
    border-radius: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #E8F4FD;
    color: #2196F3;
}
"""

# 닫기 버튼 스타일
CLOSE_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    color: #999999;
    border-radius: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #FFEEEE;
    color: #FF5252;
}
"""

# URL 입력 섹션 스타일
URL_INPUT_CONTAINER_STYLE = """
QFrame {
    background-color: #F8F9FA;
    border-radius: 10px;
}
"""

URL_INPUT_STYLE = """
QLineEdit {
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 0 12px;
    background-color: #FFFFFF;
    color: #333333;
}
QLineEdit:focus {
    border: 1px solid #5F428B;
    background-color: #FFFFFF;
}
"""

# 다운로드 버튼 스타일
DOWNLOAD_BUTTON_STYLE = """
QPushButton {
    background-color: #5F428B;
    color: #FFFFFF;
    border: none;
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
}
QPushButton:hover { background-color: #70529E; }
QPushButton:pressed { background-color: #4E3672; }
QPushButton:disabled { background-color: #E0E0E0; color: #A0A0A0; }
"""

# 설정 버튼 스타일
SETTINGS_BUTTON_STYLE = """
QPushButton {
    background-color: #EDEDED;
    color: #555555;
    border: none;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}
QPushButton:hover { background-color: #DCDCDC; }
QPushButton:pressed { background-color: #CFCFCF; }
"""

# 토글 버튼 스타일 (활성화)
TOGGLE_BUTTON_ENABLED_STYLE = """
QPushButton {
    border: none;
    background-color: #DBC4F0;
    color: #5F428B;
    border-radius: 20px;
    padding: 0px;
    margin: 0px;
    text-align: center;
}
QPushButton:hover { background-color: #C9A8E8; }
"""

# 토글 버튼 스타일 (비활성화/정지)
TOGGLE_BUTTON_DISABLED_STYLE = """
QPushButton {
    border: none;
    background-color: #FFE0B2;
    color: #E65100;
    border-radius: 20px;
    padding: 0px;
    margin: 0px;
    text-align: center;
}
QPushButton:hover { background-color: #FFCC80; }
"""

# 상태 표시줄 스타일
STATUS_BAR_STYLE = "background: transparent;"

STATUS_LABEL_STYLE = "color: #666666;"

# 프로그레스 슬라이더 스타일
PROGRESS_SLIDER_STYLE = """
QSlider::groove:horizontal {
    border: none;
    background: #E0E0E0;
    height: 4px;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #5F428B;
    height: 4px;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 0px; 
    height: 0px; 
    margin: 0; 
    background: transparent;
}
"""

# 선택 상태 색상
COLOR_SELECTED = "5F428B"  # 선택됨 (메인 테마 색상)

# 작업 카드 스타일
def get_card_style(color_hex, selected=False):
    """카드 테두리 스타일 생성
    
    Args:
        color_hex: 색상 코드 (예: "#D1D3D4" 또는 "D1D3D4")
        selected: 선택 상태 여부
    """
    # # 접두사가 없으면 추가
    if not color_hex.startswith('#'):
        color_hex = '#' + color_hex
    
    # 직접 위젯에 적용되므로 선택자 없이 스타일 정의
    if selected:
        # 선택된 상태: 배경색 변경 + 테두리 강조
        return f"""
background-color: #F3E8FF;
border: 4px solid #{COLOR_SELECTED};
border-radius: 8px;
"""
    else:
        return f"""
background-color: #FFFFFF;
border: 4px solid {color_hex};
border-radius: 8px;
"""

# 썸네일 라벨 스타일
THUMBNAIL_LABEL_STYLE = "background: #F0F0F0; border-radius: 4px; border: none; color: #888;"

# 제목 라벨 스타일
TITLE_LABEL_STYLE = "color: #333333; border: none; background: transparent;"

# 업로더 라벨 스타일
UPLOADER_LABEL_STYLE = "color: #888888; border: none; background: transparent;"

# 프로그레스 바 스타일
PROGRESS_BAR_STYLE = """
QProgressBar {
    border: none;
    background: #EAEAEA;
    border-radius: 3px;
}
QProgressBar::chunk {
    background-color: #5F428B;
    border-radius: 3px;
}
"""

# 프로그레스 바 스타일 (완료)
PROGRESS_BAR_FINISHED_STYLE = """
QProgressBar { border: none; background: #EAEAEA; border-radius: 3px; }
QProgressBar::chunk { background-color: #4CAF50; border-radius: 3px; }
"""

# 프로그레스 바 스타일 (실패)
PROGRESS_BAR_ERROR_STYLE = """
QProgressBar { border: none; background: #EAEAEA; border-radius: 3px; }
QProgressBar::chunk { background-color: #F44336; border-radius: 3px; }
"""

# 퍼센트 라벨 스타일
PERCENT_LABEL_STYLE = "color: #5F428B; border: none; background: transparent;"

# 상태 라벨 스타일
STATUS_LABEL_NORMAL_STYLE = "color: #666666; border: none; background: transparent;"
STATUS_LABEL_SUCCESS_STYLE = "color: #4CAF50; font-weight: bold; border: none; background: transparent;"
STATUS_LABEL_ERROR_STYLE = "color: #F44336; font-weight: bold; border: none; background: transparent;"
STATUS_LABEL_WARNING_STYLE = "color: #FF9800; font-weight: bold; border: none; background: transparent;"

# 크기 라벨 스타일
SIZE_LABEL_STYLE = "color: #999999; border: none; background: transparent;"

# 액션 버튼 스타일
def get_action_button_style(color="#555555"):
    """액션 버튼 스타일 생성"""
    return f"""
QPushButton {{
    background-color: #F5F5F5;
    color: {color};
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    font-family: 'Segoe UI Emoji';
    padding: 0px;
    margin: 0px;
}}
QPushButton:hover {{ background-color: #E0E0E0; }}
QPushButton:pressed {{ background-color: #D0D0D0; }}
"""

# 빈 상태 라벨 스타일
EMPTY_LABEL_STYLE = "color: #AAAAAA; padding: 20px;"

# ===== 설정 다이얼로그 스타일 =====

# 설정 다이얼로그 컨테이너 스타일
SETTINGS_CONTAINER_STYLE = """
QFrame#Container {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 15px;
}
QLabel {
    font-family: 'Segoe UI', sans-serif;
    color: #333333;
}
"""

# 설정 다이얼로그 타이틀 라벨 스타일
SETTINGS_TITLE_LABEL_STYLE = "color: #333333;"

# 설정 다이얼로그 닫기 버튼 스타일
SETTINGS_CLOSE_BUTTON_STYLE = """
QPushButton {
    background: transparent;
    border: none;
    color: #999999;
    border-radius: 12px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #FFEEEE;
    color: #FF5252;
}
"""

# 설정 다이얼로그 섹션 라벨 스타일
SETTINGS_SECTION_LABEL_STYLE = "color: #5F428B; margin-top: 10px; margin-bottom: 5px;"

# 설정 다이얼로그 일반 라벨 스타일
SETTINGS_LABEL_STYLE = "color: #555555;"

# 설정 다이얼로그 찾아보기 버튼 스타일
SETTINGS_BROWSE_BUTTON_STYLE = """
QPushButton {
    background-color: #F0F0F0;
    border: 1px solid #D0D0D0;
    border-radius: 6px;
    padding: 5px 10px;
    color: #555555;
    font-family: 'Segoe UI';
}
QPushButton:hover { background-color: #E0E0E0; }
QPushButton:pressed { background-color: #D0D0D0; }
"""

# 설정 다이얼로그 입력 필드 스타일
SETTINGS_INPUT_STYLE = """
QLineEdit, QSpinBox {
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 0 10px;
    background-color: #F9F9F9;
    color: #333333;
    font-family: 'Segoe UI';
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 20px;
}
"""

# 설정 다이얼로그 콤보박스 스타일
SETTINGS_COMBO_STYLE = """
QComboBox {
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 0 10px;
    background-color: #FFFFFF;
    color: #333333;
    font-family: 'Segoe UI';
}
QComboBox::drop-down {
    border: none;
    width: 25px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #666666;
    margin-right: 10px;
}
"""

# 설정 다이얼로그 체크박스 스타일
SETTINGS_CHECKBOX_STYLE = """
QCheckBox {
    font-family: 'Segoe UI';
    font-size: 10pt;
    color: #333333;
    spacing: 5px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
}
"""

# 설정 다이얼로그 취소 버튼 스타일
SETTINGS_CANCEL_BUTTON_STYLE = """
QPushButton {
    background-color: #F5F5F5;
    color: #666666;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    font-family: 'Segoe UI';
}
QPushButton:hover { background-color: #EEEEEE; }
"""

# 설정 다이얼로그 저장 버튼 스타일
SETTINGS_SAVE_BUTTON_STYLE = """
QPushButton {
    background-color: #5F428B;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    font-family: 'Segoe UI';
}
QPushButton:hover { background-color: #70529E; }
QPushButton:pressed { background-color: #4E3672; }
"""
