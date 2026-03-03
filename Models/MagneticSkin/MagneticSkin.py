#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 19 09:29:11 2025

@author: benjamin
"""

# ---- Import Libraries ----
import os
import numpy as np
import Sofa
import SofaRuntime
from stlib3.scene import Scene
from splib3.animation import animate
import rigidification  
import Sofa.Core
import Sofa.constants.Key as Key
from BaseFitnessEvaluationController import BaseFitnessEvaluationController
import itertools
from Generation import MagneticSkin
import magtec 
import time



M_hw =np.array([[12,9,6,3,0],[13,10,7,4,1],[14,11,8,5,2]])
A_hw = M_hw.flatten()
sim_to_hw = np.argsort(A_hw) 

identer_position = [0, 0, 0]
set_force = -800000  # ver unidades de medida 

class FitnessEvaluationController(BaseFitnessEvaluationController):   
    
    def __init__(self, *args, **kwargs):

        print('>>> Start Init SOFA scene ...')

        super(FitnessEvaluationController,self).__init__(*args, **kwargs)

        self.ModelNode = self.rootNode.solverNode.RigidNode.RigidifiedNode.deformableNode.model     
  
        # ----- SOFA nodes and objects -----
        self.RigidMO = kwargs['RigidMO']
        self.CFF = kwargs['CFF']
        self.CFFSphereROI = kwargs['CFFSphereROI'] 
        self.CFFMO = kwargs['CFFMO']   

        # Objective evaluation variables
        self.current_iter = 0
        current_objectives = self.config.get_currently_assessed_objectives()
        self.max_iter = max([self.config.get_objective_data()[current_objectives[i]][1] for i in range(len(current_objectives))])


        # ----- Time variables -----
        self.frames_to_wait = 30

        self.waiting = False
        self.current_point =  0
        self.force_wait_counter = 0
        self.offset = None

        # ----- Data -----
        self.data_MagneticField_000pct = []
        self.data_MagneticField_010pct = []
        self.data_MagneticField_020pct = []

        # ----- Stretch variables -----
        self.stretch_levels = [0.0, 0.10, 0.20]
        self.current_stretch_idx = 0
        self.current_stretch = self.stretch_levels[self.current_stretch_idx]

        self.state = "APPLY_STRETCH"
        self.state_counter = 0
        self.save_offset_flag = False
        self.offset_per_stretch = {}
        self.data_per_stretch = { 0.0:  [], 0.10: [], 0.20: [] }


        self.simulator = magtec.MagneticFieldSimulator(mu_magnitude=self.config.mu_magnitude, distance_unit='mm')



        centers_taxels = magtec.Utils.get_taxels(xmin=-self.config.Length/2, xmax= self.config.Length/2, 
                                                 ymin=-self.config.Width/2, ymax= self.config.Width/2,
                                                 Nx = 5, Ny = 2
                                                 )

        points_trajectory = magtec.Utils.S_trajectory(points=centers_taxels, heigth=self.config.Height)
        centers_ordened = []
        z_target = self.config.Height
        for center in points_trajectory:
            center_3d = np.array([center[0], center[1], z_target])
            centers_ordened.append(center_3d)
        self.trayectoria_5puntos= np.array(centers_ordened)


    def MoveCFFSphereROI(self, pos):   
        self.CFFSphereROI.centers = [pos.tolist()]

    
    def apply_stretch(self, displacement):
        grab = self.rootNode.ExternalRefNode.getObject('ExternalMO')
        currentValue = list(grab.translation.value)
        currentValue[0] = displacement
        grab.translation.value = currentValue
        grab.reinit()

    def fix_base(self, spring_stiffness):
        base_roi = self.rootNode.solverNode.RigidNode.RigidifiedNode.deformableNode.model.getObject('BaseFixROI')
        indices = base_roi.indices.value
        tetras = self.rootNode.solverNode.RigidNode.RigidifiedNode.deformableNode.model.getObject('tetras')
        positions = tetras.position.value
        base_positions = positions[indices]
        base_node = self.rootNode.ExternalRefNodeBase
        base = base_node.getObject('ExternalBaseMO')
        base.position.value = base_positions.tolist()
        base.reinit()
        spring = self.ModelNode.getObject('BaseFixSpring')
        spring.findData('stiffness').value = [spring_stiffness]

    def onAnimateBeginEvent(self, event):
        start_total = time.perf_counter()

        
        # ---------------- APPLY STRETCH ----------------
        if self.state == "APPLY_STRETCH":

            if self.state_counter == 0:
                displacement = -self.current_stretch * self.config.Width
                print(f"displacement: {displacement}")
                self.apply_stretch(displacement=displacement)
            self.state_counter += 1

            if self.state_counter >= 25:
                self.state_counter = 0
                self.state = "FIX_BASE"

        # ---------------- FIX BASE ----------------
        if self.state == "FIX_BASE":
            self.fix_base(spring_stiffness=1e8)
            self.save_offset_flag = True
            self.state = "RUN_TRAJECTORY"
        

        if self.state == "RUN_TRAJECTORY":


            if self.current_point >= len(self.trayectoria_5puntos):
                print(f"Trajectory ended for stretch {self.current_stretch}")

                self.fix_base(spring_stiffness=0)
                self.CFF.totalForce.value = [0.0, 0.0, 0.0]

                #  stretch
                self.current_stretch_idx += 1
                if self.current_stretch_idx >= len(self.stretch_levels):
                    print("All stretches completed")
                    self.state = "FINISHED"  

                else:
                    self.current_stretch = self.stretch_levels[self.current_stretch_idx]
                    self.current_point = 0
                    self.waiting = False
                    self.force_wait_counter = 0
                    self.state_counter = 0
                    self.state = "APPLY_STRETCH"


            else:
            
                # ---------- identer position ----------
                identer_position = self.trayectoria_5puntos[self.current_point]
                self.MoveCFFSphereROI(identer_position)

                # ---------- set force ----------
                self.CFF.totalForce.value = [0.0, 0.0, set_force]

                # ---------- time ----------
                self.force_wait_counter += 1

                if self.force_wait_counter >= self.frames_to_wait:
                    self.force_wait_counter = 0
                    self.waiting = True  # Activamos la espera para guardar datos
                    self.frames_counter = 0


        # ---- Extract pose of magnets and sensors ----
        SensorPose = self.RigidMO.position.value[0:self.config.NSensors, :]
        MagnetPose = self.RigidMO.position.value[self.config.NSensors:, :]


        GlobalMagneticField = self.simulator.compute_field(SensorPose, MagnetPose)

        GlobalMagneticField_index_real = GlobalMagneticField[sim_to_hw] 
        # print(f"GlobalMagneticField_index_real: {GlobalMagneticField_index_real}")


        if self.save_offset_flag:
            self.offset_per_stretch[self.current_stretch] = GlobalMagneticField_index_real.copy()
            self.save_offset_flag = False


        # ---- Restar offset  ----
        if self.current_stretch in self.offset_per_stretch:
            offset = self.offset_per_stretch[self.current_stretch]
            GlobalMagneticField_index_real = GlobalMagneticField_index_real - offset
        else:
            GlobalMagneticField_index_real = GlobalMagneticField_index_real 


        # print(f"GlobalMagneticField_index_real: {GlobalMagneticField_index_real}")

        if self.waiting:
            self.frames_counter += 1
 
            if self.frames_counter >= self.frames_to_wait:  

                if len(self.data_per_stretch[self.current_stretch]) <= self.current_point:
                    self.data_per_stretch[self.current_stretch].append([])

                    # print(f"GlobalMagneticField_index_real: {GlobalMagneticField_index_real}")

                self.data_per_stretch[self.current_stretch][self.current_point].append(GlobalMagneticField_index_real)

                self.current_point += 1
                self.waiting = False


        if self.current_iter == self.max_iter-1:
            
            current_objectives_names = self.config.get_currently_assessed_objectives()
            print(f"[Objective] Current objectives: {current_objectives_names}")

            for i in range(len(current_objectives_names)):

                current_objective_name =  current_objectives_names[i]

                if "SensorNumber" == current_objective_name:
                    sensors = self.config.NumberSensors
                    print("Number of sensors =", sensors)
                    self.objectives.append(sensors)

                if "MagnetNumber" == current_objective_name:
                    magnets = len(MagnetPose)
                    print("Number of magnets =", magnets)
                    self.objectives.append(magnets)

                # Sensibility metric. 
                if "MagneticSensitivity" == current_objective_name:

                    MagneticField_000pct = np.concatenate(self.data_per_stretch[0.0], axis=0)
                    MagneticField_010pct = np.concatenate(self.data_per_stretch[0.1], axis=0)
                    MagneticField_020pct = np.concatenate(self.data_per_stretch[0.2], axis=0)

                    # Combinations
                    index_sensors = np.arange(15)
                    k = int(self.config.NumberSensors)
                    print('k', k)
                    combinations_k = list(itertools.combinations(index_sensors, k))

                    # Metric
                    metrics_000pct, stds_000pct, order_000pct, combs_000pct, total_sum_per_taxel_000pct = magtec.Utils.compute_metrics(MagneticField_000pct, combinations_k)

                    best_idx = int(np.argmax(metrics_000pct))
                    best_metric = float(metrics_000pct[best_idx])
                    best_combination = combs_000pct[best_idx]

                    metric_000pct  = best_metric
                    metric_010pct  = magtec.Utils.compute_metric_single_combination(MagneticField_010pct, best_combination)
                    metric_020pct  = magtec.Utils.compute_metric_single_combination(MagneticField_020pct, best_combination)

                    metric = np.mean([metric_000pct, metric_010pct, metric_020pct])
                    print(f"Combination {best_combination} metric: {metric}")


                    self.objectives.append(metric)

        self.current_iter += 1





def createScene(rootNode, config):

    # -----------------------------
    # Load Required Plugins
    # -----------------------------
    pluginsList = [
        'Sofa.Component.Visual',
        'ArticulatedSystemPlugin',
        'SoftRobots',
        "SofaPython3",
        "Sofa.Component.LinearSolver.Iterative",
        "Sofa.Component.ODESolver.Backward",
        'SoftRobots.Inverse',
        'Sofa.Component.AnimationLoop',
        'Sofa.Component.Constraint.Lagrangian.Correction',
        'Sofa.Component.Constraint.Lagrangian.Solver',
        'Sofa.Component.Setting',
        'Sofa.Component.Constraint.Projective',
        'Sofa.Component.IO.Mesh',
        'Sofa.Component.Topology.Container.Dynamic',
        'Sofa.Component.LinearSolver.Direct',
        'Sofa.GL.Component.Shader',
        'Sofa.Component.Mapping.NonLinear',
        'Sofa.Component.Mass',
        'Sofa.Component.SolidMechanics.FEM.Elastic',
        'Sofa.Component.Engine.Select', 
        'Sofa.Component.SolidMechanics.Spring',
        'Sofa.Component.Mapping.Linear', 
        'Sofa.Component.StateContainer',
        'Sofa.Component.Topology.Container.Constant',
        'Sofa.Component.Visual',
        'Sofa.GL.Component.Rendering3D',
        'Sofa.GUI.Component',
        'Sofa.Component.MechanicalLoad',
        "AdvancedTimer"

    ]

    for name in pluginsList:
        rootNode.addObject("RequiredPlugin", name=name)

    
    # -----------------------------
    # Root Node Settings
    # -----------------------------
    rootNode.addObject('VisualStyle', displayFlags='hideWireframe showBehaviorModels hideCollisionModels hideBoundingCollisionModels showForceFields showInteractionForceFields')
    rootNode.findData('gravity').value = [0, 0, -9810]
    rootNode.findData('dt').value = 0.02


    # -----------------------------
    # Animation Loops and Solvers
    # -----------------------------
    rootNode.addObject('FreeMotionAnimationLoop')
    rootNode.addObject('QPInverseProblemSolver', printLog='0', epsilon="1e-1", maxIterations="1000", tolerance="1e-5")
    rootNode.addObject('GenericConstraintSolver', tolerance="1e-6", maxIterations="500")
    rootNode.addObject('DefaultVisualManagerLoop')


    # -----------------------------
    # Lighting
    # -----------------------------
    rootNode.addObject('LightManager')
    lights = [
    {"name":"light1","color":[0.8,0.8,0.8],"position":[0,0,25]},
    {"name":"light2","color":[0.8,0.8,0.8],"position":[0,0,-7]}
    ]
    for l in lights:
        rootNode.addObject("PositionalLight", **l)


    #----------------------
    # Goal Node
    #---------------------- 
 
    #----------------------
    # Rigidification - start
    #----------------------          

    completeMesh = rootNode.addChild('completeMesh')
    completeMesh.addObject('MeshVTKLoader', name='loader', 
                    filename = config.get_mesh_filename(mode = "Volume", refine = 0, 
                                                        generating_function = MagneticSkin, 
                                                        length = config.Length, 
                                                        width = config.Width,
                                                        height = config.Height,                                                    
                                                        magnet_boxes=config.MagnetSensors,
                                                        # magnet_boxes=None,
                                                        # lc_surface = config.SurfaceMeshCharacteristicLength,
                                                        lc= config.VolumeMeshCharacteristicLength))

    completeMesh.addObject('TetrahedronSetTopologyContainer', src='@loader', name='container')
    completeMesh.init()
    MeshTetra = completeMesh.addObject('MeshTopology', name="AllMesh", src='@loader')


    # ----------------------------------------
    # Create BoxROIs for rigid blocks
    # ----------------------------------------
    Boxes = []
    for i in range(len(config.rigidObjectsBoxCoords[1:])):
        boxTip = completeMesh.addObject('BoxROI', name='Tip'+str(i), box=[config.rigidObjectsBoxCoords[i+1]], drawBoxes=True, 
                                        tetrahedra="@container.tetrahedra" , position="@container.position")
        Boxes.append(boxTip)
        boxTip.init()

      
    positionAllPoints = MeshTetra.findData('position').value;
    nbPoints = len(positionAllPoints)

    
    IndicesWithRigidIdx = np.empty((0,2), dtype=int)
    
    for (i,Box) in enumerate(Boxes):
        IndicesNP = np.array(Box.indices.value, dtype=int)
        NPoints = len(IndicesNP)
        RigidIdx = np.ones(NPoints,dtype=int)*i
        CurrentIndicesWithRigidIdx = np.append(IndicesNP.reshape((NPoints,1)), RigidIdx.reshape((NPoints,1)),1)
        IndicesWithRigidIdx = np.append(IndicesWithRigidIdx, CurrentIndicesWithRigidIdx,0)
    

    IndicesWithRigidIdxSorted = np.sort(IndicesWithRigidIdx[:,0],0)
    SortedIdxs = np.argsort(IndicesWithRigidIdx[:,0],0)
    SortedRigidIdxs = IndicesWithRigidIdx[:,1][SortedIdxs]
    indicesTip = IndicesWithRigidIdxSorted.tolist()
    rigidBlocks = [IndicesWithRigidIdxSorted.tolist()] 
    
    DeformableIndicesTotal = []    
    
    for i in range(nbPoints):
        if i not in indicesTip:
            DeformableIndicesTotal.append(i)                                 

    freeBlocks = np.sort(DeformableIndicesTotal)    
    IdxsOrderedFreeBlocks = np.argsort(DeformableIndicesTotal)    
    indexPairs = np.array(rigidification.fillIndexPairs(nbPoints,freeBlocks,rigidBlocks))
    NPPointsDeformable = positionAllPoints[DeformableIndicesTotal,:]   
    NPSortedPointsDeformable = NPPointsDeformable[IdxsOrderedFreeBlocks, :]
    PointsDeformable = NPSortedPointsDeformable.flatten().tolist()
    pointsBody = PointsDeformable
    #deformablePoints = pointsBody
       
    pointsTip = np.array(positionAllPoints[indicesTip,:]).flatten().tolist()                                                 
    rigidIndexPerPoint = SortedRigidIdxs.tolist()


    # -----------------------------
    # Solver Node
    # -----------------------------
    solverNode = rootNode.addChild("solverNode")
    solverNode.addObject('EulerImplicitSolver',rayleighStiffness="0.1", rayleighMass="0.1")
    solverNode.addObject('SparseLDLSolver',name='preconditioner')
    solverNode.addObject('GenericConstraintCorrection', linearSolver='@preconditioner')


    # -----------------------------
    # Rigid Node
    # -----------------------------
    RigidNode= solverNode.addChild('RigidNode')
     
    nominal_pose = [] 
    TipOrientation = [0, 0, 0, 1]       
    
    for center in config.rigidObjects[1:]:
        CurrentPose = center + TipOrientation
        nominal_pose += CurrentPose
    RigidMO = RigidNode.addObject("MechanicalObject",template="Rigid3d",name="RigidMesh", position=nominal_pose, 
                                  showObject=True, showObjectScale=1, showIndices=True)

    # -----------------------------
    # Rigidified Node
    # -----------------------------
    RigidifiedNode =  RigidNode.addChild('RigidifiedNode')   
    RigidifiedNode.addObject('MechanicalObject', name='RigidifiedMesh', position=pointsTip,
                             template='Vec3d', showObject=True, showObjectScale=3, showColor=1)       
    RigidifiedNode.addObject("RigidMapping", globalToLocalCoords="true", rigidIndexPerPoint=rigidIndexPerPoint)
    

    # -----------------------------
    # Deformable Node
    # -----------------------------
    deformableNode = RigidifiedNode.addChild("deformableNode")
    deformableNode.addObject('PointSetTopologyContainer', position=pointsBody)
    deformableNode.addObject('MechanicalObject', name='DeformableMech', showObject = False, showObjectScale = 4)


    # -----------------------------
    # Model Node
    # -----------------------------
    model = deformableNode.addChild('model')
    RigidifiedNode.addChild(model)

    # model.addObject('EulerImplicitSolver', name='nodesolver')  
    # model.addObject('ShewchukPCGLinearSolver', iterations='15', name='linearsolver', tolerance='1e-5', update_step='1')


    model.addObject('MeshVTKLoader', name='loader', 
                filename = config.get_mesh_filename(mode = "Volume", refine = 0, 
                                                    generating_function = MagneticSkin, 
                                                    length = config.Length, 
                                                    width = config.Width,
                                                    height = config.Height,                                                    
                                                    magnet_boxes=config.MagnetSensors,
                                                    # MagnetCenters = config.MagnetCenters,
                                                    # lc_surface = config.SurfaceMeshCharacteristicLength,
                                                    lc= config.VolumeMeshCharacteristicLength))
    
    model.addObject('TetrahedronSetTopologyContainer', src='@loader', name='container')
    model.addObject('MechanicalObject', name='tetras', template='Vec3', showIndices=False, showIndicesScale='4e-5', rx='0', dz='0')
    model.addObject('UniformMass', totalMass='0.09')
    model.addObject('TetrahedronFEMForceField', template='Vec3', name='FEM', method='large', poissonRatio=config.PoissonRatio,  youngModulus=config.YoungsModulus) 
    #CAJA PART1              
    model.addObject('BoxROI', name='BaseROI', box=config.BoxROIFixCoords_base, drawBoxes=False, position="@tetras.rest_position", tetrahedra="@container.tetrahedra", drawPoints = False, drawSize = 3)              
    model.addObject('RestShapeSpringsForceField', points='@BaseROI.indices', stiffness='1e10')

              
    model.addObject("SubsetMultiMapping",
                    name="subsetMapping",
                    template="Vec3d,Vec3d", 
                    input='@'+deformableNode.getPathName()+'/DeformableMech' + ' ' + '@'+RigidifiedNode.getPathName()+'/RigidifiedMesh' , 
                    output='@./tetras', 
                    indexPairs=indexPairs.tolist())


    # -----------------------------
    # ROIs and RestShapeSprings
    # -----------------------------
    # EndROI: part that moves during stretching
    model.addObject('BoxROI', name='EndROI', box=config.BoxROIFixCoords1, drawBoxes=False, position="@tetras.rest_position", tetrahedra="@container.tetrahedra")              

    # BaseFixROI: nodes to be fixed at specific time (t=30)
    model.addObject('BoxROI', name='BaseFixROI', box=config.BoxROIFixCoords, drawBoxes=False, position="@tetras.rest_position", tetrahedra="@container.tetrahedra")            


    # -----------------------------
    # External Reference Nodes
    # -----------------------------
    #    #Parte que se mueve
    ExternalRefNode = rootNode.addChild("ExternalRefNode")
    ExternalRefNode.addObject('MechanicalObject', name='ExternalMO', template='Vec3', showObject=True, showObjectScale=3, showColor = [0,.7,.0],
                                showIndices=False, showIndicesScale=4e-5,
                                position='@../solverNode/RigidNode/RigidifiedNode/deformableNode/model/EndROI.pointsInROI')

    #Parte para fijar la base 
    ExternalRefNodeBase = rootNode.addChild("ExternalRefNodeBase")
    ExternalRefNodeBase.addObject('MechanicalObject', name='ExternalBaseMO', template='Vec3', showObject=True, showObjectScale=3, showColor = [0,0,.7],
                                    showIndices=False, showIndicesScale=4e-5,
                                    position='@../solverNode/RigidNode/RigidifiedNode/deformableNode/model/BaseFixROI.pointsInROI')
                        

    model.addObject('RestShapeSpringsForceField',name='StretchFixSpring', points='@EndROI.indices', stiffness='1e8', external_rest_shape='@ExternalRefNode/ExternalMO')
    model.addObject('RestShapeSpringsForceField',name='BaseFixSpring', points='@BaseFixROI.indices', stiffness='0', external_rest_shape='@ExternalRefNodeBase/ExternalBaseMO')

        
    # ----------------------------------------
    # Visualization                          
    # ----------------------------------------
    modelVisu = model.addChild('visu')
    modelVisu.addObject('MeshSTLLoader', name="loader", 
                    filename = config.get_mesh_filename(mode = "Surface", refine = 0, 
                                                    generating_function = MagneticSkin, 
                                                    length = config.Length, 
                                                    width = config.Width,
                                                    height = config.Height,
                                                    magnet_boxes= config.MagnetSensors,
                                                    lc= config.SurfaceMeshCharacteristicLength))
    

    modelVisu.addObject('OglModel', src="@loader", scale3d=[1, 1, 1])
    modelVisu.addObject('BarycentricMapping')
    

    # ------------------------------------------
    # Sphere ROI for interactive selection (CFF)
    # ------------------------------------------
    CFFNode = model.addChild('CFFNode')
    CFFNode.addObject('MeshSTLLoader', name="loader", 
                    filename = config.get_mesh_filename(mode = "Surface", refine = 0, 
                                                    generating_function = MagneticSkin, 
                                                    length = config.Length, 
                                                    width = config.Width,
                                                    height = config.Height,
                                                    magnet_boxes=None,
                                                    lc= config.SurfaceMeshCharacteristicLength))

    CFFMO = CFFNode.addObject('MechanicalObject', position='@loader.position') 
    CFFSphereROI = CFFNode.addObject('SphereROI', template="Vec3d", name='CFFSphereROI', centers=[0, 0, 5*1e-3], radii=[config.indenterRadius], drawSphere=False, drawPoints = False, drawSize=6)
    CFFSphereROI.init()              
    CFF = CFFNode.addObject('ConstantForceField', name='CFF', template='Vec3', indices='@CFFSphereROI.indices', totalForce=[0, 0, 0], showArrowSize=0.1*1e-3)                               
    CFFNode.addObject("BarycentricMapping")


    # -----------------------------
    # Fitness Evaluation Controller
    # -----------------------------
    rootNode.addObject(FitnessEvaluationController(name="FitnessEvaluationController",
                                                    rootNode=rootNode, 
                                                    config=config, 
                                                    RigidMO = RigidMO, 
                                                    CFF = CFF,
                                                    CFFMO = CFFMO,
                                                    CFFSphereROI = CFFSphereROI
                                                    )) 

    return rootNode