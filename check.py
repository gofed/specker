#!/usr/bin/python
# -*- coding: utf-8 -*-
# ####################################################################
# specker-lib - spec file manipulation library
# Copyright (C) 2015  Fridolin Pokorny, fpokorny@redhat.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# ####################################################################
'''
Library check tool
@author: Fridolin Pokorny
@contact: fpokorny@redhat.com
@organization: Red Hat Inc.
@license: GPL 2.0
'''

import unittest
import sys
import logging
import optparse
from subprocess import PIPE, Popen

LOGGER = logging.getLogger('specker-check')
VERBOSE = False

def run_specker(args, stdin = None):
	'''
	Run specker with args
	@param args: args to run specker with
	@type args: list of strings
	@param stdin: file hanler for stdin
	@type stdin: file handler
	@return: process info
	@rtype: dict {'stdout', 'stderr', 'returncode'}
	'''
	prog = ["./specker"] + args
	LOGGER.debug(">>> args: " + str(args))

	if stdin:
		fin = open(stdin, 'r')
	else:
		fin = None

	process = Popen(prog, stdin = fin, stderr = PIPE, stdout = PIPE, shell = False)
	stdout, stderr = process.communicate()
	returncode = process.returncode

	if stdin:
		fin.close()

	return { 'stdout': stdout, 'stderr': stderr, 'returncode': returncode }

def print_status(status, verbose = VERBOSE, additional = None):
	'''
	Print status of a process, if verbose
	@param status: process status to be printed
	@type status: dict {'stdout', 'stderr', 'returncode'}
	@param verbose: if True, print status
	@type verbose: Boolean
	@return: None
	@rtype: None
	'''
	if VERBOSE:
		LOGGER.debug(">>> FAILED!!!")
		LOGGER.debug(">>> Stdout:\n%s", status['stdout'])
		LOGGER.debug(">>> Stderr:\n%s", status['stderr'])
		LOGGER.debug(">>> Return code:\n%s", status['returncode'])
		if additional:
			LOGGER.debug(">>> Additional info:\n%s", additional)

def assertContains(pattern, output, status):
	'''
	Check if pattern is in output
	@param pattern: pattern to be checked
	@type pattern: string
	@param output: string to check against
	@type output: string
	@param status: status to be printed if assertion fails
	@type status: dict {'stdout', 'stderr', 'returncode'}
	'''
	if pattern not in output:
		print_status(status)
		assert False

def assertTrue(expr, status):
	'''
	Check true value
	@param expr: expression which should be true
	@type expr: Boolean
	@param status: status to be printed if assertion fails
	@type status: dict {'stdout', 'stderr', 'returncode'}
	'''
	if not expr:
		print_status(status)
		assert False

def assertFalse(expr, status):
	'''
	Check false value
	@param expr: expression which should be false
	@type expr: Boolean
	@param status: status to be printed if assertion fails
	@type status: dict {'stdout', 'stderr', 'returncode'}
	'''
	assertTrue(not expr, status)

def assertEqual(cmp1, cmp2, status):
	'''
	Check equal
	@param cmp1: expression 1 to be checked
	@param cmp2: expression 2 to be checked
	@param status: status to be printed if assertion fails
	@type status: dict {'stdout', 'stderr', 'returncode'}
	'''
	if cmp1 != cmp2:
		print_status(status)
		assert False

def assertNotEqual(cmp1, cmp2, status):
	'''
	Check not equal
	@param cmp1: expression 1 to be checked
	@param cmp2: expression 2 to be checked
	@param status: status to be printed if assertion fails
	@type status: dict {'stdout', 'stderr', 'returncode'}
	'''
	if cmp1 == cmp2:
		print_status(status)
		assert False

def assertNoDiff(stdout, f, status):
		with open(f, 'r') as fout:
			content = fout.read()

		if stdout != content:
			cmd = Popen(["diff", "-Naur", f, '-'], stdout=PIPE, stdin=PIPE)
			diff = cmd.communicate(input = stdout)[0]
			print_status(status, additional = diff)
			assert False

################################################################################

class TestGeneric(unittest.TestCase):
	'''
	Generic tests
	'''
	def test_nonexisting_file(self):
		input_file = "somenonlongnameofanonexistentfile"
		result = run_specker([input_file])
		assertContains('No such file or directory', result['stderr'], result)
		assertNotEqual(0, result['returncode'], result)

	def test_golang_flannel(self):
		input_file = "./testsuite/golang-flannel.spec"
		result = run_specker([input_file])
		assertEqual(0, result['returncode'], result)
		assertNoDiff(result['stdout'], input_file, result)

	def test_golang_flannel(self):
		input_file = "./testsuite/EMPTY"
		result = run_specker([input_file])
		assertEqual(0, result['returncode'], result)
		assertNoDiff(result['stdout'], input_file, result)

	def test_custom_editor(self):
		input_file = "./testsuite/custom_editor.spec"
		source_file  = "./testsuite/custom_editor.py"
		output_file = "./testsuite/custom_editor_out.spec"
		result = run_specker([
										'--custom-editor=%s' % source_file,
										'--install-edit=777',
										input_file,
									],
									stdin = source_file)
		assertEqual(0, result['returncode'], result)
		assertNoDiff(result['stdout'], output_file, result)

	def test_custom_manipulator_editor(self):
		input_file = "./testsuite/custom_manipulator_editor.spec"
		source_file  = "./testsuite/custom_manipulator_editor.py"
		output_file = "./testsuite/custom_manipulator_editor_out.txt"
		result = run_specker([
										"--custom-manipulator-renderer=%s" % source_file,
										"--provides-show=*",
										input_file
									],
									stdin = source_file)
		assertEqual(0, result['returncode'], result)
		assertNoDiff(result['stdout'], output_file, result)

	def test_custom_model_writer(self):
		input_file = "./testsuite/custom_model_writer.spec"
		source_file  = "./testsuite/custom_model_writer.py"
		output_file = "./testsuite/custom_model_writer_out.spec"
		result = run_specker([
										"--custom-model-writer=%s" % source_file,
										"--provides-remove=/bin/cp",
										input_file
									],
									stdin = source_file)
		assertEqual(0, result['returncode'], result)
		assertNoDiff(result['stdout'], output_file, result)

################################################################################

class TestModel(unittest.TestCase):
	'''
	Test L{SpecModel}
	'''
	def test_sections_add(self):
		input_file1 = "./testsuite/sections_add_in1.spec"
		input_file2 = "./testsuite/sections_add_in2.spec"
		output_file = './testsuite/sections_add_out.spec'
		result = run_specker([input_file1, '--sections-add'], stdin = input_file2)
		assertEqual(0, result['returncode'], result)
		assertNoDiff(result['stdout'], output_file, result)

################################################################################

class TestFileParser(unittest.TestCase):
	'''
	Test L{SpecFileParser}
	'''
	pass

################################################################################

class TestDefaultEditor(unittest.TestCase):
	'''
	Test L{SpecDefaultEditor}
	'''
	pass

################################################################################

class TestFileRenderer(unittest.TestCase):
	'''
	Test L{SpecFileRenderer}
	'''
	pass

################################################################################

if __name__ == '__main__':
	LOGGER.addHandler(logging.StreamHandler(sys.stderr))
	parser = optparse.OptionParser("%prog OPTIONS")

	parser.add_option(
		"", "-v", "--verbose", dest="verbose", action = "store_true",
		default = False, help = "verbose output"
	)

	options, args = parser.parse_args()
	if len(args) > 0:
		LOGGER.error("Error: Incorrect number of arguments")
		exit(1)

	if options.verbose:
		VERBOSE = True
		LOGGER.setLevel(logging.DEBUG)
		LOGGER.debug(">>> running in verbose mode")
		unittest_verbosity = 0
	else:
		unittest_verbosity = 2

	loader = unittest.TestLoader()

	suites_list = []
	for test_class in [TestGeneric, TestFileParser, TestModel, TestDefaultEditor, TestFileRenderer]:
		suites_list.append(loader.loadTestsFromTestCase(test_class))

	ret = unittest.TextTestRunner(verbosity = unittest_verbosity).run(unittest.TestSuite(suites_list))
	sys.exit(not (len(ret.errors) == 0 and len(ret.failures) == 0))

