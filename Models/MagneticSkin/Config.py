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
import math

def generate_grid(length, width, margin_x, margin_y, rows, cols):
    '''Generates a 2D grid of (x, y) points within a rectangle'''
    x = np.linspace(-(length - margin_x) / 2, (length - margin_x) / 2, cols)
    y = np.linspace(-(width - margin_y) / 2, (width - margin_y) / 2, rows)
    X, Y = np.meshgrid(x, y)
    return np.column_stack((X.ravel(), Y.ravel()))



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
        self.PoissonRatio = 0.4         # Poisson's ratio of the material
        self.YoungsModulus = 275790     # Young's modulus DSkin30 - 40psi (material stiffness)

        # --- Magnet Parameters ---
        self.MagnetSide = 1
        self.mu_magnitude = 4.627195188680999e-06

        # --- Meshing parameters ---
        self.SurfaceMeshCharacteristicLength = 0.8
        self.VolumeMeshCharacteristicLength = 1.13

        # ---- Generate grid for magnets and sensors positions  ----
        self.GridRowsMagnets = 2
        self.GridColsMagnets = 3
        self.GridRowsSensors = 2
        self.GridColsSensors = 3

        # margin 
        self.margin_x = 6
        self.margin_y = 10
        self.EdgeMargin = 0.1  

        self.BoxTolerance = 0.1
        self.mask_magnets = np.ones((self.GridRowsMagnets, self.GridColsMagnets))

        self.indenterRadius = 3

        self.ArticulationAngleRad = np.deg2rad(0)  




        '''
        ------------------------------------------------------------------------------------
                                End of configurable parameters 
        ------------------------------------------------------------------------------------
        '''


        # ---- Generate grid points on the XY plane for magnets and sensors----
        self.MagnetGridPoints = generate_grid(self.Length, self.Width, self.margin_x, self.margin_y, self.GridRowsMagnets,  self.GridColsMagnets)
        self.SensorGridPoints = generate_grid(self.Length, self.Width, self.margin_x, self.margin_y, self.GridRowsSensors,  self.GridColsSensors)

        # ---- Magnets and Sensors centers 3D coordinates ---- 
        self.MagnetCenters = [[px, py, 4 ] for px, py in self.MagnetGridPoints]
        self.SensorCenters = [[px, py, 1.25 ] for px, py in self.SensorGridPoints]  # - ArticulationAxis in z axis for Simulationthumbfinger  

        # ---- Number of magnets and sensors ----
        self.NMagnets = len(self.MagnetCenters)    
        self.NSensors = len(self.SensorCenters)


        # ---- Rigid Articulation center 3D coordinates ----
        self.rigidArticulationCenter = np.array([[-self.Length/2, 0, 0]])

        # ---- Rigid center 3D coordinates ----
        self.rigidObjects = np.vstack([self.rigidArticulationCenter, self.MagnetCenters, self.SensorCenters]).tolist()



        # Defines a fixed region of interest (ROI) box with margins around the magnetic skin (rigid)
        self.BoxROIFixCoords = getBoxroiCoords(centers = [[-0, 0, 0]] , #3.5
                                        lengths = [self.Length/1.01, self.Width, self.BoxTolerance], #2.3
                                        tolerance = self.BoxTolerance)


        
        # Defines a rigidified region box on the opposite side (articulation)
        self.BoxROIFixCoordsArt = getBoxroiCoords(centers = [[-self.Length/4  , 0, 0]] , 
                                            lengths = [self.Length/2, self.Width, self.BoxTolerance],
                                            tolerance = self.BoxTolerance)



        # Rigidified region for the thumb finger
        self.BoxROIFixCoordsThumb = getBoxroiCoords(centers = [[-self.Length/6.5, 0, 0]] , 
                                            lengths = [self.Length/1.4, self.Width, self.BoxTolerance],
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
            self.Length / 2 - self.EdgeMargin,       
            -(self.Width / 2 + self.BoxTolerance),
            - self.BoxTolerance 
            ]

        # --- left BoxROI ---
        self.BoxROIFixCoords1 = [
            -(self.Length / 2 - self.EdgeMargin),           
            self.Width  / 2 + self.BoxTolerance,   
            self.Height + self.BoxTolerance,       
            -(self.Length / 2 + self.BoxTolerance),
            -(self.Width / 2 + self.BoxTolerance), 
            -self.BoxTolerance     
            ]



        # self.ObjectsBoxCoords = np.vstack([ self.BoxROIFixCoordsArt, self.MagnetBoxCoords, self.SensorBoxCoords])
        
        # rigidObjectsBoxCoordsThumb = np.vstack([BoxROIFixCoordsThumb, MagnetBoxCoords, SensorBoxCoords])
        # rigidObjectsBoxCoordsThumb = rigidObjectsBoxCoordsThumb.tolist()

        self.rigidObjectsBoxCoords = np.vstack([self.BoxROIFixCoordsArt, self.MagnetBoxCoords, self.SensorBoxCoords]).tolist()
   

        self.ObjectsBoxCoords = np.vstack([ self.MagnetBoxCoords, self.SensorBoxCoords])
        print(self.ObjectsBoxCoords)

        # IndexPairs para mappings
        self.IndexPairs = [0, 1]
        for i in range(len(self.MagnetCenters)):
            self.IndexPairs.extend([1, i])

        # ---- Index for Sensor Centers ---- 
        self.indexPerPointSensor = []
        for center in self.SensorCenters:
            if center[0] > self.BoxTolerance:
                index = 0
            else:
                index = 1
            self.indexPerPointSensor.append(index)
    
        
        print('MagnetsBoxs')
        print(self.MagnetBoxCoords)

        print("MagnetGridPoints:")
        print(self.MagnetGridPoints)


        print(len(self.rigidObjectsBoxCoords))



    def get_design_variables(self):
        return {
            "Length": [self.Length, 20.0, 60.0],
            "Width": [self.Width, 10.0, 30.0],
            "Height": [self.Height, 2.0, 5.0],
            "MagnetSide": [self.MagnetSide, 0.5, 2.0],
        }
    

    def get_objective_data(self):
        return {
        "MagneticSensitivity": ["maximize", 100],
        "Deformation": ["minimize", 80]
        }


    def get_assessed_together_objectives(self):
        return [["MagneticSensitivity", "Deformation"]]


if __name__ == "__main__":
    cfg = Config()

