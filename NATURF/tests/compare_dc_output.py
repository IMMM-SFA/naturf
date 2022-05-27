import filecmp

def test_DC():
    """
    Temporary test for comparing the output of DC's C-5 3.2x3.2km region before and after refactoring. 
    """
    actual_dir = "./NATURF/_C-5/"
    expected_dir = "./NATURF/tests/"
    files = ["00065-00096.00065-00096", "C-5.csv", "index"]

    for file in files:
        assert filecmp.cmp(f"{actual_dir}{file}", f"{expected_dir}{file}")
