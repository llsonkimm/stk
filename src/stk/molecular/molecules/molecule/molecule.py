import json
import os
import rdkit.Chem.AllChem as rdkit

from stk.utilities import mol_from_mae_file, remake


class Molecule:
    """
    An abstract base class for all molecules.

    """

    @classmethod
    def init_from_dict(self, molecule_dict):
        """
        Initialize from a :class:`dict` representation.

        Parameters
        ----------
        molecule_dict : :class:`dict`
            A :class:`dict` holding the :class:`dict` representation
            of a molecule, generated by :meth:`to_dict`.

        Returns
        -------
        :class:`Molecule`
            The molecule represented by `molecule_dict`.

        """

        raise NotImplementedError()

    def apply_displacement(self, displacement):
        """
        Shift the centroid by `displacement`.

        Parameters
        ----------
        displacement : :class:`numpy.ndarray`
            A displacement vector applied to the molecule.

        Returns
        -------
        :class:`.Molecule`
            The molecule.

        """

        raise NotImplementedError()

    def apply_rotation_about_axis(self, angle, axis, origin):
        """
        Rotate by `angle` about `axis` on the `origin`.

        Parameters
        ----------
        angle : :class:`float`
            The size of the rotation in radians.

        axis : :class:`numpy.ndarray`
            The axis about which the rotation happens.

        origin : :class:`numpy.ndarray`
            The origin about which the rotation happens.

        Returns
        -------
        :class:`.Molecule`
            The molecule.

        """

        raise NotImplementedError()

    def apply_rotation_between_vectors(self, start, target, origin):
        """
        Rotate by a rotation from `start` to `target`.

        Given two direction vectors, `start` and `target`, this method
        applies the rotation required transform `start` to `target`
        onto the molecule. The rotation occurs about the `origin`.

        For example, if the `start` and `target` vectors
        are 45 degrees apart, a 45 degree rotation will be applied to
        the molecule. The rotation will be along the appropriate
        direction.

        The great thing about this method is that you as long as you
        can associate a geometric feature of the molecule with a
        vector, then the molecule can be rotated so that this vector is
        aligned with `target`. The defined vector can be virtually
        anything. This means that any geometric feature of the molecule
        can be easily aligned with any arbitrary axis.

        Parameters
        ----------
        start : :class:`numpy.ndarray`
            A vector which is to be rotated so that it transforms into
            the `target` vector.

        target : :class:`numpy.ndarray`
            The vector onto which `start` is rotated.

        origin : :class:`numpy.ndarray`
            The point about which the rotation occurs.

        Returns
        -------
        :class:`.Molecule`
            The molecule.

        """

        raise NotImplementedError()

    def apply_rotation_to_minimize_angle(
        self,
        start,
        target,
        axis,
        origin
    ):
        """
        Rotate to minimize the angle between `start` and `target`.

        Note that this function will not necessarily overlay the
        `start` and `target` vectors. This is because the possible
        rotation is restricted to the `axis`.

        Parameters
        ----------
        start : :class:`numpy.ndarray`
            The vector which is rotated.

        target : :class:`numpy.ndarray`
            The vector which is stationary.

        axis : :class:`numpy.ndarray`
            The vector about which the rotation happens.

        origin : :class:`numpy.ndarray`
            The origin about which the rotation happens.

        Returns
        -------
        :class:`.Molecule`
            The molecule.

        """

        raise NotImplementedError()

    def clone(self):
        """
        Return a clone.

        Any public attributes are inherited by the clone but any
        private ones are not.

        Returns
        -------
        :class:`.Molecule`
            The clone.

        """

        raise NotImplementedError()

    def get_atom_positions(self, atom_ids=None):
        """
        Yield the positions of atoms.

        Parameters
        ----------
        atom_ids : :class:`iterable` of :class:`int`, optional
            The ids of the atoms whose positions are desired.
            If ``None``, then the positions of all atoms will be
            yielded.

        Yields
        ------
        :class:`numpy.ndarray`
            The x, y and z coordinates of an atom.

        """

        raise NotImplementedError()

    def get_atom_distance(self, atom1_id, atom2_id):
        """
        Return the distance between 2 atoms.

        This method does not account for the van der Waals radius of
        atoms.

        Parameters
        ----------
        atom1_id : :class:`int`
            The id of the first atom.

        atom2_id : :class:`int`
            The id of the second atom.

        Returns
        -------
        :class:`float`
            The distance between the first and second atoms.

        """

        raise NotImplementedError()

    def get_center_of_mass(self, atom_ids=None):
        """
        Return the centre of mass.

        Parameters
        ----------
        atom_ids : :class:`iterable` of :class:`int`, optional
            The ids of atoms which should be used to calculate the
            center of mass. If ``None``, then all atoms will be used.

        Returns
        -------
        :class:`numpy.ndarray`
            The coordinates of the center of mass.

        Raises
        ------
        :class:`ValueError`
            If `atom_ids` has a length of ``0``.

        References
        ----------
        https://en.wikipedia.org/wiki/Center_of_mass

        """

        raise NotImplementedError()

    def get_atoms(self, atom_ids=None):
        """
        Yield the atoms in the molecule, ordered by id.

        Parameters
        ----------
        atom_ids : :class:`iterable` of :class:`int`, optional
            The ids of atoms to yield. If ``None`` then all atoms are
            yielded.

        Yields
        ------
        :class:`.Atom`
            An atom in the molecule.

        """

        raise NotImplementedError()

    def get_bonds(self):
        """
        Yield the bond in the molecule.

        Yields
        ------
        :class:`.Bond`
            A bond in the molecule.

        """

        raise NotImplementedError()

    def get_centroid(self, atom_ids=None):
        """
        Return the centroid.

        Parameters
        ----------
        atom_ids : :class:`iterable` of :class:`int`, optional
            The ids of atoms which are used to calculate the
            centroid. If ``None``, then all atoms will be used.

        Returns
        -------
        :class:`numpy.ndarray`
            The centroid of atoms specified by `atom_ids`.

        Raises
        ------
        :class:`ValueError`
            If `atom_ids` has a length of ``0``.

        """

        raise NotImplementedError()

    def get_direction(self, atom_ids=None):
        """
        Return a vector of best fit through the atoms.

        Parameters
        ----------
        atom_ids : :class:`iterable` of :class:`int`, optional
            The ids of atoms which should be used to calculate the
            vector. If ``None``, then all atoms will be used.

        Returns
        -------
        :class:`numpy.ndarray`
            The vector of best fit.

        Raises
        ------
        :class:`ValueError`
            If `atom_ids` has a length of ``0``.

        """

        raise NotImplementedError()

    def get_identity_key(self):
        """
        Return the identity key.

        The identity key wil be equal for two molecules which
        ``stk`` sees as identical. The identity key does not take
        the conformation into account but it does account for
        isomerism.

        Returns
        -------
        :class:`object`
            A hashable object which represents the identity of the
            molecule.

        """

        raise NotImplementedError()

    def get_maximum_diameter(self, atom_ids=None):
        """
        Return the maximum diameter.

        This method does not account for the van der Waals radius of
        atoms.

        Parameters
        ----------
        atom_ids : :class:`iterable` of :class:`int`
            The ids of atoms which are considered when looking for the
            maximum diameter. If ``None`` then all atoms in the
            molecule are considered.

        Returns
        -------
        :class:`float`
            The maximum diameter in the molecule.

        Raises
        ------
        :class:`ValueError`
            If `atom_ids` has a length of ``0``.

        """

        raise NotImplementedError()

    def get_plane_normal(self, atom_ids=None):
        """
        Return the normal to the plane of best fit.

        Parameters
        ----------
        atom_ids : :class:`iterable` of :class:`int`, optional
            The ids of atoms which should be used to calculate the
            plane. If ``None``, then all atoms will be used.

        Returns
        -------
        :class:`numpy.ndarray`
            Vector orthonormal to the plane of the molecule.

        Raises
        ------
        :class:`ValueError`
            If `atom_ids` has a length of ``0``.

        """

        raise NotImplementedError()

    def get_position_matrix(self):
        """
        Return a matrix holding the atomic positions.

        Returns
        -------
        :class:`numpy.ndarray`
            The array has the shape ``(n, 3)``. Each row holds the
            x, y and z coordinates of an atom.

        """

        raise NotImplementedError()

    def set_centroid(self, position, atom_ids=None):
        """
        Set the centroid to `position`.

        Parameters
        ----------
        position : :class:`numpy.ndarray`
            This array holds the position on which the centroid of the
            molecule is going to be placed.

        atom_ids : :class:`iterable` of :class:`int`
            The ids of atoms which should have their centroid set to
            `position`. If ``None`` then all atoms are used.

        Returns
        -------
        :class:`Molecule`
            The molecule.

        """

        centroid = self.get_centroid(atom_ids=atom_ids)
        self.apply_displacement(position-centroid)
        return self

    def set_position_matrix(self, position_matrix):
        """
        Set the coordinates to those in `position_matrix`.

        Parameters
        ----------
        position_matrix : :class:`numpy.ndarray`
            A position matrix of the molecule. The shape of the matrix
            is ``(n, 3)``.

        Returns
        -------
        :class:`Molecule`
            The molecule.

        """

        raise NotImplementedError()

    def dump(self, path):
        """
        Write a :class:`dict` representation to a file.

        Parameters
        ----------
        path : :class:`str`
            The full path to the file to which the  :class:`dict`
            should be written.

        Returns
        -------
        :class:`Molecule`
            The molecule.

        """

        with open(path, 'w') as f:
            d = self.to_dict()
            json.dump(d, f, indent=4)

    @classmethod
    def load(cls, path):
        """
        Initialize from a dump file.

        Parameters
        ----------
        path : :class:`str`
            The full path to a file holding a dumped molecule.

        Returns
        -------
        :class:`Molecule`
            The molecule held in `path`.

        """

        with open(path, 'r') as f:
            molecule_dict = json.load(f)

        return cls.init_from_dict(molecule_dict)

    def _to_mdl_mol_block(self, atom_ids=None):
        """
        Return a V3000 mol block of the molecule.

        Parameters
        ----------
        atom_ids : :class:`iterable` of :class:`int`, optional
            The atom ids of atoms to write. If ``None`` then all atoms
            are written.

        Returns
        -------
        :class:`str`
            The V3000 mol block representing the molecule.

        """

        raise NotImplementedError()

    def to_rdkit_mol(self):
        """
        Return an :mod:`rdkit` representation.

        Returns
        -------
        :class:`rdkit.Mol`
            The molecule in :mod:`rdkit` format.

        """

        raise NotImplementedError()

    def to_dict(self):
        """
        Return a :class:`dict` representation.

        All public attributes are included in the representation
        and private ones are not.

        Returns
        -------
        :class:`dict`
            A :class:`dict` representation of the molecule.

        """

        raise NotImplementedError()

    def update_from_rdkit_mol(self, molecule):
        """
        Update the structure to match `molecule`.

        Parameters
        ----------
        molecule : :class:`rdkit.Mol`
            The :mod:`rdkit` molecule to use for the structure update.

        Returns
        -------
        :class:`.Molecule`
            The molecule.

        """

        pos_mat = molecule.GetConformer().GetPositions()
        self.set_position_matrix(pos_mat)
        return self

    def update_from_file(self, path):
        """
        Update the structure from a file.

        Multiple file types are supported, namely:

        #. ``.mol``, ``.sdf`` - MDL V2000 and V3000 files
        #. ``.xyz`` - XYZ files
        #. ``.mae`` - Schrodinger Maestro files
        #. ``.coord`` - Turbomole files

        Parameters
        ----------
        path : :class:`str`
            The path to a molecular structure file holding updated
            coordinates for the :class:`.Molecule`.

        Returns
        -------
        :class:`.Molecule`
            The molecule.

        """

        update_fns = {
            '.mol': self._update_from_mol,
            '.sdf': self._update_from_mol,
            '.mae': self._update_from_mae,
            '.xyz': self._update_from_xyz,
            '.coord': self._update_from_turbomole,
        }
        _, ext = os.path.splitext(path)
        update_fns[ext](path=path)
        return self

    def _update_from_mae(self, path):
        """
        Update the structure to match an ``.mae`` file.

        Parameters
        ----------
        path : :class:`str`
            The full path of the ``.mae`` file from which the structure
            should be updated.

        Returns
        -------
        None : :class:`NoneType`

        """

        self.update_from_rdkit_mol(mol_from_mae_file(path))

    def _update_from_mol(self, path):
        """
        Update the structure to match a ``.mol`` file.

        Parameters
        ----------
        path : :class:`str`
            The full path of the ``.mol`` file from which the structure
            should be updated.

        Returns
        -------
        None : :class:`NoneType`

        """

        molecule = remake(
            rdkit.MolFromMolFile(
                molFileName=path,
                sanitize=False,
                removeHs=False,
            )
        )
        self.update_from_rdkit_mol(molecule=molecule)

    def _update_from_xyz(self, path):
        """
        Update the structure to match an ``.xyz`` file.

        Parameters
        ----------
        path : :class:`str`
            The full path of the ``.mol`` file from which the structure
            should be updated.

        Returns
        -------
        None : :class:`NoneType`

        Raises
        ------
        :class:`RuntimeError`
            If the number of atoms in the file does not match the
            number of atoms in the molecule or if atom elements in the
            file do not agree with the atom elements in the molecule.

        """

        raise NotImplementedError()

    def _update_from_turbomole(self, path):
        """
        Update the structure from a Turbomole ``.coord`` file.

        Note that coordinates in ``.coord`` files are given in Bohr.

        Parameters
        ----------
        path : :class:`str`
            The full path of the ``.coord`` file from which the
            structure should be updated.

        Returns
        -------
        None : :class:`NoneType`

        Raises
        ------
        :class:`RuntimeError`
            If the number of atoms in the file does not match the
            number of atoms in the molecule or if atom elements in the
            file do not agree with the atom elements in the molecule.

        """

        raise NotImplementedError()

    def write(self, path, atom_ids=None):
        """
        Write the structure to a file.

        This function will write the format based on the extension
        of `path`.

        #. ``.mol``, ``.sdf`` - MDL V3000 MOL file
        #. ``.xyz`` - XYZ file
        #. ``.pdb`` - PDB file

        Parameters
        ----------
        path : :class:`str`
            The `path` to which the molecule should be written.

        atom_ids : :class:`iterable` of :class:`int`, optional
            The atom ids of atoms to write. If ``None`` then all atoms
            are written.

        Returns
        -------
        :class:`.Molecule`
            The molecule.

        """

        writers = {
            '.mol': self._write_mdl_mol_file,
            '.sdf': self._write_mdl_mol_file,
            '.xyz': self._write_xyz_file,
            '.pdb': self._write_pdb_file,
        }

        _, ext = os.path.splitext(path)
        write_func = writers[ext]
        write_func(path, atom_ids)
        return self

    def _write_mdl_mol_file(self, path, atom_ids):
        """
        Write to a V3000 ``.mol`` file.

        This function should not be used directly, only via
        :meth:`write`.

        Parameters
        ----------
        path : :class:`str`
            The full path to the file being written.

        atom_ids : :class:`iterable` of :class:`int`
            The atom ids of atoms to write. If ``None`` then all atoms
            are written.

        Returns
        -------
        None : :class:`NoneType`

        """

        with open(path, 'w') as f:
            f.write(self._to_mdl_mol_block(atom_ids))

    def _write_xyz_file(self, path, atom_ids):
        """
        Write to a ``.xyz`` file.

        This function should not be used directly, only via
        :meth:`write`.

        Parameters
        ----------
        path : :class:`str`
            The full path to the file being written.

        atom_ids : :class:`iterable` of :class:`int`
            The atom ids of atoms to write. If ``None`` then all atoms
            are written.

        Returns
        -------
        None : :class:`NoneType`

        """

        raise NotImplementedError()

    def _write_pdb_file(self, path, atom_ids):
        """
        Write to a ``.pdb`` file.

        This function should not be used directly, only via
        :meth:`write`.

        Parameters
        ----------
        path : :class:`str`
            The full path to the file being written.

        atom_ids : :class:`iterable` of :class:`int`
            The atom ids of atoms to write. If ``None`` then all atoms
            are written.

        Returns
        -------
        None : :class:`NoneType`

        """

        raise NotImplementedError()