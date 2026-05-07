import streamlit as st
import requests
import base64
import json
from datetime import datetime

# GitHub配置 - 从secrets读取（安全方式）
try:
    GITHUB_TOKEN = st.secrets["github_token"]
    GITHUB_OWNER = st.secrets.get("github_owner", "lucisl")
    GITHUB_REPO = st.secrets.get("github_repo", "fin-tools")
except KeyError:
    st.error("⚠️ 请在Streamlit Cloud配置Secrets！查看README了解如何配置")
    st.stop()
GITHUB_FILE_PATH = "data/shopping_list.json"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"


def get_github_headers():
    """获取GitHub API请求头"""
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }


def get_file_from_github():
    """从GitHub获取文件内容"""
    try:
        response = requests.get(
            GITHUB_API_URL,
            headers=get_github_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            sha = data["sha"]
            return json.loads(content), sha
        elif response.status_code == 404:
            # 文件不存在，返回空数据和None sha
            return [], None
        else:
            st.error(f"获取文件失败: {response.status_code}")
            return [], None
    except Exception as e:
        st.error(f"GitHub API调用失败: {e}")
        return [], None


def update_file_on_github(content, sha=None, message="更新购物清单"):
    """更新GitHub上的文件"""
    try:
        # 编码内容为base64
        content_encoded = base64.b64encode(
            json.dumps(content, ensure_ascii=False, indent=2).encode("utf-8")
        ).decode("utf-8")
        
        # 构建请求体
        payload = {
            "message": message,
            "content": content_encoded,
            "branch": "main"
        }
        
        # 如果文件已存在，需要提供sha
        if sha:
            payload["sha"] = sha
        
        response = requests.put(
            GITHUB_API_URL,
            headers=get_github_headers(),
            json=payload,
            timeout=15
        )
        
        if response.status_code in [200, 201]:
            return True, response.json().get("content", {}).get("sha")
        else:
            st.error(f"更新文件失败: {response.status_code} - {response.text}")
            return False, sha
    except Exception as e:
        st.error(f"更新GitHub文件失败: {e}")
        return False, sha


def load_data():
    """加载购物清单数据"""
    data, sha = get_file_from_github()
    return data if data else []


def save_data(data, message="更新购物清单"):
    """保存购物清单数据到GitHub"""
    items, sha = get_file_from_github()
    success, new_sha = update_file_on_github(data, sha, message)
    return success


def add_item(name, budget_price, platform, notes=""):
    """新增商品"""
    items = load_data()
    
    new_item = {
        "id": str(datetime.now().timestamp()),
        "name": name,
        "budget_price": float(budget_price),
        "platform": platform,
        "status": "待购买",
        "actual_price": 0.0,
        "notes": notes,
        "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    items.append(new_item)
    
    if save_data(items, f"新增商品: {name}"):
        return new_item
    return None


def update_item(item_id, **kwargs):
    """更新商品信息"""
    items = load_data()
    
    for item in items:
        if item["id"] == item_id:
            item.update(kwargs)
            item["updated_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    
    save_data(items, f"更新商品信息")


def delete_item(item_id):
    """删除商品"""
    items = load_data()
    items = [item for item in items if item["id"] != item_id]
    save_data(items, f"删除商品")


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
    
    save_data(items, f"切换商品状态")


def get_items(status=None):
    """获取商品列表,支持筛选"""
    items = load_data()
    
    if status and status != "全部":
        items = [item for item in items if item["status"] == status]
    
    # 按创建时间倒序排序
    items.sort(key=lambda x: x.get("created_time", ""), reverse=True)
    
    return items


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
st.title("🛒 购物清单")

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
            
            budget_price = st.number_input("预算价格", min_value=0.0, value=float(item["budget_price"]), step=0.01)
            
            platforms = ["淘宝", "天猫", "京东", "拼多多", "其他"]
            platform_index = platforms.index(item["platform"]) if item["platform"] in platforms else 0
            platform = st.selectbox("购买平台", platforms, index=platform_index)
            
            notes = st.text_area("备注", value=item.get("notes", ""))
            
            if item["status"] == "已购买":
                actual_price = st.number_input("实际价格", min_value=0.0, value=float(item.get("actual_price", 0)), step=0.01)
            else:
                actual_price = float(item.get("actual_price", 0))
            
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