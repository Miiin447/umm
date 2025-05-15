# import os
# import shutil
# import logging
# from datetime import datetime, timedelta
# import pandas as pd
# from openpyxl import load_workbook
# from openpyxl.utils import range_boundaries, get_column_letter
# import re
# from copy import copy
# from openpyxl.styles import Border, Side
# from tkinter import messagebox

# # class ExcelBackend:
#     def __init__(self):
#         # 로거 설정
#         self.logger = logging.getLogger("ExcelBackend")
#         self.logger.setLevel(logging.DEBUG)
        
#         # 파일 핸들러 추가
#         log_dir = "logs"
#         os.makedirs(log_dir, exist_ok=True)
#         file_handler = logging.FileHandler(
#             os.path.join(log_dir, f'excel_backend_{datetime.now().strftime("%Y%m%d")}.log'),
#             encoding='utf-8'
#         )
#         file_handler.setLevel(logging.DEBUG)
        
#         # 콘솔 핸들러 추가
#         console_handler = logging.StreamHandler()
#         console_handler.setLevel(logging.INFO)
        
#         # 포맷터 설정
#         formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#         file_handler.setFormatter(formatter)
#         console_handler.setFormatter(formatter)
        
#         # 핸들러 추가
#         self.logger.addHandler(file_handler)
#         self.logger.addHandler(console_handler)
        
#         # 제외할 키워드 목록
#         self.excluded_keywords = {'heale', 'tele', 'develop', 'test', 'patient', 'kdoc', 'k-doc', 'k- doc'}
#         self.logger.info("ExcelBackend 초기화 완료")

#     def should_exclude_row(self, row_data):
#         """행을 제외해야 하는지 확인하는 함수"""
#         # pandas Series를 딕셔너리로 변환
#         if isinstance(row_data, pd.Series):
#             row_dict = row_data.to_dict()
#         else:
#             row_dict = row_data
            
#         for value in row_dict.values():
#             if isinstance(value, str):
#                 value_lower = value.lower()
#                 if any(keyword in value_lower for keyword in self.excluded_keywords):
#                     return True
#         return False

#     def standardize_value(self, val, preserve_format=False):
#         if val is None:
#             return ""
#         try:
#             dt = pd.to_datetime(val, errors='coerce')
#             if pd.notnull(dt):
#                 return f"{dt.year}년 {dt.month}월 {dt.day}일"
#         except:
#             pass
        
#         # 이름이나 의사명인 경우 원본 형식 유지
#         if preserve_format:
#             return str(val).strip()
            
#         return re.sub(r'[^a-zA-Z0-9가-힣]', '', str(val).lower())

#     def standardize_date(self, date_value):
#         if not date_value or pd.isna(date_value):
#             return None
#         try:
#             if isinstance(date_value, datetime):
#                 return f"{date_value.year}년 {date_value.month}월 {date_value.day}일"
#             if isinstance(date_value, str):
#                 date_str = str(date_value).strip()
#                 if "년" in date_str and "월" in date_str and "일" in date_str:
#                     return date_str
#                 # 한글 날짜 형식 처리 (예: "4월 1, 2024")
#                 if "월" in date_str and "," in date_str:
#                     try:
#                         month = int(date_str.split("월")[0])
#                         day = int(date_str.split(",")[0].split("월")[1].strip())
#                         year = int(date_str.split(",")[1].strip())
#                         return f"{year}년 {month}월 {day}일"
#                     except Exception as e:
#                         self.logger.warning(f"한글 날짜 형식 변환 실패: {date_str} -> {str(e)}")
#                 # 숫자 형식 날짜 처리 (예: 2024-04-01)
#                 try:
#                     dt = pd.to_datetime(date_str, errors='coerce')
#                     if pd.notnull(dt):
#                         return f"{dt.year}년 {dt.month}월 {dt.day}일"
#                 except:
#                     pass
#             return None
#         except Exception as e:
#             self.logger.warning(f"날짜 정규화 실패: {date_value} -> {str(e)}")
#             return None

#     def check_file_access(self, file_path):
#         if not os.path.exists(file_path):
#             self.logger.error(f"파일이 존재하지 않습니다: {file_path}")
#             return False
#         try:
#             with open(file_path, 'r+b') as f:
#                 return True
#         except IOError:
#             self.logger.warning(f"파일이 다른 프로세스에 의해 잠겨 있습니다: {file_path}")
#             return False

#     def find_table(self, table_name, workbook_or_sheet):
#         """테이블 찾기 함수 개선 (워크북 또는 시트 모두 지원)"""
#         self.logger.info(f"테이블 찾기 시작: {table_name}")
#         # 시트 객체가 들어오면 그 시트에서만 찾기
#         if hasattr(workbook_or_sheet, 'tables') and hasattr(workbook_or_sheet, 'title'):
#             for table in workbook_or_sheet.tables.values():
#                 self.logger.debug(f"테이블 이름: {table.name}")
#                 if table_name in table.name:
#                     self.logger.info(f"테이블 찾음: {table.name} (시트: {workbook_or_sheet.title})")
#                     return table
#             self.logger.warning(f"테이블을 찾을 수 없음: {table_name}")
#             return None
#         # 워크북 객체면 전체 시트에서 찾기
#         for sheet in workbook_or_sheet.worksheets:
#             self.logger.debug(f"시트 검색 중: {sheet.title}")
#             for table in sheet.tables.values():
#                 self.logger.debug(f"테이블 이름: {table.name}")
#                 if table_name in table.name:
#                     self.logger.info(f"테이블 찾음: {table.name} (시트: {sheet.title})")
#                     return table
#         self.logger.warning(f"테이블을 찾을 수 없음: {table_name}")
#         return None

#     def process_patients_file(self, main_file, patients_file):
#         try:
#             self.logger.info(f"환자 파일 처리 시작: {patients_file}")
            
#             wb = load_workbook(main_file)
#             patients_df = pd.read_csv(patients_file)
#             self.logger.debug(f"CSV 파일 로드 완료: {len(patients_df)} 행")
#             self.logger.debug(f"CSV 컬럼 목록: {patients_df.columns.tolist()}")
            
#             # 제외된 행 수 카운트
#             excluded_count = 0
            
#             # 제외 키워드가 포함된 행 제거
#             for idx, row in patients_df.iterrows():
#                 if self.should_exclude_row(row):
#                     self.logger.info(f"제외 키워드가 포함된 행 제거: {row.get('이름', '')}")
#                     patients_df = patients_df.drop(idx)
#                     excluded_count += 1
            
#             self.logger.info(f"제외된 행 수: {excluded_count}")
            
#             # 등록 날짜 형식 통일
#             if '등록 날짜' in patients_df.columns:
#                 patients_df['등록 날짜'] = patients_df['등록 날짜'].apply(self.standardize_date)
#                 self.logger.info("등록 날짜 형식 통일 완료")
            
#             table = self.find_table("환자자동", wb)
#             if not table:
#                 self.logger.error("환자자동 테이블을 찾을 수 없음")
#                 return {"success": False, "msg": "환자자동 테이블 없음"}
            
#             patients_sheet = None
#             for sheet in wb.worksheets:
#                 if table in sheet.tables.values():
#                     patients_sheet = sheet
#                     break
            
#             if not patients_sheet:
#                 self.logger.error("환자자동 테이블이 있는 시트를 찾을 수 없음")
#                 return {"success": False, "msg": "환자자동 테이블이 있는 시트를 찾을 수 없음"}

#             min_col, min_row, max_col, max_row = range_boundaries(table.ref)
#             excel_headers = {}
#             col_to_letter = {}
            
#             for col in range(min_col, max_col + 1):
#                 cell_value = patients_sheet.cell(row=min_row, column=col).value
#                 if cell_value:
#                     header_name = str(cell_value).strip()
#                     excel_headers[header_name] = col
#                     col_to_letter[header_name] = get_column_letter(col)
#                     self.logger.debug(f"헤더 매핑: {header_name} -> 열 {col} (열 문자: {get_column_letter(col)})")
            
#             # 중복 데이터 체크를 위한 컬럼 찾기
#             name_col = excel_headers.get("이름")
#             dob_col = excel_headers.get("생년월일")
#             reg_date_col = excel_headers.get("등록 날짜")
#             state_col = excel_headers.get("주")
#             age_range_col = excel_headers.get("Age_Range") or excel_headers.get("연령대")
#             age_col = excel_headers.get("Age") or excel_headers.get("나이")
#             gender_col = excel_headers.get("성별")

#             # 컬럼 찾기 상세 로깅
#             self.logger.info("\n=== 환자자동 테이블 컬럼 정보 ===")
#             self.logger.info(f"엑셀 헤더 전체 목록: {excel_headers}")
#             self.logger.info(f"이름 열: {name_col} ({col_to_letter.get('이름', '?')})")
#             self.logger.info(f"등록 날짜 열: {reg_date_col} ({col_to_letter.get('등록 날짜', '?')})")
#             self.logger.info(f"주 열: {state_col} ({col_to_letter.get('주', '?')})")
#             self.logger.info(f"생년월일 열: {dob_col} ({col_to_letter.get('생년월일', '?')})")
#             self.logger.info(f"연령대 열: {age_range_col} ({col_to_letter.get('Age_Range', col_to_letter.get('연령대', '?'))})")
#             self.logger.info(f"나이 열: {age_col} ({col_to_letter.get('Age', col_to_letter.get('나이', '?'))})")
#             self.logger.info(f"성별 열: {gender_col} ({col_to_letter.get('성별', '?')})")
            
#             # 기존 데이터 수집 (이름, 생년월일, 성별, 주만으로 중복 체크)
#             existing_records = set()
#             for row in range(min_row + 1, max_row + 1):
#                 name = self.standardize_value(patients_sheet.cell(row=row, column=name_col).value, preserve_format=True)
#                 dob = self.standardize_value(patients_sheet.cell(row=row, column=dob_col).value, preserve_format=True) if dob_col else ""
#                 gender = self.standardize_value(patients_sheet.cell(row=row, column=gender_col).value, preserve_format=True) if gender_col else ""
#                 state = self.standardize_value(patients_sheet.cell(row=row, column=state_col).value, preserve_format=True) if state_col else ""
#                 record = (name, dob, gender, state)
#                 existing_records.add(record)
#                 self.logger.debug(f"기존 데이터 수집(이름,생년월일,성별,주): {record}")

#             added_count = 0
#             skipped_count = 0
            
#             for idx, row in patients_df.iterrows():
#                 name = self.standardize_value(row.get("이름", ""), preserve_format=True)
#                 dob = self.standardize_value(row.get("생년월일", ""), preserve_format=True)
#                 gender = self.standardize_value(row.get("성별", ""), preserve_format=True)
#                 state = self.standardize_value(row.get("현재 있는 주", ""), preserve_format=True)
#                 record = (name, dob, gender, state)
#                 if record in existing_records:
#                     self.logger.info(f"중복 데이터 건너뛰기: {name} (이름,생년월일,성별,주 동일)")
#                     skipped_count += 1
#                     continue
                
#                 self.logger.info(f"\n=== 새로운 환자 데이터 처리 ===")
#                 self.logger.info(f"이름: {name}")
#                 self.logger.info(f"생년월일: {dob}")
#                 self.logger.info(f"주: {state}")
#                 self.logger.info(f"성별: {gender}")
                    
#                 max_row += 1
#                 for header, col in excel_headers.items():
#                     value = row.get(header, "")
#                     # '주' 컬럼에 '현재 있는 주' 데이터 매핑
#                     if header == "주":
#                         value = row.get("현재 있는 주", "")
#                     cell = patients_sheet.cell(row=max_row, column=col)
                    
#                     if header == "등록 날짜" and value:
#                         cell.value = value  # 이미 표준화된 형식
#                     else:
#                         cell.value = value
                    
#                     if max_row > min_row + 1:
#                         try:
#                             source_cell = patients_sheet.cell(row=min_row + 1, column=col)
#                             if source_cell.has_style:
#                                 cell.font = copy(source_cell.font)
#                                 cell.fill = copy(source_cell.fill)
#                                 cell.border = copy(source_cell.border)
#                                 cell.alignment = copy(source_cell.alignment)
#                                 cell.number_format = source_cell.number_format
#                         except Exception as e:
#                             self.logger.warning(f"셀 스타일 복사 실패 (행: {max_row}, 열: {col}): {str(e)}")
                
#                 # 나이와 연령대 계산 및 추가
#                 if dob_col:  # 생년월일 컬럼이 있는 경우
#                     birth_date = patients_sheet.cell(row=max_row, column=dob_col).value
#                     self.logger.info(f"\n=== 나이/연령대 계산 시작 ===")
#                     self.logger.info(f"생년월일 데이터: {birth_date}")
                    
#                     # 나이 계산
#                     age = None
#                     if birth_date and not pd.isna(birth_date):
#                         age = self.calculate_age_from_birthdate(birth_date)
#                         self.logger.info(f"생년월일로 계산된 나이: {age}")
                    
#                     # 나이와 연령대 입력
#                     if age is not None:
#                         # 나이 입력
#                         if age_col:
#                             age_cell = patients_sheet.cell(row=max_row, column=age_col)
#                             age_cell.value = age  # 숫자 그대로 입력
#                             self.logger.info(f"나이 입력 완료: {age}세 (열: {age_col})")
                        
#                         # 연령대 입력
#                         if age_range_col:
#                             age_range = self.get_age_range(age)
#                             self.logger.info(f"계산된 연령대: {age_range}")
#                             age_range_cell = patients_sheet.cell(row=max_row, column=age_range_col)
#                             age_range_cell.value = age_range  # 문자열 그대로 입력
#                             self.logger.info(f"연령대 입력 완료: {age_range} (열: {age_range_col})")
#                     else:
#                         self.logger.warning("나이를 계산할 수 없어 연령대를 입력하지 않음")
                
#                 added_count += 1
#                 existing_records.add(record)
#                 self.logger.info(f"환자 데이터 추가 완료 (행: {max_row})")

#             # 빈 행 삭제
#             empty_rows = []
#             for row in range(min_row + 1, max_row + 1):
#                 is_empty = True
#                 for col in range(min_col, max_col + 1):
#                     if patients_sheet.cell(row=row, column=col).value:
#                         is_empty = False
#                         break
#                 if is_empty:
#                     empty_rows.append(row)

#             # 다른 행이 없는 경우에만 첫 번째 행 보존
#             if len(empty_rows) == max_row - min_row:
#                 empty_rows.remove(min_row + 1)  # 첫 번째 행은 보존

#             # 빈 행 삭제 (역순으로 삭제하여 인덱스 변화 방지)
#             for row in sorted(empty_rows, reverse=True):
#                 patients_sheet.delete_rows(row)
#                 max_row -= 1

#             if added_count > 0:
#                 table.ref = f"{get_column_letter(min_col)}{min_row}:{get_column_letter(max_col)}{max_row}"
#             wb.save(main_file)
            
#             self.logger.info(f"환자 처리 완료: {added_count}명 추가, {skipped_count}명 중복, {excluded_count}명 제외")
#             return {"success": True, "msg": f"환자 {added_count}명 추가, 중복 {skipped_count}명, 제외 {excluded_count}명"}
#         except Exception as e:
#             self.logger.error(f"환자 파일 처리 중 오류 발생: {str(e)}", exc_info=True)
#             return {"success": False, "msg": str(e)}

#     def process_PaymentItems_items(self, main_file, PaymentItems_file):
#         try:
#             self.logger.info(f"결제 항목 파일 처리 시작: {PaymentItems_file}")
            
#             wb = load_workbook(main_file)
#             self.logger.debug("엑셀 파일 로드 완료")
            
#             encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-16']
#             df = None
            
#             for encoding in encodings:
#                 try:
#                     self.logger.debug(f"CSV 파일 읽기 시도 (인코딩: {encoding})")
#                     df = pd.read_csv(PaymentItems_file, encoding=encoding)
#                     self.logger.info(f"CSV 파일 로드 성공 (인코딩: {encoding})")
#                     break
#                 except UnicodeDecodeError:
#                     continue
#                 except Exception as e:
#                     self.logger.error(f"CSV 파일 읽기 실패 (인코딩: {encoding}): {str(e)}")
#                     continue
            
#             if df is None:
#                 self.logger.error("지원되는 인코딩으로 CSV 파일을 읽을 수 없음")
#                 return {"success": False, "msg": "CSV 파일을 읽을 수 없음"}
            
#             self.logger.info(f"CSV 컬럼 목록: {df.columns.tolist()}")
            
#             # 필요한 컬럼만 매핑
#             column_mapping = {
#                 '날짜': '등록날짜',
#                 '환자': '환자 명',
#                 '의료인 이름': '진단 의사명'
#             }
            
#             df = df.rename(columns=column_mapping)
            
#             # 날짜 데이터 전처리
#             if '등록날짜' in df.columns:
#                 # 원본 날짜 데이터를 datetime으로 변환
#                 df['원본_날짜'] = pd.to_datetime(df['등록날짜'], errors='coerce')
#                 # 표시용 날짜 형식으로 변환 (시간 포함)
#                 df['등록날짜'] = df['원본_날짜'].apply(
#                     lambda x: x.strftime('%Y년 %m월 %d일 %H:%M:%S') if pd.notnull(x) else None
#                 )
#             else:
#                 self.logger.error("날짜 컬럼을 찾을 수 없음")
#                 return {"success": False, "msg": "날짜 컬럼을 찾을 수 없음"}
            
#             # 환자명과 의사명 정규화
#             for col in ['환자 명', '진단 의사명']:
#                 if col in df.columns:
#                     df[col] = df[col].apply(lambda x: self.standardize_value(x, preserve_format=True) if pd.notnull(x) else '')
            
#             # 환불 처리: 음수 금액이 있는 행 찾기
#             refund_rows = df[df['양'] < 0].copy()
#             if not refund_rows.empty:
#                 self.logger.info(f"환불 데이터 {len(refund_rows)}건 발견")
                
#                 # 환불 처리할 행 찾기
#                 for _, refund_row in refund_rows.iterrows():
#                     refund_amount = abs(refund_row['양'])
#                     refund_date = refund_row['원본_날짜']
                    
#                     # 같은 환자, 같은 의사, 같은 금액의 양수 거래 찾기
#                     matching_rows = df[
#                         (df['환자 명'] == refund_row['환자 명']) &
#                         (df['진단 의사명'] == refund_row['진단 의사명']) &
#                         (df['양'] == refund_amount)
#                     ]
                    
#                     if not matching_rows.empty:
#                         # 날짜 차이 계산
#                         matching_rows['날짜_차이'] = abs(matching_rows['원본_날짜'] - refund_date)
#                         # 가장 가까운 날짜의 거래 선택
#                         closest_row = matching_rows.loc[matching_rows['날짜_차이'].idxmin()]
                        
#                         # 매칭되는 행 제외
#                         df = df.drop(closest_row.name)
#                         self.logger.info(f"환불 처리: {refund_row['환자 명']} - {refund_amount}원 (날짜 차이: {closest_row['날짜_차이'].days}일)")
            
#             # 원본 날짜 컬럼 삭제
#             df = df.drop('원본_날짜', axis=1)
            
#             table = self.find_table("고객관리자동", wb)
#             if not table:
#                 self.logger.error("고객관리자동 테이블을 찾을 수 없음")
#                 return {"success": False, "msg": "고객관리자동 테이블 없음"}
            
#             sheet = None
#             for ws in wb.worksheets:
#                 if table in ws.tables.values():
#                     sheet = ws
#                     break
            
#             if not sheet:
#                 self.logger.error("고객관리자동 테이블이 있는 시트를 찾을 수 없음")
#                 return {"success": False, "msg": "고객관리자동 테이블이 있는 시트를 찾을 수 없음"}

#             min_col, min_row, max_col, max_row = range_boundaries(table.ref)
#             headers = []
#             for col in range(min_col, max_col + 1):
#                 cell_value = sheet.cell(row=min_row, column=col).value
#                 headers.append(cell_value if cell_value else '')
            
#             self.logger.debug(f"엑셀 테이블 헤더: {headers}")
            
#             column_indices = {}
#             for header in column_mapping.values():
#                 if header in headers:
#                     column_indices[header] = headers.index(header) + min_col
#                 else:
#                     self.logger.warning(f"필수 컬럼을 찾을 수 없음: {header}")

#             # 필수 컬럼 확인 및 처리
#             required_columns = ['환자 명', '등록날짜', '진단 의사명']
#             missing_columns = [col for col in required_columns if col not in column_indices]
#             if missing_columns:
#                 self.logger.warning(f"일부 컬럼을 찾을 수 없음: {', '.join(missing_columns)}")
#                 self.logger.info("해당 컬럼은 건너뛰고 나머지 데이터를 처리합니다.")
            
#             # 기존 데이터 수집 (등록날짜와 환자명 기준)
#             existing_records = set()
#             for row in range(min_row + 1, max_row + 1):
#                 name = self.standardize_value(sheet.cell(row=row, column=column_indices['환자 명']).value, preserve_format=True)
#                 date = self.standardize_date(sheet.cell(row=row, column=column_indices.get('등록날짜', 0)).value) if '등록날짜' in column_indices else None
#                 if name and date:
#                     existing_records.add((name, date))
#                     self.logger.debug(f"기존 데이터 수집: {name} - {date}")

#             added_count = 0
#             skipped_count = 0
#             excluded_count = 0
            
#             # 제외 키워드가 포함된 행 제거
#             for idx, row in df.iterrows():
#                 if self.should_exclude_row(row):
#                     self.logger.info(f"제외 키워드가 포함된 행 제거: {row.get('환자', '')}")
#                     df = df.drop(idx)
#                     excluded_count += 1
            
#             df = df.sort_values('등록날짜') if '등록날짜' in df.columns else df
            
#             for idx, row in df.iterrows():
#                 name = self.standardize_value(row.get('환자 명', ''), preserve_format=True)
#                 date = self.standardize_date(row.get('등록날짜', '')) if '등록날짜' in df.columns else None
#                 doctor = self.standardize_value(row.get('진단 의사명', ''), preserve_format=True) if '진단 의사명' in df.columns else None
                
#                 if not name or not date or not doctor:
#                     self.logger.warning(f"필수 데이터 누락: 행 {idx + 2}")
#                     skipped_count += 1
#                     continue
                
#                 # 등록날짜와 환자명 기준으로 중복 체크
#                 if (name, date) in existing_records:
#                     self.logger.info(f"중복 데이터 건너뛰기: {name} - {date} (등록날짜와 환자명이 일치)")
#                     skipped_count += 1
#                     continue
                
#                 max_row += 1
#                 for header, col in column_indices.items():
#                     value = row.get(header, '')
#                     sheet.cell(row=max_row, column=col).value = value
                    
#                     if max_row > min_row + 1:
#                         try:
#                             source_cell = sheet.cell(row=min_row + 1, column=col)
#                             if source_cell.has_style:
#                                 sheet.cell(row=max_row, column=col).font = copy(source_cell.font)
#                                 sheet.cell(row=max_row, column=col).fill = copy(source_cell.fill)
#                                 sheet.cell(row=max_row, column=col).border = copy(source_cell.border)
#                                 sheet.cell(row=max_row, column=col).alignment = copy(source_cell.alignment)
#                                 sheet.cell(row=max_row, column=col).number_format = source_cell.number_format
#                         except Exception as e:
#                             self.logger.warning(f"셀 스타일 복사 실패 (행: {max_row}, 열: {col}): {str(e)}")
                
#                 existing_records.add((name, date))
#                 added_count += 1
#                 self.logger.info(f"데이터 추가 완료: {name} - {date}")

#             if added_count > 0:
#                 table.ref = f"{get_column_letter(min_col)}{min_row}:{get_column_letter(max_col)}{max_row}"
#             wb.save(main_file)
            
#             self.logger.info(f"결제 항목 처리 완료: {added_count}건 추가, {skipped_count}건 중복/오류, {excluded_count}건 제외")
#             return {
#                 "success": True, 
#                 "msg": f"데이터 {added_count}건 추가, 중복/오류 {skipped_count}건, 제외 {excluded_count}건"
#             }
#         except Exception as e:
#             self.logger.error(f"결제 항목 처리 중 오류 발생: {str(e)}", exc_info=True)
#             return {"success": False, "msg": str(e)}

#     def run_patient_update(self, main_file):
#         try:
#             self.logger.info("환자 정보 업데이트 시작")
            
#             wb = load_workbook(main_file)
#             self.logger.info(f"메인 파일 로드 완료: {main_file}")
            
#             # 환자자동 테이블 찾기
#             patients_table = self.find_table("환자자동", wb)
#             if not patients_table:
#                 self.logger.error("환자자동 테이블을 찾을 수 없음")
#                 return {"success": False, "msg": "환자자동 테이블 없음"}
            
#             # 고객관리자동 테이블 찾기
#             customer_table = self.find_table("고객관리자동", wb)
#             if not customer_table:
#                 self.logger.error("고객관리자동 테이블을 찾을 수 없음")
#                 return {"success": False, "msg": "고객관리자동 테이블 없음"}
            
#             # 환자자동 시트와 고객관리자동 시트 찾기
#             patients_sheet = None
#             customer_sheet = None
#             for sheet in wb.worksheets:
#                 if patients_table in sheet.tables.values():
#                     patients_sheet = sheet
#                     self.logger.info(f"환자자동 시트 찾음: {sheet.title}")
#                 if customer_table in sheet.tables.values():
#                     customer_sheet = sheet
#                     self.logger.info(f"고객관리자동 시트 찾음: {sheet.title}")
            
#             if not patients_sheet or not customer_sheet:
#                 self.logger.error("필요한 시트를 찾을 수 없음")
#                 return {"success": False, "msg": "필요한 시트를 찾을 수 없음"}
            
#             # 환자자동 테이블 범위
#             p_min_col, p_min_row, p_max_col, p_max_row = range_boundaries(patients_table.ref)
#             self.logger.info(f"환자자동 테이블 범위: {patients_table.ref}")
            
#             # 고객관리자동 테이블 범위
#             c_min_col, c_min_row, c_max_col, c_max_row = range_boundaries(customer_table.ref)
#             self.logger.info(f"고객관리자동 테이블 범위: {customer_table.ref}")
            
#             # 헤더 매핑
#             patients_headers = {}
#             customer_headers = {}
            
#             # 환자자동 헤더
#             for col in range(p_min_col, p_max_col + 1):
#                 header = patients_sheet.cell(row=p_min_row, column=col).value
#                 if header:
#                     patients_headers[header] = col
#                     self.logger.debug(f"환자자동 헤더: {header} -> 열 {col}")
            
#             # 고객관리자동 헤더
#             for col in range(c_min_col, c_max_col + 1):
#                 header = customer_sheet.cell(row=c_min_row, column=col).value
#                 if header:
#                     customer_headers[header] = col
#                     self.logger.debug(f"고객관리자동 헤더: {header} -> 열 {col}")
            
#             self.logger.info(f"환자자동 헤더 목록: {list(patients_headers.keys())}")
#             self.logger.info(f"고객관리자동 헤더 목록: {list(customer_headers.keys())}")
            
#             # 환자 데이터 수집
#             patients_data = {}
#             for row in range(p_min_row + 1, p_max_row + 1):
#                 name = patients_sheet.cell(row=row, column=patients_headers.get("이름")).value
#                 birth_date = patients_sheet.cell(row=row, column=patients_headers.get("생년월일")).value
#                 age_range = patients_sheet.cell(row=row, column=patients_headers.get("연령대")).value
#                 age = patients_sheet.cell(row=row, column=patients_headers.get("나이")).value
#                 gender = patients_sheet.cell(row=row, column=patients_headers.get("성별")).value
#                 state = patients_sheet.cell(row=row, column=patients_headers.get("주")).value
                
#                 if name:
#                     # 생년 처리 (이전 방식)
#                     birth_year = ""
#                     if birth_date and isinstance(birth_date, str):
#                         if "년" in birth_date:
#                             birth_year = birth_date.split("년")[0]
#                         elif "월" in birth_date and "," in birth_date:
#                             birth_year = birth_date.split(",")[1].strip()
                    
#                     patients_data[name] = {
#                         "생년": birth_year,
#                         "연령대": age_range if age_range else "",
#                         "나이": age if age else "",
#                         "성별": gender if gender else "",
#                         "주": state if state else ""
#                     }
            
#             self.logger.info(f"수집된 환자 데이터 수: {len(patients_data)}")
            
#             # 고객관리자동 테이블 업데이트
#             updated_count = 0
#             empty_rows = []  # 공란인 행 번호 저장
            
#             for row in range(c_min_row + 1, c_max_row + 1):
#                 name = customer_sheet.cell(row=row, column=customer_headers.get("환자 명")).value
#                 if name and name in patients_data:
#                     data = patients_data[name]
                    
#                     # 생년 업데이트
#                     if "생년" in customer_headers:
#                         cell = customer_sheet.cell(row=row, column=customer_headers["생년"])
#                         cell.value = data["생년"]
#                         cell.number_format = '@'
                    
#                     # 연령대 업데이트
#                     if "연령대" in customer_headers:
#                         cell = customer_sheet.cell(row=row, column=customer_headers["연령대"])
#                         cell.value = data["연령대"]
#                         cell.number_format = '@'
                    
#                     # 나이 업데이트
#                     if "나이" in customer_headers:
#                         cell = customer_sheet.cell(row=row, column=customer_headers["나이"])
#                         cell.value = data["나이"]
#                         cell.number_format = '@'
                    
#                     # 성별 업데이트 (male/female -> 남/여)
#                     if "성별" in customer_headers:
#                         cell = customer_sheet.cell(row=row, column=customer_headers["성별"])
#                         gender_val = data["성별"].strip().lower() if data["성별"] else ""
#                         if gender_val == "male":
#                             cell.value = "남"
#                         elif gender_val == "female":
#                             cell.value = "여"
#                         else:
#                             cell.value = data["성별"]
#                         cell.number_format = '@'
                    
#                     # 주 업데이트
#                     if "주" in customer_headers:
#                         cell = customer_sheet.cell(row=row, column=customer_headers["주"])
#                         cell.value = data["주"]
#                         cell.number_format = '@'
                    
#                     updated_count += 1
#                 else:
#                     # 행의 모든 셀이 비어있는지 확인
#                     is_empty = True
#                     for col in range(c_min_col, c_max_col + 1):
#                         if customer_sheet.cell(row=row, column=col).value:
#                             is_empty = False
#                             break
#                     if is_empty:
#                         empty_rows.append(row)
            
#             # 다른 행이 없는 경우에만 첫 번째 행 보존
#             if len(empty_rows) == c_max_row - c_min_row:
#                 empty_rows.remove(c_min_row + 1)  # 첫 번째 행은 보존
            
#             # 빈 행 삭제 (역순으로 삭제하여 인덱스 변화 방지)
#             deleted_count = 0
#             for row in sorted(empty_rows, reverse=True):
#                 customer_sheet.delete_rows(row)
#                 deleted_count += 1
            
#             # 테이블 범위 업데이트
#             if deleted_count > 0:
#                 c_max_row -= deleted_count
#                 customer_table.ref = f"{get_column_letter(c_min_col)}{c_min_row}:{get_column_letter(c_max_col)}{c_max_row}"
            
#             wb.save(main_file)
#             self.logger.info(f"환자 정보 업데이트 완료: {updated_count}건 업데이트, {deleted_count}건 공란 행 삭제")
            
#             return {"success": True, "msg": f"{updated_count}건의 환자 정보 업데이트 완료, {deleted_count}건의 공란 행 삭제"}
            
#         except Exception as e:
#             self.logger.error(f"환자 정보 업데이트 중 오류 발생: {str(e)}", exc_info=True)
#             return {"success": False, "msg": str(e)}

#     def run_table_update(self, main_file, patients_file=None, payment_file=None, update_patient_info=True):
#         try:
#             self.logger.info("테이블 업데이트 작업 시작")
            
#             # 메인 파일만 체크
#             if not os.path.exists(main_file):
#                 self.logger.error(f"메인 파일이 존재하지 않습니다: {main_file}")
#                 return {"success": False, "msg": "메인 파일이 존재하지 않습니다"}
            
#             backup_dir = os.path.join(os.path.dirname(main_file), "BACK UP")
#             os.makedirs(backup_dir, exist_ok=True)
#             backup_file = os.path.join(backup_dir, f"BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(main_file)}")
#             shutil.copy2(main_file, backup_file)
#             self.logger.info(f"파일 백업 완료: {backup_file}")
            
#             result = {}
            
#             # 환자 파일 처리
#             if patients_file and os.path.exists(patients_file):
#                 self.logger.info("환자 파일 처리 시작")
#                 result['patients'] = self.process_patients_file(main_file, patients_file)
#                 if not result['patients']['success']:
#                     self.logger.error("환자 파일 처리 실패")
#                     return result
#             else:
#                 self.logger.info("환자 파일이 없어 처리하지 않습니다")
#                 result['patients'] = {"success": True, "msg": "환자 파일 없음"}
            
#             # 결제 파일 처리
#             if payment_file and os.path.exists(payment_file):
#                 self.logger.info("결제 파일 처리 시작")
#                 result['payments'] = self.process_PaymentItems_items(main_file, payment_file)
#                 if not result['payments']['success']:
#                     self.logger.error("결제 파일 처리 실패")
#                     return result
#             else:
#                 self.logger.info("결제 파일이 없어 처리하지 않습니다")
#                 result['payments'] = {"success": True, "msg": "결제 파일 없음"}
            
#             # 환자 정보 업데이트 여부 확인
#             if update_patient_info:
#                 result['update'] = self.run_patient_update(main_file)
#                 if not result['update']['success']:
#                     self.logger.error("환자 정보 업데이트 실패")
#                     return result
#             else:
#                 self.logger.info("환자 정보 업데이트를 건너뜁니다")
#                 result['update'] = {"success": True, "msg": "환자 정보 업데이트 건너뜀"}
            
#             self.logger.info("테이블 업데이트 작업 완료")
#             return {"success": True, "msg": "표 업데이트 전체 완료", "detail": result}
#         except Exception as e:
#             self.logger.error(f"테이블 업데이트 중 오류 발생: {str(e)}", exc_info=True)
#             return {"success": False, "msg": str(e)}

#     def calculate_age_from_birthdate(self, birthdate_str):
#         if not birthdate_str or pd.isna(birthdate_str):
#             return None
#         try:
#             # "11월 25, 1980" 형식 처리
#             if "월" in birthdate_str and "," in birthdate_str:
#                 month = int(birthdate_str.split("월")[0])
#                 day = int(birthdate_str.split(",")[0].split("월")[1].strip())
#                 year = int(birthdate_str.split(",")[1].strip())
                
#                 birth_date = datetime(year, month, day)
#                 today = datetime.now()
                
#                 # 엑셀의 DATEDIF 함수와 동일한 계산
#                 age = today.year - birth_date.year
#                 if (today.month, today.day) < (birth_date.month, birth_date.day):
#                     age -= 1
                
#                 return age
#             return None
#         except Exception as e:
#             self.logger.warning(f"나이 계산 실패: {birthdate_str} -> {str(e)}")
#             return None

#     def get_age_range(self, age):
#         if age is None:
#             self.logger.warning("나이가 None이어서 연령대를 계산할 수 없음")
#             return None
#         try:
#             if age < 20:
#                 return "10s"
#             elif age < 30:
#                 return "20s"
#             elif age < 40:
#                 return "30s"
#             elif age < 50:
#                 return "40s"
#             elif age < 60:
#                 return "50s"
#             elif age < 70:
#                 return "60s"
#             else:
#                 return "70+"
#         except Exception as e:
#             self.logger.warning(f"연령대 계산 중 오류 발생: {age} -> {str(e)}")
#             return None

#     def run_chart_update(self, main_file):
#         """도표 업데이트 기능 실행"""
#         self.logger.info("도표 업데이트 시작")
#         self.logger.info(f"메인 파일: {main_file}")
#         try:
#             # 메인 파일 존재 확인
#             if not os.path.exists(main_file):
#                 self.logger.error(f"메인 파일이 존재하지 않음: {main_file}")
#                 return {"success": False, "msg": "메인 파일을 찾을 수 없습니다."}
            
#             # 메인 파일 로드
#             self.logger.info("메인 파일 로드 시작")
#             wb = load_workbook(main_file)
#             self.logger.info("메인 파일 로드 완료")
            
#             # 현재 달 계산
#             today = datetime.now()
#             current_month = today.month
#             current_year = today.year
#             month_str = str(current_month)
#             self.logger.info(f"현재 달 계산: {current_month}월")
            
#             # 새로운 시트 이름
#             new_patients_sheet_name = f"{month_str}월_회원"
#             new_payment_sheet_name = f"{month_str}월_진료"
#             self.logger.info(f"새로운 시트 이름: {new_patients_sheet_name}, {new_payment_sheet_name}")
            
#             # 기존 시트 찾기
#             existing_patients_sheet = None
#             existing_payment_sheet = None
#             old_patients_name = None
#             old_payment_name = None
#             for sheet_name in wb.sheetnames:
#                 if sheet_name.endswith("_회원"):
#                     existing_patients_sheet = wb[sheet_name]
#                     old_patients_name = sheet_name
#                     self.logger.info(f"기존 회원 시트 발견: {sheet_name}")
#                 elif sheet_name.endswith("_진료"):
#                     existing_payment_sheet = wb[sheet_name]
#                     old_payment_name = sheet_name
#                     self.logger.info(f"기존 진료 시트 발견: {sheet_name}")
#             if not existing_patients_sheet or not existing_payment_sheet:
#                 self.logger.error("필요한 시트를 찾을 수 없음")
#                 return {"success": False, "msg": "필요한 시트를 찾을 수 없습니다."}
#             # 시트 이름 변경
#             self.logger.info(f"시트 이름 변경 시도: {old_patients_name} → {new_patients_sheet_name}")
#             if existing_patients_sheet.title != new_patients_sheet_name:
#                 existing_patients_sheet.title = new_patients_sheet_name
#                 self.logger.info(f"회원 시트 이름 변경 완료: {old_patients_name} → {existing_patients_sheet.title}")
#             else:
#                 self.logger.info(f"회원 시트 이름이 이미 {new_patients_sheet_name}임")
#             self.logger.info(f"시트 이름 변경 시도: {old_payment_name} → {new_payment_sheet_name}")
#             if existing_payment_sheet.title != new_payment_sheet_name:
#                 existing_payment_sheet.title = new_payment_sheet_name
#                 self.logger.info(f"진료 시트 이름 변경 완료: {old_payment_name} → {existing_payment_sheet.title}")
#             else:
#                 self.logger.info(f"진료 시트 이름이 이미 {new_payment_sheet_name}임")
#             # 시트 이름 변경 후 저장
#             wb.save(main_file)
#             self.logger.info(f"시트 이름 변경 후 저장 완료: {main_file}")
#             # 테이블 찾기
#             patients_table = self.find_table("최근환자", existing_patients_sheet)
#             payment_table = self.find_table("최근진료", existing_payment_sheet)
#             if not patients_table:
#                 self.logger.error("최근환자 테이블을 찾을 수 없음")
#                 return {"success": False, "msg": "최근환자 테이블을 찾을 수 없습니다."}
#             if not payment_table:
#                 self.logger.error("최근진료 테이블을 찾을 수 없음")
#                 return {"success": False, "msg": "최근진료 테이블을 찾을 수 없습니다."}
#             # 환자자동, 고객관리자동 테이블 찾기
#             auto_patients_table = self.find_table("환자자동", wb)
#             auto_customers_table = self.find_table("고객관리자동", wb)
#             if not auto_patients_table or not auto_customers_table:
#                 self.logger.error("환자자동/고객관리자동 테이블을 찾을 수 없음")
#                 return {"success": False, "msg": "환자자동/고객관리자동 테이블을 찾을 수 없습니다."}
#             # 시트 찾기
#             auto_patients_sheet = None
#             auto_customers_sheet = None
#             for sheet in wb.worksheets:
#                 if auto_patients_table in sheet.tables.values():
#                     auto_patients_sheet = sheet
#                 if auto_customers_table in sheet.tables.values():
#                     auto_customers_sheet = sheet
#             # 테이블 범위
#             p_min_col, p_min_row, p_max_col, p_max_row = range_boundaries(patients_table.ref)
#             py_min_col, py_min_row, py_max_col, py_max_row = range_boundaries(payment_table.ref)
#             ap_min_col, ap_min_row, ap_max_col, ap_max_row = range_boundaries(auto_patients_table.ref)
#             ac_min_col, ac_min_row, ac_max_col, ac_max_row = range_boundaries(auto_customers_table.ref)
#             # 헤더 추출
#             patients_headers = [existing_patients_sheet.cell(row=p_min_row, column=col).value for col in range(p_min_col, p_max_col+1)]
#             auto_patients_headers = [auto_patients_sheet.cell(row=ap_min_row, column=col).value for col in range(ap_min_col, ap_max_col+1)]
#             payment_headers = [existing_payment_sheet.cell(row=py_min_row, column=col).value for col in range(py_min_col, py_max_col+1)]
#             auto_customers_headers = [auto_customers_sheet.cell(row=ac_min_row, column=col).value for col in range(ac_min_col, ac_max_col+1)]
#             # 최근달 데이터만 추출 (등록 날짜/등록날짜 기준)
#             # 환자자동 → 최근환자
#             recent_rows = []
#             for row in range(ap_min_row+1, ap_max_row+1):
#                 date_val = auto_patients_sheet.cell(row=row, column=auto_patients_headers.index("등록 날짜")+ap_min_col).value
#                 if date_val:
#                     # 날짜 파싱
#                     try:
#                         if "년" in str(date_val) and "월" in str(date_val):
#                             y = int(str(date_val).split("년")[0])
#                             m = int(str(date_val).split("년")[1].split("월")[0].strip())
#                             if y == current_year and m == current_month:
#                                 recent_rows.append(row)
#                     except:
#                         continue
#             # 기존 데이터 삭제 (헤더 제외)
#             for row in range(p_min_row+1, p_max_row+1):
#                 for col in range(p_min_col, p_max_col+1):
#                     existing_patients_sheet.cell(row=row, column=col).value = None
#             # 붙여넣기
#             for i, src_row in enumerate(recent_rows):
#                 for j, header in enumerate(patients_headers):
#                     if header in auto_patients_headers:
#                         src_col = auto_patients_headers.index(header) + ap_min_col
#                         dst_col = p_min_col + j
#                         val = auto_patients_sheet.cell(row=src_row, column=src_col).value
#                         existing_patients_sheet.cell(row=p_min_row+1+i, column=dst_col).value = val
#             # 테이블 ref 조정 (최근환자)
#             last_row = p_min_row + len(recent_rows)
#             patients_table.ref = f"{get_column_letter(p_min_col)}{p_min_row}:{get_column_letter(p_max_col)}{last_row}"

#             # 고객관리자동 → 최근진료
#             recent_rows2 = []
#             for row in range(ac_min_row+1, ac_max_row+1):
#                 date_val = auto_customers_sheet.cell(row=row, column=auto_customers_headers.index("등록날짜")+ac_min_col).value
#                 if date_val:
#                     try:
#                         if "년" in str(date_val) and "월" in str(date_val):
#                             y = int(str(date_val).split("년")[0])
#                             m = int(str(date_val).split("년")[1].split("월")[0].strip())
#                             if y == current_year and m == current_month:
#                                 recent_rows2.append(row)
#                     except:
#                         continue
#             # 기존 데이터 삭제 (헤더 제외)
#             for row in range(py_min_row+1, py_max_row+1):
#                 for col in range(py_min_col, py_max_col+1):
#                     existing_payment_sheet.cell(row=row, column=col).value = None
#             # 붙여넣기
#             for i, src_row in enumerate(recent_rows2):
#                 for j, header in enumerate(payment_headers):
#                     if header in auto_customers_headers:
#                         src_col = auto_customers_headers.index(header) + ac_min_col
#                         dst_col = py_min_col + j
#                         val = auto_customers_sheet.cell(row=src_row, column=src_col).value
#                         existing_payment_sheet.cell(row=py_min_row+1+i, column=dst_col).value = val
#             # 테이블 ref 조정 (최근진료)
#             last_row2 = py_min_row + len(recent_rows2)
#             payment_table.ref = f"{get_column_letter(py_min_col)}{py_min_row}:{get_column_letter(py_max_col)}{last_row2}"

#             # 수식 업데이트 (기존 코드)
#             updated_formulas = 0
#             for sheet in wb.worksheets:
#                 for row in sheet.iter_rows():
#                     for cell in row:
#                         if cell.value and isinstance(cell.value, str) and cell.value.startswith('='):
#                             formula = cell.value
#                             if old_patients_name and old_patients_name in formula:
#                                 formula = formula.replace(old_patients_name, new_patients_sheet_name)
#                                 updated_formulas += 1
#                             if old_payment_name and old_payment_name in formula:
#                                 formula = formula.replace(old_payment_name, new_payment_sheet_name)
#                                 updated_formulas += 1
#                             cell.value = formula
#             self.logger.info(f"수식 업데이트 완료: {updated_formulas}개의 수식이 업데이트됨")
#             wb.save(main_file)
#             return {
#                 "success": True,
#                 "msg": "도표 업데이트가 완료되었습니다.",
#                 "detail": {
#                     "patients": {"msg": f"회원 데이터가 {new_patients_sheet_name}에 복사되었습니다."},
#                     "payment": {"msg": f"진료 데이터가 {new_payment_sheet_name}에 복사되었습니다."},
#                     "formulas": {"msg": f"{updated_formulas}개의 수식이 업데이트되었습니다."}
#                 }
#             }
#         except Exception as e:
#             self.logger.error(f"도표 업데이트 중 오류 발생: {str(e)}")
#             return {"success": False, "msg": f"도표 업데이트 중 오류가 발생했습니다: {str(e)}"}

# # if __name__ == "__main__":
# #     backend = ExcelBackend()
# #     result = backend.run_table_update("회원-sales.xlsx", "Patients.csv", "PaymentItems.csv")
# #     print(result) 
