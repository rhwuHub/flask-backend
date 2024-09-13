# app.py
import os

from flask import Flask, request, jsonify
import gmsh
import paramiko

app = Flask(__name__)



# 初始化 GMSH 的方法
def initialize_gmsh():
    if not gmsh.isInitialized():
        gmsh.initialize()  # 确保 GMSH 只在主线程中初始化
        print("Gmsh initialized")

# 定义一个简单的 POST 接口
@app.route('/test', methods=['POST'])
def test():
    data = request.json
    sqrCirc()
    # 返回接收到的数据，可以根据实际情况修改处理逻辑
    return jsonify({"received_data": data}), 200


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

    # 终止 Gmsh
    # gmsh.finalize()

# 用python登录服务器，构建python脚本执行
# python ../../../utils/Gmsh/LibGmsh2Specfem_convert_Gmsh_to_Specfem2D_official.py SqrCirc -t F -b A -r A -l A将msh转换成specfem2d需要的网格文件
# cd .. 返回run/gmshtest
# 运行run_this_example.sh

def login_operation():
    # 配置连接参数
    hostname = ''  # 服务器地址
    port = 22  # SSH 端口，通常是 22
    username = 'root'  # SSH 用户名
    password = ''  # SSH 密码
    remote_directory = '/path/to/new_directory'  # 远程服务器上要创建的文件夹路径

    try:
        # 创建 SSH 客户端对象
        ssh = paramiko.SSHClient()

        # 自动添加主机密钥
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # 连接到服务器
        ssh.connect(hostname, port, username, password)

        # 使用 SSH 连接执行命令
        stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_directory}')

        # 获取命令执行结果
        error = stderr.read().decode()
        if error:
            print(f'Error: {error}')
        else:
            print(f'Folder created successfully at {remote_directory}')

    finally:
        # 关闭连接
        ssh.close()


if __name__ == '__main__':
    if not gmsh.isInitialized():
        initialize_gmsh()
    app.run(host='0.0.0.0', port=5000)
