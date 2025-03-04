import logging
from flask import Flask, request, jsonify, send_file
import gmsh
import mesh_generator
import os
import re
from PIL import Image
import subprocess
app = Flask(__name__)

# 设置日志
logging.basicConfig(level=logging.INFO)

class MeshConfig:
    def __init__(self, length=3.0, width=2.0, lc1=0.1,
                 big_circle_radius=0.2, big_circle_center=(0.25, 0),
                 small_circle_radius=0.1, small_circle_center=(-0.25, 0),
                 mesh_algorithm=8, element_order=2, characteristic_length_factor=0.8,shape='circle'):
        self.length = length
        self.width = width
        self.lc1 = lc1
        self.big_circle_radius = big_circle_radius
        self.big_circle_center = big_circle_center
        self.small_circle_radius = small_circle_radius
        self.small_circle_center = small_circle_center
        self.mesh_algorithm = mesh_algorithm
        self.element_order = element_order
        self.characteristic_length_factor = characteristic_length_factor
        self.shape = shape

# 初始化 GMSH
def initialize_gmsh():
    if not gmsh.isInitialized():
        gmsh.initialize()  # 确保 GMSH 只在主线程中初始化
        logging.info("Gmsh initialized")

# 执行linux命令
def execute_command(command):
    """
    执行给定的 Linux 命令。
    参数:
    command (str): 要执行的命令行字符串。
    """
    try:
        # 使用 subprocess.run 执行命令
        subprocess.run(command, shell=True, check=True)
        print(f"命令 '{command}' 执行成功。")
    except subprocess.CalledProcessError as e:
        print(f"执行命令时出错: {e}")

# 登录并执行所需操作
def container_operation():
    GMSHTEST_PATH = '/app/gmshtest'
    # 生成网格文件
    LibGmsh2Specfem_PATH = '/app/specfem2d/utils/Gmsh'
    # 执行 Python 脚本
    python_command = (
        f'cd {GMSHTEST_PATH}/MESH && '
        f'python3 {LibGmsh2Specfem_PATH}/LibGmsh2Specfem_convert_Gmsh_to_Specfem2D_official.py '
        'SqrCirc -t F -b A -r A -l A'
    )
    execute_command(python_command)
    # 执行 Shell 脚本 生成 jpg和semp文件
    shell_command = f'cd {GMSHTEST_PATH} && ./run_this_example.sh'
    execute_command(shell_command)
    # 生成gif
    create_gif_from_images(f'{GMSHTEST_PATH}/OUTPUT_FILES',f'{GMSHTEST_PATH}/OUTPUT_FILES/output.gif')
    logging.info('生成Gif成功')

def sqrCirc(shape_type,config):
    if shape_type == 'circle':
        mesh_generator.generate_circle_mesh( output_filename="SqrCirc.msh",
    length=config.length, width=config.width,  # 矩形尺寸
    lc1=config.lc1,  # 网格尺寸
    big_circle_radius=config.big_circle_radius, big_circle_center=config.big_circle_center,  # 大圆参数
    small_circle_radius=config.small_circle_radius, small_circle_center=config.small_circle_center,  # 小圆参数
    mesh_algorithm=config.mesh_algorithm,  # 网格算法
    element_order=config.element_order,  # 单元阶数
    characteristic_length_factor=config.characteristic_length_factor)  # 调用生成圆形网格的函数
    elif shape_type == 'ellipse':
        mesh_generator.generate_ellipse_mesh()  # 调用生成椭圆网格的函数

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
    config = MeshConfig(**data)  # 反序列化 JSON 为对象
    # 根据 shape 参数决定调用哪个函数
    if config.shape == 'circle':
        sqrCirc('circle',config)
    elif config.shape == 'ellipse':
        sqrCirc('ellipse',config)
    else:
        return jsonify({"error": "Invalid shape type"}), 400
    container_operation()
    return jsonify({"message": "success"}), 200


# 定义一个路由来发送图片文件
@app.route('/get_image/<filename>', methods=['GET'])
def get_image(filename):
    # 确保图片存在于文件夹中
    image_path = os.path.join('/app/gmshtest/OUTPUT_FILES', filename)

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