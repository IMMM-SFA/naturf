import os
from typing import List, Union

import pandas as pd
from hamilton import driver, base
from hamilton.plugins import h_tqdm

import naturf.nodes as nodes
import naturf.output as output

DAGWORKS_API_KEY = os.environ.get("DAGWORKS_API_KEY")
DAGWORKS_USERNAME = os.environ.get("DAGWORKS_USERNAME")
DAGWORKS_PROJECT_ID = os.environ.get("DAGWORKS_PROJECT_ID")


class Model:
    def __init__(self, inputs: dict, outputs: List[str], **kwargs):
        # dictionary of parameter inputs required to construct the DAG
        self.inputs = inputs

        # desired output parameters
        self.outputs = outputs

        # instantiate any adapters we want
        hamilton_adapters = [
            base.SimplePythonDataFrameGraphAdapter(),
            h_tqdm.ProgressBar("Naturf DAG"),
        ]
        if DAGWORKS_API_KEY and DAGWORKS_USERNAME and DAGWORKS_PROJECT_ID:
            from dagworks import adapters

            hamilton_adapters.append(
                adapters.DAGWorksTracker(
                    project_id=int(DAGWORKS_PROJECT_ID),
                    api_key=DAGWORKS_API_KEY,
                    username=DAGWORKS_USERNAME,
                    dag_name="naturf-dag",
                    tags={"env": "dev", "status": "development", "version": "1"},
                )
            )

        # instantiate driver with function definitions & adapters
        self.dr = (
            driver.Builder()
            .with_config(self.inputs)
            .with_modules(nodes, output)
            .with_adapters(*hamilton_adapters)
            .build()
        )

    def execute(self) -> pd.DataFrame:
        """Run the driver."""

        # generate initial data frame
        df = self.dr.execute(self.outputs)

        return df

    def graph(self, view: bool = True, output_file_path: Union[str, None] = None) -> object:
        """Show the DAG. Return the graph object for the given inputs to execute."""

        return self.dr.visualize_execution(
            final_vars=self.outputs, output_file_path=output_file_path, render_kwargs={"view": view}
        )

    def list_parameters(self):
        """List all available parameters."""

        return self.dr.list_available_variables()
