from stork_agent.app import lines_to_tuple


def test_lines_to_tuple_strips_blank_lines() -> None:
    assert lines_to_tuple("a\n\n b \n") == ("a", "b")
