import itertools
from collections import deque
from scipy.spatial.distance import euclidean
import numpy as np
import rdkit.Chem.AllChem as rdkit

from ..base import Topology
from ....utilities import (centroid,
                           vector_theta,
                           add_fragment_props,
                           normalize_vector)


class Vertex:
    """
    Used to represent the vertices of cage polyhedra.

    This class stores information about the vertices which make up a
    cage's structure.

    Attributes
    ----------
    coord : :class:`numpy.array`
        An array which holds the x, y and z coordinates of the
        vertex, in that order.

    connected : :class:`list` of :class:`Edge` or :class:`Vertex`
        This :class:`list` holds the :class:`Edge` or :class:`Vertex`
        instances which represent the edges or vertices connected to
        this one.

    bonder_ids : :class:`list` of :class:`int`
        This :class:`list` holds the ids of atoms which belong to the
        building block placed on the vertex and will form bonds. The
        ids reflect those in the macromolecule not in the building block
        itself.

    atom_position_pairs : :class:`list`
        A :class:`list` of the form

        .. code-block:: python

            atom_position_pairs = [(4, v1), (8, v2)]

        Where ``v1`` and ``v2`` are :class:`Vertex` instances.

        Each atom which  is paired to a neighboring vertex or
        edge first. Only after this is the atom-atom pairing
        performed. The atom-edge/vertex pairing is stored here. The
        int represents the id of the atom.

    distances : :class:`list`
        A :class:`list` of the form

        .. code-block:: python

            distances = [(15.2, 5, 10), (18.4, 3, 8), ...]

        After bonder atoms have been associated with vertices to which
        they join, the idividual atoms are paired up. To do this the
        distance between every bonder atom on the paired vertex and the
        bonder atom which is paired to the vertex is found. This
        information is stored here the first element of each
        :class:`tuple` the distance, and the second and third elements
        represent the bonder atoms.

    id_ : :class:`object`, optional
        An id to identify the vertex. Used by
        :meth:`CageTopology.place_mols`.

    custom_position : :class:`bool`
        A flag to inidcate if the position of :attr:`coord` was derived
        from connected vertices or set manually. If the position is
        derived from the vertices then the position of the building
        block being placed is derived from the bonder atoms in the
        conncected vertices.

    """

    def __init__(self, x, y, z, id_=None, custom_position=True):
        """
        Initializes a :class:`Vertex`.

        Parameters
        ----------
        x : :class:`int` or :class:`float`
            The x coordinate.

        y : :class:`int` or :class:`float`
            The y coordiante

        z : :class:`int` or :class:`float`
            The z coordiante

        id : :class:`object`, optional
            An id to identify the vertex.

        custom_position : :class:`bool`, optional
            See :attr:`custom_position`.

        """

        self.coord = np.array([x, y, z])
        self.custom_position = custom_position
        self.connected = []
        self.bonder_ids = []
        self.atom_position_pairs = []
        self.distances = []
        self.id = id_

    @classmethod
    def vertex_init(cls, *vertices):
        """
        Intializes the :class:`Vertex` from other vertices.

        This initalizer automatically calculates the position of the
        vertex from the positions of the vertices provided to the
        initializer. Its position is set to the centroid of the
        provided vertices.

        The :attr:`connected` attributes of all the involved vertices
        are also updated.

        Parameters
        ----------
        vertices : :class:`tuple` of :class:`Vertex`
            Holds :class:`Vertex` objects used for initialization.

        Returns
        -------
        :class:`Vertex`
            The initialized vertex.

        """

        # Get the position of this Vertex, as the centroid of the
        # supplied vertices.
        obj = cls(*centroid(*(v.coord for v in vertices)),
                  custom_position=False)
        # Update the `connected` attributes.
        obj.connected.extend(vertices)
        for v in vertices:
            v.connected.append(obj)
        return obj

    def place_mol(self,
                  scale,
                  building_block,
                  aligner=0,
                  aligner_edge=0,
                  macro_mol=None):
        """
        Place a :class:`.StructUnit3` building block on the vertex.

        The orientation of the building block is aligned with 2
        parameters. Firstly, the normal of the plane of bonder atoms of
        the building block is aligned with the normal of the plane
        formed by the edges connected to the vertex. Because the normal
        of the plane of bonder atoms always points in the direction of
        the building block's centroid, this alignment causes the bulk
        of the building block  molecule to point away from the center
        of the cage.

        Secondly, the building block is rotated so that a bonder atom
        is aligned perfectly with an edge. This reduces the rms
        distance between the edges and bonder atoms to some extent,
        probably.

        Parameters
        ----------
        scale : :class:`float`
            The amount by which the size of the topology is scaled.

        building_block : :class:`.StructUnit3`
            The building block molecule to be placed on a vertex.

        aligner : :class:`int`, optional
            The index of the atom within
            :attr`.StructUnit.bonder_ids` which is to be aligned
            with an edge.

        aligner_edge : :class:`int`, optional
            The index of an edge in :attr:`connected`. It is the edge
            with which `aligner` is aligned.

        macro_mol : :class:`.MacroMolecule`, optional
            The macromolecule being built. Used for vertex only cage
            topologies where the position of some of the vertices
            is derived from the positions of the bonder atoms of
            connceted vertices.

        Returns
        -------
        :class:`rdkit.Chem.rdchem.Mol`
            The ``rdkit`` instance holding the building block molecule
            with the coordinates placed on the vertex and orientation
            set as described in the docstring.

        """

        # Flush the list of data from previous molecules.
        self.distances = []

        # The method first aligns the normal of the bonder atom plane
        # to the normal of the edge plane. This means the bulk of the
        # building block is always pointed away from the center of the
        # molecule.
        building_block.set_orientation2(self.edge_plane_normal(scale))

        # Next, define the direction vector going from the edge
        # centroid to the edge with which the atom is aligned.

        building_block.set_bonder_centroid(
                            self.bonder_centroid(macro_mol, scale))
        vector = (self.connected[aligner_edge].coord*scale -
                  self.edge_centroid(scale))
        # Get the id of the atom which is being aligned.
        atom = building_block.bonder_ids[aligner]
        # Minimize the angle between these things by rotating about the
        # normal of the edge plane.
        building_block.minimize_theta2(atom,
                                       vector,
                                       self.edge_plane_normal(scale))

        return building_block.mol

    def edge_plane_normal(self, scale):
        """
        Return the normal of the plane formed by the connected edges.

        The normal is set such that it always points away from the
        origin.

        Parameters
        ----------
        scale : :class:`float`
            The amount by which the size of the topology is scaled.

        Returns
        -------
        :class:`numpy.array`
            A normalized vector which defines the normal pointed away
            from the origin.

        """
        # Get two of the direction vectors running between the edges.
        v1, v2 = itertools.islice(self.edge_direction_vectors(scale), 2)
        # To get the normal to the plane get the cross product of these
        # vectors. Normalize it.
        normal = normalize_vector(np.cross(v1, v2))

        # To check that the normal is pointing away from the center of
        # cage, find the angle, `theta`, between it and one of the
        # position vectors of the edges on the plane. Assuming that the
        # center of the cage is at the origin, which it should be as
        # this is specified in the documentation, if the angle between
        # the normal the position vector is less than 90 degrees they
        # point in the same general direction. If the angle is greater
        # than 90 degrees it means that they are pointing in opposite
        # directions. If this is the case make sure to multiply the
        # nomral by -1 in all axes so that it points in the correct
        # direction while still acting as the normal to the plane.
        theta = vector_theta(normal, self.connected[0].coord*scale)

        if theta > np.pi/2:
            normal *= -1

        return normal

    def edge_plane(self, scale):
        """
        Return coefficients of plane of edges connected to the vertex.

        A plane is defined by the scalar plane equation::

            ax + by + cz = d.

        This method returns the ``a``, ``b``, ``c`` and ``d``
        coefficients of this equation for the plane formed by the
        connected edges. The coefficents ``a``, ``b`` and ``c`` decribe
        the normal vector to the plane. The coefficent ``d`` is found
        by substituting these coefficients along with the ``x``, ``y``
        and ``z`` variables in the scalar equation and solving for
        ``d``. The variables ``x``, ``y`` and ``z`` are substituted by
        the coordinate of some point on the plane. For example, the
        position of one of the connected edges.

        Parameters
        ----------
        scale : :class:`float`
            The amount by which the size of the topology is scaled.

        Returns
        -------
        :class:`numpy.array`
            This array has the form ``[a, b, c, d]`` and represents the
            scalar equation of the plane formed by the connected edges.

        References
        ----------
        https://tinyurl.com/okpqv6

        """

        edge_coord = self.edges[0].coord*scale
        d = -np.sum(self.edge_plane_normal(scale) * edge_coord)
        return np.append(self.edge_plane_normal(scale), d)

    def edge_direction_vectors(self, scale):
        """
        Yields direction vectors between edges connected to the vertex.

        Parameters
        ---------
        scale : :class:`float`
            The amount by which the size of the topology is scaled.

        Yields
        ------
        :class:`numpy.array`
            A normalized direction vector running from one edge
            connected to the vertex to another.

        """

        for edge1, edge2 in itertools.combinations(self.connected, 2):
            yield normalize_vector(scale*(edge1.coord-edge2.coord))

    def edge_coord_matrix(self, scale):
        """
        Return matrix holding coords of edges joined to the vertex.

        Parameters
        ----------
        scale : :class:`float`
            The amount by which the size of the topology is scaled.

        Returns
        -------
        :class:`numpy.matrix`
            The matrix of shape ``[n, 3]``, where ``n`` is the number
            of edges connected to the vertex. The row holds the x, y
            and z coordinates, respectively.

        """

        coords = []
        for edge in self.connected:
            coords.append(edge.coord*scale)
        return np.matrix(coords)

    def edge_centroid(self, scale):
        """
        Returns the centroid of the edges connected to the vertex.

        Parameters
        ----------
        scale : :class:`float`
            The amount by which the size of the topology is scaled.

        Returns
        -------
        :class:`numpy.array`
            An array which holds the x, y and z positions of the
            centroid of the edges connected to the vertex.

        """

        # The connected edges are held in the `edges`. To get the
        # centroid, add up all the x, y and z coordinates (separately)
        # and divide each sum by the number of edges.
        return (sum(edge.coord*scale for edge in self.connected) /
                len(self.connected))

    def bonder_centroid(self, macro_mol, scale):
        """
        Calculates the centroid of the bonder atoms on the vertex.

        However if :attr:`custom_position` is ``True`` or
        `macro_mol` is ``None``, then :attr:`coord` is returned.

        Parameters
        ----------
        macro_mol : :class:`.MacroMolecule`
            The macromolecule being built.

        scale : :class:`float`
            The amount by which the size of the topology is scaled.

        Returns
        -------
        :class:`numpy.array`
            The centroid of the bonder atoms.

        """

        if self.custom_position or macro_mol is None:
            return self.coord*scale

        centroid = np.zeros((3, ))
        count = 0
        for v in self.connected:
            for bonder, edge in v.atom_position_pairs:
                if edge is self:
                    centroid += macro_mol.atom_coords(bonder)
                    count += 1
        return centroid / count

    def __repr__(self):
        return "Vertex({:.3}, {:.3}, {:.3})".format(*self.coord)

    def __str__(self):
        return repr(self)


class Edge(Vertex):
    """
    Used to represent the edges of Cage polyhedra.

    This class stores information about the edges which make up a
    cage's structure.

    Attributes
    ----------
    direction : :class:`numpy.array`
        This vector represents the orientation of the edge. It is a
        normalized direction vector which runs from `v2` to `v1`,
        provided in the initalizer.

    """

    def __init__(self, v1, v2, id_=None, custom_position=False):
        """
        Initializes an :class:`Edge` instance.

        Parameters
        ----------
        v1 : :class:`Vertex`
            A vertex joined to the edge.

        v2 : :class:`Vertex`
            Another vertex joined to the edge.

        id_ : :class`str`, optional
            An id for the edge.

        custom_position : :class:`bool`
            See :attr:`Vertex.custom_position`


        """

        Vertex.__init__(self,
                        *centroid(v1.coord, v2.coord),
                        id_,
                        custom_position)

        self.connected.extend([v1, v2])
        v1.connected.append(self)
        v2.connected.append(self)

    def direction(self, macro_mol, scale):
        if self.custom_position or macro_mol is None:
            v1, v2 = self.connected
            return normalize_vector(v1.coord - v2.coord)

        bonders = []
        for v in self.connected:
            for bonder, edge in v.atom_position_pairs:
                if edge is self:
                    bonders.append(macro_mol.atom_coords(bonder))
        return normalize_vector(bonders[0] - bonders[1])

    def place_mol(self, scale, linker, alignment, macro_mol):
        """
        Places a linker molecule on the coordinates of an edge.

        It also orientates the linker so that a the bonder atoms sit
        exactly on the edge and the bulk of the linker points away from
        the center of the cage.

        Parameters
        ----------
        scale : :class:`float`
            The amount by which the size of the topology is scaled.

        linker : :class:`.StructUnit2`
            The linker which is to be placed and orientated as
            described in the docstring.

        alignment : :class:`int`
            ``1`` for parallel alignment with :attr:`direction` and
            ``-1`` for anti-parallel alignment with :attr:`direction`.

        macro_mol : :class:`.MacroMolecule`
            The macromolecule being constructed.

        Returns
        -------
        :class:`rdkit.Chem.rdchem.Mol`
            The ``rdkit`` instance holding the linker molecule with the
            coordinates placed on the edge and orientation set as
            described in the docstring.

        """

        # Flush the lists from data of previous molecules.
        self.distances = []

        # Align then place the linker.
        linker.set_orientation2(self.direction(macro_mol, scale)*alignment)
        linker.minimize_theta2(self.coord*scale,
                               self.direction(macro_mol, scale))
        linker.set_bonder_centroid(self.bonder_centroid(macro_mol, scale))

        return linker.mol

    def __repr__(self):
        v1, v2 = self.connected
        return f"Edge({v1}, {v2})"

    def __str__(self):
        return repr(self)


class CageTopology(Topology):
    """
    An abstract base class for cage topologies.

    Attributes
    ----------
    A_alignments : :class:`list` of :class:`int`
        The length of this :class:`list` must be equal to the number of
        building blocks in the cage. When cages are built one of the
        bonder atoms of each building block is aligned with an edge
        during placement. The :class:`int` indicates which bonder atom
        is aligned. The :class:`int` corresponds to an index in
        :attr:`.StructUnit.bonder_ids`.

        If ``None`` the first atom in `bonder_ids` is always aligned.

        For example,

        .. code-block:: python

            A_alignments = [0, 2, 1, 2]

        In this case there must be 4 building blocks in the cage. The
        the first building block has its first (index ``0``) bonder
        atom aligned. The 2nd building block has the 3rd (index ``2``)
        atom aligned. The 3rd building block has the 2nd (index ``1``)
        atom aligned. The 4th building block has the 3rd (index ``2``)
        atom aligned.

    B_alignments : :class:`list` of :class:`int`
        The length of this :class:`list` should be euqal to the number
        of linkers in the cage. The linkers of a cage can have either 2
        functional groups or 3 or more, depending on the topology.

        When the linkers have 2 functional groups, the :class:`list`
        should hold either ``1`` or ``-1``. The value indicates that
        the linker is aligned parallel or antiparallel with the edge
        its placed on. For example, in a tetrahedral topology,

        .. code-block:: python

            B_alignments = [-1, 1, 1, -1, 1, -1]

        It indicates that the first linker is aligned anti parallel and
        the second is aligned in parallel, and so on.

        If the linkers have 3 or more functional groups, the values
        in :attr:`B_alignments` have the same role as
        :attr:`A_alignments`. The only difference is that by default
        the second atom is aligned, rather than the first.

    edge_alignments : :class:`list` of :class:`int`
        The length of the :class:`list` is equal to the number of
        building blocks in the cage. Each element is an :class:`int`
        which holds the id of an edge. For example,

        .. code-block:: python

            edge_alignments = [1, 2, 3, 4]

        then the first building block is aligned with the edge with
        :attr:`Vertex.id_` of ``1``, the second building block is
        aligned with the edge with :attr:`Vertex.id_` ``2`` and so on.
        For this to work, the edges must have their :attr:`Vertex.id_`
        attributes defined.

    bb_assignments : :class:`dict`
        A :class:`dict` of the form

        .. code-block:: python

            bb_assignments = {
                0: [0, 1, 3],
                1: [2]
                2: [0, 4, 5],
                3: [1, 2, 3]
            }

        This means the building block at index ``0`` of
        :attr:`.MacroMolecule.building_blocks` sits on the vertices
        of indices ``0``, ``1``, and ``3``. The building block at
        index ``1`` of :attr:`.MacroMolecule.building_blocks` sits on
        verticex of index ``2``.

        The building block at index ``2`` in
        :attr:`.MacroMolecule.building_blocks` also sits on the vertex
        of index ``0``. However each cage is composed of two sets of
        building blocks, called building blocks and linkers. This means
        that the building block at index ``0`` is builing block while
        the one at index ``2`` is a linker, or vice versa. Which one
        is which is automatically deduced by looking at the number of
        functional groups.

        If ``None`` then building blocks are assigned at random.

    """

    def __init__(self,
                 A_alignments=None,
                 B_alignments=None,
                 edge_alignments=None,
                 bb_assignments=None):

        if A_alignments is None:
            A_alignments = np.zeros(len(self.positions_A))
        if B_alignments is None:
            B_alignments = np.ones(len(self.positions_B))
        if edge_alignments is None:
            edge_alignments = [None for x in
                               range(len(self.positions_A))]

        super().__init__()
        self.A_alignments = A_alignments
        self.B_alignments = B_alignments
        self.edge_alignments = edge_alignments
        self.bb_assignments = bb_assignments

    def _bb_maps(self, macro_mol):
        """

        """

        bb_fgs = max(len(bb.functional_group_atoms()) for
                     bb in macro_mol.building_blocks)
        bb_map, lk_map = {}, {}

        if self.bb_assignments is None:
            bbs = [bb for bb in macro_mol.building_blocks if
                   len(bb.functional_group_atoms()) == bb_fgs]
            lks = [bb for bb in macro_mol.building_blocks if
                   len(bb.functional_group_atoms()) != bb_fgs]

            for i in range(len(self.positions_A)):
                bb_map[i] = np.random.choice(bbs)
            for i in range(len(self.positions_B)):
                lk_map[i] = np.random.choice(lks)

        else:

            for bb_index, positions in self.bb_assignments.items():
                bb = macro_mol.building_blocks[bb_index]
                n_fgs = len(bb.functional_group_atoms())
                map_ = bb_map if n_fgs == bb_fgs else lk_map
                for position in positions:
                    map_[position] = bb

        return bb_map, lk_map

    def join_mols(self, macro_mol):
        """
        Joins up the separate building blocks which form the molecule.

        Parameters
        ----------
        macro_mol : :class:`.MacroMolecule`
            The macromolecule being assembled.

        Returns
        -------
        None : :class:`NoneType`

        """

        editable_mol = rdkit.EditableMol(macro_mol.mol)
        macro_mol.bonds_made = 0

        # This loop finds all the distances between an atom paired with
        # a postion and all other atoms at the paired position.
        for position in self.positions_A:
            for atom_id, vertex in position.atom_position_pairs:
                # Get all the distances between the atom and the other
                # bonding atoms on the vertex. Store this information
                # on the vertex.
                for atom2_id in vertex.bonder_ids:
                    distance = macro_mol.atom_distance(atom_id,
                                                       atom2_id)
                    position.distances.append((distance,
                                               atom_id, atom2_id))

        # This loop creates bonds between atoms at two different
        # positions so that each atom only bonds once and so that the
        # total length of all bonds made is minimzed.
        paired = set()
        for position in self.positions_A:
            for _, atom1_id, atom2_id in sorted(position.distances):
                if atom1_id in paired or atom2_id in paired:
                    continue

                bond_type = self.determine_bond_type(macro_mol,
                                                     atom1_id,
                                                     atom2_id)
                # Add the bond.
                editable_mol.AddBond(atom1_id, atom2_id, bond_type)
                macro_mol.bonds_made += 1
                paired.add(atom1_id)
                paired.add(atom2_id)

        macro_mol.mol = editable_mol.GetMol()

    def pair_bonders_with_positions(self, scale, macro_mol, vertex):
        """
        Matches atoms with the closest building block position.

        After a building block is placed on a position, each atom
        which forms a bond must be paired with the location of the
        building block to which it bonds. This function matches atoms
        and positions so that each is only present in one pairing and
        so that the total distance of the pairings is minimized.

        This updates of :attr:`Vertex.atom_position_pairs` attribute of
        `vertex`.

        Parameters
        ----------
        scale : :class:`float`
            The amount by which the size of the topology is scaled.

        macro_mol : :class:`.MacroMolecule`
            The macromolecule being buit.

        vertex : :class:`Vertex`
            The position at which all the atoms being paired are
            located.

        Returns
        -------
        None : :class:`NoneType`

        """

        # This loop looks at each atom which forms a new bond and all
        # the positions (not atoms) to which it may end up bonding. It
        # finds the distances of all the options.
        distances = []
        for bonder_id in vertex.bonder_ids:
            atom_coord = macro_mol.atom_coords(bonder_id)
            for position in vertex.connected:
                distance = euclidean(atom_coord, position.coord*scale)
                distances.append((distance, bonder_id, position))

        # Sort the pairings of atoms with potential bonding position,
        # smallest first.
        distances.sort(key=lambda x: x[0])

        # This loop looks at all the potential pairings of atoms to
        # positions. It pairs the shortest combinations of atoms and
        # positions, making sure that each atom and position is only
        # paired once. The pairings are saved to the `
        # atom_positions_pairs` attribute of the position on which all
        # the bonder atoms are placed.
        paired_pos = set()
        paired_ids = set()
        vertex.atom_position_pairs = []
        for _, bonder_id, pos in distances:
            if bonder_id in paired_ids or pos in paired_pos:
                continue
            vertex.atom_position_pairs.append((bonder_id, pos))
            paired_ids.add(bonder_id)
            paired_pos.add(pos)

    def place_mols(self, macro_mol):
        """
        Places all building block molecules on correct coordinates.

        The building block molecules are placed in their appropriate
        positions based on the topology. It does not join them.

        Also updates :attr:`.MacroMolecule.bb_counter`.

        Parameters
        ----------
        macro_mol : :class:`.MacroMolecule`
            The macromolecule being built.

        Returns
        -------
        None : :class:`NoneType`

        """

        macro_mol.mol = rdkit.Mol()
        bb_map, lk_map = self._bb_maps(macro_mol)
        scale = max(bb.max_diameter()[0] for bb in macro_mol.building_blocks)
        # Save the original orientationss of building blocks.
        # This means that when orienation of molecules is done,
        # the starting position is always the same. Ensures
        # consistency.
        ipositions = {bb: bb.position_matrix() for
                      bb in macro_mol.building_blocks}

        # This loop places all building-blocks* on the points at
        # `positions_A`. It then pairs all atoms which form a new bond
        # with the positions to which they will be bonding. It also
        # counts the nubmer of building-blocks* which make up the
        # structure.
        for i, position in enumerate(self.positions_A):
            bb = bb_map[i]
            bb_pos = ipositions[bb]
            n_bb = len(bb.functional_group_atoms())
            # Position the molecule on the vertex.
            bb.set_position_from_matrix(bb_pos)
            aligner_edge_id = self.edge_alignments[i]
            aligner_edge = next((position.connected.index(x) for x in
                                 position.connected if
                                 x.id == aligner_edge_id), 0)
            bb_mol = position.place_mol(scale,
                                        bb,
                                        int(self.A_alignments[i]),
                                        aligner_edge)
            add_fragment_props(bb_mol,
                               macro_mol.building_blocks.index(bb),
                               i)

            macro_mol.mol = rdkit.CombineMols(macro_mol.mol, bb_mol)
            # Update the counter each time a building-block* is added.
            macro_mol.bb_counter.update([bb])

            # Get ids of atoms which form new bonds.
            bonder_ids = deque(maxlen=n_bb)
            for atom in macro_mol.mol.GetAtoms():
                if atom.HasProp('bonder'):
                    bonder_ids.append(atom.GetIdx())

            # Save the ids of atoms which form new bonds and pair them
            # up with positions.
            position.bonder_ids = sorted(bonder_ids)
            self.pair_bonders_with_positions(scale, macro_mol, position)

        # This loop places all linkers on the points at `positions_B`.
        # It then saves all atoms which form a new bond to the position
        # they are found at. It also counts the number of linkers which
        # make up the structure.
        for i, position in enumerate(self.positions_B):
            lk = lk_map[i]
            lk_pos = ipositions[lk]
            n_lk = len(lk.functional_group_atoms())

            lk.set_position_from_matrix(lk_pos)
            lk_mol = position.place_mol(scale,
                                        lk,
                                        int(self.B_alignments[i]),
                                        macro_mol=macro_mol)
            add_fragment_props(lk_mol,
                               macro_mol.building_blocks.index(lk),
                               i)

            macro_mol.mol = rdkit.CombineMols(macro_mol.mol, lk_mol)
            # Update the counter each time a linker is added.
            macro_mol.bb_counter.update([lk])

            # Get ids of atoms which form new bonds.
            bonder_ids = deque(maxlen=n_lk)
            for atom in macro_mol.mol.GetAtoms():
                if atom.HasProp('bonder'):
                    bonder_ids.append(atom.GetIdx())

            # Save the ids of atoms which form new bonds.
            position.bonder_ids = list(bonder_ids)


class VertexOnlyCageTopology(CageTopology):
    """
    Abstract base class for cage topologies using ditopics.

    """

    ...


class NoLinkerCageTopology(CageTopology):
    """
    Abstract base class for cage topologies without linkers.

    This means that all building blocks have the same number of
    functional groups.

    Attributes
    ----------
    alignments : :class:`list` of :class:`int`
        See :attr:`CageTopology.A_alignments`

    bb_assignments : :class:`list` of :class:`int`
        For each vertex, the :class:`int` is the index of a
        building block in :attr:`.MacroMolecule.building_blocks`.
        It is the building block to be placed on that vertex. Can be
        ``None`` if a random building block should be placed.

    """

    def __init__(self, alignments=None, bb_assignments=None):
        if alignments is None:
            alignments = np.zeros(len(self.positions_A))
        if bb_assignments is None:
            bb_assignments = [None for i in range(len(self.positions_A))]

        self.alignments = alignments
        self.bb_assignments = bb_assignments
        self.connect()

    def place_mols(self, macro_mol):

        macro_mol.mol = rdkit.Mol()
        scale = max(bb.max_diameter()[0] for bb in macro_mol.building_blocks)

        for position, orientation, bb_index in zip(self.positions_A,
                                                   self.alignments,
                                                   self.bb_assignments):
            if bb_index is None:
                bb = np.random.choice(macro_mol.building_blocks)
            else:
                bb = macro_mol.building_blocks[bb_index]
            ipos = bb.position_matrix()
            n_bb = len(bb.functional_group_atoms())

            macro_mol.mol = rdkit.CombineMols(macro_mol.mol,
                                              position.place_mol(
                                                scale, bb, int(orientation)))
            macro_mol.bb_counter.update([bb])

            bonder_ids = deque(maxlen=n_bb)
            for atom in macro_mol.mol.GetAtoms():
                if atom.HasProp('bonder'):
                    bonder_ids.append(atom.GetIdx())

            position.bonder_ids = sorted(bonder_ids)
            self.pair_bonders_with_positions(scale, macro_mol, position)
            bb.set_position_from_matrix(ipos)

    @classmethod
    def connect(cls):
        """
        Updates each :attr:`Vertex.connected`.

        Returns
        -------
        None : :class:`NoneType`

        """

        if getattr(cls, 'connected', False):
            return

        for v1, v2 in cls.connections:
            v1.connected.append(v2)
            v2.connected.append(v1)
        cls.connected = True
