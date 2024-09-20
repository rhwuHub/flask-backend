import paramiko
import logging
from flask import Flask, request, jsonify, send_file
import gmsh
import mesh_generator
import os
import re
from PIL import Image
app = Flask(__name__)

# 设置日志
logging.basicConfig(level=logging.INFO)

# 初始化 GMSH
def initialize_gmsh():
    if not gmsh.isInitialized():
        gmsh.initialize()  # 确保 GMSH 只在主线程中初始化
        logging.info("Gmsh initialized")

# 从文件加载配置
# 从文件加载配置
def load_config(filename):
    config = {}
    try:
        with open(filename, 'r',encoding='utf-8') as file:
            for line in file:
                # 忽略以 # 开头的注释行
                if line.strip().startswith("#") or not line.strip():
                    continue
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
    config_file = '../config.txt'  # 根据环境（docker/本地）调整路径
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
        # gmshtest目录
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

        #     生成gif
        # create_gif_from_images('/data/specfem2d/my-gmsh-data/data/gmshtest/OUTPUT_FILES','/data/specfem2d/my-gmsh-data/data/gmshtest/OUTPUT_FILES/output.gif')
        logging.info('生成Gif成功')
    finally:
        ssh.close()

def sqrCirc():
    # mesh_generator.generate_circle_mesh()
    mesh_generator.generate_ellipse_mesh()

# 调用方法的示例：将图片生成gif
# create_gif_from_images('/data/picture', '/data/picture/output.gif')
def create_gif_from_images(image_dir, output_gif,max_size=(800,800)):
    """
    将指定目录中的所有 .jpg 文件按照文件名中的数字顺序合并为一个 GIF 动图。

    参数:
    - image_dir: 包含原图片的文件夹路径。
    - output_gif: 生成的 GIF 文件的保存路径。

    返回:
    - None
    """
    # 获取目录中所有的 .jpg 文件
    jpg_files = [f for f in os.listdir(image_dir) if f.endswith('.jpg')]

    # 使用正则表达式提取文件名中的数字，并按升序排序
    def get_image_number(filename):
        match = re.search(r'forward_image(\d+).jpg', filename)
        return int(match.group(1)) if match else -1

    sorted_jpg_files = sorted(jpg_files, key=get_image_number)
    # 读取所有图片并进行压缩
    images = []
    for file_name in sorted_jpg_files:
        file_path = os.path.join(image_dir, file_name)
        img = Image.open(file_path)

        # 如果图片的尺寸超过 max_size，则压缩图片
        img.thumbnail(max_size)

        images.append(img)

    # 将图片保存为 GIF
    if images:
        images[0].save(output_gif, save_all=True, append_images=images[1:], duration=500, loop=0)
        print(f"GIF 动图已成功生成并保存在: {output_gif}")
    else:
        print("未找到任何 .jpg 图片")




# 定义一个简单的 POST 接口
@app.route('/test_update', methods=['POST'])
def test():
    data = request.json
    sqrCirc()
    login_operation()
    return jsonify({"received_data": data}), 200


# 定义一个路由来发送图片文件
@app.route('/get_image/<filename>', methods=['GET'])
def get_image(filename):
    # 确保图片存在于文件夹中
    image_path = os.path.join('/app/OUTPUT_FILES', filename)

    if os.path.exists(image_path):
        # 发送图片文件到前端
        return send_file(image_path, mimetype='image/gif')  # 可以根据图片类型设置 MIME 类型
    else:
        # 如果文件不存在，返回错误信息
        return jsonify({"error": "File not found"}), 404


if __name__ == '__main__':
    if not gmsh.isInitialized():
        initialize_gmsh()
    app.run(host='0.0.0.0', port=5000)