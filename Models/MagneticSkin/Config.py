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
import magtec


class Config(GmshDesignOptimization):
    def __init__(self):
        super(GmshDesignOptimization,self).__init__("MagneticSkin")

        
    def init_model_parameters(self):

        # ----Geometric parameters (mm)----
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
        self.VolumeMeshCharacteristicLength = 1.2

        self.GridRowsSensors = 3
        self.GridColsSensors = 5

        # margin 
        self.margin_x = 6
        self.margin_y = 10
        self.BoxTolerance = 0.2
        self.indenterRadius = 2

        
        # --- Magnet density ---
        self.MagnetDensity_x = 0.031
        self.MagnetDensity_y = 0.041
        self.MagnetGridOrientation = 0  
        self.delta_x =0
        self.delta_y = 0

        self.spacing_x = np.sqrt(1.0 / self.MagnetDensity_x)
        self.spacing_y = np.sqrt(1.0 / self.MagnetDensity_y)
        self.grid_xy = magtec.Utils.generate_infinite_grid(self.spacing_x, 
                                                           self.spacing_y, n=30, 
                                                           angle_deg=self.MagnetGridOrientation, 
                                                           origin=(self.delta_x, self.delta_y))


        # ------------------------------------------------------------------------------------
        #                         End of configurable parameters 
        # ------------------------------------------------------------------------------------

        # ---- Generate grid points on the XY plane for magnets and sensors----
        self.MagnetGridPoints = magtec.Utils.cut_grid(self.grid_xy, length=self.Length, width=self.Width, margin_x=2.5, margin_y=2.5)
        self.SensorGridPoints = magtec.Utils.generate_grid(self.Length, self.Width, self.margin_x, self.margin_y, self.GridRowsSensors,  self.GridColsSensors)

        # ---- Magnets and Sensors centers 3D coordinates ---- 
        self.MagnetCenters = [[px, py, 4 ] for px, py in self.MagnetGridPoints]
        self.SensorCenters = [[px, py, 1.25 ] for px, py in self.SensorGridPoints] 

        # ---- Number of magnets and sensors ----
        self.NMagnets = len(self.MagnetCenters)    
        self.NSensors = len(self.SensorCenters)
        self.NumberSensors = 15    # design variable for selection of number of sensors

        # ---- Rigid Articulation center 3D coordinates ----
        self.rigidArticulationCenter = np.array([[-self.Length/2, 0, 0]])

        # ---- Rigid center 3D coordinates ----
        self.rigidObjects = np.vstack([self.rigidArticulationCenter, self.SensorCenters, self.MagnetCenters]).tolist()

        # Defines a fixed region of interest (ROI) box with margins around the magnetic skin (rigid)
        self.BoxROIFixCoords = magtec.Utils.getBoxroiCoords(centers = [[-0, 0, 0]] , #3.5
                                        lengths = [self.Length/1.01, self.Width, self.BoxTolerance], #2.3
                                        tolerance = self.BoxTolerance)

        # Defines a rigidified region box on the opposite side (articulation)
        self.BoxROIFixCoordsArt = magtec.Utils.getBoxroiCoords(centers = [[-self.Length/4  , 0, 0]] , 
                                            lengths = [self.Length/2, self.Width, self.BoxTolerance],
                                            tolerance = self.BoxTolerance)


        # ---- BoxROI coordinates for sensors and magnets----
        self.SensorBoxCoords = magtec.Utils.getBoxroiCoords(centers = self.SensorCenters, 
                                        lengths = (3, 3, 1.5), 
                                        tolerance = self.BoxTolerance)

        self.MagnetBoxCoords = magtec.Utils.getBoxroiCoords(centers = self.MagnetCenters, 
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
            "MagnetDensity_x": [self.MagnetDensity_x, 0.005, 0.031],   
            "MagnetDensity_y": [self.MagnetDensity_y, 0.005, 0.041], 
            "MagnetGridOrientation": [self.MagnetGridOrientation, 0.0, 45.0],
            "delta_x": [self.delta_x, -4.5/2, 4.5/2],
            "delta_y": [self.delta_y, -3.8/2, 3.8/2], 
            "NumberSensors": [self.NumberSensors, 1, 15.0],
        }
    

    def get_objective_data(self):
        return {
            "MagnetNumber": ["minimize", 145],
            "SensorNumber": ["minimize", 145],
            "MagneticSensitivity": ["maximize", 1085],     
        }

    def get_assessed_together_objectives(self):
        return [["MagnetNumber", "SensorNumber", "MagneticSensitivity"]]                    

    def set_design_variables(self, new_values):
        super(Config,self).set_design_variables(new_values)

        # ---- Update dependent parameters ----
        self.spacing_x = np.sqrt(1.0 / self.MagnetDensity_x)
        self.spacing_y = np.sqrt(1.0 / self.MagnetDensity_y)

        self.grid_xy = magtec.Utils.generate_infinite_grid(self.spacing_x, self.spacing_y, 
                                              n=30, angle_deg=self.MagnetGridOrientation, 
                                              origin=(self.delta_x, self.delta_y))
        
        self.MagnetGridPoints = magtec.Utils.cut_grid(self.grid_xy, length=self.Length, width=self.Width, margin_x=3, margin_y=3)
        self.MagnetCenters = [[px, py, 4 ] for px, py in self.MagnetGridPoints]
        self.NMagnets = len(self.MagnetCenters)    

        self.rigidObjects = np.vstack([self.rigidArticulationCenter,
                                       self.SensorCenters, 
                                       self.MagnetCenters]).tolist()
        
        self.MagnetBoxCoords = magtec.Utils.getBoxroiCoords(centers = self.MagnetCenters, 
                                               lengths = (self.MagnetSide, self.MagnetSide, self.MagnetSide),
                                               tolerance = self.BoxTolerance)
        
        self.rigidObjectsBoxCoords = np.vstack([self.BoxROIFixCoordsArt, 
                                                self.SensorBoxCoords, 
                                                self.MagnetBoxCoords]).tolist()
        
        self.MagnetSensors = np.vstack([ self.MagnetBoxCoords, self.SensorBoxCoords]).tolist()