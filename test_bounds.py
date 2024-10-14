from bounds import Bounds


def test_invert():
    """Test bound inversion"""
    b = Bounds(((None, 1), (2, 3), (4, 5), (6, None)))
    b.invert()

    assert (b.get_bounds() == ((1, 2), (3, 4), (5, 6)))


def test_intersection():

    assert (
        Bounds(((1, 10),)).intersect_interval(
            (2, 5)
        ).get_bounds() == ((2, 5),)
    )

    assert (
        Bounds(((1, 2), (3, 6), (8, 10))).intersect_interval(
            (4, 5)
        ).get_bounds() == ((4, 5),)
    )

    assert (
        Bounds(((1, 2), (4, 5), (8, 10))).intersect_interval(
            (3, 6)
        ).get_bounds() == ((4, 5),)
    )

    assert (
        Bounds(((1, 3), (4, 5), (8, 10))).intersect_interval(
            (2, 9)
        ).get_bounds() == ((2, 3), (4, 5), (8, 9))
    )

    assert (
        Bounds(((1, 3), (4, 5), (8, 10), (11, 20))).intersect_interval(
            (2, 9)
        ).get_bounds() == ((2, 3), (4, 5), (8, 9))
    )

    assert (
        Bounds(((1, 3), (4, 6), (8, 10), (11, 20))).intersect_interval(
            (5, 9)
        ).get_bounds() == ((5, 6), (8, 9))
    )


def test_intersection_equal_bounds():
    assert (
        Bounds(((1, 2), (3, 4))).intersect_interval(
            (1, 3)
        ).get_bounds() == ((1, 2), (3, 3))
    )
    # assert (
    #     Bounds(((None, 5), (10, None))).intersect_interval(
    #         ()
    #     ).get_bounds() == ((1, 2), (3, 3))
    # )


def test_intersections_none():

    assert (
        Bounds(((1, 2),)).intersect_interval(
            (None, None)
        ).get_bounds() == ((1, 2),)
    ), "Intersection with None means intersect with +- infty, returning the bounds"

    assert (
        Bounds(((1, 3),)).intersect_interval(
            (None, 2)
        ).get_bounds() == ((1, 2),)
    )

    assert (
        Bounds(((1, 3), (6, 10))).intersect_interval(
            (None, 2)
        ).get_bounds() == ((1, 2),)
    )

    assert (
        Bounds(((1, 3), (4, 6), (8, 10))).intersect_interval(
            (None, 5)
        ).get_bounds() == ((1, 3), (4, 5))
    )

    assert (
        Bounds(((1, 3),)).intersect_interval(
            (2, None)
        ).get_bounds() == ((2, 3),)
    )

    assert (
        Bounds(((1, 3), (6, 10))).intersect_interval(
            (2, None)
        ).get_bounds() == ((2, 3), (6, 10))
    )

    assert (
        Bounds(((1, 3), (4, 7), (8, 10),)).intersect_interval(
            (6, None)
        ).get_bounds() == ((6, 7), (8, 10))
    )

    assert (
        Bounds(((None, 1), (3, None),)).intersect_interval(
            (None, 2)
        ).get_bounds() == ((None, 1),)
    )
    assert (
        Bounds(((None, 3), (4, None),)).intersect_interval(
            (None, 2)
        ).get_bounds() == ((None, 2),)
    )
    assert (
        Bounds(((None, 1), (3, None),)).intersect_interval(
            (2, None)
        ).get_bounds() == ((3, None),)
    )

    assert (
        Bounds(((None, 3), (4, None),)).intersect_interval(
            (6, None)
        ).get_bounds() == ((6, None),)
    )

    assert (
        Bounds(((None, 3), (6, None),)).intersect_interval(
            (4, None)
        ).get_bounds() == ((6, None),)
    )


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


def test_union_interval_nones_in_bounds():
    """Test union of intervals with None values in original bounds"""

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


def test_union_interval_nones_in_interval():
    """Test union of intervals with None values in original bounds"""
    assert (
        Bounds(((1, 3),)).union_interval(
            (None, 2)).get_bounds() == ((None, 3),)
    )

    assert (
        Bounds(((1, 3), (4, 6))).union_interval(
            (None, 2)).get_bounds() == ((None, 3), (4, 6))
    )

    assert (
        Bounds(((1, 3), (4, 6))).union_interval(
            (None, 5)).get_bounds() == ((None,  6),)
    )

    assert (
        Bounds(((1, 3),)).union_interval(
            (2, None)).get_bounds() == ((1, None),)
    )


def test_union_interval_nones_in_both():

    assert (
        Bounds(((None, 3),)).union_interval(
            (None, 2)).get_bounds() == ((None, 3),)
    )
    assert (
        Bounds(((None, 2),)).union_interval(
            (None, 3)).get_bounds() == ((None, 3),)
    )
    assert (
        Bounds(((None, 2), (4, 6))).union_interval(
            (None, 3)).get_bounds() == ((None, 3), (4, 6))
    )
    assert (
        Bounds(((3, None),)).union_interval(
            (2, None)).get_bounds() == ((2, None),)
    )


def test_union_bounds():
    assert (
        Bounds(((3, None),)).union_bounds(Bounds(
            ((2, None),)
        )).get_bounds() == ((2, None),)
    )
