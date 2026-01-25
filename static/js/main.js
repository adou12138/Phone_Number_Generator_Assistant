/**
 * 手机号码生成查询系统 - JavaScript工具库
 * 
 * 本文件包含项目中常用的JavaScript工具函数和公共逻辑。
 * 可以在所有页面中引入使用。
 * 
 * 功能模块：
 * 1. API请求封装
 * 2. 表单验证工具
 * 3. DOM操作工具
 * 4. 格式化工具
 * 5. 事件处理工具
 * 
 * 作者：Phone Number Generator
 * 版本：1.0.0
 */


/**
 * API请求模块
 * 封装常用的HTTP请求方法
 */
const API = {
    /**
     * 发送GET请求
     * @param {string} url - 请求URL
     * @param {object} params - URL参数对象
     * @returns {Promise} 请求Promise
     */
    get: function(url, params = {}) {
        // 构建URL参数
        const urlObj = new URL(url, window.location.origin);
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                urlObj.searchParams.append(key, params[key]);
            }
        });
        
        return fetch(urlObj.toString(), {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(this._handleResponse);
    },
    
    /**
     * 发送POST请求
     * @param {string} url - 请求URL
     * @param {object} data - 请求数据
     * @returns {Promise} 请求Promise
     */
    post: function(url, data = {}) {
        return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        }).then(this._handleResponse);
    },
    
    /**
     * 处理响应
     * @param {Response} response - Fetch响应对象
     * @returns {Promise} 解析后的数据
     */
    _handleResponse: function(response) {
        // 检查HTTP状态码
        if (!response.ok) {
            throw new Error(`HTTP Error: ${response.status}`);
        }
        
        // 解析JSON响应
        return response.json().then(data => {
            // 如果状态码表示错误，抛出异常
            if (data.code && data.code >= 400) {
                throw new Error(data.message || '请求失败');
            }
            return data;
        });
    }
};


/**
 * 表单验证模块
 * 提供常用的表单验证功能
 */
const Validator = {
    /**
     * 验证必填字段
     * @param {string} value - 输入值
     * @returns {boolean} 是否通过验证
     */
    required: function(value) {
        return value !== null && value !== undefined && value.trim() !== '';
    },
    
    /**
     * 验证手机号段（3位数字）
     * @param {string} value - 输入值
     * @returns {boolean} 是否通过验证
     */
    prefix: function(value) {
        return /^[0-9]{3}$/.test(value);
    },
    
    /**
     * 验证后4位号码
     * @param {string} value - 输入值
     * @returns {boolean} 是否通过验证
     */
    suffix4: function(value) {
        return value === '' || /^[0-9]{4}$/.test(value);
    },
    
    /**
     * 验证后3位号码
     * @param {string} value - 输入值
     * @returns {boolean} 是否通过验证
     */
    suffix3: function(value) {
        return value === '' || /^[0-9]{3}$/.test(value);
    },
    
    /**
     * 验证运营商类型
     * @param {Array} values - 运营商值数组
     * @returns {boolean} 是否通过验证
     */
    operators: function(values) {
        const validOperators = [1, 2, 3, 4, 5];
        if (!values || values.length === 0) {
            return true; // 可选字段
        }
        return values.every(op => validOperators.includes(op));
    },
    
    /**
     * 验证表单数据
     * @param {object} formData - 表单数据对象
     * @returns {object} 验证结果 {valid, message}
     */
    validateForm: function(formData) {
        // 验证号段
        if (!this.required(formData.prefix)) {
            return { valid: false, message: '请输入手机号前3位号段' };
        }
        if (!this.prefix(formData.prefix)) {
            return { valid: false, message: '号段必须为3位数字' };
        }
        
        // 验证省份
        if (!this.required(formData.province)) {
            return { valid: false, message: '请选择省份' };
        }
        
        // 验证城市
        if (!this.required(formData.city)) {
            return { valid: false, message: '请选择城市' };
        }
        
        // 验证后4位
        if (!this.suffix4(formData.suffix4)) {
            return { valid: false, message: '后4位必须为4位数字' };
        }
        
        // 验证后3位
        if (!this.suffix3(formData.suffix3)) {
            return { valid: false, message: '后3位必须为3位数字' };
        }
        
        // 验证运营商
        if (!this.operators(formData.operators)) {
            return { valid: false, message: '包含无效的运营商类型' };
        }
        
        return { valid: true };
    }
};


/**
 * DOM操作工具模块
 * 提供常用的DOM操作功能
 */
const DOM = {
    /**
     * 根据ID获取元素
     * @param {string} id - 元素ID
     * @returns {HTMLElement|null} 元素或null
     */
    getById: function(id) {
        return document.getElementById(id);
    },
    
    /**
     * 根据选择器获取元素
     * @param {string} selector - CSS选择器
     * @returns {NodeList} 元素列表
     */
    queryAll: function(selector) {
        return document.querySelectorAll(selector);
    },
    
    /**
     * 根据选择器获取单个元素
     * @param {string} selector - CSS选择器
     * @returns {HTMLElement|null} 元素或null
     */
    query: function(selector) {
        return document.querySelector(selector);
    },
    
    /**
     * 创建元素
     * @param {string} tagName - 标签名
     * @param {object} attributes - 属性对象
     * @param {string} textContent - 文本内容
     * @returns {HTMLElement} 创建的元素
     */
    create: function(tagName, attributes = {}, textContent = '') {
        const element = document.createElement(tagName);
        
        // 设置属性
        Object.keys(attributes).forEach(key => {
            if (key === 'className') {
                element.className = attributes[key];
            } else if (key === 'dataset') {
                Object.keys(attributes[key]).forEach(dataKey => {
                    element.dataset[dataKey] = attributes[key][dataKey];
                });
            } else {
                element.setAttribute(key, attributes[key]);
            }
        });
        
        // 设置文本内容
        if (textContent) {
            element.textContent = textContent;
        }
        
        return element;
    },
    
    /**
     * 显示元素
     * @param {HTMLElement} element - 元素
     */
    show: function(element) {
        if (element) {
            element.style.display = '';
        }
    },
    
    /**
     * 隐藏元素
     * @param {HTMLElement} element - 元素
     */
    hide: function(element) {
        if (element) {
            element.style.display = 'none';
        }
    },
    
    /**
     * 添加类名
     * @param {HTMLElement} element - 元素
     * @param {string} className - 类名
     */
    addClass: function(element, className) {
        if (element) {
            element.classList.add(className);
        }
    },
    
    /**
     * 移除类名
     * @param {HTMLElement} element - 元素
     * @param {string} className - 类名
     */
    removeClass: function(element, className) {
        if (element) {
            element.classList.remove(className);
        }
    },
    
    /**
     * 设置元素文本
     * @param {HTMLElement} element - 元素
     * @param {string} text - 文本内容
     */
    setText: function(element, text) {
        if (element) {
            element.textContent = text;
        }
    }
};


/**
 * 格式化工具模块
 * 提供常用的格式化功能
 */
const Format = {
    /**
     * 格式化数字（添加千分位）
     * @param {number} num - 数字
     * @returns {string} 格式化后的字符串
     */
    number: function(num) {
        return num.toLocaleString('zh-CN');
    },
    
    /**
     * 格式化文件大小
     * @param {number} bytes - 字节数
     * @returns {string} 格式化后的大小字符串
     */
    fileSize: function(bytes) {
        if (bytes === 0) return '0 B';
        
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        const k = 1024;
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + units[i];
    },
    
    /**
     * 格式化日期时间
     * @param {Date|string} date - 日期对象或日期字符串
     * @param {string} format - 格式模板
     * @returns {string} 格式化后的日期字符串
     */
    dateTime: function(date, format = 'YYYY-MM-DD HH:mm:ss') {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    }
};


/**
 * 事件处理工具模块
 */
const Event = {
    /**
     * 添加事件监听器
     * @param {HTMLElement} element - 元素
     * @param {string} eventType - 事件类型
     * @param {Function} handler - 事件处理函数
     */
    on: function(element, eventType, handler) {
        if (element) {
            element.addEventListener(eventType, handler);
        }
    },
    
    /**
     * 移除事件监听器
     * @param {HTMLElement} element - 元素
     * @param {string} eventType - 事件类型
     * @param {Function} handler - 事件处理函数
     */
    off: function(element, eventType, handler) {
        if (element) {
            element.removeEventListener(eventType, handler);
        }
    },
    
    /**
     * 阻止表单默认提交行为
     * @param {HTMLFormElement} form - 表单元素
     */
    preventFormSubmit: function(form) {
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
            });
        }
    },
    
    /**
     * 监听输入变化（防抖）
     * @param {HTMLElement} input - 输入元素
     * @param {Function} handler - 处理函数
     * @param {number} delay - 延迟时间（毫秒）
     */
    onInputDebounce: function(input, handler, delay = 300) {
        if (input) {
            let timeoutId = null;
            input.addEventListener('input', function() {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => {
                    handler(this.value);
                }, delay);
            });
        }
    }
};


/**
 * 提示消息工具
 * 提供友好的用户提示功能
 */
const Toast = {
    /**
     * 显示成功提示
     * @param {string} message - 消息内容
     */
    success: function(message) {
        this._show(message, 'success');
    },
    
    /**
     * 显示错误提示
     * @param {string} message - 消息内容
     */
    error: function(message) {
        this._show(message, 'error');
    },
    
    /**
     * 显示警告提示
     * @param {string} message - 消息内容
     */
    warning: function(message) {
        this._show(message, 'warning');
    },
    
    /**
     * 显示信息提示
     * @param {string} message - 消息内容
     */
    info: function(message) {
        this._show(message, 'info');
    },
    
    /**
     * 内部提示显示方法
     * @param {string} message - 消息内容
     * @param {string} type - 提示类型
     */
    _show: function(message, type) {
        // 创建提示元素
        const toast = DOM.create('div', {
            className: `toast toast-${type}`,
            dataset: { role: 'toast' }
        }, message);
        
        // 设置样式
        Object.assign(toast.style, {
            position: 'fixed',
            top: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            padding: '12px 24px',
            borderRadius: '6px',
            color: '#ffffff',
            fontSize: '14px',
            zIndex: '9999',
            opacity: '0',
            transition: 'opacity 0.3s ease',
            backgroundColor: type === 'success' ? '#4CAF50' :
                            type === 'error' ? '#f44336' :
                            type === 'warning' ? '#ff9800' : '#2196F3'
        });
        
        // 添加到页面
        document.body.appendChild(toast);
        
        // 显示动画
        setTimeout(() => {
            toast.style.opacity = '1';
        }, 10);
        
        // 自动消失
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
};


/**
 * Loading状态管理
 */
const Loading = {
    /**
     * 显示Loading
     * @param {string} message - 提示消息
     */
    show: function(message = '加载中...') {
        // 检查是否已存在Loading
        if (DOM.query('.loading-overlay')) {
            return;
        }
        
        // 创建遮罩层
        const overlay = DOM.create('div', {
            className: 'loading-overlay',
            dataset: { role: 'loading' }
        });
        
        // 设置样式
        Object.assign(overlay.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            width: '100%',
            height: '100%',
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: '9998'
        });
        
        // 创建Loading内容
        const content = DOM.create('div', {
            className: 'loading-content'
        });
        
        // 设置内容样式
        Object.assign(content.style, {
            backgroundColor: '#ffffff',
            padding: '30px 40px',
            borderRadius: '8px',
            textAlign: 'center'
        });
        
        // 创建旋转图标
        const spinner = DOM.create('div', {
            className: 'loading-spinner'
        });
        
        // 设置旋转图标样式
        Object.assign(spinner.style, {
            width: '40px',
            height: '40px',
            border: '3px solid #f0f0f0',
            borderTopColor: '#2196F3',
            borderRadius: '50%',
            margin: '0 auto 15px',
            animation: 'spin 0.8s linear infinite'
        });
        
        // 创建消息文本
        const messageEl = DOM.create('p', {}, message);
        Object.assign(messageEl.style, {
            color: '#666666',
            fontSize: '14px'
        });
        
        // 组装元素
        content.appendChild(spinner);
        content.appendChild(messageEl);
        overlay.appendChild(content);
        
        // 添加动画样式
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
        
        // 添加到页面
        document.body.appendChild(overlay);
    },
    
    /**
     * 隐藏Loading
     */
    hide: function() {
        const overlay = DOM.query('.loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }
};


/**
 * 工具函数集合
 */
const Utils = {
    /**
     * 获取URL参数
     * @param {string} name - 参数名
     * @returns {string|null} 参数值
     */
    getUrlParam: function(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    },
    
    /**
     * 复制文本到剪贴板
     * @param {string} text - 要复制的文本
     * @returns {Promise} 复制结果Promise
     */
    copyToClipboard: function(text) {
        return navigator.clipboard.writeText(text);
    },
    
    /**
     * 下载文件
     * @param {string} url - 文件URL
     * @param {string} filename - 文件名
     */
    downloadFile: function(url, filename) {
        const link = DOM.create('a', {
            href: url,
            download: filename
        });
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },
    
    /**
     * 获取选中的复选框值
     * @param {string} name - 复选框name属性
     * @returns {Array} 选中的值数组
     */
    getCheckedValues: function(name) {
        const checkboxes = DOM.queryAll(`input[name="${name}"]:checked`);
        return Array.from(checkboxes).map(cb => parseInt(cb.value));
    },
    
    /**
     * 延迟函数
     * @param {number} ms - 延迟毫秒数
     * @returns {Promise} Promise对象
     */
    delay: function(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
};


// 导出工具到全局
window.API = API;
window.Validator = Validator;
window.DOM = DOM;
window.Format = Format;
window.Event = Event;
window.Toast = Toast;
window.Loading = Loading;
window.Utils = Utils;
