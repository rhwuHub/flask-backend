import paramiko
import logging
from flask import Flask, request, jsonify
import gmsh
import os
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
        with open(filename, 'r') as file:
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

def sqrCirc():
    gmsh.model.add("t4")

    cm = 1e-02

    # 定义矩形的尺寸
    length = 2.0
    width = 2.0
    lc1 = 0.1

    factory = gmsh.model.geo

    # add a square
    factory.addPoint(length / 2, width / 2, 0, lc1, 1)
    factory.addPoint(length / 2, -width / 2, 0, lc1, 2)
    factory.addPoint(-length / 2, -width / 2, 0, lc1, 3)
    factory.addPoint(-length / 2, width / 2, 0, lc1, 4)

    factory.addLine(1, 4, 1)
    factory.addLine(4, 3, 2)
    factory.addLine(3, 2, 3)
    factory.addLine(2, 1, 4)

    factory.addCurveLoop([1, 2, 3, 4], 10)
    # factory.addPlaneSurface([1], 1)

    # add a big circle
    R = 0.2
    Centx = 0.25
    Centy = 0
    factory.addPoint(Centx, R + Centy, 0, lc1, 5)
    factory.addPoint(R + Centx, Centy, 0, lc1, 6)
    factory.addPoint(-R + Centx, Centy, 0, lc1, 7)
    factory.addPoint(Centx, -R + Centy, 0, lc1, 8)
    factory.addPoint(Centx, Centy, 0, lc1, 9)
    factory.addCircleArc(5, 9, 7, 5)
    factory.addCircleArc(7, 9, 8, 6)
    factory.addCircleArc(8, 9, 6, 7)
    factory.addCircleArc(6, 9, 5, 8)
    factory.addCurveLoop([5, 6, 7, 8], 9)

    # add a small circle
    R = 0.1
    Centx = -0.25
    Centy = 0
    factory.addPoint(Centx, R + Centy, 0, lc1, 105)
    factory.addPoint(R + Centx, Centy, 0, lc1, 106)
    factory.addPoint(-R + Centx, Centy, 0, lc1, 107)
    factory.addPoint(Centx, -R + Centy, 0, lc1, 108)
    factory.addPoint(Centx, Centy, 0, lc1, 109)
    factory.addCircleArc(105, 109, 107, 105)
    factory.addCircleArc(107, 109, 108, 106)
    factory.addCircleArc(108, 109, 106, 107)
    factory.addCircleArc(106, 109, 105, 108)
    factory.addCurveLoop([105, 106, 107, 108], 109)

    factory.addPlaneSurface([10, 9, 109], 10)
    factory.addPlaneSurface([9], 11)
    factory.addPlaneSurface([109], 12)

    factory.synchronize()

    # 创建物理组
    # 1. 矩形区域的物理组，包括整个矩形区域

    top_physical_group = gmsh.model.addPhysicalGroup(1, [1])
    gmsh.model.setPhysicalName(1, top_physical_group, "Top")

    left_physical_group = gmsh.model.addPhysicalGroup(1, [2])
    gmsh.model.setPhysicalName(1, left_physical_group, "Left")

    right_physical_group = gmsh.model.addPhysicalGroup(1, [4])
    gmsh.model.setPhysicalName(1, right_physical_group, "Right")

    bottom_physical_group = gmsh.model.addPhysicalGroup(1, [3])
    gmsh.model.setPhysicalName(1, bottom_physical_group, "Bottom")

    # 2. 圆形区域的物理组，实际上为圆形内的单元指定不同的属性
    circle_physical_group = gmsh.model.addPhysicalGroup(2, [10])
    gmsh.model.setPhysicalName(2, circle_physical_group, "M1")

    sc_physical_group = gmsh.model.addPhysicalGroup(2, [11, 12])
    gmsh.model.setPhysicalName(2, sc_physical_group, "M2")

    # 生成四边形网格
    gmsh.option.setNumber("Mesh.Algorithm", 8)  # 使用四边形网格生成算法
    # gmsh.option.setNumber("Mesh.RecombineAll", 1)  # 强制使用四边形网格
    gmsh.option.setNumber("Mesh.ElementOrder", 2)  # 使用一阶网格
    gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 1)
    gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 2)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", 0.8)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.model.mesh.generate(2)
    output_dir = "data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # 保存网格为 .msh 文件
    gmsh.write(os.path.join(output_dir, "SqrCirc.msh"))


# 定义一个简单的 POST 接口
@app.route('/test_update', methods=['POST'])
def test():
    data = request.json
    sqrCirc()
    login_operation()
    return jsonify({"received_data": data}), 200

if __name__ == '__main__':
    if not gmsh.isInitialized():
        initialize_gmsh()
    app.run(host='0.0.0.0', port=5000)