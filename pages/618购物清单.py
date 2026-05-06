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


def add_item(name, category, quantity, unit, budget_price, priority, platform, notes=""):
    """新增商品"""
    items = load_data()
    new_item = {
        "id": str(datetime.now().timestamp()),
        "name": name,
        "category": category,
        "quantity": quantity,
        "unit": unit,
        "budget_price": budget_price,
        "priority": priority,
        "platform": platform,
        "status": "待购买",
        "actual_price": 0,
        "notes": notes,
        "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    items.append(new_item)
    save_data(items)
    return new_item


def update_item(item_id, **kwargs):
    """更新商品信息"""
    items = load_data()
    for item in items:
        if item["id"] == item_id:
            item.update(kwargs)
            item["updated_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    save_data(items)


def delete_item(item_id):
    """删除商品"""
    items = load_data()
    items = [item for item in items if item["id"] != item_id]
    save_data(items)


def toggle_status(item_id):
    """切换购买状态"""
    items = load_data()
    status_cycle = ["待购买", "已购买", "已取消"]
    for item in items:
        if item["id"] == item_id:
            current_index = status_cycle.index(item["status"])
            next_index = (current_index + 1) % len(status_cycle)
            item["status"] = status_cycle[next_index]
            item["updated_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    save_data(items)


def get_items(category=None, priority=None, status=None):
    """获取商品列表,支持筛选"""
    items = load_data()
    
    if category and category != "全部":
        items = [item for item in items if item["category"] == category]
    
    if priority and priority != "全部":
        items = [item for item in items if item["priority"] == priority]
    
    if status and status != "全部":
        items = [item for item in items if item["status"] == status]
    
    return items


def load_categories():
    """加载分类列表"""
    if not os.path.exists(CATEGORIES_PATH):
        return []
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("categories", [])


def save_categories(categories):
    """保存分类列表"""
    os.makedirs("config", exist_ok=True)
    with open(CATEGORIES_PATH, "w", encoding="utf-8") as f:
        json.dump({"categories": categories}, f, ensure_ascii=False, indent=2)


def add_category(category_name):
    """新增分类"""
    categories = load_categories()
    if category_name not in categories:
        categories.append(category_name)
        save_categories(categories)
        return True
    return False


def delete_category(category_name):
    """删除分类"""
    items = load_data()
    has_items = any(item["category"] == category_name for item in items)
    if has_items:
        return False
    
    categories = load_categories()
    if category_name in categories:
        categories.remove(category_name)
        save_categories(categories)
        return True
    return False


def calculate_budget_summary(items):
    """计算预算汇总"""
    total_budget = sum(item.get("budget_price", 0) * item.get("quantity", 1) for item in items)
    spent = sum(item.get("actual_price", 0) for item in items if item["status"] == "已购买")
    remaining = total_budget - spent
    return {
        "total_budget": total_budget,
        "spent": spent,
        "remaining": remaining
    }


def calculate_category_stats(items):
    """按分类统计"""
    stats = {}
    for item in items:
        category = item.get("category", "未分类")
        if category not in stats:
            stats[category] = {
                "count": 0,
                "budget": 0,
                "spent": 0
            }
        stats[category]["count"] += 1
        stats[category]["budget"] += item.get("budget_price", 0) * item.get("quantity", 1)
        if item["status"] == "已购买":
            stats[category]["spent"] += item.get("actual_price", 0)
    return stats


def calculate_priority_stats(items):
    """按优先级统计"""
    stats = {
        "必须": {"count": 0, "budget": 0, "spent": 0},
        "想买": {"count": 0, "budget": 0, "spent": 0},
        "可选": {"count": 0, "budget": 0, "spent": 0}
    }
    
    for item in items:
        priority = item.get("priority", "可选")
        if priority in stats:
            stats[priority]["count"] += 1
            stats[priority]["budget"] += item.get("budget_price", 0) * item.get("quantity", 1)
            if item["status"] == "已购买":
                stats[priority]["spent"] += item.get("actual_price", 0)
    
    return stats


def calculate_completion_rate(items):
    """计算购买完成率"""
    if not items:
        return 0
    
    completed = sum(1 for item in items if item["status"] == "已购买")
    return (completed / len(items)) * 100


# ======================================
#               Web UI
# ======================================
st.title("🛒 618购物清单")

# 侧边栏筛选
st.sidebar.header("🔍 筛选条件")

# 加载分类
categories = load_categories()
category_filter = st.sidebar.selectbox("按分类筛选", ["全部"] + categories)

# 按优先级筛选
priority_filter = st.sidebar.selectbox("按优先级筛选", ["全部", "必须", "想买", "可选"])

# 按状态筛选
status_filter = st.sidebar.selectbox("按状态筛选", ["全部", "待购买", "已购买", "已取消"])

# 获取筛选后的商品
filtered_items = get_items(
    category=category_filter,
    priority=priority_filter,
    status=status_filter
)

# 侧边栏预算统计
st.sidebar.markdown("---")
st.sidebar.header("💰 预算统计")
budget_summary = calculate_budget_summary(load_data())
st.sidebar.metric("总预算", f"¥{budget_summary['total_budget']:.2f}")
st.sidebar.metric("已花费", f"¥{budget_summary['spent']:.2f}")
st.sidebar.metric("剩余预算", f"¥{budget_summary['remaining']:.2f}")