import naturf.nodes as nodes
import naturf.output as output
import time

from hamilton import driver

if __name__ == "__main__":
    path = "naturf/data/C-5.shp"
    config = {}
    dr = driver.Driver(config, nodes, output)

    output_columns = ["write_binary", "write_index"]
    inputs = {"input_shapefile": path}

    start_time = time.perf_counter()

    df = dr.execute(output_columns, inputs=inputs)
    dr.visualize_execution(
        output_columns,
        inputs=inputs,
        output_file_path="notebooks/dag",
        render_kwargs={"format": "png"},
    )

    end_time = time.perf_counter()
    print(f"Ran naturf using hamilton in {end_time - start_time:0.2f} seconds.")
