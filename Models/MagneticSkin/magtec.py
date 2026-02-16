#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 15 09:29:11 2025

@author: benjamin
"""

# ---- import libraries ----
import numpy as np
import h5py
import os
import itertools
import matplotlib.pyplot as plt
from collections import defaultdict
from scipy.spatial.transform import Rotation as R

class Utils:
    @staticmethod
    def minmax_norm(x):
        return (x - x.min()) / (x.max() - x.min() + 1e-8)
    @staticmethod
    def taxel_grid(n):
        k = int(np.log2(np.sqrt(n)))
        p = 2**k

        while n % p != 0:
            p //= 2
        return n // p, p
    
    @staticmethod
    def generate_grid(length, width, margin_x, margin_y, rows, cols):
        '''Generates a 2D grid of (x, y) points within a rectangle'''
        x = np.linspace(-(length - margin_x) / 2, (length - margin_x) / 2, cols)
        y = np.linspace(-(width - margin_y) / 2, (width - margin_y) / 2, rows)
        X, Y = np.meshgrid(x, y)
        return np.column_stack((X.ravel(), Y.ravel()))
    
    @staticmethod
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
    
    @staticmethod
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
    

    @staticmethod
    def get_taxels(xmin, xmax, ymin, ymax, Nx, Ny):

        Lx = xmax - xmin
        Ly = ymax - ymin

        dx = Lx / Nx
        dy = Ly / Ny

        center_taxels = []
        for iy in range(Ny):
            for ix in range(Nx):
                cx = xmin + (ix + 0.5) * dx
                cy = ymin + (iy + 0.5) * dy
                center_taxels.append((cx, cy))

        return center_taxels
    
    
    @staticmethod    
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


    @staticmethod
    def S_trajectory(points, heigth):
        """
        Generates an S-shaped trajectory
        """
        pts = np.array(points)
        x_vals = np.unique(pts[:, 0])
        trayectoria = []
        invertir = False

        for x in x_vals:
            columna = pts[pts[:, 0] == x]
            columna = columna[np.argsort(columna[:, 1])]
            if invertir:
                columna = columna[::-1]

            for p in columna:
                x_, y_ = p
                trayectoria.append([x_, y_, heigth])  
            invertir = not invertir

        return np.array(trayectoria)

    
    @staticmethod
    def compute_metric_single_combination(MagneticField, sensor_idx):

        B_magnitude = np.linalg.norm(MagneticField[:, sensor_idx, :], axis=2)
        B_sum_per_taxel = np.sum(B_magnitude, axis=1)

        return float(np.mean(B_sum_per_taxel))



    @staticmethod
    def compute_metrics(MagneticField, combinations_k):

        B_norm = np.linalg.norm(MagneticField, axis=2)

        n_comb = len(combinations_k)

        metric = np.zeros(n_comb)
        stds = np.zeros(n_comb)
        total_sum_per_taxel = []
        combs = list(combinations_k)

        for i, comb in enumerate(combinations_k):
            sensor_idx = list(comb)

            B_sum_per_taxel = np.sum(B_norm[:, sensor_idx], axis=1)

            metric[i] = np.mean(B_sum_per_taxel)
            stds[i]   = np.std(B_sum_per_taxel)

            total_sum_per_taxel.append(B_sum_per_taxel)

        order = np.argsort(metric)

        return metric, stds, order, combs, total_sum_per_taxel


class MagneticFieldModel:
    """
    Magnetic dipole field model.

    Parameters
    ----------
    mu_hat : array-like (3,)
        Unit vector indicating magnetic moment direction.
    mu_magnitude : float
        Magnetic moment magnitude (A·m²).
    """

    def __init__(self, mu_hat, mu_magnitude):

        self.mu_hat = np.asarray(mu_hat, dtype=float)
        self.mu_hat = self.mu_hat / np.linalg.norm(self.mu_hat)

        self.mu_magnitude = float(mu_magnitude)
        self.mu = self.mu_hat * self.mu_magnitude

    def compute_field(self, r):
        """
        Compute magnetic field at position r.

        Parameters
        ----------
        r : array-like (..., 3)
            Position vector(s) relative to dipole (meters).

        Returns
        -------
        B : ndarray (..., 3)
            Magnetic field in microTesla (µT).
        """

        r = np.asarray(r, dtype=float)
        r_norm = np.linalg.norm(r, axis=-1, keepdims=True)

        r_hat = r / r_norm

        tensor_term = 3 * np.sum(r_hat * self.mu, axis=-1, keepdims=True) * r_hat - self.mu

        B = tensor_term / (4 * np.pi * (r_norm**3))
        return B * 1e6  # convert to microTesla



class MagneticFieldSimulator:
    """
    Simulates the magnetic field at multiple sensor positions from multiple magnets.
    """

    def __init__(self, mu_magnitude):
        self.mu_magnitude = mu_magnitude

    def compute_field(
        self,
        sensor_pose: np.ndarray,
        magnet_pose: np.ndarray
    ) -> np.ndarray:
        """
        Compute the total magnetic field at each sensor position.

        Parameters
        ----------
        sensor_pose : (NSensors, 7) array
            Sensor positions and quaternions (x, y, z, qx, qy, qz, qw)
        magnet_pose : (NMagnets, 7) array
            Magnet positions and quaternions (x, y, z, qx, qy, qz, qw)

        Returns
        -------
        GlobalMagneticField : (NSensors, 3)
            Total magnetic field at each sensor
        """

        NSensors = sensor_pose.shape[0]
        NMagnets = magnet_pose.shape[0]

        SensorPosition = sensor_pose[:, :3]
        MagnetPosition = magnet_pose[:, :3]

        GlobalMagneticField = []

        for j in range(NSensors):

            LocalMagneticField = []

            quat_sensor = sensor_pose[j, 3:7]
            R_sensor = R.from_quat(quat_sensor).inv().as_matrix()

            for i in range(NMagnets):
                delta_local = R_sensor @ (SensorPosition[j] - MagnetPosition[i])

                quat_magnet = magnet_pose[i, 3:7]
                R_magnet = R.from_quat(quat_magnet).as_matrix()
                rotation_matrix = R_sensor @ R_magnet
                mu_direction = rotation_matrix[:, 2]

                magnet_model = MagneticFieldModel(mu_direction, self.mu_magnitude)
                B_local = magnet_model.compute_field(delta_local)
                LocalMagneticField.append(B_local)

            GlobalMagneticField.append(np.sum(LocalMagneticField, axis=0))

        return np.array(GlobalMagneticField)