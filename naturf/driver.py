import os
from typing import List, Union

import pandas as pd
from hamilton import driver, base
from hamilton.plugins import h_tqdm

import naturf.nodes as nodes
import naturf.output as output

DAGWORKS_API_KEY = os.environ.get("DAGWORKS_API_KEY")
HAMILTON_UI_PROJECT_ID = os.environ.get("HAMILTON_UI_PROJECT_ID")
HAMILTON_UI_USERNAME = os.environ.get("HAMILTON_UI_USERNAME")
ENV = os.environ.get("ENV", "dev")


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
        # use the hosted version (there's a free tier) of the Hamilton UI to log telemetry to.
        if DAGWORKS_API_KEY and HAMILTON_UI_USERNAME and HAMILTON_UI_PROJECT_ID:
            try:
                from dagworks import adapters
            except ImportError:
                # dagworks-sdk not installed
                pass
            else:
                hamilton_adapters.append(  # pragma: no cover
                    adapters.DAGWorksTracker(
                        project_id=int(HAMILTON_UI_PROJECT_ID),
                        api_key=DAGWORKS_API_KEY,
                        username=HAMILTON_UI_USERNAME,
                        dag_name="naturf-dag",
                        tags={"env": ENV},
                    )
                )
        # use the self-hosted version of the Hamilton UI to log telemetry to.
        elif HAMILTON_UI_USERNAME and HAMILTON_UI_PROJECT_ID:
            try:
                from hamilton_sdk import adapters
            except ImportError:
                # hamilton-sdk not installed
                pass
            else:
                hamilton_adapters.append(  # pragma: no cover
                    adapters.HamiltonTracker(
                        project_id=int(HAMILTON_UI_PROJECT_ID),
                        username=HAMILTON_UI_USERNAME,
                        dag_name="naturf-dag",
                        tags={"env": ENV},
                    )
                )

        # instantiate driver with function definitions & adapters
        self.dr = (
            driver.Builder()
            .with_config({})
            .with_modules(nodes, output)
            .with_adapters(*hamilton_adapters)
            .build()
        )

    def execute(self) -> pd.DataFrame:
        """Run the driver."""

        # generate initial data frame
        df = self.dr.execute(self.outputs, inputs=self.inputs)

        return df

    def graph(self, view: bool = True, output_file_path: Union[str, None] = None) -> object:
        """Show the DAG. Return the graph object for the given inputs to execute."""

        return self.dr.visualize_execution(
            final_vars=self.outputs,
            inputs=self.inputs,
            output_file_path=output_file_path,
            render_kwargs={"view": view},
        )

    def list_parameters(self):
        """List all available parameters."""

        return self.dr.list_available_variables()
