import argparse
from enum import Enum
import os
from rich import get_console


directory = os.getcwd()

file_path = os.path.dirname(__file__)


class MikroOptions(str, Enum):
    GEN = "gen"


v1_file= """
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
          ModelData: mikro.scalars.ModelData
          ModelFile: mikro.scalars.ModelFile
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
          Omero:
            - mikro.traits.Omero
          Objective:
            - mikro.traits.Objective
          Position:
            - mikro.traits.Position
          Stage:
            - mikro.traits.Stage
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
                GraphQLProject,
                GeneratorConfig,
            )
            from turms.config import Extensions, GeneratorConfig, FreezeConfig
            from turms.plugins.enums import EnumsPlugin
            from turms.plugins.inputs import InputsPlugin
            from turms.plugins.fragments import FragmentsPlugin
            from turms.plugins.operations import OperationsPlugin
            from turms.plugins.funcs import FuncsPlugin
        except ImportError:
            raise ImportError(
                "Please install turms to use the gen command. `pip install turms`"
            )

        
        project = GraphQLProject(
          schema= os.path.join(file_path, "schemas/v1.graphql"),
          documents= documents,
          extensions=Extensions(
            turms=GeneratorConfig(
              out_dir=app_directory,
              generated_name=codefile,
              freeze=FreezeConfig(
                enabled=True
              ),
              plugins=[
                {"type": "turms.plugins.enums.EnumsPlugin"},
                {"type": "turms.plugins.inputs.InputsPlugin"},
                {"type": "turms.plugins.fragments.FragmentsPlugin"},
                {"type": "turms.plugins.operations.OperationsPlugin"},
                {"type": "turms.plugins.funcs.FuncsPlugin"},
              ]

  
          )
          )

        )


        generated_code = generate(project)

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
        default="*.graphql",
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
