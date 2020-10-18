# Copyright (c) 2015, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals, absolute_import, print_function
import click
import frappe
from frappe.commands import pass_context, get_site

def call_command(cmd, context):
	return click.Context(cmd, obj=context).forward(cmd)

commands = []