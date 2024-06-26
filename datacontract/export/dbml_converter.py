from datetime import datetime
from importlib.metadata import version
from typing import Tuple

import pytz

import datacontract.model.data_contract_specification as spec
from datacontract.export.sql_type_converter import convert_to_sql_type


def to_dbml_diagram(contract: spec.DataContractSpecification, server: spec.Server) -> str:
    result = ""
    result += add_generated_info(contract, server) + "\n"
    result += generate_project_info(contract) + "\n"

    for model_name, model in contract.models.items():
        table_description = generate_table(model_name, model, server)
        result += f"\n{table_description}\n"

    return result


def add_generated_info(contract: spec.DataContractSpecification, server: spec.Server) -> str:
    tz = pytz.timezone("UTC")
    now = datetime.now(tz)
    formatted_date = now.strftime("%b %d %Y")
    datacontract_cli_version = get_version()
    dialect = "Logical Datacontract" if server is None else server.type

    generated_info = """
Generated at {0} by datacontract-cli version {1}
for datacontract {2} ({3}) version {4} 
Using {5} Types for the field types
    """.format(
        formatted_date, datacontract_cli_version, contract.info.title, contract.id, contract.info.version, dialect
    )

    comment = """/*
{0}
*/
    """.format(generated_info)

    note = """Note project_info {{
'''
{0}
'''
}}
    """.format(generated_info)

    return """{0}
{1}
    """.format(comment, note)


def get_version() -> str:
    try:
        return version("datacontract_cli")
    except Exception:
        return ""


def generate_project_info(contract: spec.DataContractSpecification) -> str:
    return """Project "{0}" {{
    Note: "{1}"
}}\n
    """.format(contract.info.title, " ".join(contract.info.description.splitlines()))


def generate_table(model_name: str, model: spec.Model, server: spec.Server) -> str:
    result = """Table "{0}" {{ 
Note: "{1}"
    """.format(model_name, " ".join(model.description.splitlines()))

    references = []

    # Add all the fields
    for field_name, field in model.fields.items():
        ref, field_string = generate_field(field_name, field, model_name, server)
        if ref is not None:
            references.append(ref)
        result += "{0}\n".format(field_string)

    result += "}\n"

    # and if any: add the references
    if len(references) > 0:
        for ref in references:
            result += "Ref: {0}\n".format(ref)

        result += "\n"

    return result


def generate_field(field_name: str, field: spec.Field, model_name: str, server: spec.Server) -> Tuple[str, str]:
    field_attrs = []
    if field.primary:
        field_attrs.append("pk")

    if field.unique:
        field_attrs.append("unique")

    if field.required:
        field_attrs.append("not null")
    else:
        field_attrs.append("null")

    if field.description:
        field_attrs.append('Note: "{0}"'.format(" ".join(field.description.splitlines())))

    field_type = field.type if server is None else convert_to_sql_type(field, server.type)

    field_str = '"{0}" "{1}" [{2}]'.format(field_name, field_type, ",".join(field_attrs))
    ref_str = None
    if (field.references) is not None:
        # we always assume many to one, as datacontract doesn't really give us more info
        ref_str = "{0}.{1} > {2}".format(model_name, field_name, field.references)
    return (ref_str, field_str)
