import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from io import BytesIO
from openpyxl.styles import Font, Alignment, PatternFill

SHOPPING_LIST_PATH = "config/shopping_list.json"
CATEGORIES_PATH = "config/categories.json"


def load_data():
    """加载购物清单数据"""
    if not os.path.exists(SHOPPING_LIST_PATH):
        return []
    with open(SHOPPING_LIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    """保存购物清单数据"""
    os.makedirs("config", exist_ok=True)
    with open(SHOPPING_LIST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_to_excel(items):
    """导出购物清单到Excel"""
    df = pd.DataFrame(items)
    
    if df.empty:
        return None
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="购物清单")
        
        workbook = writer.book
        sheet = writer.sheets["购物清单"]
        
        column_widths = {
            "A": 20,
            "B": 12,
            "C": 8,
            "D": 8,
            "E": 12,
            "F": 10,
            "G": 12,
            "H": 10,
            "I": 12,
            "J": 20,
        }
        
        for col, width in column_widths.items():
            sheet.column_dimensions[col].width = width
        
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for col in range(1, sheet.max_column + 1):
            cell = sheet.cell(row=1, column=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row):
            for cell in row:
                cell.alignment = Alignment(vertical="center")
    
    return output.getvalue()