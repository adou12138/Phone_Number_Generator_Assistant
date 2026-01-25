# 手机号码生成查询系统

一个基于Web的手机号码生成查询系统，支持根据用户输入的筛选条件（手机号前3位、后3/4位、归属地、运营商类型等）生成符合条件的所有手机号码，并支持导出为.txt文件下载。

## 功能特性

- **多条件查询**：支持按号段、归属地、运营商筛选
- **精确匹配**：后3/后4位精确匹配
- **多进程生成**：利用多核CPU加速号码生成
- **分批下载**：大文件自动分批处理
- **用户认证**：支持配置开关的登录功能
- **响应式设计**：完美支持PC端和移动端
- **配置灵活**：通过YAML文件配置所有参数

## 技术栈

- **后端**：Python 3.8+ + Flask
- **数据库**：SQLite
- **前端**：HTML5 + CSS3 + 原生JavaScript
- **部署环境**：Linux云主机

## 目录结构

```
phone_number_generator/
├── app.py                    # Flask应用入口
├── config.py                 # 配置文件读取模块
├── config.yaml               # 应用配置文件
├── requirements.txt          # Python依赖列表
├── final_import.py           # CSV数据导入脚本
│
├── data/                     # 数据目录
│   ├── phone_location.csv    # 号码归属地数据源
│   └── phone_location.db     # SQLite数据库文件
│
├── templates/                # HTML模板
│   ├── login.html            # 登录页面
│   └── index.html            # 查询主页面
│
├── static/                   # 静态资源
│   ├── css/
│   │   └── style.css         # 样式文件
│   └── js/
│       └── main.js           # 前端脚本
│
├── downloads/                # 下载临时目录
├── logs/                     # 日志目录
│
└── README.md                 # 项目说明文档
```

## 快速开始

### 环境要求

- Python 3.8 或更高版本
- Linux云主机（Ubuntu/CentOS/Debian推荐）
- 至少512MB内存
- 至少1GB磁盘空间

### 安装步骤

#### 1. 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置应用

复制配置文件模板并编辑：

```bash
cp config.yaml.example config.yaml
vim config.yaml
```

#### 4. 初始化数据

```bash
python final_import.py
```

#### 5. 启动应用

```bash
python app.py
```

应用将在 `http://0.0.0.0:5000` 启动。

## 配置说明

### 配置文件结构

```yaml
# 应用配置
app:
  host: "0.0.0.0"       # 绑定地址
  port: 5000            # 监听端口
  debug: false          # 调试模式
  secret_key: "your-key"  # Flask密钥

# 登录配置
login:
  enabled: false        # 是否启用登录
  users:                # 用户列表
    - username: "admin"
      password: "admin123"

# 生成器配置
generator:
  max_count: 10000000   # 最大生成数量
  batch_size: 500       # 每批次生成数量
  file_size_limit: 20   # 分批下载阈值（MB）

# 数据库配置
database:
  path: "data/phone_location.db"
  csv_path: "data/phone_location.csv"
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| app.host | 字符串 | "0.0.0.0" | 绑定IP，0.0.0.0表示所有网卡 |
| app.port | 整数 | 5000 | 监听端口 |
| app.debug | 布尔值 | false | 调试模式 |
| login.enabled | 布尔值 | false | 是否启用登录验证 |
| login.users | 列表 | - | 用户账号密码列表 |
| generator.max_count | 整数 | 10000000 | 最大生成数量 |
| generator.batch_size | 整数 | 500 | 每批次生成数量 |
| generator.file_size_limit | 整数 | 20 | 分批下载阈值（MB） |

## 使用说明

### 访问应用

打开浏览器访问：`http://localhost:5000`

### 查询条件

| 字段 | 必填 | 说明 |
|------|------|------|
| 前3位号段 | 是 | 手机号前3位，如：130、138、159 |
| 后4位号码 | 否 | 手机号最后4位，精确匹配 |
| 后3位号码 | 否 | 手机号最后3位，精确匹配 |
| 省份 | 是 | 归属地省份 |
| 城市 | 是 | 归属地城市 |
| 运营商 | 否 | 运营商类型（可多选） |

### 运营商编码

| 编码 | 运营商 |
|------|--------|
| 1 | 移动 |
| 2 | 联通 |
| 3 | 电信 |
| 4 | 广电 |
| 5 | 工信 |

### 下载文件

生成完成后，点击下载链接即可下载文件。文件格式为`.txt`，每行一个手机号码。

## API文档

### 登录接口

```http
POST /api/login
Content-Type: application/json

{
    "username": "admin",
    "password": "admin123"
}
```

**响应**：
```json
{
    "code": 200,
    "message": "登录成功",
    "redirect_url": "/"
}
```

### 生成接口

```http
POST /api/generate
Content-Type: application/json

{
    "prefix": "130",
    "suffix_4": "1234",
    "province": "湖北",
    "city": "武汉",
    "operators": [1, 2]
}
```

**响应**：
```json
{
    "code": 200,
    "message": "生成成功",
    "data": {
        "count": 15000,
        "files": [
            {
                "name": "130_湖北_武汉_1234_20250123.txt",
                "size": "156 KB",
                "url": "/download/130_湖北_武汉_1234_20250123.txt"
            }
        ]
    }
}
```

### 下载接口

```http
GET /download/<filename>
```

## 部署说明

### 使用Systemd服务

1. 创建服务文件：

```bash
sudo vim /etc/systemd/system/phone-generator.service
```

2. 服务文件内容：

```ini
[Unit]
Description=Phone Number Generator
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/project
ExecStart=/path/to/project/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. 启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable phone-generator
sudo systemctl start phone-generator
```

### 使用Nginx反向代理（可选）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 数据管理

### 初始化数据

```bash
python final_import.py              # 自动模式
python final_import.py --force      # 强制重新导入
python final_import.py --check      # 仅检查状态
```

### 数据格式

CSV文件格式（UTF-8编码）：

```csv
号段,区域码,省份,城市,运营商类型
130,0008,湖北,武汉,2
138,0000,湖北,武汉,1
```

## 常见问题

### 登录页面不显示？

检查 `config.yaml` 中 `login.enabled` 是否设为 `true`。

### 生成的号码不完整？

检查查询条件是否过于宽泛，或超过最大生成数量限制（默认1000万条）。

### 下载文件乱码？

使用支持UTF-8编码的文本编辑器打开文件。

### 导入数据失败？

检查CSV文件编码是否为UTF-8，格式是否正确。

### 如何清理过期文件？

访问 `/api/cleanup` 接口或等待系统自动清理（默认24小时后）。

## 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看Systemd服务日志
sudo journalctl -u phone-generator -f
```

## 更新部署

```bash
# 停止服务
sudo systemctl stop phone-generator

# 备份数据
cp -r data/ data_backup/

# 更新代码
git pull

# 重启服务
sudo systemctl start phone-generator
```

## 许可证

本项目仅供学习和研究使用。

## 作者

Phone Number Generator
