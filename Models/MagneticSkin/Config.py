# -*- coding: utf-8 -*-

"""
Created on Mon May 19 09:29:11 2025

@author: benjamin

Config for the MagTecSkinSensor
"""


import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.absolute())+"/../")
sys.path.insert(0, str(pathlib.Path(__file__).parent.absolute()))

from BaseConfig import GmshDesignOptimization
import numpy as np 


def generate_grid(length, width, margin_x, margin_y, rows, cols):
    '''Generates a 2D grid of (x, y) points within a rectangle'''
    x = np.linspace(-(length - margin_x) / 2, (length - margin_x) / 2, cols)
    y = np.linspace(-(width - margin_y) / 2, (width - margin_y) / 2, rows)
    X, Y = np.meshgrid(x, y)
    return np.column_stack((X.ravel(), Y.ravel()))


def generate_infinite_grid(spacing_x, spacing_y, n, angle_deg, origin=(0.0, 0.0)):
    xs = np.arange(-n, n+1) * spacing_x
    ys = np.arange(-n, n+1) * spacing_y
    X, Y = np.meshgrid(xs, ys)
    points = np.column_stack((X.ravel(), Y.ravel()))

    theta = np.deg2rad(angle_deg)
    R = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta),  np.cos(theta)]
    ])
    points = points @ R.T

    points[:, 0] += origin[0]
    points[:, 1] += origin[1]

    return points

def cut_grid(points, length, width, margin_x, margin_y):
    xmin = -(length - margin_x) / 2
    xmax = +(length - margin_x) / 2
    ymin = -(width  - margin_y) / 2
    ymax = +(width  - margin_y) / 2

    mask = (
        (points[:, 0] >= xmin) & (points[:, 0] <= xmax) &
        (points[:, 1] >= ymin) & (points[:, 1] <= ymax)
    )
    return points[mask]



def getBoxroiCoords(centers, lengths, tolerance):
    '''Generates the coordinates for creating a BoxROI'''
    lx, ly, lz = lengths
    boxes = []

    for px, py, pz in centers:
        box = [
            px - (lx / 2 + tolerance),
            py - (ly / 2 + tolerance),
            pz - (lz / 2 + tolerance),
            px + (lx / 2 + tolerance),
            py + (ly / 2 + tolerance),
            pz + (lz / 2 + tolerance)
        ]
        boxes.append(box)
    return boxes


class Config(GmshDesignOptimization):
    def __init__(self):
        super(GmshDesignOptimization,self).__init__("MagneticSkin")

        
    def init_model_parameters(self):

        # ----Geometric parameters----
        self.Length = 50
        self.Width = 20 
        self.Height = 5 

        # ----Elasticity parameters----
        self.PoissonRatio = 0.47         # Poisson's ratio of the material
        self.YoungsModulus = 151685     # Young's modulus DSkin30 - 40psi (material stiffness)

        # --- Magnet Parameters ---
        self.MagnetSide = 1
        self.mu_magnitude = 4.627195188680999e-08

        # --- Meshing parameters ---
        self.SurfaceMeshCharacteristicLength = 0.8
        self.VolumeMeshCharacteristicLength = 1.4

        self.GridRowsSensors = 3
        self.GridColsSensors = 5

        # margin 
        self.margin_x = 6
        self.margin_y = 10
        self.BoxTolerance = 0.1
        self.indenterRadius = 2

        
        # --- Magnet density ---
        self.MagnetDensity_x = 0.01
        self.MagnetDensity_y = 0.035
        self.MagnetGridOrientation = 0  # degrees
        self.delta_x = 0
        self.delta_y = 0

        self.spacing_x = np.sqrt(1.0 / self.MagnetDensity_x)
        self.spacing_y = np.sqrt(1.0 / self.MagnetDensity_y)
        self.grid_xy = generate_infinite_grid(self.spacing_x, self.spacing_y, n=30, angle_deg=self.MagnetGridOrientation, origin=(self.delta_x, self.delta_y))


        
        # ------------------------------------------------------------------------------------
        #                         End of configurable parameters 
        # ------------------------------------------------------------------------------------

        # ---- Generate grid points on the XY plane for magnets and sensors----
        self.MagnetGridPoints = cut_grid(self.grid_xy, length=self.Length, width=self.Width, margin_x=2.5, margin_y=2.5)
        self.SensorGridPoints = generate_grid(self.Length, self.Width, self.margin_x, self.margin_y, self.GridRowsSensors,  self.GridColsSensors)

        # ---- Magnets and Sensors centers 3D coordinates ---- 
        self.MagnetCenters = [[px, py, 4 ] for px, py in self.MagnetGridPoints]
        self.SensorCenters = [[px, py, 1.25 ] for px, py in self.SensorGridPoints]  # - ArticulationAxis in z axis for Simulationthumbfinger  

        # ---- Number of magnets and sensors ----
        self.NMagnets = len(self.MagnetCenters)    
        self.NSensors = len(self.SensorCenters)
        self.NumberSensors = 14    # design variable for selection of number of sensors

        # ---- Rigid Articulation center 3D coordinates ----
        self.rigidArticulationCenter = np.array([[-self.Length/2, 0, 0]])

        # ---- Rigid center 3D coordinates ----
        self.rigidObjects = np.vstack([self.rigidArticulationCenter, self.SensorCenters, self.MagnetCenters]).tolist()

        # Defines a fixed region of interest (ROI) box with margins around the magnetic skin (rigid)
        self.BoxROIFixCoords = getBoxroiCoords(centers = [[-0, 0, 0]] , #3.5
                                        lengths = [self.Length/1.01, self.Width, self.BoxTolerance], #2.3
                                        tolerance = self.BoxTolerance)

        # Defines a rigidified region box on the opposite side (articulation)
        self.BoxROIFixCoordsArt = getBoxroiCoords(centers = [[-self.Length/4  , 0, 0]] , 
                                            lengths = [self.Length/2, self.Width, self.BoxTolerance],
                                            tolerance = self.BoxTolerance)


        # ---- BoxROI coordinates for sensors and magnets----
        self.SensorBoxCoords = getBoxroiCoords(centers = self.SensorCenters, 
                                        lengths = (3, 3, 1.5), 
                                        tolerance = self.BoxTolerance)

        self.MagnetBoxCoords = getBoxroiCoords(centers = self.MagnetCenters, 
                                        lengths = (self.MagnetSide, self.MagnetSide, self.MagnetSide),
                                        tolerance = self.BoxTolerance)


        # --- right BoxROI para el borde derecho ---
        self.BoxROIFixCoords_base = [
            self.Length / 2 + self.BoxTolerance, 
            self.Width / 2 + self.BoxTolerance, 
            self.Height  + self.BoxTolerance,  
            self.Length / 2 - self.BoxTolerance,       
            -(self.Width / 2 + self.BoxTolerance),
            - self.BoxTolerance 
            ]

        # --- left BoxROI ---
        self.BoxROIFixCoords1 = [
            -(self.Length / 2 - self.BoxTolerance),           
            self.Width  / 2 + self.BoxTolerance,   
            self.Height + self.BoxTolerance,       
            -(self.Length / 2 + self.BoxTolerance),
            -(self.Width / 2 + self.BoxTolerance), 
            -self.BoxTolerance     
            ]

        self.rigidObjectsBoxCoords = np.vstack([self.BoxROIFixCoordsArt, self.SensorBoxCoords, self.MagnetBoxCoords]).tolist()
        self.MagnetSensors = np.vstack([ self.MagnetBoxCoords, self.SensorBoxCoords]).tolist()
   


    def get_design_variables(self):
        return {
            # "numberSensor": [self.NSensors, 0.0, 14],
            "MagnetDensity_x": [self.MagnetDensity_x, 0.005, 0.05],   # me falta agregar el de numero de sensores (con una mascara)
            "MagnetDensity_y": [self.MagnetDensity_y, 0.005, 0.05], 
            "MagnetGridOrientation": [self.MagnetGridOrientation, 0.0, 45.0],
            "delta_x": [self.delta_x, -0.5, 0.5],
            "delta_y": [self.delta_y, -0.5, 0.5], 
            "NumberSensors": [self.NumberSensors, 1, 15.0],
        }
    

    def get_objective_data(self):
        return {
        "MagnetNumber": ["minimize", 142],
        "SensorNumber": ["minimize", 142],
        "MagneticSensitivity": ["maximize", 142],     
        }

    def get_assessed_together_objectives(self):
        # return [["MagneticSensitivity", "SensorsNumber"]]
        return [["MagnetNumber", "SensorNumber", "MagneticSensitivity"]]                    

    def set_design_variables(self, new_values):
        super(Config,self).set_design_variables(new_values)

        # ---- Update dependent parameters ----
        self.spacing_x = np.sqrt(1.0 / self.MagnetDensity_x)
        self.spacing_y = np.sqrt(1.0 / self.MagnetDensity_y)

        self.grid_xy = generate_infinite_grid(self.spacing_x, self.spacing_y, 
                                              n=30, angle_deg=self.MagnetGridOrientation, 
                                              origin=(self.delta_x, self.delta_y))
        
        self.MagnetGridPoints = cut_grid(self.grid_xy, length=self.Length, width=self.Width, margin_x=3, margin_y=3)
        self.MagnetCenters = [[px, py, 4 ] for px, py in self.MagnetGridPoints]
        self.NMagnets = len(self.MagnetCenters)    

        self.rigidObjects = np.vstack([self.rigidArticulationCenter,
                                       self.SensorCenters, 
                                       self.MagnetCenters]).tolist()
        
        self.MagnetBoxCoords = getBoxroiCoords(centers = self.MagnetCenters, 
                                               lengths = (self.MagnetSide, self.MagnetSide, self.MagnetSide),
                                               tolerance = self.BoxTolerance)
        
        self.rigidObjectsBoxCoords = np.vstack([self.BoxROIFixCoordsArt, 
                                                self.SensorBoxCoords, 
                                                self.MagnetBoxCoords]).tolist()
        


# # -*- coding: utf-8 -*-
# """
# Created on Mon May 19 09:29:11 2025

# @author: benjamin

# Config for the MagTecSkinSensor
# UNITS: SI (meters, seconds, kilograms)
# """

# import sys
# import pathlib
# sys.path.insert(0, str(pathlib.Path(__file__).parent.absolute()) + "/../")
# sys.path.insert(0, str(pathlib.Path(__file__).parent.absolute()))

# from BaseConfig import GmshDesignOptimization
# import numpy as np


# # ============================================================
# # Unit conversion
# # ============================================================
# MM_TO_M = 1e-3


# # ============================================================
# # Helper functions
# # ============================================================
# def generate_grid(length, width, margin_x, margin_y, rows, cols):
#     """Generates a 2D grid of (x, y) points within a rectangle"""
#     x = np.linspace(-(length - margin_x) / 2, (length - margin_x) / 2, cols)
#     y = np.linspace(-(width - margin_y) / 2, (width - margin_y) / 2, rows)
#     X, Y = np.meshgrid(x, y)
#     return np.column_stack((X.ravel(), Y.ravel()))


# def generate_infinite_grid(spacing_x, spacing_y, n, angle_deg, origin=(0.0, 0.0)):
#     xs = np.arange(-n, n + 1) * spacing_x
#     ys = np.arange(-n, n + 1) * spacing_y
#     X, Y = np.meshgrid(xs, ys)
#     points = np.column_stack((X.ravel(), Y.ravel()))

#     theta = np.deg2rad(angle_deg)
#     R = np.array([
#         [np.cos(theta), -np.sin(theta)],
#         [np.sin(theta),  np.cos(theta)]
#     ])
#     points = points @ R.T

#     points[:, 0] += origin[0]
#     points[:, 1] += origin[1]

#     return points


# def cut_grid(points, length, width, margin_x, margin_y):
#     xmin = -(length - margin_x) / 2
#     xmax = +(length - margin_x) / 2
#     ymin = -(width  - margin_y) / 2
#     ymax = +(width  - margin_y) / 2

#     mask = (
#         (points[:, 0] >= xmin) & (points[:, 0] <= xmax) &
#         (points[:, 1] >= ymin) & (points[:, 1] <= ymax)
#     )
#     return points[mask]


# def getBoxroiCoords(centers, lengths, tolerance):
#     """Generates the coordinates for creating a BoxROI"""
#     lx, ly, lz = lengths
#     boxes = []

#     for px, py, pz in centers:
#         box = [
#             px - (lx / 2 + tolerance),
#             py - (ly / 2 + tolerance),
#             pz - (lz / 2 + tolerance),
#             px + (lx / 2 + tolerance),
#             py + (ly / 2 + tolerance),
#             pz + (lz / 2 + tolerance)
#         ]
#         boxes.append(box)
#     return boxes


# # ============================================================
# # Config class
# # ============================================================
# class Config(GmshDesignOptimization):

#     def __init__(self):
#         super(GmshDesignOptimization, self).__init__("MagneticSkin")

#     def init_model_parameters(self):

#         # --------------------------------------------------------
#         # Geometry (meters)
#         # --------------------------------------------------------
#         self.Length = 50 * MM_TO_M
#         self.Width  = 20 * MM_TO_M
#         self.Height = 5  * MM_TO_M

#         # --------------------------------------------------------
#         # Elasticity (SI)
#         # --------------------------------------------------------
#         self.PoissonRatio = 0.47
#         self.YoungsModulus = 151685  # Pa

#         # --------------------------------------------------------
#         # Magnet parameters (meters)
#         # --------------------------------------------------------
#         self.MagnetSide = 1 * MM_TO_M
#         self.mu_magnitude = 4.627195188680999e-08

#         # --------------------------------------------------------
#         # Meshing (meters)
#         # --------------------------------------------------------
#         self.SurfaceMeshCharacteristicLength = 0.8 * MM_TO_M
#         self.VolumeMeshCharacteristicLength  = 1.4 * MM_TO_M

#         # --------------------------------------------------------
#         # Sensor grid
#         # --------------------------------------------------------
#         self.GridRowsSensors = 3
#         self.GridColsSensors = 5

#         self.margin_x = 6  * MM_TO_M
#         self.margin_y = 10 * MM_TO_M
#         self.BoxTolerance = 0.1 * MM_TO_M
#         self.indenterRadius = 2 * MM_TO_M

#         # --------------------------------------------------------
#         # Magnet density (converted from mm⁻² → m⁻²)
#         # --------------------------------------------------------
#         self.MagnetDensity_x = 0.01  / (MM_TO_M ** 2)
#         self.MagnetDensity_y = 0.035 / (MM_TO_M ** 2)

#         self.MagnetGridOrientation = 0
#         self.delta_x = 0.0
#         self.delta_y = 0.0

#         self.spacing_x = np.sqrt(1.0 / self.MagnetDensity_x)
#         self.spacing_y = np.sqrt(1.0 / self.MagnetDensity_y)

#         self.grid_xy = generate_infinite_grid(
#             self.spacing_x,
#             self.spacing_y,
#             n=30,
#             angle_deg=self.MagnetGridOrientation,
#             origin=(self.delta_x, self.delta_y)
#         )

#         # --------------------------------------------------------
#         # Generate magnet and sensor grids
#         # --------------------------------------------------------
#         self.MagnetGridPoints = cut_grid(
#             self.grid_xy,
#             length=self.Length,
#             width=self.Width,
#             margin_x=2.5 * MM_TO_M,
#             margin_y=2.5 * MM_TO_M
#         )

#         self.SensorGridPoints = generate_grid(
#             self.Length,
#             self.Width,
#             self.margin_x,
#             self.margin_y,
#             self.GridRowsSensors,
#             self.GridColsSensors
#         )

#         # --------------------------------------------------------
#         # 3D centers (meters)
#         # --------------------------------------------------------
#         self.MagnetCenters = [[px, py, 4 * MM_TO_M] for px, py in self.MagnetGridPoints]
#         self.SensorCenters = [[px, py, 1.25 * MM_TO_M] for px, py in self.SensorGridPoints]

#         self.NMagnets = len(self.MagnetCenters)
#         self.NSensors = len(self.SensorCenters)
#         self.NumberSensors = 14

#         # --------------------------------------------------------
#         # Rigid objects
#         # --------------------------------------------------------
#         self.rigidArticulationCenter = np.array([[-self.Length / 2, 0.0, 0.0]])
#         self.rigidObjects = np.vstack([
#             self.rigidArticulationCenter,
#             self.SensorCenters,
#             self.MagnetCenters
#         ]).tolist()

#         # --------------------------------------------------------
#         # ROI definitions
#         # --------------------------------------------------------
#         self.BoxROIFixCoords = getBoxroiCoords(
#             centers=[[0.0, 0.0, 0.0]],
#             lengths=[self.Length / 1.01, self.Width, self.BoxTolerance],
#             tolerance=self.BoxTolerance
#         )

#         self.BoxROIFixCoordsArt = getBoxroiCoords(
#             centers=[[-self.Length / 4, 0.0, 0.0]],
#             lengths=[self.Length / 2, self.Width, self.BoxTolerance],
#             tolerance=self.BoxTolerance
#         )

#         self.SensorBoxCoords = getBoxroiCoords(
#             centers=self.SensorCenters,
#             lengths=(3 * MM_TO_M, 3 * MM_TO_M, 1.5 * MM_TO_M),
#             tolerance=self.BoxTolerance
#         )

#         self.MagnetBoxCoords = getBoxroiCoords(
#             centers=self.MagnetCenters,
#             lengths=(self.MagnetSide, self.MagnetSide, self.MagnetSide),
#             tolerance=self.BoxTolerance
#         )

#         self.rigidObjectsBoxCoords = np.vstack([
#             self.BoxROIFixCoordsArt,
#             self.SensorBoxCoords,
#             self.MagnetBoxCoords
#         ]).tolist()

#         self.MagnetSensors = np.vstack([
#             self.MagnetBoxCoords,
#             self.SensorBoxCoords
#         ]).tolist()

#         self.BoxROIFixCoords_base = [
#                 self.Length / 2 + self.BoxTolerance, 
#                 self.Width / 2 + self.BoxTolerance, 
#                 self.Height  + self.BoxTolerance,  
#                 self.Length / 2 - self.BoxTolerance,       
#                 -(self.Width / 2 + self.BoxTolerance),
#                 - self.BoxTolerance 
#             ]

#         # --- left BoxROI ---
#         self.BoxROIFixCoords1 = [
#             -(self.Length / 2 - self.BoxTolerance),           
#             self.Width  / 2 + self.BoxTolerance,   
#             self.Height + self.BoxTolerance,       
#             -(self.Length / 2 + self.BoxTolerance),
#             -(self.Width / 2 + self.BoxTolerance), 
#             -self.BoxTolerance     
#             ]

#     # ============================================================
#     # Optimization interface
#     # ============================================================
#     def get_design_variables(self):
#         return {
#             "MagnetDensity_x": [self.MagnetDensity_x, 0.005 / (MM_TO_M**2), 0.05 / (MM_TO_M**2)],
#             "MagnetDensity_y": [self.MagnetDensity_y, 0.005 / (MM_TO_M**2), 0.05 / (MM_TO_M**2)],
#             "MagnetGridOrientation": [self.MagnetGridOrientation, 0.0, 45.0],
#             "delta_x": [self.delta_x, -0.5 * MM_TO_M, 0.5 * MM_TO_M],
#             "delta_y": [self.delta_y, -0.5 * MM_TO_M, 0.5 * MM_TO_M],
#             "NumberSensors": [self.NumberSensors, 1, 15.0],
#         }

#     def get_objective_data(self):
#         return {
#             "MagnetNumber": ["minimize", 142],
#             "SensorNumber": ["minimize", 142],
#             "MagneticSensitivity": ["maximize", 142],
#         }

#     def get_assessed_together_objectives(self):
#         return [["MagnetNumber", "SensorNumber", "MagneticSensitivity"]]

#     def set_design_variables(self, new_values):
#         super(Config, self).set_design_variables(new_values)

#         self.spacing_x = np.sqrt(1.0 / self.MagnetDensity_x)
#         self.spacing_y = np.sqrt(1.0 / self.MagnetDensity_y)

#         self.grid_xy = generate_infinite_grid(
#             self.spacing_x,
#             self.spacing_y,
#             n=30,
#             angle_deg=self.MagnetGridOrientation,
#             origin=(self.delta_x, self.delta_y)
#         )

#         self.MagnetGridPoints = cut_grid(
#             self.grid_xy,
#             length=self.Length,
#             width=self.Width,
#             margin_x=3 * MM_TO_M,
#             margin_y=3 * MM_TO_M
#         )

#         self.MagnetCenters = [[px, py, 4 * MM_TO_M] for px, py in self.MagnetGridPoints]
#         self.NMagnets = len(self.MagnetCenters)

#         self.rigidObjects = np.vstack([
#             self.rigidArticulationCenter,
#             self.SensorCenters,
#             self.MagnetCenters
#         ]).tolist()

#         self.MagnetBoxCoords = getBoxroiCoords(
#             centers=self.MagnetCenters,
#             lengths=(self.MagnetSide, self.MagnetSide, self.MagnetSide),
#             tolerance=self.BoxTolerance
#         )

#         self.rigidObjectsBoxCoords = np.vstack([
#             self.BoxROIFixCoordsArt,
#             self.SensorBoxCoords,
#             self.MagnetBoxCoords
#         ]).tolist()
