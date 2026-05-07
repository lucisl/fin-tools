# 🛒 618购物清单 - 配置指南

## 数据存储方式

购物清单数据使用 **GitHub仓库** 存储，数据永久保存，重启不丢失！

数据文件位置：`data/shopping_list.json`

---

## 🔐 安全配置步骤（必做！）

### 步骤1：创建GitHub Personal Access Token

1. **访问GitHub Token页面**
   - 登录GitHub：https://github.com
   - 点击右上角头像 → **Settings**
   - 左侧菜单 → **Developer settings** (最下方)
   - 点击 **Personal access tokens** → **Tokens (classic)**

2. **创建新Token**
   - 点击 **Generate new token (classic)**

3. **Token配置**
   - **Note**: `fin-tools-shopping-list`
   - **Expiration**: 选择 `No expiration` (永不过期)
   - **Select scopes**: 勾选以下权限
     - ✅ `repo` (完整的仓库访问权限)
       - ✅ `repo:status`
       - ✅ `repo_deployment`
       - ✅ `public_repo`
       - ✅ `repo:invite`
       - ✅ `repo:hook`

4. **生成并保存Token**
   - 点击底部 **Generate token** 按钮
   - **⚠️ 重要**: 立即复制生成的token（类似：`ghp_xxxxxxxxxxxx`）
   - 这个token只会显示一次，请妥善保存！

---

### 步骤2：配置Streamlit Cloud Secrets

1. **登录Streamlit Cloud**
   - 访问：https://share.streamlit.io
   - 使用GitHub账号登录

2. **找到你的应用**
   - 在应用列表中找到：**lucisl-fin-tools**

3. **配置Secrets**
   - 点击右上角 **Settings** ⚙️ 按钮
   - 找到 **Secrets** 部分
   - 在文本框中输入以下内容：

```toml
github_token = "你刚才生成的GitHub_Token"
github_owner = "lucisl"
github_repo = "fin-tools"
```

**示例：**
```toml
github_token = "ghp_ABCD1234EFGH5678IJKL"
github_owner = "lucisl"
github_repo = "fin-tools"
```

4. **保存配置**
   - 点击 **Save** 按钮
   - 应用会自动重启（大约需要10-30秒）

---

### 步骤3：本地开发配置

如果你想在本地运行应用，需要创建 `.streamlit/secrets.toml` 文件：

```toml
github_token = "你的GitHub_Token"
github_owner = "lucisl"
github_repo = "fin-tools"
```

**注意：**
- `.streamlit/secrets.toml` 文件已被 `.gitignore` 忽略
- 不会提交到GitHub，保持安全

---

## ✅ 验证配置

配置完成后，访问应用：

**应用地址：**
https://lucisl-fin-tools.streamlit.app/购物清单

**测试步骤：**
1. 添加一个商品（例如：iPhone 15）
2. 设置预算价格
3. 点击保存
4. 等待几分钟或手动重启应用
5. 再次访问，检查商品是否还在

**如果商品还在 → 配置成功！✅**

---

## 🎯 技术架构

```
Streamlit Cloud (前端)
    ↓ GitHub API调用
GitHub Repository (数据层)
    ↓ 文件: data/shopping_list.json
永久存储 ✅
```

**优势：**
- ✅ 数据永久保存，重启不丢失
- ✅ 无需数据库服务器
- ✅ 无需防火墙配置
- ✅ GitHub自动备份
- ✅ 可以在GitHub仓库查看数据文件

---

## 📋 数据文件位置

购物清单数据存储在：
- GitHub仓库：`lucisl/fin-tools`
- 文件路径：`data/shopping_list.json`

你可以直接在GitHub查看数据：
https://github.com/lucisl/fin-tools/blob/main/data/shopping_list.json

---

## 🔧 故障排查

### 问题1：应用报错"请在Streamlit Cloud配置Secrets"

**原因：** Secrets没有配置或配置错误

**解决：**
1. 检查Streamlit Cloud的Secrets是否配置
2. 检查token是否正确复制
3. 检查格式是否正确（不要有多余空格）

### 问题2：添加商品失败

**原因：** Token权限不足或失效

**解决：**
1. 检查token是否有 `repo` 权限
2. 检查token是否过期
3. 重新生成token并更新Secrets

### 问题3：数据仍然丢失

**可能原因：**
- Secrets配置错误
- Token权限不足
- GitHub API调用失败

**解决：**
- 检查GitHub仓库是否有 `data/shopping_list.json` 文件
- 检查Streamlit Cloud的日志（Settings → Logs）

---

## 🚨 安全提醒

**⚠️ 绝对不要：**
- ❌ 将token提交到GitHub代码中
- ❌ 在公开对话中分享token
- ❌ 使用已经暴露的token

**✅ 正确做法：**
- ✅ Token只保存在Streamlit Cloud Secrets中
- ✅ 本地开发时使用 `.streamlit/secrets.toml`（不提交）
- ✅ Token泄露后立即删除重新生成

---

## 📞 需要帮助？

如果遇到问题，请检查：
1. Streamlit Cloud Secrets是否正确配置
2. GitHub Token是否有足够权限
3. GitHub仓库是否存在

**查看应用日志：**
- Streamlit Cloud → Settings → Logs

---

## 🎉 完成！

配置完成后，购物清单数据将永久保存在GitHub仓库中！

添加商品、修改、删除都会自动同步到GitHub。