from typing import List, Union

import pandas as pd
from hamilton import driver

import naturf.nodes as nodes


class Model:
    def __init__(self, inputs: dict, outputs: List[str], **kwargs):
        # dictionary of parameter inputs required to construct the DAG
        self.inputs = inputs

        # desired output parameters
        self.outputs = outputs

        # instantiate driver with function definitions
        self.dr = driver.Driver(self.inputs, nodes)

    def execute(self) -> pd.DataFrame:
        """Run the driver."""

        # generate initial data frame
        df = self.dr.execute(self.outputs)

        return df

    def graph(self, view: bool = True, output_file_path: Union[str, None] = None):
        """Show the DAG."""

        self.dr.visualize_execution(
            final_vars=self.outputs, output_file_path=output_file_path, render_kwargs={"view": view}
        )

    def list_parameters(self):
        """List all available parameters."""

        return self.dr.list_available_variables()
