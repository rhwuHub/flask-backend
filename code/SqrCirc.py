# -*- coding: utf-8 -*-
"""
Created on Tue Sep  3 23:32:02 2024

@author: firew
"""

import gmsh

gmsh.initialize()

gmsh.model.add("t4")

cm = 1e-02

# 定义矩形的尺寸
length = 2.0
width = 2.0
lc1 = 0.1

factory = gmsh.model.geo


# add a square
factory.addPoint(length/2, width/2, 0, lc1, 1)
factory.addPoint(length/2, -width/2, 0, lc1, 2)
factory.addPoint(-length/2, -width/2, 0, lc1, 3)
factory.addPoint(-length/2, width/2, 0, lc1, 4)

factory.addLine(1,4,1)
factory.addLine(4,3,2)
factory.addLine(3,2,3)
factory.addLine(2,1,4)

factory.addCurveLoop([1, 2, 3, 4], 10)
# factory.addPlaneSurface([1], 1)

# add a big circle
R = 0.2
Centx = 0.25
Centy = 0
factory.addPoint(Centx, R+Centy, 0, lc1, 5)
factory.addPoint(R+Centx, Centy, 0, lc1, 6)
factory.addPoint(-R+Centx, Centy, 0, lc1, 7)
factory.addPoint(Centx, -R+Centy, 0, lc1, 8)
factory.addPoint(Centx, Centy, 0, lc1, 9)
factory.addCircleArc(5, 9, 7, 5)
factory.addCircleArc(7, 9, 8, 6)
factory.addCircleArc(8, 9, 6, 7)
factory.addCircleArc(6, 9, 5, 8)
factory.addCurveLoop([5, 6, 7, 8], 9)

# add a small circle
R=0.1
Centx=-0.25
Centy=0
factory.addPoint(Centx, R+Centy, 0, lc1, 105)
factory.addPoint(R+Centx, Centy, 0, lc1, 106)
factory.addPoint(-R+Centx, Centy, 0, lc1, 107)
factory.addPoint(Centx, -R+Centy, 0, lc1, 108)
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

# 保存网格为 .msh 文件
gmsh.write("SqrCirc.msh")

# 终止 Gmsh
gmsh.finalize()