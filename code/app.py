import paramiko
import logging
from flask import Flask, request, jsonify
import gmsh
app = Flask(__name__)

# 设置日志
logging.basicConfig(level=logging.INFO)

# 初始化 GMSH
def initialize_gmsh():
    if not gmsh.isInitialized():
        gmsh.initialize()  # 确保 GMSH 只在主线程中初始化
        logging.info("Gmsh initialized")

# 从文件加载配置
def load_config(filename):
    config = {}
    try:
        with open(filename, 'r') as file:
            for line in file:
                key, value = line.strip().split('=', 1)
                config[key] = value
    except FileNotFoundError as e:
        logging.error(f"配置文件未找到: {e}")
        raise
    return config

# 执行SSH命令的通用函数
def execute_ssh_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    stderr_output = stderr.read().decode().strip()
    if stderr_output:
        logging.error(f"执行命令失败: {command}\n错误: {stderr_output}")
        return False
    return True

# 登录并执行所需操作
def login_operation():
    config_file = '/app/config.txt'  # 根据环境（docker/本地）调整路径
    config = load_config(config_file)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # 连接到服务器
        ssh.connect(
            hostname=config['hostname'],
            port=int(config['port']),
            username=config['username'],
            password=config['password']
        )

        # 复制 SqrCirc.msh 文件
        source_path = config['SqrCirc_PATH']
        destination_path = config['GMSHTEST_PATH']
        copy_command = f'cp -rf {source_path} {destination_path}/MESH'
        if execute_ssh_command(ssh, copy_command):
            logging.info('成功将 SqrCirc 复制到 MESH 目录')
        else:
            logging.error('复制 SqrCirc 到 MESH 失败')

        LibGmsh2Specfem_PATH = config['LibGmsh2Specfem_PATH']
        # 执行 Python 脚本
        python_command = (
            f'cd {destination_path}/MESH && '
            f'python3 {LibGmsh2Specfem_PATH}/LibGmsh2Specfem_convert_Gmsh_to_Specfem2D_official.py '
            'SqrCirc -t F -b A -r A -l A'
        )
        if execute_ssh_command(ssh, python_command):
            logging.info('Python 脚本执行成功')
        else:
            logging.error('Python 脚本执行失败')

        # 执行 Shell 脚本
        shell_command = f'cd {destination_path} && ./run_this_example.sh'
        if execute_ssh_command(ssh, shell_command):
            logging.info('Shell 脚本执行成功')
        else:
            logging.error('Shell 脚本执行失败')

    finally:
        ssh.close()

# 定义一个简单的 POST 接口
@app.route('/test_update', methods=['POST'])
def test():
    data = request.json
    initialize_gmsh()
    login_operation()
    return jsonify({"received_data": data}), 200
