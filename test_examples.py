import os
import subprocess
import glob
import pytest


def pytest_generate_tests(metafunc):

    examples_dir = os.path.join(os.path.dirname(__file__), 'examples')
    bdsl_files = sorted(glob.glob(os.path.join(examples_dir, '*.bdsl')))

    # print('bdsl_file', metafunc.fixturenames)
    if 'bdsl_file' in metafunc.fixturenames:
        if not bdsl_files:
            raise RuntimeError(
                'No files found for parameterization!',
                os.path.dirname(__file__),
                # examples_dir,
                # os.path.join(examples_dir, '*.bdsl'),
                glob.glob(os.path.join(examples_dir, '*.bdsl')),
            )

        # Generate test cases based on the test_data list
        metafunc.parametrize(
            'bdsl_file', bdsl_files, ids=[os.path.basename(f) for f in bdsl_files]
        )


def test_bdsl_example(bdsl_file):
    """Tests a .bdsl file."""
    bounds_script = os.path.join(os.path.dirname(__file__), 'bdsl.py')
    print(f'Processing {os.path.basename(bdsl_file)}...')
    # Read first line of file
    with open(bdsl_file, 'r') as f:
        first_line = f.readline().strip()

    expected_exception = None
    if first_line.startswith(';; !!!RAISES '):
        expected_exception = first_line.split('!!!RAISES ')[1]

    try:
        result = subprocess.run(
            ['python', bounds_script, bdsl_file],
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)

        # Fail test if exception was expected but none raised
        if expected_exception:
            pytest.fail(f'Expected {expected_exception} but script succeeded')

    except subprocess.CalledProcessError as e:
        if not expected_exception:
            pytest.fail(
                f'Unexpected error occurred: {e.stderr}'
            )  # No exception expected but failed

        # Verify expected exception in stderr
        assert (
            expected_exception in e.stderr
        ), f'Expected {expected_exception} not found in error output:\n{e.stderr}'
