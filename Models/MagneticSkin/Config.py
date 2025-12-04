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

def generate_grid(length, width, margin, rows, cols):

    '''Generates a 2D grid of (x, y) points within a rectangle'''
    x = np.linspace(-(length - margin) / 2, (length - margin) / 2, cols)
    y = np.linspace(-(width - margin) / 2, (width - margin) / 2, rows)
    X, Y = np.meshgrid(x, y)
    return np.column_stack((X.ravel(), Y.ravel()))


def getBoxroiCoords( centers, lengths, tolerance):
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
        self.Length = 40
        self.Width = 20
        self.Height = 3

        # ----Elasticity parameters----
        self.PoissonRatio = 0.4
        self.YoungsModulus = 60000

        # --- Magnet ---
        self.MagnetSide = 1
        self.mu_magnitude = 4.627195188680999e-08

        # --- Meshing parameters ---
        self.SurfaceMeshCharacteristicLength = 0.8
        self.VolumeMeshCharacteristicLength = 1.13

        self.GridMargin = 10
        self.GridRowsMagnets = 2
        self.GridColsMagnets = 3
        self.GridRowsSensors = 2
        self.GridColsSensors = 3

        self.BoxTolerance = 0.1
        self.mask_magnets = np.ones((self.GridRowsMagnets, self.GridColsMagnets))

        self.indenterRadius = 2

        self.ArticulationAngleRad = np.deg2rad(0)  


        self.BoxROIFixCoords = getBoxroiCoords(centers = [[self.Length/3.5, 0, 0]] , #3.5
                    lengths = [self.Length/2.3, self.Width, self.BoxTolerance], #2.3
                    tolerance = self.BoxTolerance)
        

        self.BoxROIFixCoords = getBoxroiCoords(centers=[[self.Length/3.5, 0, 0]],
                                                lengths=[self.Length/2.3, self.Width, self.BoxTolerance],
                                                tolerance=self.BoxTolerance)
        
        self.MagnetGridPoints = generate_grid(self.Length, self.Width, self.GridMargin,
                                                    self.GridRowsMagnets, self.GridColsMagnets)
        self.SensorGridPoints = generate_grid(self.Length, self.Width, self.GridMargin,
                                                    self.GridRowsSensors, self.GridColsSensors)

        self.MagnetCenters = [
            [px, py, self.Height/2]
            for (px, py), keep in zip(self.MagnetGridPoints, self.mask_magnets.ravel()) if keep == 1
        ]
        self.SensorCenters = [[px, py, -self.Height/2] for px, py in self.SensorGridPoints]

        # Centros de articulación rígida
        
        self.rigidArticulationCenter = np.array([[-self.Length/4, 0, 0]])
        self.rigidObjects = np.vstack([self.rigidArticulationCenter, self.MagnetCenters]).tolist()


        # BoxROI para articulacion
        self.BoxROIFixCoordsArt = getBoxroiCoords(centers=[[-self.Length/4, 0, 0]],
                                                  lengths=[self.Length/2, self.Width, self.BoxTolerance],
                                                  tolerance=self.BoxTolerance
                                            )
        self.MagnetBoxCoords = getBoxroiCoords( centers=self.rigidObjects[1:],
                                                lengths=(self.MagnetSide, self.MagnetSide, self.MagnetSide),
                                                tolerance=self.BoxTolerance
                                            )
        self.rigidObjectsBoxCoords = np.vstack([self.BoxROIFixCoordsArt, self.MagnetBoxCoords]).tolist()

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

        # print("SensorGridPoints:")
        # print(self.SensorGridPoints)

        # print("MagnetCenters:")
        # print(self.MagnetCenters)

        # print("SensorCenters:")
        # print(self.SensorCenters)

        # print("Rigid Objects:")
        # print(self.rigidObjects)

        # print("IndexPairs:")
        # print(self.IndexPairs)


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



    # def set_design_variables(self, new_values):
    #     super(Config,self).set_design_variables(new_values)


    #     # IndexPairs para mappings
    #     self.IndexPairs = [0, 1]
    #     for i in range(len(self.MagnetCenters)):
    #         self.IndexPairs.extend([1, i])



if __name__ == "__main__":
    cfg = Config()

