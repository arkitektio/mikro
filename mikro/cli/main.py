import argparse
from enum import Enum
import os
from rich import get_console


directory = os.getcwd()


class MikroOptions(str, Enum):
    GEN = "gen"


default_settings = """
projects:
  mikro:
    schema: http://localhost:8080/graphql
    documents: graphql/mikro/*/**.graphql
    extensions:
      turms:
        out_dir: mikro/api
        freeze:
          enabled: true
        stylers:
          - type: turms.stylers.default.DefaultStyler
          - type: turms.stylers.appender.AppenderStyler
            append_fragment: "Fragment"
        plugins:
          - type: turms.plugins.enums.EnumsPlugin
          - type: turms.plugins.inputs.InputsPlugin
          - type: turms.plugins.fragments.FragmentsPlugin
          - type: turms.plugins.operations.OperationsPlugin
          - type: turms.plugins.funcs.FuncsPlugin
            global_kwargs:
              - type: mikro.rath.MikroRath
                key: rath
                description: "The mikro rath client"
            definitions:
              - type: subscription
                is_async: True
                use: mikro.funcs.asubscribe
              - type: query
                is_async: True
                use: mikro.funcs.aexecute
              - type: mutation
                is_async: True
                use: mikro.funcs.aexecute
              - type: subscription
                use: mikro.funcs.subscribe
              - type: query
                use: mikro.funcs.execute
              - type: mutation
                use: mikro.funcs.execute
        processors:
          - type: turms.processors.black.BlackProcessor
        scalar_definitions:
          XArrayInput: mikro.scalars.XArrayInput
          File: mikro.scalars.File
          ImageFile: mikro.scalars.File
          Upload: mikro.scalars.Upload
          ParquetInput: mikro.scalars.ParquetInput
          Store: mikro.scalars.Store
          Parquet: mikro.scalars.Parquet
          ID: rath.scalars.ID
          MetricValue: mikro.scalars.MetricValue
          FeatureValue: mikro.scalars.FeatureValue
        additional_bases:
          Representation:
            - mikro.traits.Representation
          Table:
            - mikro.traits.Table
          ROI:
            - mikro.traits.ROI
          InputVector:
            - mikro.traits.Vectorizable
"""


def main(script: MikroOptions, documents: str, codefile: str):
    """The main entrypoint for the CLI"""

    app_directory = os.getcwd()

    if script == MikroOptions.GEN:
        try:

            from turms.run import (
                gen,
                load_projects_from_configpath,
                generate,
                write_code_to_file,
            )
        except ImportError:
            raise ImportError(
                "Please install turms to use the gen command. `pip install turms`"
            )

        config = os.path.join(app_directory, "graphql.config.yaml")
        if not os.path.exists(os.path.join(app_directory, "graphql.config.yaml")):
            with open(config, "w") as f:
                f.write(default_settings)

        projects = load_projects_from_configpath(config, "mikro")
        mikro_project = projects["mikro"]
        mikro_project.documents = documents
        mikro_project.extensions.turms.out_dir = app_directory
        mikro_project.extensions.turms.generated_name = codefile
        generated_code = generate(mikro_project)

        get_console().print(f"-------------- Generating project: mikro --------------")

        write_code_to_file(
            generated_code,
            app_directory,
            codefile,
        )

        get_console().print("Sucessfull!! :right-facing_fist::left-facing_fist:")


def entrypoint():
    parser = argparse.ArgumentParser(description="Say hello")
    parser.add_argument("script", type=MikroOptions, help="The Script Type")
    parser.add_argument(
        "documents",
        type=str,
        help="The gloab to documents",
        nargs="?",
        default="mikrogql/**.graphql",
    )
    parser.add_argument(
        "codefile",
        type=str,
        help="The gloab to documents",
        nargs="?",
        default="generated.py",
    )
    args = parser.parse_args()
    try:
        main(
            script=args.script,
            documents=args.documents,
            codefile=args.codefile,
        )
    except Exception as e:
        get_console().print_exception()


if __name__ == "__main__":
    entrypoint()
