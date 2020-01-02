from .. import FunctionalGroup_


class Bromo(FunctionalGroup_):
    """
    Represents a bromo functional group.

    The structure of the functional group is given by the pseudo-SMILES
    ``[bromine][atom]``.

    """

    def __init__(self, bromine, atom, bonders, deleters):
        atom_map = {
            bromine.id: bromine.clone(),
            atom.id: atom.clone()
        }
        self._bromine = atom_map[bromine.id]
        self._atom = atom_map[atom.id]
        bonders = tuple(atom_map[a.id] for a in bonders)
        deleters = tuple(atom_map[a.id] for a in deleters)
        super()._init(tuple(atom_map.values()), bonders, deleters)

    def get_bromine(self):
        return self._bromine.clone()

    def get_atom(self):
        return self._atom.clone()

    def clone(self, atom_map=None):
        if atom_map is None:
            atom_map = {}
        else:
            atom_map = dict(atom_map)

        atoms = (self._bromine, self._atom)
        for atom in atoms:
            if atom.id not in atom_map:
                atom_map[atom.id] = atom.clone()

        clone = super().clone(atom_map)
        clone._bromine = atom_map[self._bromine.id]
        clone._atom = atom_map[self._atom.id]
        return clone

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'{self._bromine}, {self._atom}, '
            f'bonders={self._bonders}, deleters={self._deleters})'
        )