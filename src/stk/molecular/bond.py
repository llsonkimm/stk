"""
Defines :class:`Bond`.

"""


class Bond:
    """
    Represents an atomic bond.

    """

    def __init__(self, atom1, atom2, order, periodicity=(0, 0, 0)):
        """
        Initialize a :class:`Bond`.

        Parameters
        ----------
        atom1 : :class:`.Atom`
            The first atom in the bond.

        atom2 : :class:`.Atom`
            The second atom in the bond.

        order : :class:`int`
            The bond order.

        periodicity : :class:`tuple` of :class:`int`, optional
            The directions across which the bond is periodic. For
            example, ``(1, 0, -1)`` means that when going from
            `atom1` to `atom2` the bond is
            periodic across the x axis in the positive direction, is
            not periodic across the y axis and is periodic across the z
            axis in the negative direction.

        """

        self._atom1 = atom1.clone()
        self._atom2 = atom2.clone()
        self._order = order
        self._periodicity = periodicity

    @classmethod
    def dangerous_init(
        cls,
        atom1,
        atom2,
        order,
        periodicity=(0, 0, 0),
    ):
        """
        Dangerously initialize a :class:`.Bond`.

        Notes
        -----
        This method behaves like :meth:`__init__`, except that
        the bond does not create copies of `atom1` and `atom2` for
        its internal state, but uses them directly.
        This means the bond initialized with this method is not
        fully encapsulated, and is therefore dangerous. However, the
        bond also takes up less memory, because it does not create
        an extra copy of the atoms.

        Parameters
        ----------
        atom1 : :class:`.Atom`
            The first atom in the bond.

        atom2 : :class:`.Atom`
            The second atom in the bond.

        order : :class:`int`
            The bond order.

        periodicity : :class:`tuple` of :class:`int`, optional
            The directions across which the bond is periodic. For
            example, ``(1, 0, -1)`` means that when going from
            `atom1` to `atom2` the bond is
            periodic across the x axis in the positive direction, is
            not periodic across the y axis and is periodic across the z
            axis in the negative direction.

        """

        obj = cls.__new__(cls)
        obj._atom1 = atom1
        obj._atom2 = atom2
        obj._order = order
        obj._periodicity = periodicity
        return obj

    def get_atom1(self):
        """
        Get the first atom of the bond.

        Returns
        -------
        :class:`.Atom`
            The first atom of the bond.

        """

        return self._atom1.clone()

    def get_atom2(self):
        """
        Get the second atom of the bond.

        Returns
        -------
        :class:`.Atom`
            The second atom of the bond.

        """

        return self._atom2.clone()

    def get_order(self):
        """
        Get the bond order of the bond.

        Returns
        -------
        :class:`int`
            THe bond order.

        """

        return self._order

    def get_periodicity(self):
        """
        Get the periodicity of the bond.

        Returns
        -------
        :class:`tuple` of :class:`int`
            The directions across which the bond is periodic. For
            example, ``(1, 0, -1)`` means that when going from
            `atom1` to `atom2` the bond is
            periodic across the x axis in the positive direction, is
            not periodic across the y axis and is periodic across the z
            axis in the negative direction.

        """

        return self._periodicity

    def to_dict(self):
        """
        Get :class:`dict` representation of the bond.

        Returns
        -------
        :class:`dict`
            A :class:`dict` representation.

        """

        return {
            'atom1_id': self._atom1.get_id(),
            'atom2_id': self._atom2.get_id(),
            'order': self._order,
            'periodicity': self._periodicity,
        }

    def clone(self, atom_map=None):
        """
        Return a clone.

        Private attributes are not passed to the clone.

        Parameters
        ----------
        atom_map : :class:`dict`, optional
            If the clone should hold specific :class:`.Atom`
            instances, then a :class:`dict` should be provided, which
            maps atom ids of atoms in the current :class:`.Bond` to the
            :class:`.Atom` which the clone should hold.

        Returns
        -------
        :class:`.Bond`
            The clone.

        Examples
        --------
        .. code-block:: python

            import stk

            c0 = stk.C(0)
            c5 = stk.C(5)
            bond = stk.Bond(c0, c5, 1)

            # bond_clone holds clones of c0 and c5.
            bond_clone = bond.clone()

        It is possible to make sure that the clone holds specific
        atoms

        .. code-block:: python

            li2 = stk.Li(2)
            n3 = stk.N(3)

            # clone2 is also a clone, except that it holds
            # li2 internally. It also holds a clone of c0.
            clone2 = bond.clone(atom_map={
                c5.get_id(): li2,
            })

            # clone3 is also a clone, except that it holds n3 and
            # li2 internally.
            clone3 = bond.clone(atom_map={
                c0.get_id(): n3,
                c5.get_id(): li2,
            })

        """

        if atom_map is None:
            atom_map = {}

        clone = self.__class__.__new__(self.__class__)
        for attr, val in vars(self).items():
            if not attr.startswith('_'):
                setattr(clone, attr, val)
        clone._atom1 = atom_map.get(
            self._atom1.get_id(),
            self._atom1.clone(),
        )
        clone._atom2 = atom_map.get(
            self._atom2.get_id(),
            self._atom2.clone(),
        )
        clone._order = self._order
        clone._periodicity = self._periodicity
        return clone

    def is_periodic(self):
        """
        Return ``True`` if the bond is periodic.

        Returns
        -------
        :class:`bool`
            ``True`` if the bond is periodic.

        """

        return any(direction != 0 for direction in self._periodicity)

    def __repr__(self):
        if isinstance(self._order, float) and self._order.is_integer():
            self._order = int(self._order)

        periodicity = (
            f', periodicity={self._periodicity}'
            if self.is_periodic()
            else ''
        )

        cls_name = self.__class__.__name__
        return (
            f'{cls_name}({self._atom1!r}, {self._atom2!r}, '
            f'{self._order}{periodicity})'
        )

    def __str__(self):
        return repr(self)
