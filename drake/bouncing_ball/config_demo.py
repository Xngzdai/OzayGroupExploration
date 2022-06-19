"""
config_demo.py
Description:
    Trying to support the basic meshcat visualizer from within a Drake container.
    Using this to visualize Kinova Gen3 6DoF
"""

import importlib
import sys
from urllib.request import urlretrieve

# Start a single meshcat server instance to use for the remainder of this notebook.
server_args = []
from meshcat.servers.zmqserver import start_zmq_server_as_subprocess
proc, zmq_url, web_url = start_zmq_server_as_subprocess(server_args=server_args)

# from manipulation import running_as_notebook

# Imports
import numpy as np
import pydot
from ipywidgets import Dropdown, Layout
from IPython.display import display, HTML, SVG

from pydrake.all import (
    AddMultibodyPlantSceneGraph, ConnectMeshcatVisualizer, DiagramBuilder, 
    FindResourceOrThrow, GenerateHtml, InverseDynamicsController, 
    MultibodyPlant, Parser, Simulator, RigidTransform , RotationMatrix )
from pydrake.multibody.jupyter_widgets import MakeJointSlidersThatPublishOnCallback

from pydrake.geometry import (Cylinder, GeometryInstance,
                                MakePhongIllustrationProperties)

##########################
## Function Definitions ##
##########################

def AddTriad(source_id,
             frame_id,
             scene_graph,
             length=.25,
             radius=0.01,
             opacity=1.,
             X_FT=RigidTransform(),
             name="frame"):
    """
    Adds illustration geometry representing the coordinate frame, with the
    x-axis drawn in red, the y-axis in green and the z-axis in blue. The axes
    point in +x, +y and +z directions, respectively.
    Args:
      source_id: The source registered with SceneGraph.
      frame_id: A geometry::frame_id registered with scene_graph.
      scene_graph: The SceneGraph with which we will register the geometry.
      length: the length of each axis in meters.
      radius: the radius of each axis in meters.
      opacity: the opacity of the coordinate axes, between 0 and 1.
      X_FT: a RigidTransform from the triad frame T to the frame_id frame F
      name: the added geometry will have names name + " x-axis", etc.
    """
    # x-axis
    X_TG = RigidTransform(RotationMatrix.MakeYRotation(np.pi / 2),
                          [length / 2., 0, 0])
    geom = GeometryInstance(X_FT.multiply(X_TG), Cylinder(radius, length),
                            name + " x-axis")
    geom.set_illustration_properties(
        MakePhongIllustrationProperties([1, 0, 0, opacity]))
    scene_graph.RegisterGeometry(source_id, frame_id, geom)

    # y-axis
    X_TG = RigidTransform(RotationMatrix.MakeXRotation(np.pi / 2),
                          [0, length / 2., 0])
    geom = GeometryInstance(X_FT.multiply(X_TG), Cylinder(radius, length),
                            name + " y-axis")
    geom.set_illustration_properties(
        MakePhongIllustrationProperties([0, 1, 0, opacity]))
    scene_graph.RegisterGeometry(source_id, frame_id, geom)

    # z-axis
    X_TG = RigidTransform([0, 0, length / 2.])
    geom = GeometryInstance(X_FT.multiply(X_TG), Cylinder(radius, length),
                            name + " z-axis")
    geom.set_illustration_properties(
        MakePhongIllustrationProperties([0, 0, 1, opacity]))
    scene_graph.RegisterGeometry(source_id, frame_id, geom)

def AddMultibodyTriad(frame, scene_graph, length=.25, radius=0.01, opacity=1.):
    plant = frame.GetParentPlant()
    AddTriad(plant.get_source_id(),
             plant.GetBodyFrameIdOrThrow(frame.body().index()), scene_graph,
             length, radius, opacity, frame.GetFixedPoseInBodyFrame())

# Building Diagram

builder = DiagramBuilder()

plant, scene_graph = AddMultibodyPlantSceneGraph(builder, time_step=1e-4)

# Parse CAD models and add them to the plant.
# Kinova Gen3 6DoF
Parser(plant, scene_graph).AddModelFromFile(FindResourceOrThrow("drake/kinova_drake/models/gen3_6dof/urdf/GEN3-6DOF.urdf"))
# Desk
Parser(plant, scene_graph).AddModelFromFile("/root/OzayGroupExploration/drake/simpleDesk2/simpleDesk2.urdf")
# Bouncy Ball
Parser(plant, scene_graph).AddModelFromFile("/root/OzayGroupExploration/drake/bouncing_ball/ball_model/ball.urdf")

"""# Ball location
pusher_position = [0.8,0.5,0.25]
# pusher_rotation=[0,np.pi/2,0]
pusher_rotation=[0,0,0]
X_pusher = RigidTransform()
X_pusher.set_translation(pusher_position)
X_pusher.set_rotation(RotationMatrix(RollPitchYaw(pusher_rotation)))
station.AddManipulandFromFile("pusher/pusher1_urdf.urdf",X_pusher)"""

# Weld table to world frame, with rotation about x
p_RightTableO = [0, 0, 0]
R_RightTableO = RotationMatrix.MakeXRotation(np.pi/2.0)
X_WorldTable = RigidTransform(R_RightTableO,p_RightTableO)
plant.WeldFrames(
    plant.world_frame(), plant.GetFrameByName("simpleDesk"),X_WorldTable)

# Weld robot to table, with translation in x, y and z
p_PlaceOnTable0 = [0.15,0.75,-0.20]
R_PlaceOnTableO = RotationMatrix.MakeXRotation(-np.pi/2.0)
X_TableRobot = RigidTransform(R_PlaceOnTableO,p_PlaceOnTable0)
plant.WeldFrames(
    plant.GetFrameByName("simpleDesk"),plant.GetFrameByName("base_link"),X_TableRobot)

plant.Finalize()
# Draw the frames
for body_name in ["base_link", "shoulder_link", "bicep_link", "forearm_link", "spherical_wrist_1_link", "spherical_wrist_2_link", "bracelet_with_vision_link", "end_effector_link"]:
    AddMultibodyTriad(plant.GetFrameByName(body_name), scene_graph)

meshcat = ConnectMeshcatVisualizer(builder, scene_graph, zmq_url=zmq_url)

""" 
meshcat.Delete()
meshcat.ResetRenderMode()
visualizer = MeshcatVisualizerCpp.AddToBuilder(
    builder, scene_graph, meshcat)
"""
diagram = builder.Build()

context = diagram.CreateDefaultContext()
meshcat.load()
diagram.Publish(context)

while True:
    1   
