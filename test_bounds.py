from bounds import Bounds


def test_invert():
    """Test bound inversion"""
    b = Bounds(((None, 1), (2, 3), (4, 5), (6, None)))
    b.invert()

    assert (b.get_bounds() == ((1, 2), (3, 4), (5, 6)))


def test_union_interval():
    """Test union of intervals"""

    assert (
        Bounds(((1, 2),)).union_interval(
            (2, 3)).get_bounds() == ((1, 3),)
    )
    assert (
        Bounds(((1, 2),)).union_interval(
            (3, 4)).get_bounds() == ((1, 2), (3, 4))
    )
    assert (
        Bounds(((1, 3),)).union_interval(
            (2, 4)).get_bounds() == ((1, 4),)
    )
    assert (
        Bounds(((1, 3), (7, 10))).union_interval(
            (4, 6)).get_bounds() == ((1, 3), (4, 6), (7, 10))
    )


def test_union_interval_nones():
    """Test union of intervals with None values"""

    assert (
        Bounds(((None, 2),)).union_interval(
            (1, 3)).get_bounds() == ((None, 3),)
    )
    assert (
        Bounds(((2, None),)).union_interval(
            (1, 3)).get_bounds() == ((1, None),)
    )

    assert (
        Bounds(((None, 1), (10, None))).union_interval(
            (3, 6)).get_bounds() == ((None, 1), (3, 6), (10, None),)
    )
