import rich_click as click
import asyncio
import subprocess
from rich.console import Console
from rich.progress import Progress, TextColumn
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
import os


directory = os.getcwd()

file_path = os.path.dirname(__file__)



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



@click.group()
def cli():
    pass



@cli.command()
def version():
    """Shows the current version of mikro"""


@cli.command()
def generate():
    """Generates the mikro api"""
    with open(f"{file_path}/../graphql.config.yaml", "w") as f:
        f.write(v1_file)
    subprocess.run(["turms", "generate", "--config", f"{file_path}/../graphql.config.yaml"])
    os.remove(f"{file_path}/../graphql.config.yaml")

    



if __name__ == '__main__':
    cli()
   