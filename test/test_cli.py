import multiprocessing
import pytest
import time

from click.testing import CliRunner

from delirium.apps import dns


runner = CliRunner()

def run_clirunner():
    response = runner.invoke(dns,)

def test_cli_help():
    response = runner.invoke(dns, ['--help'])
    assert 'Show this message and exit.' in response.output


def test_cli_bad_switch():
    response = runner.invoke(dns, ['oiuytrew'])
    assert 'Got unexpected extra argument' in response.output


def test_cli_no_args():


    p = multiprocessing.Process(target=run_clirunner)
    p.start()
    assert p.is_alive() == True
    p.kill()
