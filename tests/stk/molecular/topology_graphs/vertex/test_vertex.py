import numpy as np


def test_apply_scale(vertex_data, position, scale):
    vertex = vertex_data.get_vertex()
    before = vertex.get_position()
    vertex.apply_scale(scale)
    assert np.allclose(
        a=vertex.get_position(),
        b=scale*before,
        atol=1e-32,
    )


def test_clone(vertex_data):
    vertex = vertex_data.get_vertex()
    vertex.attr = 1
    vertex._attr = 2
    clone = vertex.clone()
    assert clone.get_position() == vertex.get_position()
    assert clone.attr == vertex.attr
    assert not hasattr(clone, '_attr')
    assert clone.get_num_edges() == vertex.get_num_edges()
    assert list(clone.get_edge_ids()) == list(vertex.get_edge_ids())
    assert clone.get_cell() == vertex.get_cell()


def test_get_position(vertex_data, position):
    vertex = vertex_data.get_vertex()
    assert np.all(np.equal(vertex.get_position(), position))


def test_get_num_edges(vertex_data):
    vertex = vertex_data.get_vertex()
    assert vertex.get_num_edges() == len(edge_data)


def test_get_edge_ids(make_vertex, edge_data):
    vertex = make_vertex(edge_data=edge_data)
    assert (
        tuple(vertex.get_edge_ids())
        == tuple(data.id for data in edge_data)
    )


def test_get_cell(make_vertex, cell):
    vertex = make_vertex(cell=cell)
    assert vertex.get_cell() == cell


def test_set_constructed_molecule(
    make_vertex,
    constructed_molecule,
    get_atom_ids,
):
    vertex = make_vertex()
    vertex.set_constructed_molecule(constructed_molecule)
    atom_ids = get_atom_ids(constructed_molecule)
    centroid = constructed_molecule.get_centroid(atom_ids)
    constructed_molecule._position_matrix = (
        constructed_molecule._position_matrix.T
    )
    assert (
        vertex.test_get_molecule_centroid(atom_ids=atom_ids)
        == centroid
    )


def test_get_edge_centroid(graph):
    centroid_edges = tuple(
        graph.edges[edge_id] for edge_id in graph.vertex.get_edge_ids()
    )
    centroid = graph.vertex._get_edge_centroid(
        centroid_edges=centroid_edges,
        vertices=graph.vertices,
    )
    assert np.allclose(
        a=centroid,
        b=graph.edge_centroid,
        atol=1e-32,
    )


def test_get_edge_plane_normal(graph):
    plane_edges = tuple(
        graph.edges[edge_id] for edge_id in graph.vertex.get_edge_ids()
    )
    normal = graph.vertex.test_get_edge_plane_normal(
        reference=graph.reference,
        plane_edges=plane_edges,
        vertices=graph.vertices,
    )
    assert np.allclose(
        a=normal,
        b=graph.edge_plane_normal,
        atol=1e-32,
    )


def test_get_molecule_centroid(
    make_vertex,
    constructed_molecule,
    get_atom_ids,
    position,
):
    vertex = make_vertex()
    atom_ids = get_atom_ids(constructed_molecule)
    constructed_molecule.set_position(position, atom_ids)
    constructed_molecule._position_matrix = (
        constructed_molecule._position_matrix.T
    )
    vertex.set_constructed_molecule(constructed_molecule)
    assert vertex._get_molecule_centroid(atom_ids) == position
