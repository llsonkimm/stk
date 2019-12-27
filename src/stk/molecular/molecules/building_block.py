"""
Building Block
==============

"""


import logging
import os
import numpy as np
import itertools as it
import rdkit.Chem.AllChem as rdkit
from functools import partial
from scipy.spatial.distance import euclidean

from .. import atoms, bond, functional_groups
from ..functional_groups import FunctionalGroup
from ..atoms import Atom
from ..bond import Bond
from .molecule import Molecule_
from ...utilities import vector_angle, remake


logger = logging.getLogger(__name__)


class BuildingBlock(Molecule_):
    """
    Represents a building block of a :class:`.ConstructedMolecule`.

    A :class:`BuildingBlock` can represent either an entire molecule or
    a molecular fragments used to construct a
    :class:`.ConstructedMolecule`. The building block uses
    :class:`.FunctionalGroup` instances to identify which atoms are
    modified during construction.

    """

    # Maps file extensions to functions which can be used to
    # create an rdkit molecule from that file type.
    _init_funcs = {
        '.mol': partial(
            rdkit.MolFromMolFile,
            sanitize=False,
            removeHs=False
        ),

        '.sdf': partial(
            rdkit.MolFromMolFile,
            sanitize=False,
            removeHs=False
        ),

        '.pdb': partial(
            rdkit.MolFromPDBFile,
            sanitize=False,
            removeHs=False
        ),
    }

    def __init__(self, smiles, functional_groups=None, random_seed=4):
        """
        Initialize a :class:`.BuildingBlock`.

        Notes
        -----
        The molecule is given 3D coordinates with
        :func:`rdkit.ETKDGv2()`.

        Parameters
        ----------
        smiles : :class:`str`
            A SMILES string of the molecule.

        functional_groups : :class:`iterable`, optional
            An :class:`iterable` of :class:`.FunctionalGroup` or
            :class:`.FunctionalGroupFactory` or both.
            :class:`.FunctionalGroup` instances are added to the
            building block and :class:`.FunctionalGroupFactory`
            instances are used to create :class:`.FunctionalGroup`
            instances the building block should hold.
            :class:`.FunctionalGroup` instances are used to identify
            which atoms are modified during
            :class:`.ConstructedMolecule` construction.

        random_seed : :class:`int`, optional
            Random seed passed to :func:`rdkit.ETKDGv2`

        Raises
        ------
        :class:`RuntimeError`
            If embedding the molecule fails.

        """

        if functional_groups is None:
            functional_groups = ()

        molecule = rdkit.AddHs(rdkit.MolFromSmiles(smiles))
        params = rdkit.ETKDGv2()
        params.randomSeed = random_seed
        if rdkit.EmbedMolecule(molecule, params) == -1:
            raise RuntimeError(
                f'Embedding with seed value of {random_seed} failed.'
            )
        key = self._get_identity_key_from_rdkit_mol(molecule)
        rdkit.Kekulize(molecule)
        self._init_from_rdkit_mol(molecule, functional_groups, key)

    @classmethod
    def init_from_molecule(cls, molecule, functional_groups=None):
        """
        Initialize from a :class:`.Molecule`.

        Parameters
        ----------
        molecule : :class:`.Molecule`
            The molecule to initialize from.

        functional_groups : :class:`iterable`, optional
            An :class:`iterable` of :class:`.FunctionalGroup` or
            :class:`.FunctionalGroupFactory` or both.
            :class:`.FunctionalGroup` instances are added to the
            building block and :class:`.FunctionalGroupFactory`
            instances are used to create :class:`.FunctionalGroup`
            instances the building block should hold.
            :class:`.FunctionalGroup` instances are used to identify
            which atoms are modified during
            :class:`.ConstructedMolecule` construction.

        Returns
        -------
        :class:`.BuildingBlock`
             The building block. It will have the same atoms, bonds and
             atomic positions as `mol`.

        """

        return cls.init_from_rdkit_mol(
            molecule=molecule.to_rdkit_mol(),
            functional_groups=functional_groups,
        )

    @classmethod
    def init_from_file(cls, path, functional_groups=None):
        """
        Initialize from a file.

        Parameters
        ----------
        path : :class:`str`
            The path to a molecular structure file. Supported file
            types are:

                #. ``.mol``, ``.sdf`` - MDL V3000 MOL file
                #. ``.pdb`` - PDB file

        functional_groups : :class:`iterable`, optional
            An :class:`iterable` of :class:`.FunctionalGroup` or
            :class:`.FunctionalGroupFactory` or both.
            :class:`.FunctionalGroup` instances are added to the
            building block and :class:`.FunctionalGroupFactory`
            instances are used to create :class:`.FunctionalGroup`
            instances the building block should hold.
            :class:`.FunctionalGroup` instances are used to identify
            which atoms are modified during
            :class:`.ConstructedMolecule` construction.

        Returns
        -------
        :class:`.BuildingBlock`
            The building block.

        Raises
        ------
        :class:`ValueError`
            If the file type cannot be used for initialization.

        """

        if os.path.exists(path):
            _, ext = os.path.splitext(path)

            if ext not in cls._init_funcs:
                raise ValueError(
                    f'Unable to initialize from "{ext}" files.'
                )
            # This remake needs to be here because molecules loaded
            # with rdkit often have issues, because rdkit tries to do
            # bits of structural analysis like stereocenters. remake
            # gets rid of all this problematic metadata.
            molecule = remake(cls._init_funcs[ext](path))

        return cls.init_from_rdkit_mol(
            molecule=molecule,
            functional_groups=functional_groups,
        )

    @classmethod
    def init_from_rdkit_mol(cls, molecule, functional_groups=None):
        """
        Initialize from an :mod:`rdkit` molecule.

        Parameters
        ----------
        molecule : :class:`rdkit.Mol`
            The molecule.

        functional_groups : :class:`iterable`, optional
            An :class:`iterable` of :class:`.FunctionalGroup` or
            :class:`.FunctionalGroupFactory` or both.
            :class:`.FunctionalGroup` instances are added to the
            building block and :class:`.FunctionalGroupFactory`
            instances are used to create :class:`.FunctionalGroup`
            instances the building block should hold.
            :class:`.FunctionalGroup` instances are used to identify
            which atoms are modified during
            :class:`.ConstructedMolecule` construction.

        Returns
        -------
        :class:`BuildingBlock`
            The molecule.

        """

        key = cls._get_identity_key_from_rdkit_mol(molecule)
        bb = cls.__new__(cls)
        bb._init_from_rdkit_mol(
            molecule=molecule,
            functional_groups=functional_groups,
            identity_key=key,
        )

        return bb

    def _init_from_rdkit_mol(
        self,
        molecule,
        functional_groups,
        identity_key,
    ):
        """
        Initialize from an :mod:`rdkit` molecule.

        Parameters
        ----------
        molecule : :class:`rdkit.Mol`
            The molecule.

        functional_groups : :class:`iterable`, optional
            An :class:`iterable` of :class:`.FunctionalGroup` or
            :class:`.FunctionalGroupFactory` or both.
            :class:`.FunctionalGroup` instances are added to the
            building block and :class:`.FunctionalGroupFactory`
            instances are used to create :class:`.FunctionalGroup`
            instances the building block should hold.
            :class:`.FunctionalGroup` instances are used to identify
            which atoms are modified during
            :class:`.ConstructedMolecule` construction.

        identity_key : :class:`tuple`
            The identity key of the molecule.

        Returns
        -------
        None : :class:`NoneType`

        """

        if functional_groups is None:
            functional_groups = ()

        atoms = tuple(
            Atom(a.GetIdx(), a.GetAtomicNum(), a.GetFormalCharge())
            for a in molecule.GetAtoms()
        )
        bonds = tuple(
            Bond(
                atoms[b.GetBeginAtomIdx()],
                atoms[b.GetEndAtomIdx()],
                b.GetBondTypeAsDouble()
            )
            for b in molecule.GetBonds()
        )
        position_matrix = molecule.GetConformer().GetPositions()

        super().__init__(atoms, bonds, position_matrix)
        self._identity_key = identity_key
        self._functional_groups = []
        for functional_group in functional_groups:
            if isinstance(functional_group, FunctionalGroup):
                self._with_functional_group(functional_group)
            # Else it is a factory.
            else:
                self._with_functional_groups(functional_group)

    def _with_functional_group(self, functional_group):
        """
        Add a functional group.

        Parameters
        ----------
        functional_group : :class:`.FunctionalGroup`
            The functional group to add.

        Returns
        -------
        :class:`.BuildingBlock`
            The building block.

        """

        # Use atom_map to make sure the clone stored in the building
        # block uses the atoms in _atoms, so that multiple Atom
        # instances are not held by the building block, wasting
        # space.
        self._functional_groups.append(functional_group.clone({
            atom.id: self._atoms[atom.id]
            for atom in functional_group.get_atoms()
        }))
        return self

    def with_functional_group(self, functional_group):
        """
        Return a clone with an additional functional group.

        Parameters
        ----------
        functional_group : :class:`.FunctionalGroup`
            The functional group to add.

        Returns
        -------
        :class:`.BuildingBlock`
            The clone.

        """

        return self.clone()._with_functional_group(functional_group)

    def _with_functional_groups(self, factory):
        """
        Add functional groups produced by `factory`.

        Parameters
        ----------
        factory : :class:`.FunctionalGroupFactory`
            Produces a set of functional groups, which are added to
            the bulding block.

        Returns
        -------
        :class:`.BuildingBlock`
            The building block.

        """

        for functional_group in factory.get_functional_groups(self):
            self._with_functional_group(functional_group)
        return self

    def with_functional_groups(self, factory):
        """
        Return a clone with additional functional groups.

        Parameters
        ----------
        factory : :class:`.FunctionalGroupFactory`
            Produces the additional functional groups, which are
            added to the clone.

        Returns
        -------
        :class:`.BuildingBlock`
            The clone.

        """

        return self.clone()._with_functional_groups(factory)

    def get_num_functional_groups(self):
        """
        Return the number of functional groups.

        Returns
        -------
        :class:`int`
            The number of functional groups in the building block.

        """

        return len(self._functional_groups)

    def get_functional_groups(self, fg_ids=None):
        """
        Yield the functional groups, ordered by id.

        Parameters
        ----------
        fg_ids : :class:`iterable` of :class:`int`, optional
            The ids of functional groups yielded. If ``None``, then
            all functional groups are yielded.

        Yields
        ------
        :class:`.FunctionalGroup`
            A functional group of the building block.

        """

        if fg_ids is None:
            fg_ids = range(len(self._functional_groups))

        for fg_id in fg_ids:
            yield self._functional_groups[fg_id].clone()

    @classmethod
    def init_from_dict(cls, molecule_dict):
        """
        Initialize from a :class:`dict` representation.

        Parameters
        ----------
        molecule_dict : :class:`dict`
            A :class:`dict` representation of a molecule generated
            by :meth:`to_dict`.

        Returns
        -------
        :class:`BuildingBlock`
            The molecule described by `molecule_dict`.

        """

        obj = cls.__new__(cls)
        obj._identity_key = molecule_dict['identity_key']
        obj._position_matrix = np.array(
            molecule_dict['position_matrix']
        ).T
        obj._atoms = eval(molecule_dict['atoms'], vars(atoms))
        obj._bonds = eval(molecule_dict['bonds'], vars(bond))
        for bond_ in obj._bonds:
            bond_.atom1 = obj._atoms[bond_.atom1]
            bond_.atom2 = obj._atoms[bond_.atom2]

        obj._functional_groups = []
        globals_ = vars(functional_groups)
        globals_.update(vars(atoms))
        fgs = eval(molecule_dict['functional_groups'], globals_)
        for functional_group in fgs:
            obj._with_functional_group(functional_group)

        return obj

    def clone(self):
        """
        Return a clone.

        Returns
        -------
        :class:`.BuildingBlock`
            The clone.

        """

        clone = super().clone()
        atom_map = {a.id: a for a in clone._atoms}
        clone._identity_key = str(self._identity_key)
        clone._functional_groups = [
            fg.clone(atom_map) for fg in self._functional_groups
        ]
        return clone

    def get_bonder_ids(self, fg_ids=None):
        """
        Yield ids of bonder atoms.

        Parameters
        ----------
        fg_ids : :class:`iterable` of :class:`int`
            The ids of functional groups whose bonder atoms should be
            yielded. If ``None`` then all bonder atom ids in the
            :class:`.BuildingBlock` will be yielded.

        Yields
        ------
        :class:`int`
            The id of a bonder atom.

        """

        if fg_ids is None:
            fg_ids = range(len(self._functional_groups))

        for fg_id in fg_ids:
            yield from self._functional_groups[fg_id].get_bonder_ids()

    def get_bonder_centroids(self, fg_ids=None):
        """
        Yield the centroids of bonder atoms.

        A bonder centroid is the centroid of all bonder atoms in a
        particular functional group.

        Parameters
        ----------
        fg_ids : :class:`iterable` of :class:`int`
            The ids of functional groups to be used. The bonder
            centroids will be yielded in this order.
            If ``None`` then all functional groups are used and
            centroids are yielded in ascending order of functional
            group id.

        Yields
        ------
        :class:`numpy.ndarray`
            The centroid of a functional group.

        """

        if fg_ids is None:
            fg_ids = range(len(self._functional_groups))

        for fg_id in fg_ids:
            fg = self._functional_groups[fg_id]
            yield self.get_centroid(fg.get_bonder_ids())

    def get_bonder_plane(self, fg_ids=None):
        """
        Return coeffs of the plane formed by the bonder centroids.

        A bonder centroid is the centroid of all bonder atoms in a
        particular functional group.

        A plane is defined by the scalar plane equation::

            ax + by + cz = d.

        This method returns the ``a``, ``b``, ``c`` and ``d``
        coefficients of this equation for the plane formed by the
        bonder centroids. The coefficents ``a``, ``b`` and ``c``
        describe the normal vector to the plane. The coefficent ``d``
        is found by substituting these coefficients along with the
        x, y and z variables in the scalar equation and
        solving for ``d``. The variables x, y and z are
        substituted by the coordinates of some point on the plane. For
        example, the position of one of the bonder centroids.

        Parameters
        ----------
        fg_ids : :class:`iterable` of :class:`int`
            The ids of functional groups used to construct the plane.
            If there are more than three, a plane of best fit through
            the bonder centroids of the functional groups will be made.
            If ``None``, all functional groups in the
            :class:`BuildingBlock` will be used.

        Returns
        -------
        :class:`numpy.ndarray`
            This array has the form ``[a, b, c, d]`` and represents the
            scalar equation of the plane formed by the bonder
            centroids.

        References
        ----------
        https://tinyurl.com/okpqv6

        """

        if fg_ids is None:
            fg_ids = range(len(self._functional_groups))
        else:
            # Iterable is used multiple times.
            fg_ids = list(fg_ids)

        fg = self._functional_groups[fg_ids[0]]
        centroid = self.get_centroid(fg.get_bonder_ids())
        normal = self.get_bonder_plane_normal(fg_ids=fg_ids)
        d = np.sum(normal * centroid)
        return np.append(normal, d)

    def get_bonder_plane_normal(self, fg_ids=None):
        """
        Return the normal to the plane formed by bonder centroids.

        A bonder centroid is the centroid of all bonder atoms in a
        particular functional group.

        The normal of the plane is defined such that it goes in the
        direction toward the centroid of the molecule.

        Parameters
        ----------
        fg_ids  : :class:`iterable` of :class:`int`, optional
            The ids of functional groups used to construct the plane.
            If there are more than three, a plane of best fit through
            the bonder centroids of the functional groups will be made.
            If ``None``, all functional groups in the
            :class:`BuildingBlock` will be used.

        Returns
        -------
        :class:`numpy.ndarray`
            A unit vector which describes the normal to the plane of
            the bonder centroids.

        Raises
        ------
        :class:`ValueError`
            If there are not at least 3 functional groups, which is
            necessary to define a plane.

        """

        if fg_ids is None:
            fg_ids = range(len(self._functional_groups))
        else:
            # The iterable is used mutliple times.
            fg_ids = list(fg_ids)

        if len(fg_ids) < 3:
            raise ValueError(
                'At least 3 functional groups '
                'are necessary to create a plane.'
            )

        centroids = np.array(list(self.get_bonder_centroids(
            fg_ids=fg_ids
        )))
        bonder_centroid = self.get_centroid(
            atom_ids=self.get_bonder_ids(fg_ids=fg_ids)
        )
        normal = np.linalg.svd(centroids - bonder_centroid)[-1][2, :]
        cc_vector = self.get_centroid_centroid_direction_vector(
            fg_ids=fg_ids
        )
        if (
            # vector_angle is NaN if cc_vector is [0, 0, 0].
            not np.allclose(cc_vector, [0, 0, 0], atol=1e-5)
            and vector_angle(normal, cc_vector) > np.pi/2
        ):
            normal *= -1
        return normal

    def get_bonder_distances(self, fg_ids=None):
        """
        Yield distances between pairs of bonder centroids.

        A bonder centroid is the centroid of all bonder atoms in a
        particular functional group.

        Parameters
        ----------
        fg_ids : :class:`iterable` of :class:`int`
            The ids of functional groups to be used.
            If ``None`` then all functional groups are used.

        Yields
        ------
        :class:`tuple`
            A :class:`tuple` of the form ``(3, 54, 12.54)``.
            The first two elements are the ids of the involved
            functional groups and the third element is the distance
            between them.

        """

        if fg_ids is None:
            fg_ids = range(len(self._functional_groups))

        # Iterator yielding tuples of form (fg_id, bonder_centroid)
        centroids = ((
            i, self.get_centroid(
                atom_ids=self._functional_groups[i].get_bonder_ids()
            ))
            for i in fg_ids
        )
        pairs = it.combinations(iterable=centroids, r=2)
        for (id1, c1), (id2, c2) in pairs:
            yield id1, id2, float(euclidean(c1, c2))

    def get_bonder_direction_vectors(
        self,
        fg_ids=None
    ):
        """
        Yield the direction vectors between bonder centroids.

        A bonder centroid is the centroid of all bonder atoms in a
        particular functional group.

        Parameters
        ----------
        fg_ids : :class:`iterable` of :class:`int`
            The ids of functional groups to be used.
            If ``None`` then all functional groups are used.

        Yields
        ------
        :class:`tuple`
            They yielded tuple has the form

            .. code-block:: python

                (3, 54, np.array([12.2, 43.3, 9.78]))

            The first two elements of the tuple represent the ids
            of the start and end fgs of the vector, respectively. The
            array is the direction vector running between the
            functional group positions.

        """

        if fg_ids is None:
            fg_ids = range(len(self._functional_groups))

        # Iterator yielding tuples of form (fg_id, bonder_centroid)
        centroids = ((
            i, self.get_centroid(
                atom_ids=self._functional_groups[i].get_bonder_ids()
            ))
            for i in fg_ids
        )
        pairs = it.combinations(iterable=centroids, r=2)
        for (id1, c1), (id2, c2) in pairs:
            yield id2, id1, c1-c2

    def get_centroid_centroid_direction_vector(
        self,
        fg_ids=None
    ):
        """
        Return the direction vector between the 2 molecular centroids.

        The first molecular centroid is the centroid of the entire
        molecule. The second molecular centroid is the of the
        bonder atoms in the molecule.

        Parameters
        ----------
        fg_ids : :class:`iterable` of :class:`int`
            The ids of functional groups to be used for calculating the
            bonder centroid. If ``None`` then all functional groups are
            used.

        Returns
        -------
        :class:`numpy.ndarray`
            The vector running from the centroid of the bonder atoms to
            the molecular centroid.

        """

        if fg_ids is None:
            fg_ids = range(len(self._functional_groups))
        else:
            # This iterable gets used more than once.
            fg_ids = list(fg_ids)

        bonder_centroid = self.get_centroid(
            atom_ids=self.get_bonder_ids(fg_ids=fg_ids)
        )
        return self.get_centroid() - bonder_centroid

    def to_dict(self):
        """
        Return a :class:`dict` representation.

        Returns
        -------
        :class:`dict`
            A :class:`dict` which represents the molecule.

        """

        bonds = []
        for bond_ in self._bonds:
            clone = bond_.clone()
            clone.atom1 = clone.atom1.id
            clone.atom2 = clone.atom2.id
            bonds.append(clone)

        return {
            'class': self.__class__.__name__,
            'functional_groups': repr(self._functional_groups),
            'position_matrix': self.get_position_matrix().tolist(),
            'atoms': repr(self._atoms),
            'bonds': repr(bonds),
            'identity_key': self._identity_key,
        }

    @staticmethod
    def _get_identity_key_from_rdkit_mol(molecule):
        # Don't modify the original molecule.
        mol = rdkit.Mol(molecule)
        rdkit.SanitizeMol(mol)
        return rdkit.MolToSmiles(molecule, canonical=True)

    def __str__(self):
        if self._functional_groups:
            fg_repr = f', {self._functional_groups!r}'
        else:
            fg_repr = ''

        smiles = rdkit.MolToSmiles(rdkit.RemoveHs(self.to_rdkit_mol()))
        return f'{self.__class__.__name__}({smiles!r}{fg_repr})'

    def __repr__(self):
        return str(self)
