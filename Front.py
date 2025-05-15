# coding: utf-8
# 사전 준비:
#   pip install customtkinter pillow

import os
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageSequence
import customtkinter as ctk
import shutil
import sys
from datetime import datetime
import excel_backend
import threading
from copy import copy
import logging
from logging.handlers import RotatingFileHandler
from logic.dataProcessing import DataProcessing

# 로깅 상태
LOGGING_ENABLED = False

# 로깅 설정
def setup_logging():
    global LOGGING_ENABLED
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # 현재 날짜와 시간으로 로그 파일명 생성
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"app_{current_time}.log")
    
    # 로거 설정
    logger = logging.getLogger("KedakLogger")
    logger.setLevel(logging.INFO)
    
    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    if LOGGING_ENABLED:
        # 파일 핸들러 설정 (최대 5MB, 최대 5개 파일 유지)
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # 핸들러 추가
        logger.addHandler(file_handler)
        
        # 백엔드 로거도 같은 핸들러 사용하도록 설정
        backend_logger = logging.getLogger("DataProcessing")
        backend_logger.setLevel(logging.INFO)
        backend_logger.addHandler(file_handler)
    else:
        # 로깅이 비활성화된 경우 NullHandler 추가
        logger.addHandler(logging.NullHandler())
        backend_logger = logging.getLogger("DataProcessing")
        backend_logger.addHandler(logging.NullHandler())
    
    return logger

# 로거 초기화
logger = setup_logging()

processor = DataProcessing()

# ─────────────────────────── 테마 설정 ───────────────────────────
# Light 모드 고정 및 컬러 테마 설정
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ─────────────────────────── 전역 상태 정의 ───────────────────────────
# STATE: READY(준비) / WORKING(작업중) 중앙 배경 이미지 전환
STATE = "READY"

# 파일 경로 저장
UPLOADED_FILES = {
    "main": None,
    "patients": None,
    "Paymentitems": None
}

# UI 요소 참조
UI_ELEMENTS = {
    "main_file_label": None,
    "patient_file_label": None,
    "payment_file_label": None,
    "main_cancel_btn": None,
    "patient_cancel_btn": None,
    "payment_cancel_btn": None,
    "main_upload_btn": None,
    "patient_upload_btn": None,
    "payment_upload_btn": None
}

# 이미지 캐시 (참조 유지용)
IMAGE_CACHE = {
    "active_frames": {},  # 활성화 상태 프레임 캐시
    "lock_frames": None,  # 잠금 프레임 (모든 버튼이 공유)
    "current_images": {}  # 현재 표시 중인 이미지 저장
}

# ─────────────────────────── 콜백 함수 정의 ───────────────────────────

def on_help():
    """도움말 창 표시"""
    logger.info("도움말 버튼 클릭")
    print("❓ 사용법")
    
    # 도움말 창 생성
    help_window = ctk.CTkToplevel(root)
    help_window.title("케이닥 마크7 4.0 사용법")
    help_window.geometry("600x700")
    help_window.resizable(False, False)
    
    # 스크롤 가능한 프레임 생성
    scroll_frame = ctk.CTkScrollableFrame(help_window, width=580, height=680)
    scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # 도움말 내용
    help_content = [
        ("🌟 프로그램 소개", """
        케이닥 마크7 4.0은 환자 정보와 결제 정보를 효율적으로 관리하는 프로그램입니다.
        메인 파일에 환자 정보와 결제 정보를 자동으로 업데이트하여 작업 시간을 단축시켜 줍니다.
        """),
        
        ("📁 파일 준비", """
        1. 메인 파일: 업데이트할 엑셀 파일입니다.
        2. 환자 파일: 'patients'로 시작하는 CSV 파일입니다.
        3. 결제 파일: 'PaymentItems'로 시작하는 CSV 파일입니다.
        """),
        
        ("🔧 기본 사용법", """
        1. 메인 파일 업로드
           - '업로드' 버튼을 클릭하여 메인 파일을 선택합니다.
           - 파일이 다른 프로그램에서 열려있지 않은지 확인합니다.
        
        2. 환자/결제 파일 업로드
           - 필요한 파일을 '업로드' 버튼으로 선택합니다.
           - 파일명이 올바른 형식인지 확인합니다.
        
        3. 원하는 기능 실행
           - 표 업데이트: 환자/결제 정보를 메인 파일에 업데이트
           - 환자 정보 업데이트: 환자 정보만 업데이트
           - 도표 업데이트: 선택한 달의 도표 생성
        """),
        
        ("⚠️ 주의사항", """
        1. 메인 파일이 다른 프로그램에서 열려있으면 작업이 불가능합니다.
        2. 파일 업로드 전에 파일명이 올바른 형식인지 확인하세요.
        3. 작업 중에는 프로그램을 종료하지 마세요.
        4. 중요한 파일은 자동으로 백업됩니다.
        """),
        
        ("💡 팁", """
        1. 로그 기능을 켜두면 문제 발생 시 원인 파악이 쉽습니다.
        2. 파일 업로드 후 상태 표시줄을 확인하세요.
        3. 작업 완료 후 엑셀 파일을 자동으로 열어볼 수 있습니다.
        """),
        
        ("❓ 문제 해결", """
        문제가 발생하면 다음을 확인하세요:
        1. 모든 파일이 올바른 형식인지
        2. 메인 파일이 다른 프로그램에서 열려있지 않은지
        3. 로그 파일에서 오류 메시지 확인
        """)
    ]
    
    # 도움말 내용 표시
    for title, content in help_content:
        # 제목
        title_label = ctk.CTkLabel(
            scroll_frame,
            text=title,
            font=("맑은 고딕", 14, "bold"),
            text_color="#333333"
        )
        title_label.pack(pady=(20,5), padx=10, anchor="w")
        
        # 내용
        content_label = ctk.CTkLabel(
            scroll_frame,
            text=content.strip(),
            font=("맑은 고딕", 12),
            text_color="#666666",
            justify="left",
            wraplength=550
        )
        content_label.pack(pady=(0,10), padx=20, anchor="w")
    
    # 닫기 버튼
    close_btn = ctk.CTkButton(
        help_window,
        text="닫기",
        font=("맑은 고딕", 12, "bold"),
        fg_color="#4CAF50",
        hover_color="#388E3C",
        text_color="white",
        corner_radius=8,
        width=100,
        height=35,
        command=help_window.destroy
    )
    close_btn.pack(pady=10)
    
    # 모달 창으로 설정
    help_window.transient(root)
    help_window.grab_set()
    root.wait_window(help_window)

def on_upload_main_file():
    """메인 파일 업로드"""
    logger.info("메인 파일 업로드 시작")
    file_path = filedialog.askopenfilename(
        title="메인 파일 선택",
        filetypes=(("Excel 파일", "*.xlsx"), ("CSV 파일", "*.csv"), ("모든 파일", "*.*")),
        defaultextension=".xlsx"
    )
    if file_path:
        # UPLOADED_FILES["main"] = file_path
        # main_file_name = os.path.basename(file_path)
        # logger.info(f"메인 파일 업로드 완료: {main_file_name}")
        
        # # 파일 정보 업데이트
        # update_file_labels()
        
        # 백업 생성
        try:
            # backup_dir = "BACK UP"
            # os.makedirs(backup_dir, exist_ok=True)
            # backup_file = os.path.join(backup_dir, f"BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{main_file_name}")
            # shutil.copy2(file_path, backup_file)
            # logger.info(f"메인 파일 백업 생성 완료: {backup_file}")
              # 파일이 다른 프로그램에서 열려있는지 확인
            if not check_file_access(file_path):
                logger.error(f"파일이 다른 프로그램에서 열려있음: {file_path}")
                messagebox.showerror("오류", f"파일이 다른 프로그램에서 열려있습니다.\n파일을 닫고 다시 시도해주세요: {file_path}")
                return
                
            UPLOADED_FILES["main"] = file_path
            main_file_name = os.path.basename(file_path)
            logger.info(f"메인 파일 업로드 완료: {main_file_name}")
            
            # 파일 정보 업데이트
            update_file_labels()
            
            # 백업 생성
            try:
                backup_dir = os.path.join(os.path.dirname(file_path), "BACK UP")
                os.makedirs(backup_dir, exist_ok=True)
                backup_file = os.path.join(backup_dir, f"BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{main_file_name}")
                shutil.copy2(file_path, backup_file)
                logger.info(f"메인 파일 백업 생성 완료: {backup_file}")
                messagebox.showinfo("백업 완료", f"메인 파일이 백업되었습니다.\n위치: {backup_file}")
            except Exception as e:
                logger.error(f"백업 생성 중 오류 발생: {str(e)}")
                messagebox.showwarning("백업 실패", f"파일 백업 중 오류가 발생했습니다: {str(e)}")
        except Exception as e:
            logger.error(f"파일 업로드 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"파일 업로드 중 오류가 발생했습니다: {str(e)}")
            UPLOADED_FILES["main"] = None
            update_file_labels()

def on_upload_patients_file():
    """환자 파일 업로드"""
    logger.info("환자 파일 업로드 시작")
    file_path = filedialog.askopenfilename(
        title="환자 파일 선택",
        filetypes=(("CSV 파일", "*.csv"), ("Excel 파일", "*.xlsx"), ("모든 파일", "*.*")),
        defaultextension=".csv"
    )
    if file_path:
        # 파일 이름이 'patients'로 시작하는지 확인
        file_name = os.path.basename(file_path).lower()
        if not file_name.startswith('patients'):
            logger.warning(f"잘못된 환자 파일 형식: {file_name}")
            messagebox.showwarning("파일 형식 오류", "환자 파일은 'patients'로 시작해야 합니다.")
            return
            
        UPLOADED_FILES["patients"] = file_path
        logger.info(f"환자 파일 업로드 완료: {file_name}")
        update_file_labels()

def on_upload_Paymentitems_file():
    """결제 파일 업로드"""
    logger.info("결제 파일 업로드 시작")
    file_path = filedialog.askopenfilename(
        title="결제 파일 선택",
        filetypes=(("CSV 파일", "*.csv"), ("Excel 파일", "*.xlsx"), ("모든 파일", "*.*")),
        defaultextension=".csv"
    )
    if file_path:
        # 대소문자 구분 없이 'paymentitems' 또는 'paymentItems'로 시작하는지 확인
        file_name = os.path.basename(file_path).lower()
        if not file_name.startswith('paymentitems'):
            logger.warning(f"잘못된 결제 파일 형식: {file_name}")
            messagebox.showwarning("파일 형식 오류", "결제 파일은 'PaymentItems' 또는 'Paymentitems'로 시작해야 합니다.")
            return
            
        UPLOADED_FILES["Paymentitems"] = file_path
        logger.info(f"결제 파일 업로드 완료: {file_name}")
        update_file_labels()

def on_table_update():
    """표 업데이트 기능 실행"""
    logger.info("표 업데이트 시작")
    
    # 메인 파일 존재 확인
    if not UPLOADED_FILES["main"]:
        logger.error("메인 파일 없음")
        messagebox.showerror("오류", "메인 파일을 찾을 수 없습니다. 파일을 먼저 업로드해주세요.")
        return
        
    # 필요한 파일 확인
    if not UPLOADED_FILES["patients"] and not UPLOADED_FILES["Paymentitems"]:
        logger.warning("Patients 파일과 Paymentitems 파일 모두 없음")
        messagebox.showwarning("파일 없음", "Patients 파일과 Paymentitems 파일이 모두 없습니다. 파일을 먼저 업로드해주세요.")
        return
        
    # 메인 파일 접근 가능 여부 확인
    if not check_file_access(UPLOADED_FILES["main"]):
        logger.error(f"메인 파일 접근 불가: {UPLOADED_FILES['main']}")
        messagebox.showerror("오류", f"메인 파일이 열려있거나 접근할 수 없습니다.\n파일을 닫고 다시 시도해주세요: {UPLOADED_FILES['main']}")
        return
    
    # 작업 시작 시 상태를 "WORKING"으로 변경
    update_center_image("WORKING")
    root.update()  # UI 즉시 업데이트
    
    try:
        # 환자 정보 업데이트 여부 확인
        update_patient_info = messagebox.askyesno("확인", "환자 정보도 같이 업데이트 하시겠습니까?")
        
        # ExcelBackend를 사용하여 표 업데이트 실행
        logger.info("백엔드 표 업데이트 작업 시작")
        logger.info(f"메인 파일: {UPLOADED_FILES['main']}")
        logger.info(f"환자 파일: {UPLOADED_FILES['patients']}")
        logger.info(f"결제 파일: {UPLOADED_FILES['Paymentitems']}")
        logger.info(f"환자 정보 업데이트: {update_patient_info}")
        
        result = processor.run_table_update(
            main_file=UPLOADED_FILES["main"],
            patients_file=UPLOADED_FILES["patients"],
            payment_file=UPLOADED_FILES["Paymentitems"],
            update_patient_info=update_patient_info
        )
        
        if result["success"]:
            logger.info(f"표 업데이트 성공: {result['msg']}")
            if "detail" in result:
                for key, value in result["detail"].items():
                    if isinstance(value, dict):
                        logger.info(f"- {key}: {value.get('msg', '')}")
            
            # 모든 작업이 완료된 후 엑셀 파일 열기 여부 확인
            if messagebox.askyesno("완료", "모든 업데이트가 완료되었습니다.\n엑셀 파일을 열어보시겠습니까?"):
                try:
                    os.startfile(UPLOADED_FILES["main"])
                except Exception as e:
                    logger.error(f"엑셀 파일 열기 실패: {str(e)}")
                    messagebox.showerror("오류", "엑셀 파일을 열 수 없습니다.")
            
            # 작업 완료 후 파일 상태 초기화
            UPLOADED_FILES["patients"] = None
            UPLOADED_FILES["Paymentitems"] = None
            update_file_labels()
        else:
            logger.error(f"표 업데이트 실패: {result['msg']}")
            messagebox.showerror("오류", result["msg"])
            
    except Exception as e:
        logger.error(f"표 업데이트 중 오류 발생: {str(e)}")
        messagebox.showerror("오류", f"표 업데이트 중 오류가 발생했습니다: {str(e)}")
    finally:
        # 작업 완료 후 원래 상태로 복원
        update_center_image("READY" if UPLOADED_FILES["main"] else "READY_NO_MAIN")

def on_patient_update():
    """환자 정보 업데이트 기능 실행"""
    logger.info("환자 정보 업데이트 시작")
    
    # 메인 파일 존재 확인
    if not UPLOADED_FILES["main"]:
        logger.error("메인 파일 없음")
        messagebox.showerror("오류", "메인 파일을 찾을 수 없습니다. 파일을 먼저 업로드해주세요.")
        return
        
    # 메인 파일 접근 가능 여부 확인
    if not check_file_access(UPLOADED_FILES["main"]):
        logger.error(f"메인 파일 접근 불가: {UPLOADED_FILES['main']}")
        messagebox.showerror("오류", f"메인 파일이 열려있거나 접근할 수 없습니다.\n파일을 닫고 다시 시도해주세요: {UPLOADED_FILES['main']}")
        return
    
    # 작업 시작 시 상태를 "WORKING"으로 변경
    update_center_image("WORKING")
    root.update()  # UI 즉시 업데이트
    
    try:
        # ExcelBackend를 사용하여 환자 정보 업데이트 실행
        logger.info("백엔드 환자 정보 업데이트 작업 시작")
        result = processor.run_patient_update(main_file=UPLOADED_FILES["main"])
        
        if result["success"]:
            logger.info(f"환자 정보 업데이트 성공: {result['msg']}")
            if "detail" in result:
                for key, value in result["detail"].items():
                    if isinstance(value, dict):
                        logger.info(f"- {key}: {value.get('msg', '')}")
            messagebox.showinfo("완료", result["msg"])
            # 작업 완료 후 파일 상태 초기화
            UPLOADED_FILES["patients"] = None
            update_file_labels()
        else:
            logger.error(f"환자 정보 업데이트 실패: {result['msg']}")
            messagebox.showerror("오류", result["msg"])
            
    except Exception as e:
        logger.error(f"환자 정보 업데이트 중 오류 발생: {str(e)}")
        messagebox.showerror("오류", f"환자 정보 업데이트 중 오류가 발생했습니다: {str(e)}")
    finally:
        # 작업 완료 후 원래 상태로 복원
        update_center_image("READY" if UPLOADED_FILES["main"] else "READY_NO_MAIN")

def on_exit():
    """프로그램 종료"""
    logger.info("프로그램 종료 시작")
    
    # 애니메이션 중지 플래그를 모든 버튼에 설정
    for frame in group.winfo_children():
        for widget in frame.winfo_children():
            if hasattr(widget, 'animation_running'):
                widget.animation_running = False
                widget.is_destroyed = True
            if hasattr(widget, 'after_id'):
                try:
                    widget.after_cancel(widget.after_id)
                except:
                    pass
    
    logger.info("프로그램 종료 완료")
    # 프로그램 완전 종료
    root.destroy()
    sys.exit(0)  # 프로세스 강제 종료

def on_chart_update():
    """도표 업데이트 버튼 클릭 시 실행되는 함수"""
    if not UPLOADED_FILES["main"]:
        messagebox.showerror("오류", "메인 파일을 먼저 업로드해주세요.")
        return
    
    # 메인 파일이 다른 프로그램에서 열려있는지 확인
    if not processor.check_file_access(UPLOADED_FILES["main"]):
        messagebox.showerror("오류", "메인 파일이 다른 프로그램에서 열려있습니다.\n파일을 닫고 다시 시도해주세요.")
        return
    
    # # UI 상태 업데이트
    # update_center_image("WORKING")
    # root.update()  # UI 즉시 업데이트
     # 달 선택 다이얼로그 생성
    month_dialog = ctk.CTkToplevel(root)
    month_dialog.title("달 선택")
    month_dialog.geometry("300x200")
    month_dialog.resizable(False, False)
    
    # try:
    #     # 백엔드 도표 업데이트 작업 실행
    #     logger.info("백엔드 도표 업데이트 작업 시작")
    #     result = processor.run_chart_update(main_file=UPLOADED_FILES["main"])
        
    #     if result["success"]:
    #         logger.info("도표 업데이트 성공")
    #         messagebox.showinfo("성공", result["msg"])
       # 현재 연도와 월 가져오기
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # 연도 선택
    year_frame = ctk.CTkFrame(month_dialog)
    year_frame.pack(pady=10)
    ctk.CTkLabel(year_frame, text="연도:").pack(side="left", padx=5)
    year_var = ctk.StringVar(value=str(current_year))
    year_entry = ctk.CTkEntry(year_frame, width=60, textvariable=year_var)
    year_entry.pack(side="left", padx=5)
    
    # 월 선택
    month_frame = ctk.CTkFrame(month_dialog)
    month_frame.pack(pady=10)
    ctk.CTkLabel(month_frame, text="월:").pack(side="left", padx=5)
    month_var = ctk.StringVar(value=str(current_month))
    month_combobox = ctk.CTkComboBox(month_frame, 
                                   values=[str(i) for i in range(1, 13)],
                                   width=60,
                                   variable=month_var)
    month_combobox.pack(side="left", padx=5)
    
    def on_confirm():
        try:
            selected_year = int(year_var.get())
            selected_month = int(month_var.get())
            
        #     # 엑셀 파일 열어볼지 물어보기
        #     if messagebox.askyesno("완료", "도표 업데이트가 완료되었습니다.\n엑셀 파일을 열어보시겠습니까?"):
        #         try:
        #             os.startfile(UPLOADED_FILES["main"])
        #         except Exception as e:
        #             logger.error(f"엑셀 파일 열기 실패: {str(e)}")
        #             messagebox.showerror("오류", "엑셀 파일을 열 수 없습니다.")
        # else:
        #     logger.error(f"도표 업데이트 실패: {result['msg']}")
        #     messagebox.showerror("오류", result["msg"])
            if not (1 <= selected_month <= 12):
                messagebox.showerror("오류", "올바른 월을 선택해주세요 (1-12)")
                return
                
            if selected_year < 2000 or selected_year > 2100:
                messagebox.showerror("오류", "올바른 연도를 입력해주세요 (2000-2100)")
                return
            
            month_dialog.destroy()
            
            # UI 상태 업데이트
            update_center_image("WORKING")
            root.update()  # UI 즉시 업데이트
            
            try:
                # 백엔드 도표 업데이트 작업 실행
                logger.info("백엔드 도표 업데이트 작업 시작")
                result = processor.run_chart_update(
                    main_file=UPLOADED_FILES["main"],
                    selected_year=selected_year,
                    selected_month=selected_month
                )
                
                if result["success"]:
                    logger.info("도표 업데이트 성공")
                    messagebox.showinfo("성공", result["msg"])
                    
                    # 엑셀 파일 열어볼지 물어보기
                    if messagebox.askyesno("완료", "도표 업데이트가 완료되었습니다.\n엑셀 파일을 열어보시겠습니까?"):
                        try:
                            os.startfile(UPLOADED_FILES["main"])
                        except Exception as e:
                            logger.error(f"엑셀 파일 열기 실패: {str(e)}")
                            messagebox.showerror("오류", "엑셀 파일을 열 수 없습니다.")
                else:
                    logger.error(f"도표 업데이트 실패: {result['msg']}")
                    messagebox.showerror("오류", result["msg"])
            
            except Exception as e:
                logger.error(f"도표 업데이트 중 오류 발생: {str(e)}")
                messagebox.showerror("오류", f"도표 업데이트 중 오류가 발생했습니다: {str(e)}")
            
            finally:
                # UI 상태 복원
                update_center_image("READY")
                
        except ValueError:
            messagebox.showerror("오류", "올바른 숫자를 입력해주세요")
    
    # except Exception as e:
    #     logger.error(f"도표 업데이트 중 오류 발생: {str(e)}")
    #     messagebox.showerror("오류", f"도표 업데이트 중 오류가 발생했습니다: {str(e)}")
     # 확인 버튼
    ctk.CTkButton(month_dialog, 
                 text="확인",
                 command=on_confirm).pack(pady=20)
    
    # finally:
    #     # UI 상태 복원
    #     update_center_image("READY")
    # 다이얼로그를 모달로 설정
    month_dialog.transient(root)
    month_dialog.grab_set()
    root.wait_window(month_dialog)

def toggle_logging():
    """로그 기록 토글"""
    global LOGGING_ENABLED
    LOGGING_ENABLED = not LOGGING_ENABLED
    setup_logging()  # 로거 재설정
    
    # 토글 버튼 상태 업데이트
    if LOGGING_ENABLED:
        log_toggle_btn.configure(text="📝 로그 켜짐", fg_color="#4CAF50", hover_color="#388E3C")
        logger.info("로그 기록이 활성화되었습니다.")
    else:
        log_toggle_btn.configure(text="📝 로그 꺼짐", fg_color="#BDBDBD", hover_color="#757575")
        print("로그 기록이 비활성화되었습니다.")

def on_log_view():
    """로그 파일 보기"""
    if not LOGGING_ENABLED:
        messagebox.showinfo("알림", "로그 기록이 비활성화되어 있습니다.")
        return
        
    log_dir = "logs"
    if os.path.exists(log_dir):
        try:
            # logs 디렉토리의 모든 로그 파일 목록 가져오기
            log_files = [f for f in os.listdir(log_dir) if f.startswith("app_") and f.endswith(".log")]
            if log_files:
                # 파일명의 날짜/시간 부분을 기준으로 정렬하여 가장 최근 파일 선택
                latest_log = sorted(log_files, reverse=True)[0]
                log_file = os.path.join(log_dir, latest_log)
                os.startfile(log_file)  # Windows에서 기본 텍스트 편집기로 열기
            else:
                messagebox.showwarning("알림", "로그 파일이 아직 생성되지 않았습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"로그 파일을 열 수 없습니다: {str(e)}")
    else:
        messagebox.showwarning("알림", "로그 디렉토리가 아직 생성되지 않았습니다.")

# ─────────────────── 중앙 이미지 업데이트 함수 ───────────────────

def update_center_image(new_state):
    """
    new_state 에 따라 중앙에 표시되는 이미지를 변경합니다.
    1) READY: 처리자 배경제거.png (메인 파일 있을 때)
    2) READY_NO_MAIN: 감시자 배경제거.png (메인 파일 없을 때)
    3) WORKING: 처리중 배경제거.png
    """
    global STATE, center_lbl, center_img
    STATE = new_state
    img_map = {
        "READY": "처리자 배경제거.png", 
        "READY_NO_MAIN": "감시자 배경제거.png",
        "WORKING": "처리중 배경제거.png"
    }
    img_file = os.path.join(ASSET_DIR, img_map[STATE])
    if os.path.exists(img_file):
        pil_img = Image.open(img_file)
        center_img = ctk.CTkImage(pil_img, size=(180,180))
        center_lbl.configure(image=center_img)
        center_lbl.image = center_img  # 참조 유지
    else:
        print(f"[경고] 이미지 파일 없음: {img_file}")

def check_file_access(file_path):
    """파일 접근 가능 여부 확인 (다른 프로세스에서 열려있는지 확인)"""
    if not os.path.exists(file_path):
        logger.error(f"파일이 존재하지 않음: {file_path}")
        return False
        
    try:
        # 파일이 다른 프로세스에 의해 잠겨있는지 확인
        with open(file_path, 'r+b') as f:
            return True
    except IOError:
        logger.error(f"파일이 다른 프로세스에 의해 잠겨 있음: {file_path}")
        return False

def setup_folders():
    """필요한 폴더를 생성합니다"""
    folders = ['DONE', 'BACK UP', 'SKIPPED']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"{folder} 폴더 생성 완료")

def update_file_labels():
    """파일 상태 레이블을 업데이트합니다"""
    # 필요한 폴더 생성
    setup_folders()
    
    # 파일 정보 가져오기
    main_file = os.path.basename(UPLOADED_FILES["main"]) if UPLOADED_FILES["main"] else None
    patients_file = os.path.basename(UPLOADED_FILES["patients"]) if UPLOADED_FILES["patients"] else None
    payment_items = os.path.basename(UPLOADED_FILES["Paymentitems"]) if UPLOADED_FILES["Paymentitems"] else None
    
    # 파일 감지 결과 출력
    file_summary = []
    if main_file:
        file_summary.append(f"메인: {main_file}")
    if patients_file:
        file_summary.append(f"Patients: {patients_file}")
    if payment_items:
        file_summary.append(f"Paymentitems: {payment_items}")
        
    if file_summary:
        logger.info(f"파일 업로드 결과: {', '.join(file_summary)}")
    
    # 메인 파일 UI 업데이트
    if main_file:
        # 파일이 업로드된 경우: 파일명 표시, 취소 버튼 표시
        UI_ELEMENTS["main_file_label"].configure(text=main_file)
        UI_ELEMENTS["main_cancel_btn"].pack(side="right", padx=(0,4))
        UI_ELEMENTS["main_file_label"].pack(side="right", padx=(0,4))
        # 메인 파일이 있을 때 "처리자 배경제거.png" 표시
        update_center_image("READY")
        # 업로드 버튼 숨기기
        UI_ELEMENTS["main_upload_btn"].pack_forget()
    else:
        # 파일이 없는 경우: 파일명 및 취소 버튼 숨김
        UI_ELEMENTS["main_file_label"].pack_forget()
        UI_ELEMENTS["main_cancel_btn"].pack_forget()
        # 업로드 버튼 표시
        UI_ELEMENTS["main_upload_btn"].pack(side="right")
        # 메인 파일이 없을 때 "감시자 배경제거.png" 표시
        update_center_image("READY_NO_MAIN")
    
    # 환자 파일 UI 업데이트
    if patients_file:
        # 파일이 업로드된 경우: 파일명 표시, 취소 버튼 표시
        UI_ELEMENTS["patient_file_label"].configure(text=patients_file)
        UI_ELEMENTS["patient_cancel_btn"].pack(side="right", padx=(0,4))
        UI_ELEMENTS["patient_file_label"].pack(side="right", padx=(0,4))
        # 업로드 버튼 숨기기
        UI_ELEMENTS["patient_upload_btn"].pack_forget()
    else:
        # 파일이 없는 경우: 파일명 및 취소 버튼 숨김
        UI_ELEMENTS["patient_file_label"].pack_forget()
        UI_ELEMENTS["patient_cancel_btn"].pack_forget()
        # 업로드 버튼 표시
        UI_ELEMENTS["patient_upload_btn"].pack(side="right")
    
    # 결제 파일 UI 업데이트
    if payment_items:
        # 파일이 업로드된 경우: 파일명 표시, 취소 버튼 표시
        UI_ELEMENTS["payment_file_label"].configure(text=payment_items)
        UI_ELEMENTS["payment_cancel_btn"].pack(side="right", padx=(0,4))
        UI_ELEMENTS["payment_file_label"].pack(side="right", padx=(0,4))
        # 업로드 버튼 숨기기
        UI_ELEMENTS["payment_upload_btn"].pack_forget()
    else:
        # 파일이 없는 경우: 파일명 및 취소 버튼 숨김
        UI_ELEMENTS["payment_file_label"].pack_forget()
        UI_ELEMENTS["payment_cancel_btn"].pack_forget()
        # 업로드 버튼 표시
        UI_ELEMENTS["payment_upload_btn"].pack(side="right")
        
    # 상태 레이블 업데이트
    if not main_file:
        status_lbl.configure(text="⚠️ 메인 파일 없음", text_color="red")
    elif not patients_file and not payment_items:
        status_lbl.configure(text="⚠️ 입력 파일 없음", text_color="orange")
    else:
        status_lbl.configure(text="준비 완료", text_color="black")
    
    # 버튼 상태 업데이트
    update_button_states(main_file, patients_file, payment_items)
    
    # 메인 파일 접근 가능 여부 확인 (파일이 다른 프로그램에서 열려있는지)
    if main_file and not check_file_access(UPLOADED_FILES["main"]):
        logger.error(f"메인 파일 접근 불가: {main_file}")
        messagebox.showerror("파일 접근 오류", f"메인 파일이 다른 프로그램에서 열려있어 접근할 수 없습니다.\n파일을 닫고 다시 시도해주세요: {main_file}")
        return False
    
    return True

def create_hover_button(parent, gif, cb, tip, col):
    """아이콘 GIF 애니메이션 및 호버 팝업 기능 설정"""
    global IMAGE_CACHE
    
    # GIF 파일 경로 저장
    gif_path = os.path.join(ICON_DIR, gif)
    lock_gif_path = os.path.join(ICON_DIR, "잠금.gif")
    
    # 잠금 프레임을 전역 캐시에 로드 (모든 버튼이 공유)
    if IMAGE_CACHE["lock_frames"] is None and os.path.exists(lock_gif_path):
        lock_pil = Image.open(lock_gif_path)
        IMAGE_CACHE["lock_frames"] = [ImageTk.PhotoImage(f.convert("RGBA").resize(icon_size, Image.LANCZOS)) 
                                      for f in ImageSequence.Iterator(lock_pil)]
        print(f"잠금 이미지 {len(IMAGE_CACHE['lock_frames'])}개 프레임 로드됨")
    
    # 활성화 상태의 GIF 로드
    if gif not in IMAGE_CACHE["active_frames"] and os.path.exists(gif_path):
        pil = Image.open(gif_path)
        IMAGE_CACHE["active_frames"][gif] = [ImageTk.PhotoImage(f.convert("RGBA").resize(icon_size, Image.LANCZOS)) 
                                            for f in ImageSequence.Iterator(pil)]
        print(f"{gif} 이미지 {len(IMAGE_CACHE['active_frames'][gif])}개 프레임 로드됨")
    
    # 버튼 컨테이너 생성
    cont = ctk.CTkFrame(master=parent, fg_color="white", corner_radius=16,
                        width=icon_size[0]+8, height=icon_size[1]+8,
                        border_width=1, border_color=BG)
    cont.grid(row=0, column=col, padx=2, pady=4)
    cont.pack_propagate(False)
    
    # 기본 프레임 설정
    active_frames = IMAGE_CACHE["active_frames"].get(gif, [])
    lock_frames = IMAGE_CACHE["lock_frames"] or []
    current_frames = active_frames if active_frames else lock_frames
    
    # 현재 이미지 참조 캐싱
    if current_frames:
        IMAGE_CACHE["current_images"][f"btn_{col}"] = current_frames[0]
        
    # 레이블(버튼) 생성
    lbl = tk.Label(cont, image=IMAGE_CACHE["current_images"].get(f"btn_{col}"), bg="white")
    lbl.btn_id = f"btn_{col}"  # 버튼 식별자
    lbl.gif_name = gif  # 원래 GIF 이름 저장
    lbl.pack(expand=True)
    popup=None
    
    # 비활성화 상태 저장 변수
    lbl.is_disabled = False
    
    def show_pop():
        nonlocal popup
        if popup: popup.destroy()
        if lbl.is_disabled: return  # 비활성화 상태면 팝업 표시 안함
        
        x = lbl.winfo_rootx() + lbl.winfo_width()//2
        y = lbl.winfo_rooty() - 40
        popup = ctk.CTkToplevel(root)
        popup.overrideredirect(True)
        popup.geometry(f"+{x}+{y}")
        ctk.CTkLabel(master=popup, text=tip,
                     fg_color="#ffe0b2", text_color="black",
                     corner_radius=8, font=("맑은 고딕",10,"bold"),
                     padx=8,pady=4).pack()
    
    def hide_pop():
        nonlocal popup
        if popup: popup.destroy(); popup=None
    
    def start_anim():
        # 현재 사용중인 프레임 결정
        frames = IMAGE_CACHE["active_frames"].get(lbl.gif_name, []) if not lbl.is_disabled else IMAGE_CACHE["lock_frames"]
        if not frames:
            return
            
        def anim(i=0): 
            if hasattr(lbl, 'is_destroyed') and lbl.is_destroyed:
                return
                
            # 애니메이션 중 비활성화 상태가 변경되었는지 확인
            current_frames = IMAGE_CACHE["active_frames"].get(lbl.gif_name, []) if not lbl.is_disabled else IMAGE_CACHE["lock_frames"]
            if current_frames != frames:
                # 프레임이 변경되었으면 애니메이션 중지하고 다시 시작
                stop_anim()
                start_anim()
                return
                
            # 현재 프레임으로 이미지 업데이트
            if frames and len(frames) > 0:
                lbl.config(image=frames[i])
                IMAGE_CACHE["current_images"][lbl.btn_id] = frames[i]  # 현재 이미지 캐싱
                lbl.after_id = lbl.after(SPEED, anim, (i+1)%len(frames))
        anim()
    
    def stop_anim():
        if hasattr(lbl,'after_id'): 
            lbl.after_cancel(lbl.after_id)
            
        # 프레임 선택
        frames = IMAGE_CACHE["active_frames"].get(lbl.gif_name, []) if not lbl.is_disabled else IMAGE_CACHE["lock_frames"]
        if frames and len(frames) > 0:
            lbl.config(image=frames[0])
            IMAGE_CACHE["current_images"][lbl.btn_id] = frames[0]  # 현재 이미지 캐싱
    
    def on_click(e):
        if lbl.is_disabled: return  # 비활성화 상태면 클릭 무시
        cb()
    
    # 버튼 활성화/비활성화 메서드 추가
    def enable():
        lbl.is_disabled = False
        lbl.configure(bg="white")  # 일반 배경색
        
        # 활성화 상태의 프레임 가져오기
        active_frames = IMAGE_CACHE["active_frames"].get(lbl.gif_name, [])
        if active_frames and len(active_frames) > 0:
            lbl.config(image=active_frames[0])
            IMAGE_CACHE["current_images"][lbl.btn_id] = active_frames[0]  # 현재 이미지 캐싱
            print(f"버튼 {col} ({lbl.gif_name}) 활성화됨")
        
        lbl.bind("<Enter>", lambda e:(start_anim(),show_pop()))
        lbl.bind("<Leave>", lambda e:(stop_anim(),hide_pop()))
        lbl.bind("<Button-1>", on_click)
    
    def disable():
        lbl.is_disabled = True
        lbl.configure(bg="white")  # 활성화 상태와 같은 배경색 유지
        
        # 잠금 프레임 사용
        if IMAGE_CACHE["lock_frames"] and len(IMAGE_CACHE["lock_frames"]) > 0:
            lbl.config(image=IMAGE_CACHE["lock_frames"][0])
            IMAGE_CACHE["current_images"][lbl.btn_id] = IMAGE_CACHE["lock_frames"][0]  # 현재 이미지 캐싱
            print(f"버튼 {col} ({lbl.gif_name}) 비활성화됨")
        
        # 비활성화 상태에서도 호버시 애니메이션은 지원
        lbl.bind("<Enter>", lambda e: start_anim())
        lbl.bind("<Leave>", lambda e: stop_anim())
        # 클릭은 비활성화
        lbl.unbind("<Button-1>")
        hide_pop()
    
    # 소멸자 대응
    def on_destroy():
        lbl.is_destroyed = True
        if hasattr(lbl, 'after_id'): 
            lbl.after_cancel(lbl.after_id)
    
    lbl.bind("<Destroy>", lambda e: on_destroy())
    
    # 기본적으로 활성화 상태로 시작 (종료 버튼)
    # 다른 버튼은 init_app에서 비활성화 설정
    lbl.enable = enable
    lbl.disable = disable
    enable()
    
    return lbl

def update_button_states(main_file, patients_file, payment_items):
    """파일 존재 여부에 따라 버튼 상태 업데이트"""
    logger.info(f"버튼 상태 업데이트 - 메인: {main_file}, 환자: {patients_file}, 결제: {payment_items}")
    
    # 버튼을 이름으로 찾기
    button_frames = group.winfo_children()
    if len(button_frames) < 4:
        logger.error("버튼 프레임을 찾을 수 없음")
        return

    # 각 버튼 프레임에서 라벨 찾기
    table_update_label = None
    patient_update_label = None
    chart_update_label = None
    
    for idx, frame in enumerate(button_frames):
        for widget in frame.winfo_children():
            if isinstance(widget, tk.Label):
                if idx == 0:  # 표 업데이트 버튼 (첫 번째)
                    table_update_label = widget
                elif idx == 1:  # 환자 정보 업데이트 버튼 (두 번째)
                    patient_update_label = widget
                elif idx == 2:  # 도표 업데이트 버튼 (세 번째)
                    chart_update_label = widget
    
    # 메인 파일이 있으면 환자 정보 업데이트 버튼과 도표 업데이트 버튼 활성화
    if main_file:
        logger.info("메인 파일 존재: 환자 정보 업데이트 버튼과 도표 업데이트 버튼 활성화")
        
        # 환자 정보 업데이트 버튼 활성화
        if patient_update_label and hasattr(patient_update_label, 'enable'):
            patient_update_label.enable()
            logger.info("환자 정보 업데이트 버튼 활성화됨")
        
        # 도표 업데이트 버튼 활성화
        if chart_update_label and hasattr(chart_update_label, 'enable'):
            chart_update_label.enable()
            logger.info("도표 업데이트 버튼 활성화됨")
        
        # 메인 파일과 Patients 또는 Paymentitems 파일 중 하나라도 있으면 표 업데이트 버튼 활성화
        if patients_file or payment_items:
            logger.info("Patients 또는 Paymentitems 파일 존재: 표 업데이트 버튼 활성화")
            if table_update_label and hasattr(table_update_label, 'enable'):
                table_update_label.enable()
        else:
            logger.info("Patients와 Paymentitems 파일 모두 없음: 표 업데이트 버튼 비활성화")
            if table_update_label and hasattr(table_update_label, 'disable'):
                table_update_label.disable()
    else:
        logger.info("메인 파일 없음: 세 버튼 모두 비활성화")
        if patient_update_label and hasattr(patient_update_label, 'disable'):
            patient_update_label.disable()
        if table_update_label and hasattr(table_update_label, 'disable'):
            table_update_label.disable()
        if chart_update_label and hasattr(chart_update_label, 'disable'):
            chart_update_label.disable()

def init_app():
    """앱 초기화: 기본 상태 설정"""
    logger.info("앱 초기화 시작")
    
    # 필요한 폴더 생성
    setup_folders()
    
    # 상태 레이블 초기화
    status_lbl.configure(text="파일 업로드가 필요합니다", text_color="#555555")
    
    # 기본 버튼 상태 설정 - 종료 버튼만 활성화하고 나머지는 비활성화
    button_frames = group.winfo_children()
    if len(button_frames) >= 4:
        # 표 업데이트, 환자 정보 업데이트, 도표 업데이트 버튼 비활성화
        for idx, frame in enumerate(button_frames):
            for widget in frame.winfo_children():
                if isinstance(widget, tk.Label):
                    if idx in [0, 1, 2] and hasattr(widget, 'disable'):  # 표 업데이트, 환자 정보, 도표 업데이트 버튼
                        widget.disable()
    
    # 초기 이미지는 메인 파일이 없는 상태인 "감시자 배경제거.png"로 설정
    update_center_image("READY_NO_MAIN")
    
    logger.info("앱 초기화 완료")

# ─────────────────────────── 메인 윈도우 설정 ───────────────────────────
BG = "#fff0e5"
root = ctk.CTk()
root.geometry("450x500")  # 세로 높이를 500으로 감소
root.title("케이닥 마크7 4.0")
root.configure(fg_color=BG)
root.resizable(False, False)  # 창 크기 조절 비활성화

# 1) 상단 타이틀
ctk.CTkLabel(
    master=root,
    text="🌟 케이닥 마크7 4.0 🌟",
    font=("맑은 고딕", 18, "bold"),
    text_color="black"
).pack(pady=(20,8))  # 상단 여백 감소

# 2) 도움말 버튼과 로그 버튼
help_frame = ctk.CTkFrame(master=root, fg_color="transparent")
help_frame.pack(fill="x", padx=16, pady=(0,8))  # 하단 여백 감소

# 로그 토글 버튼 추가
log_toggle_btn = ctk.CTkButton(
    master=help_frame,
    text="📝 로그 꺼짐",
    font=("맑은 고딕", 11, "bold"),
    fg_color="#BDBDBD",
    hover_color="#757575",
    text_color="white",
    corner_radius=12,
    width=100,
    height=30,
    command=toggle_logging
)
log_toggle_btn.pack(side="right", padx=(0,8))

# 도움말 버튼
ctk.CTkButton(
    master=help_frame,
    text="사용법",
    font=("맑은 고딕", 11, "bold"),
    fg_color="#ffe0b2",
    hover_color="#ffc8a2",
    text_color="black",
    corner_radius=12,
    width=60,
    height=30,
    command=on_help
).pack(side="right")

# 3) 중앙 이미지 표시 영역
ASSET_DIR = os.path.join(os.path.dirname(__file__), "power")
initial_img = os.path.join(ASSET_DIR, "처리자 배경제거.png")
if os.path.exists(initial_img):
    pil = Image.open(initial_img)
    center_img = ctk.CTkImage(pil, size=(180,180))  # 이미지 크기 감소
    center_lbl = ctk.CTkLabel(master=root, image=center_img, text="", fg_color="transparent")
    center_lbl.image = center_img
    center_lbl.pack(expand=True, pady=0)
else:
    tk.Frame(root, bg=BG).pack(expand=True, fill="both")

# 4) 하단 버튼 그룹 컨테이너
group = ctk.CTkFrame(master=root, fg_color="#FFF8E1", corner_radius=20,
                    border_width=1, border_color="#e0e0e0")
group.pack(side="bottom", fill="x", padx=16, pady=(0,8))  # 하단 여백 감소
for i in range(4): group.grid_columnconfigure(i, weight=1)  # 4개 버튼만 사용

# 5) 버튼 생성 및 애니메이션 + 팝업 설명
ICON_DIR = os.path.join(os.path.dirname(__file__), "icon")
icon_size = (64,64)
SPEED = 1000//60
buttons = [
    ("표 업데이트.gif", on_table_update, "표 업데이트"),
    ("환자 정보 업데이트.gif", on_patient_update, "환자 정보 업데이트"),
    ("도표 업데이트.gif", on_chart_update, "도표 업데이트"),
    ("종료.gif", on_exit, "종료"),
]

for idx,(g,cb,tip) in enumerate(buttons): create_hover_button(group, g, cb, tip, idx)

# 6) 상태 표시
status_frame = ctk.CTkFrame(master=root, fg_color="transparent")
status_frame.pack(side="bottom", fill="x", padx=16, pady=(0,8))  # 하단 여백 감소
# 상태 레이블 왼쪽 여백을 12px로 설정해 메인파일 카드와 동일한 간격 유지
status_lbl = ctk.CTkLabel(master=status_frame, text="(상태표시)", font=("맑은 고딕",11), text_color="#777777")
status_lbl.pack(side="left", padx=(12,0))

# 메인 파일 업로드 취소 함수
def cancel_main_file():
    UPLOADED_FILES["main"] = None
    update_file_labels()

# 환자 파일 업로드 취소 함수
def cancel_patients_file():
    UPLOADED_FILES["patients"] = None
    update_file_labels()

# 결제 파일 업로드 취소 함수
def cancel_Paymentitems_file():
    UPLOADED_FILES["Paymentitems"] = None
    update_file_labels()

# 7) 파일 업로드 카드
card = ctk.CTkFrame(master=root, fg_color="white", corner_radius=16, border_width=1, border_color="#e0e0e0")
card.pack(side="bottom", fill="x", padx=16, pady=(0,2))

# 메인 파일 업로드 행
main_row = ctk.CTkFrame(master=card, fg_color="transparent")
main_row.pack(fill="x", padx=12, pady=(5,2))
ctk.CTkLabel(master=main_row, text="메인파일:", font=("맑은 고딕",12), text_color="#333333").pack(side="left")

# 취소 버튼 (처음에는 보이지 않음)
main_cancel_btn = ctk.CTkButton(
    master=main_row,
    text="취소",
    font=("맑은 고딕", 10),
    fg_color="#BDBDBD",
    hover_color="#757575",
    text_color="white",
    corner_radius=8,
    width=50,
    height=25,
    command=cancel_main_file
)
main_cancel_btn.pack(side="right", padx=(0,4))
main_cancel_btn.pack_forget()  # 처음에는 숨김
UI_ELEMENTS["main_cancel_btn"] = main_cancel_btn

# 파일 이름 레이블 (처음에는 보이지 않음)
main_file_label = ctk.CTkLabel(master=main_row, text="", font=("맑은 고딕",12), text_color="#007BFF")
main_file_label.pack(side="right", padx=(0,4))
main_file_label.pack_forget()  # 처음에는 숨김
UI_ELEMENTS["main_file_label"] = main_file_label

# 메인 파일 업로드 버튼
main_upload_btn = ctk.CTkButton(
    master=main_row, 
    text="업로드", 
    font=("맑은 고딕", 10),
    fg_color="#4CAF50", 
    hover_color="#388E3C",
    text_color="white", 
    corner_radius=8,
    width=60, 
    height=25,
    command=on_upload_main_file
)
main_upload_btn.pack(side="right")
UI_ELEMENTS["main_upload_btn"] = main_upload_btn

# 환자 파일 업로드 행
patient_row = ctk.CTkFrame(master=card, fg_color="transparent")
patient_row.pack(fill="x", padx=12, pady=2)
ctk.CTkLabel(master=patient_row, text="환자파일:", font=("맑은 고딕",12), text_color="#333333").pack(side="left")

# 취소 버튼 (처음에는 보이지 않음)
patient_cancel_btn = ctk.CTkButton(
    master=patient_row,
    text="취소",
    font=("맑은 고딕", 10),
    fg_color="#BDBDBD",
    hover_color="#757575",
    text_color="white",
    corner_radius=8,
    width=50,
    height=25,
    command=cancel_patients_file
)
patient_cancel_btn.pack(side="right", padx=(0,4))
patient_cancel_btn.pack_forget()  # 처음에는 숨김
UI_ELEMENTS["patient_cancel_btn"] = patient_cancel_btn

# 파일 이름 레이블 (처음에는 보이지 않음)
patient_file_label = ctk.CTkLabel(master=patient_row, text="", font=("맑은 고딕",12), text_color="#007BFF")
patient_file_label.pack(side="right", padx=(0,4))
patient_file_label.pack_forget()  # 처음에는 숨김
UI_ELEMENTS["patient_file_label"] = patient_file_label

# 환자 파일 업로드 버튼
patient_upload_btn = ctk.CTkButton(
    master=patient_row, 
    text="업로드", 
    font=("맑은 고딕", 10),
    fg_color="#2196F3", 
    hover_color="#1976D2",
    text_color="white", 
    corner_radius=8,
    width=60, 
    height=25,
    command=on_upload_patients_file
)
patient_upload_btn.pack(side="right")
UI_ELEMENTS["patient_upload_btn"] = patient_upload_btn

# 결제 파일 업로드 행
payment_row = ctk.CTkFrame(master=card, fg_color="transparent")
payment_row.pack(fill="x", padx=12, pady=(2,5))
ctk.CTkLabel(master=payment_row, text="결제파일:", font=("맑은 고딕",12), text_color="#333333").pack(side="left")

# 취소 버튼 (처음에는 보이지 않음)
payment_cancel_btn = ctk.CTkButton(
    master=payment_row,
    text="취소",
    font=("맑은 고딕", 10),
    fg_color="#BDBDBD",
    hover_color="#757575",
    text_color="white",
    corner_radius=8,
    width=50,
    height=25,
    command=cancel_Paymentitems_file
)
payment_cancel_btn.pack(side="right", padx=(0,4))
payment_cancel_btn.pack_forget()  # 처음에는 숨김
UI_ELEMENTS["payment_cancel_btn"] = payment_cancel_btn

# 파일 이름 레이블 (처음에는 보이지 않음)
payment_file_label = ctk.CTkLabel(master=payment_row, text="", font=("맑은 고딕",12), text_color="#007BFF")
payment_file_label.pack(side="right", padx=(0,4))
payment_file_label.pack_forget()  # 처음에는 숨김
UI_ELEMENTS["payment_file_label"] = payment_file_label

# 결제 파일 업로드 버튼
payment_upload_btn = ctk.CTkButton(
    master=payment_row, 
    text="업로드", 
    font=("맑은 고딕", 10),
    fg_color="#FF9800", 
    hover_color="#F57C00",
    text_color="white", 
    corner_radius=8,
    width=60, 
    height=25,
    command=on_upload_Paymentitems_file
)
payment_upload_btn.pack(side="right")
UI_ELEMENTS["payment_upload_btn"] = payment_upload_btn

# 8) 시작시 앱 초기화
root.after(100, init_app)

root.mainloop()
