# -*- coding: utf-8 -*-
"""
MagTecSkin Sensor Generation 
"""

import gmsh
############################
### Mesh helper functions #
############################
def define_mesh_sizes(length, width, height, lc):
    """
    Set mesh options for surface and volume.
    FieldId: identificador único para este campo
    """
    gmsh.model.mesh.field.add("Box", 1)
    gmsh.model.mesh.field.setNumber(1, "VIn", lc)
    gmsh.model.mesh.field.setNumber(1, "VOut", 100000)
    gmsh.model.mesh.field.setNumber(1, "XMin", -length/2)
    gmsh.model.mesh.field.setNumber(1, "XMax", length/2)
    gmsh.model.mesh.field.setNumber(1, "YMin", -width/2)
    gmsh.model.mesh.field.setNumber(1, "YMax",width/2)
    gmsh.model.mesh.field.setNumber(1, "ZMin", 0)
    gmsh.model.mesh.field.setNumber(1, "ZMax", height)
    gmsh.model.mesh.field.setNumber(1, "Thickness", 0)
    gmsh.model.mesh.field.setAsBackgroundMesh(1)


    gmsh.option.setNumber("Mesh.CharacteristicLengthExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", 0)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 0)


    # gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", lc_surface)
    # gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", lc)
    # gmsh.option.setNumber("Mesh.CharacteristicLengthMin", lc_surface)

def defineMeshSizesZones(center,  lc, tag, tolerance):   
    # center[0], center[1], center[2] = center
    gmsh.model.mesh.field.add("Box", tag)
    gmsh.model.mesh.field.setNumber( tag, "VIn", lc)
    gmsh.model.mesh.field.setNumber( tag, "VOut", 0.9)
    gmsh.model.mesh.field.setNumber( tag, "XMin", center[0] - tolerance) # 
    gmsh.model.mesh.field.setNumber( tag, "XMax", -14)#center[0] + tolerance)
    gmsh.model.mesh.field.setNumber( tag, "YMin", 4)#center[1] - tolerance)
    gmsh.model.mesh.field.setNumber( tag, "YMax", 6) #center[1] + tolerance)
    gmsh.model.mesh.field.setNumber( tag, "ZMin", 0)#center[tag] - tolerance)
    gmsh.model.mesh.field.setNumber( tag, "ZMax", 3)#center[tag] + tolerance)    
    gmsh.model.mesh.field.setNumber( tag, "Thickness", 0.3)   
    gmsh.model.mesh.field.setAsBackgroundMesh(tag)

    gmsh.option.setNumber("Mesh.CharacteristicLengthExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromPoints", 0)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 0)

############################
### Basic CAD functions ###
############################
def create_base_box(length, width, height):
    """
    Create the main sensor volume (parallelepiped centered in XY, z=0..height)
    Returns: (3, tag) of the volume
    """
    x_half = length / 2.0
    y_half = width / 2.0

    p1 = gmsh.model.occ.addPoint( x_half,  y_half, 0)
    p2 = gmsh.model.occ.addPoint(-x_half,  y_half, 0)
    p3 = gmsh.model.occ.addPoint(-x_half, -y_half, 0)
    p4 = gmsh.model.occ.addPoint( x_half, -y_half, 0)

    l1 = gmsh.model.occ.addLine(p1, p2)
    l2 = gmsh.model.occ.addLine(p2, p3)
    l3 = gmsh.model.occ.addLine(p3, p4)
    l4 = gmsh.model.occ.addLine(p4, p1)

    wire = gmsh.model.occ.addWire([l1, l2, l3, l4])
    surf = gmsh.model.occ.addPlaneSurface([wire])

    extrude = gmsh.model.occ.extrude([(2, surf)], 0, 0, height)

    vol = next(((dim, tag) for dim, tag in extrude if dim == 3), None)
    if vol is None:
        raise RuntimeError("Extrusion did not create a volume")

    gmsh.model.occ.synchronize()
    return vol


def create_magnet_boxes(magnet_boxes):
    """
    Create Gmsh boxes for magnets.
    magnet_boxes: list of [xmin, ymin, zmin, dx, dy, dz]
    Returns: list of (3, tag)
    """
    tags = []
    for b in magnet_boxes:
        if len(b) == 6:
            x, y, z, dx, dy, dz = b
            dx = dx - x
            dy = dy - y
            dz = dz - z


            tag = gmsh.model.occ.addBox(x, y, z, dx, dy, dz)
            tags.append((3, tag))
    gmsh.model.occ.synchronize()
    return tags


def cut_magnets_from_base(base_dimtag, magnet_dimtags):
    """
    Subtract magnet boxes from the base volume
    """
    if not magnet_dimtags:
        return base_dimtag
    cut = gmsh.model.occ.cut([base_dimtag], magnet_dimtags)
    gmsh.model.occ.synchronize()
    result = cut[0]
    return result[0] if isinstance(result, (list, tuple)) else result


############################
### Public API functions ###
############################
def MagneticSkin(length, width, height, magnet_boxes, lc =0.1):
    """
    Create full 3D MagneticSkin geometry and set mesh sizes.
    Returns: (3, tag) of the volume.
    """
    base = create_base_box(length, width, height)
    mags = create_magnet_boxes(magnet_boxes) if magnet_boxes else []
    result = cut_magnets_from_base(base, mags)

    # --- Asigna un mallado global más grueso ---
    define_mesh_sizes(length, width, height, lc)

    # --- Si hay imanes, define campos locales más finos ---
    # if center:

        # for center in center:

        # # FieldId = 2  # 
            # defineMeshSizesZones(length, width, height, lc, tag=2)
    # defineMeshSizesZones(center, lc, tag=2, tolerance=2)
    # for i, c in enumerate(centers):
    

    # if MagnetCenters is None or len(MagnetCenters) == 0:
    #     raise ValueError("MagnetCenters no puede ser None ni vacío")

    # defineMeshSizesZones(center=MagnetCenters[0], lc=lc, tag=2, tolerance=2)

        # defineMeshSizesZones(BoxCoords=magnet_boxes[1], lc=lc, FieldId=2)

        # gmsh.model.mesh.field.add("Min", 3)
        # gmsh.model.mesh.field.setNumbers(3, "FieldsList", [1,2])
        # gmsh.model.mesh.field.setAsBackgroundMesh(3)


    return result