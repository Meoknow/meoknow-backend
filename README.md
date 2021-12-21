# meoknow-backend

## 目录

*   [部署](#setup)
*   [运行](#run)
*   [测试](#test)
*   [配置](#config)



## 部署 <a id="setup"> </a>

文件夹结构大致如下

```
上一级文件夹
- venv/
- logs/					# 存放ML的模型文件
- meoknow-backend/
    - .git
    - meoknow/
        - __init__.py
    - instance/
        - meoknow.db
        - photos/
        - config.py
    - tests/
    - test_instance/
    README.md
```

*   创建虚拟环境

```shell
py -3 -m venv venv
```

*   激活环境

```shell
venv\Scripts\activate
```

*   clone后端库

```shell
git clone https://github.com/Meoknow/meoknow-backend.git
cd meoknow-backend
```

*   导入requirements.txt

```shell
pip install -r requirements.txt
```

*   安装sqlite3 ：可参考
    *    [Windows10如何安装Sqlite3_Eddie-Wang的博客-CSDN博客](https://blog.csdn.net/wangchaox123/article/details/89925951)
    *   Linux系统直接 `sudo apt-get install sqlite3 `



## 运行 <a id="run"> </a>

### 对于Windows系统

#### 在开发环境下运行（目前windows上只支持此选项）

*   激活环境，在包含venv的目录下：

```cmd
venv\Scripts\activate
```

例如，如果venv在当前上一级目录下就是

```shell
..\venv\Scripts\activate
```

*   在开发模式下运行应用

```cmd
set FLASK_APP=meoknow
set FLASK_ENV=development
flask run
```

*   本地查看 [http://127.0.0.1:5000/hello]()，前端可以往[localhost:5000/]()发送数据
*   你也可以打开[http://39.104.59.169:3000/admin/login](http://39.104.59.169:3000/admin/login)进入管理员界面

### 对于Linux系统

*   激活环境，在包含venv的目录下：

```shell
source venv/bin/activate
cd meoknow-backend
```

#### 在开发环境下运行

```shell
export FLASK_APP=meoknow
export FLASK_ENV=development
export CONFIG_PATH=$PWD/instance/config.py

flask run --host=0.0.0.0 --port=3000
```

浏览器中打开 [39.104.59.169:3000/hello/](http://39.104.59.169:3000/hello/)

#### 在生产环境下运行

比如，你的网站地址是`39.104.59.169:3000` 

```shell
export FLASK_APP=meoknow
export FLASK_ENV=production
export CONFIG_PATH=$PWD/instance/config.py
```

```shell
gunicorn "meoknow:create_app()" -b 0.0.0.0:3000 -w 1 --daemon
```



## 测试  <a id="test"> </a>

*   激活venv环境
*   在meoknow-backend目录下运行：

```shell
export PYTHONPATH=$PWD
python tests/test_comment.py
python tests/test_cats.py
```



## 配置 <a id="config"> </a>

*   默认配置文件为 `instance/config.py`

*   在部署到新环境时，你需要配置以下内容：

    ```python
    MINI_PROGRAM_APPID = "appid"                        # 小程序的APPID
    MINI_PROGRAM_APPSECRET = "appsecret"                # 小程序的APPSECRET
    JWT_SECRET = "jwtsecret"
    JWT_ALGORITHM = "HS512"
    JWT_EXPIRE_SECONDS = 30 * 86400                     # 1 month
    TIME_DELTA = 8
    URI_SCHEME = "http"
    URI_AUTHORITY = "39.104.59.169:3000"                # 服务器的地址
    ML_LOG_PATH = "/home/meoknow/logs/model0017.pth"    # 机器学习模型的路径
    ADMIN_USERNAME = "admin_username"                   # 管理员登录的用户名
    ADMIN_PASSWORD = "admin_password"                   # 管理员登录的密码
    BYPASS_LOGIN_CHECK = False                          # 是否关闭登录验证
    ```

    
