# meoknow-backend

## 部署

文件夹结构大致如下

```
上一级文件夹
- venv/
- meoknow-backend/
	- .git
	- meoknow/
		- __init__.py
	- instance/
		- meoknow.db
		- photos/
		
```

*   创建虚拟环境

```shell
py -3 -m venv venv
```

*   激活环境

```shell
venv\Scripts\activate
```

*   导入requirements.txt

```shell
pip install -r requirements.txt
```

*   clone后端库

```shell
git clone https://github.com/Meoknow/meoknow-backend.git
cd meoknow-backend
git checkout dev
```

*   安装sqlite3 : [Windows10如何安装Sqlite3_Eddie-Wang的博客-CSDN博客](https://blog.csdn.net/wangchaox123/article/details/89925951)

*   在`instance/`目录下创建meoknow.db

```shell
cd instance
sqlite3 meoknow.db

sqlite> .quit

cd ..
```

这个路径其实与`meoknow/__init__.py`中的`SQLALCHEMY_DATABASE_URI`一致

*   **注**：目前的话，已经创建的数据库是无法修改结构的。如果你想要更新数据库（比如当后端更新代码后，或者你干脆想要清空数据库里的所有数据），你可以删除之前的数据库文件并按以上步骤新建一个
    *   未来会提供管理员操作数据库的接口



## 测试

### 对于Windows系统

*   激活环境，在包含venv的目录下：

```cmd
venv\Scripts\activate
```

例如，如果venv在当前上一级目录下就是

```
..\venv\Scripts\activate
```



*   在开发模式下运行应用

```cmd
set FLASK_APP=meoknow
set FLASK_ENV=development
flask run
```

*   本地查看 http://127.0.0.1:5000/hello，前端可以往[localhost:5000/]()发送数据

