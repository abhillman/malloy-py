# Copyright 2023 Google LLC
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""Malloy schema renderer"""

from .scripts import schema_scripts
from .styles import schema_styles
from .icons import get_icon_path


def field_sort(a):
  """
  Sorts fields in an order similar to the VS Code extension:
  1. Turtles
  2. Dimensions
  3. Measures
  4. Joins
  """
  is_aggregate = a.get("expressionType") == "aggregate"
  return (0 if a["type"] == "turtle" else
          3 if a["type"] == "struct" else 2 if is_aggregate else 1, a["name"])


def build_title(field, path):
  """
  Creates a tool type similar to the VS Code extension.
  """
  field_type = field.get("type")
  field_name = field_name = field.get("as") or field.get("name")
  if field_type == "struct":
    return field_name
  return f"""{field.get("as") or field.get("name")}
Path: {f"{path}{'.' if path else ''}{field_name}"}
Type: {field.get("type")}"""


def field_sorter(fields):
  """
  Bucket fields into queries, dimensions, measures and structs
  """
  queries = []
  dimensions = []
  measures = []
  structs = []

  for field in fields:
    is_aggregate = field.get("expressionType") == "aggregate"
    field_type = field.get("type")

    if is_aggregate:
      measures.append(field)
    elif field_type == "turtle":
      queries.append(field)
    elif field_type == "struct":
      structs.append(field)
    else:
      dimensions.append(field)

  return [queries, dimensions, measures, structs]


def render_field(field, path):
  field_type = field.get("type")
  is_aggregate = field.get("expressionType") == "aggregate"
  field_name = field.get("as") or field.get("name")

  return f"""<div class="field" title="{build_title(field, path)}">
  {get_icon_path(field_type, is_aggregate)}
  <span class="field_name">{field_name}</span>
</div>"""


def render_fields(root, path=""):
  """
  Render one level of the schema tree. Used recursively to handle
  nested schemas.
  """
  html = ""
  fields = root["fields"]
  join_relationship = root.get("structRelationship")
  join_type = None
  if join_relationship:
    join_type = join_relationship.get("type")
  icon_type = join_type if join_type else "struct_base"
  schema_name = root.get("as") or root.get("name")
  html += f"""
<li 
  class="schema hidden"
  title="{build_title(root, path)}"
  onclick="toggleClass(event, 'hidden');"; 
  return false;"
>
{get_icon_path(icon_type, False)} <b class="schema_name">{schema_name}</b>
<ul>
"""
  [queries, dimensions, measures, structs] = field_sorter(fields)

  if len(queries) > 0:
    html += """<li class="fields"><label>Queries</label> """
    html += " ".join(
        render_field(field, path) for field in sorted(queries, key=field_sort))
    html += "</li>"

  if len(dimensions) > 0:
    html += """<li class="fields"><label>Dimensions</label> """
    html += " ".join(
        render_field(field, path)
        for field in sorted(dimensions, key=field_sort))
    html += "</li>"

  if len(measures) > 0:
    html += """<li class="fields"><label>Measures</label> """
    html += " ".join(
        render_field(field, path) for field in sorted(measures, key=field_sort))
    html += "</li>"

  if len(structs) > 1:
    html += """<li class="fields"><label>Relations</label> """
    for field in sorted(structs, key=field_sort):
      field_name = field.get("as") or field.get("name")
      html += "<ul>"
      html += render_fields(field, f"{path}{'.' if path else ''}{field_name}")
      html += "</ul>"
    html += "</li>"
  html += """
  </ul>
</li>
"""
  return html


def render_schema(model):
  """
  Render a model into a schema tree.
  """
  html = schema_styles + schema_scripts
  html += "<ul>\n"
  for schema_name in model["contents"]:
    schema = model["contents"][schema_name]
    html += render_fields(schema)
  html += "</ul>\n"

  return html
