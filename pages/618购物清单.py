import streamlit as st
import pymysql
from datetime import datetime


def get_mysql_connection():
    """获取MySQL数据库连接"""
    try:
        conn = pymysql.connect(
            host=st.secrets["mysql_host"],
            port=int(st.secrets.get("mysql_port", 3306)),
            user=st.secrets["mysql_user"],
            password=st.secrets["mysql_password"],
            database=st.secrets["mysql_database"],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        st.error(f"数据库连接失败: {e}")
        return None


def init_db():
    """初始化数据库表"""
    conn = get_mysql_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopping_items (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                budget_price DECIMAL(10, 2) DEFAULT 0,
                platform VARCHAR(50) DEFAULT '',
                status VARCHAR(20) DEFAULT '待购买',
                actual_price DECIMAL(10, 2) DEFAULT 0,
                notes TEXT,
                created_time DATETIME NOT NULL,
                updated_time DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        conn.commit()
    except Exception as e:
        st.error(f"初始化数据库失败: {e}")
    finally:
        conn.close()


def load_data():
    """加载购物清单数据"""
    init_db()
    conn = get_mysql_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM shopping_items ORDER BY created_time DESC")
        items = cursor.fetchall()
        
        # 转换数据格式
        for item in items:
            item['budget_price'] = float(item['budget_price'])
            item['actual_price'] = float(item['actual_price'])
            if item['created_time']:
                item['created_time'] = item['created_time'].strftime("%Y-%m-%d %H:%M:%S")
            if item['updated_time']:
                item['updated_time'] = item['updated_time'].strftime("%Y-%m-%d %H:%M:%S")
        
        return items
    except Exception as e:
        st.error(f"加载数据失败: {e}")
        return []
    finally:
        conn.close()


def add_item(name, budget_price, platform, notes=""):
    """新增商品"""
    conn = get_mysql_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        item_id = str(datetime.now().timestamp())
        created_time = datetime.now()
        
        cursor.execute("""
            INSERT INTO shopping_items (id, name, budget_price, platform, status, actual_price, notes, created_time, updated_time)
            VALUES (%s, %s, %s, %s, '待购买', 0, %s, %s, %s)
        """, (item_id, name, budget_price, platform, notes, created_time, created_time))
        
        conn.commit()
        
        return {
            "id": item_id,
            "name": name,
            "budget_price": budget_price,
            "platform": platform,
            "status": "待购买",
            "actual_price": 0,
            "notes": notes,
            "created_time": created_time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_time": created_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        st.error(f"添加商品失败: {e}")
        return None
    finally:
        conn.close()


def update_item(item_id, **kwargs):
    """更新商品信息"""
    conn = get_mysql_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        updated_time = datetime.now()
        kwargs["updated_time"] = updated_time
        
        update_fields = []
        update_values = []
        for key, value in kwargs.items():
            update_fields.append(f"{key} = %s")
            update_values.append(value)
        
        update_values.append(item_id)
        
        sql = f"UPDATE shopping_items SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(sql, update_values)
        
        conn.commit()
    except Exception as e:
        st.error(f"更新商品失败: {e}")
    finally:
        conn.close()


def delete_item(item_id):
    """删除商品"""
    conn = get_mysql_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM shopping_items WHERE id = %s", (item_id,))
        
        conn.commit()
    except Exception as e:
        st.error(f"删除商品失败: {e}")
    finally:
        conn.close()


def toggle_status(item_id):
    """切换购买状态"""
    conn = get_mysql_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT status FROM shopping_items WHERE id = %s", (item_id,))
        row = cursor.fetchone()
        
        if row:
            status_cycle = ["待购买", "已购买", "已取消"]
            current_status = row['status']
            current_index = status_cycle.index(current_status)
            next_index = (current_index + 1) % len(status_cycle)
            next_status = status_cycle[next_index]
            
            updated_time = datetime.now()
            cursor.execute("""
                UPDATE shopping_items 
                SET status = %s, updated_time = %s 
                WHERE id = %s
            """, (next_status, updated_time, item_id))
            
            conn.commit()
    except Exception as e:
        st.error(f"切换状态失败: {e}")
    finally:
        conn.close()


def get_items(status=None):
    """获取商品列表,支持筛选"""
    init_db()
    conn = get_mysql_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        if status and status != "全部":
            cursor.execute("""
                SELECT * FROM shopping_items 
                WHERE status = %s 
                ORDER BY created_time DESC
            """, (status,))
        else:
            cursor.execute("SELECT * FROM shopping_items ORDER BY created_time DESC")
        
        items = cursor.fetchall()
        
        # 转换数据格式
        for item in items:
            item['budget_price'] = float(item['budget_price'])
            item['actual_price'] = float(item['actual_price'])
            if item['created_time']:
                item['created_time'] = item['created_time'].strftime("%Y-%m-%d %H:%M:%S")
            if item['updated_time']:
                item['updated_time'] = item['updated_time'].strftime("%Y-%m-%d %H:%M:%S")
        
        return items
    except Exception as e:
        st.error(f"获取商品列表失败: {e}")
        return []
    finally:
        conn.close()


def calculate_budget_summary(items):
    """计算预算汇总"""
    total_budget = sum(item.get("budget_price", 0) for item in items)
    spent = sum(item.get("actual_price", 0) for item in items if item["status"] == "已购买")
    remaining = total_budget - spent
    return {
        "total_budget": total_budget,
        "spent": spent,
        "remaining": remaining
    }


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

# 按状态筛选
status_filter = st.sidebar.selectbox("按状态筛选", ["全部", "待购买", "已购买", "已取消"])

# 获取筛选后的商品
filtered_items = get_items(status=status_filter)

# 侧边栏预算统计
st.sidebar.markdown("---")
st.sidebar.header("💰 预算统计")
budget_summary = calculate_budget_summary(load_data())
st.sidebar.metric("总预算", f"¥{budget_summary['total_budget']:.2f}")
st.sidebar.metric("已花费", f"¥{budget_summary['spent']:.2f}")
st.sidebar.metric("剩余预算", f"¥{budget_summary['remaining']:.2f}")

tab1, tab2 = st.tabs(["📝 清单管理", "📊 统计分析"])

with tab1:
    st.markdown("### 商品列表")
    
    @st.dialog("新增商品")
    def add_item_dialog():
        name = st.text_input("商品名称 *")
        budget_price = st.number_input("预算价格 *", min_value=0.0, step=0.01)
        platform = st.selectbox("购买平台", ["淘宝", "天猫", "京东", "拼多多", "其他"])
        notes = st.text_area("备注")
        
        col1, col2 = st.columns(2)
        if col1.button("保存", use_container_width=True):
            if not name.strip():
                st.error("商品名称不能为空")
            else:
                result = add_item(name, budget_price, platform, notes)
                if result:
                    st.success("新增成功!")
                    st.rerun()
        
        if col2.button("取消", use_container_width=True):
            st.rerun()
    
    if st.button("➕ 新增商品", use_container_width=True):
        add_item_dialog()
    
    st.markdown("---")
    
    if not filtered_items:
        st.info("暂无商品,请点击上方按钮新增")
    else:
        for item in filtered_items:
            status_emoji = {"待购买": "🛒", "已购买": "✅", "已取消": "❌"}
            
            with st.container():
                cols = st.columns([4, 2, 2])
                
                with cols[0]:
                    st.write(f"**{item['name']}**")
                    st.caption(f"💰 ¥{item['budget_price']:.2f} | 🏪 {item['platform']}")
                    
                    # 显示备注
                    notes = item.get("notes", "")
                    if notes:
                        if len(notes) > 30:
                            with st.expander("📝 查看备注"):
                                st.write(notes)
                        else:
                            st.caption(f"📝 {notes}")
                
                with cols[1]:
                    st.write(f"{status_emoji.get(item['status'], '')} {item['status']}")
                
                with cols[2]:
                    c1, c2, c3 = st.columns(3)
                    
                    if c1.button("🔄", key=f"toggle_{item['id']}", help="切换状态"):
                        toggle_status(item['id'])
                        st.rerun()
                    
                    if c2.button("✏️", key=f"edit_{item['id']}", help="编辑"):
                        st.session_state.edit_item_id = item['id']
                        st.rerun()
                    
                    if c3.button("🗑️", key=f"delete_{item['id']}", help="删除"):
                        st.session_state.delete_item_id = item['id']
                        st.rerun()
                
                st.markdown("---")

if "edit_item_id" in st.session_state:
    item_to_edit = next((item for item in load_data() if item["id"] == st.session_state.edit_item_id), None)
    
    if item_to_edit:
        @st.dialog("编辑商品")
        def edit_item_dialog(item):
            name = st.text_input("商品名称", value=item["name"])
            
            budget_price = st.number_input("预算价格", min_value=0.0, value=item["budget_price"], step=0.01)
            
            platforms = ["淘宝", "天猫", "京东", "拼多多", "其他"]
            platform_index = platforms.index(item["platform"]) if item["platform"] in platforms else 0
            platform = st.selectbox("购买平台", platforms, index=platform_index)
            
            notes = st.text_area("备注", value=item.get("notes", ""))
            
            if item["status"] == "已购买":
                actual_price = st.number_input("实际价格", min_value=0.0, value=item.get("actual_price", 0), step=0.01)
            else:
                actual_price = item.get("actual_price", 0)
            
            col1, col2 = st.columns(2)
            if col1.button("保存修改", use_container_width=True):
                update_item(
                    item["id"],
                    name=name,
                    budget_price=budget_price,
                    platform=platform,
                    notes=notes,
                    actual_price=actual_price
                )
                st.success("修改成功!")
                del st.session_state.edit_item_id
                st.rerun()
            
            if col2.button("取消", use_container_width=True):
                del st.session_state.edit_item_id
                st.rerun()
        
        edit_item_dialog(item_to_edit)

if "delete_item_id" in st.session_state:
    item_to_delete = next((item for item in load_data() if item["id"] == st.session_state.delete_item_id), None)
    
    if item_to_delete:
        @st.dialog("确认删除")
        def delete_item_dialog(item):
            st.warning(f"⚠️ 确定要删除商品 **{item['name']}** 吗? 删除后不可恢复!")
            
            col1, col2 = st.columns(2)
            if col1.button("确认删除", use_container_width=True):
                delete_item(item["id"])
                st.success("删除成功!")
                del st.session_state.delete_item_id
                st.rerun()
            
            if col2.button("取消", use_container_width=True):
                del st.session_state.delete_item_id
                st.rerun()
        
        delete_item_dialog(item_to_delete)

with tab2:
    st.markdown("### 📊 统计分析")
    
    all_items = load_data()
    
    if not all_items:
        st.info("暂无数据,请先添加商品")
    else:
        st.markdown("#### 💰 预算使用情况")
        budget_summary = calculate_budget_summary(all_items)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("总预算", f"¥{budget_summary['total_budget']:.2f}")
        col2.metric("已花费", f"¥{budget_summary['spent']:.2f}")
        col3.metric("剩余预算", f"¥{budget_summary['remaining']:.2f}")
        
        if budget_summary['total_budget'] > 0:
            progress = budget_summary['spent'] / budget_summary['total_budget']
            st.progress(min(progress, 1.0))
            st.caption(f"预算使用率: {progress*100:.1f}%")
        
        st.markdown("---")
        
        st.markdown("#### ✅ 购买完成率")
        completion_rate = calculate_completion_rate(all_items)
        st.metric("完成率", f"{completion_rate:.1f}%")